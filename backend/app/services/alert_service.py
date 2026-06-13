import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert_event import AlertEvent
from app.models.alert_rule import AlertRule
from app.repositories.analytics import AnalyticsRepository
from app.schemas.alert import (
    AlertDeliveryResult,
    AlertEvaluationResult,
    AlertEventRead,
    AlertRuleCreate,
    AlertRuleRead,
    AlertRuleUpdate,
    AlertTestEmailResponse,
)
from app.services.alert_email_template import AlertEmailContext, compute_severity
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

MIN_SAMPLES = {
    "error_rate": 5,
    "cost_spike": 3,
    "latency_threshold": 3,
    "token_threshold": 1,
    "provider_outage": 1,
}


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics = AnalyticsRepository(db)

    async def list_rules(self, workspace_id: uuid.UUID) -> list[AlertRuleRead]:
        stmt = (
            select(AlertRule)
            .where(AlertRule.workspace_id == workspace_id)
            .order_by(AlertRule.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [AlertRuleRead.model_validate(r) for r in result.scalars().all()]

    async def list_events(
        self,
        workspace_id: uuid.UUID,
        *,
        rule_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> list[AlertEventRead]:
        stmt = (
            select(AlertEvent, AlertRule.operator, AlertRule.threshold)
            .join(AlertRule, AlertEvent.rule_id == AlertRule.id)
            .where(AlertEvent.workspace_id == workspace_id)
            .order_by(AlertEvent.created_at.desc())
            .limit(min(limit, 100))
        )
        if rule_id:
            stmt = stmt.where(AlertEvent.rule_id == rule_id)
        result = await self.db.execute(stmt)
        events: list[AlertEventRead] = []
        for event, operator, threshold in result.all():
            events.append(
                AlertEventRead(
                    id=event.id,
                    rule_id=event.rule_id,
                    rule_name=event.rule_name,
                    metric=event.metric,
                    operator=operator,
                    threshold=threshold,
                    current_value=event.current_value,
                    message=event.message,
                    channel_type=event.channel_type,
                    channel_target=event.recipient or "",
                    delivery_success=event.status == "sent",
                    delivery_error=event.error,
                    resend_id=event.resend_id,
                    severity=event.severity,
                    agent_name=event.agent_name,
                    provider=event.provider,
                    model=event.model,
                    environment=event.environment,
                    is_test=event.is_test,
                    created_at=event.created_at,
                )
            )
        return events

    async def create_rule(
        self,
        workspace_id: uuid.UUID,
        data: AlertRuleCreate,
        created_by: uuid.UUID,
    ) -> AlertRuleRead:
        rule = AlertRule(
            workspace_id=workspace_id,
            name=data.name,
            metric=data.metric,
            operator=data.operator,
            threshold=data.threshold,
            window_minutes=data.window_minutes,
            cooldown_minutes=data.cooldown_minutes,
            channels=[c.model_dump() for c in data.channels],
            is_active=data.is_active,
            created_by=created_by,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return AlertRuleRead.model_validate(rule)

    async def update_rule(
        self,
        workspace_id: uuid.UUID,
        rule_id: uuid.UUID,
        data: AlertRuleUpdate,
    ) -> AlertRuleRead:
        rule = await self._get_rule(workspace_id, rule_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "channels" and value is not None:
                value = [c if isinstance(c, dict) else c.model_dump() for c in value]
            setattr(rule, field, value)
        await self.db.commit()
        await self.db.refresh(rule)
        return AlertRuleRead.model_validate(rule)

    async def delete_rule(self, workspace_id: uuid.UUID, rule_id: uuid.UUID) -> None:
        rule = await self._get_rule(workspace_id, rule_id)
        await self.db.execute(delete(AlertEvent).where(AlertEvent.rule_id == rule.id))
        await self.db.delete(rule)
        await self.db.commit()
        logger.info("Deleted alert rule %s and associated events", rule_id)

    async def evaluate_on_ingest(self, workspace_id: uuid.UUID) -> None:
        stmt = select(AlertRule).where(
            AlertRule.workspace_id == workspace_id,
            AlertRule.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        for rule in result.scalars().all():
            try:
                await self._evaluate_and_notify(rule)
            except Exception:
                logger.exception("Alert evaluation failed for rule %s", rule.id)

    async def evaluate_rule(
        self, workspace_id: uuid.UUID, rule_id: uuid.UUID
    ) -> AlertEvaluationResult:
        rule = await self._get_rule(workspace_id, rule_id)
        return await self._evaluate_and_notify(rule)

    async def evaluate_all(self, workspace_id: uuid.UUID) -> list[AlertEvaluationResult]:
        stmt = select(AlertRule).where(
            AlertRule.workspace_id == workspace_id,
            AlertRule.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        return [await self._evaluate_and_notify(r) for r in result.scalars().all()]

    async def send_test_email(
        self, workspace_id: uuid.UUID, recipient: str
    ) -> AlertTestEmailResponse:
        if not email_service.is_configured:
            return AlertTestEmailResponse(
                success=False,
                recipient=recipient,
                message="Resend is not configured",
                error="Set RESEND_API_KEY in backend .env",
            )

        stmt = (
            select(AlertRule)
            .where(AlertRule.workspace_id == workspace_id, AlertRule.is_active.is_(True))
            .order_by(AlertRule.created_at.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError("Create at least one active alert rule before sending a test email")

        current, message = await self._compute_metric(rule)
        context = await self._build_email_context(
            rule, current, message, is_test=True
        )
        send_result = await email_service.send_email(
            recipient,
            context.subject,
            context.plain_text(),
            html=context.html(),
        )
        success = send_result.get("success", False)
        response = send_result.get("response") or {}
        resend_id = response.get("id") if isinstance(response, dict) else None

        await self._record_event(
            rule=rule,
            current=current,
            message=message,
            channel_type="email",
            channel_target=recipient,
            success=success,
            error=send_result.get("error"),
            resend_id=resend_id,
            resend_response=response if isinstance(response, dict) else None,
            context=context,
            is_test=True,
        )

        if success:
            return AlertTestEmailResponse(
                success=True,
                recipient=recipient,
                message="Test email sent",
                resend_id=resend_id,
                resend_response=response if isinstance(response, dict) else None,
            )
        return AlertTestEmailResponse(
            success=False,
            recipient=recipient,
            message="Failed to send test email",
            error=send_result.get("error"),
        )

    async def _get_rule(self, workspace_id: uuid.UUID, rule_id: uuid.UUID) -> AlertRule:
        stmt = select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.workspace_id == workspace_id,
        )
        result = await self.db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError("Alert rule not found")
        return rule

    async def _evaluate_and_notify(self, rule: AlertRule) -> AlertEvaluationResult:
        current, message = await self._compute_metric(rule)
        sufficient = await self._has_sufficient_data(rule)
        triggered = sufficient and self._compare(rule.operator, current, rule.threshold)
        deliveries: list[AlertDeliveryResult] = []

        if triggered:
            logger.info(
                "Alert triggered rule_id=%s name=%s metric=%s current=%.4f threshold=%s %s",
                rule.id,
                rule.name,
                rule.metric,
                current,
                rule.operator,
                rule.threshold,
            )
            if self._should_notify(rule):
                context = await self._build_email_context(rule, current, message, is_test=False)
                deliveries = await self._dispatch_notifications(rule, current, message, context)
                rule.trigger_count += 1
                rule.last_triggered_at = datetime.now(timezone.utc)
                await self.db.commit()
            else:
                logger.info(
                    "Alert suppressed by cooldown rule_id=%s cooldown_minutes=%s last_triggered=%s",
                    rule.id,
                    rule.cooldown_minutes,
                    rule.last_triggered_at,
                )
        else:
            if not sufficient:
                message = f"{message} (insufficient sample size — alert suppressed)"

        return AlertEvaluationResult(
            rule_id=rule.id,
            triggered=triggered,
            current_value=current,
            message=message,
            deliveries=deliveries,
        )

    async def _has_sufficient_data(self, rule: AlertRule) -> bool:
        min_n = MIN_SAMPLES.get(rule.metric, 1)
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=rule.window_minutes)
        stats = await self.analytics.execution_stats(
            workspace_id=rule.workspace_id,
            start_date=start,
            end_date=end,
        )
        return int(stats.get("total", 0)) >= min_n

    async def _compute_metric(self, rule: AlertRule) -> tuple[float, str]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=rule.window_minutes)

        if rule.metric == "error_rate":
            stats = await self.analytics.execution_stats(
                workspace_id=rule.workspace_id,
                start_date=start,
                end_date=end,
            )
            total = int(stats.get("total", 0))
            failed = int(stats.get("failed", 0))
            rate = (failed / total * 100) if total > 0 else 0.0
            return rate, f"Error rate is {rate:.1f}% over the last {rule.window_minutes}m ({failed}/{total} failed)"

        if rule.metric == "cost_spike":
            stats = await self.analytics.execution_stats(
                workspace_id=rule.workspace_id,
                start_date=start,
                end_date=end,
            )
            cost = float(stats.get("total_cost", 0))
            return cost, f"Total cost is ${cost:.4f} over the last {rule.window_minutes}m"

        if rule.metric == "latency_threshold":
            stats = await self.analytics.execution_stats(
                workspace_id=rule.workspace_id,
                start_date=start,
                end_date=end,
            )
            avg_ms = float(stats.get("avg_latency_ms", 0))
            return avg_ms, f"Average latency is {avg_ms:.0f}ms over the last {rule.window_minutes}m"

        if rule.metric == "token_threshold":
            stats = await self.analytics.execution_stats(
                workspace_id=rule.workspace_id,
                start_date=start,
                end_date=end,
            )
            tokens = int(stats.get("total_tokens", 0))
            return float(tokens), f"Token usage is {tokens:,} over the last {rule.window_minutes}m"

        if rule.metric == "provider_outage":
            outages = await self.analytics.provider_outage_count(
                workspace_id=rule.workspace_id,
                start_date=start,
                end_date=end,
            )
            return float(outages), f"{outages} provider outage(s) detected in the last {rule.window_minutes}m"

        return 0.0, "Unknown metric"

    @staticmethod
    def _compare(operator: str, current: float, threshold: float) -> bool:
        if operator == "gt":
            return current > threshold
        if operator == "gte":
            return current >= threshold
        if operator == "lt":
            return current < threshold
        if operator == "lte":
            return current <= threshold
        return False

    def _should_notify(self, rule: AlertRule) -> bool:
        if not rule.last_triggered_at:
            return True
        cooldown = timedelta(minutes=rule.cooldown_minutes)
        elapsed = datetime.now(timezone.utc) - rule.last_triggered_at
        return elapsed >= cooldown

    async def _fetch_trace_context(self, rule: AlertRule) -> dict[str, Optional[str]]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=rule.window_minutes)
        recent = await self.analytics.recent_executions(
            workspace_id=rule.workspace_id,
            start_date=start,
            end_date=end,
            limit=1,
        )
        if not recent:
            return {"agent_name": None, "provider": None, "model": None, "environment": None}
        row = recent[0]
        env = row.get("environment")
        if not env and row.get("agent_id"):
            env = await self._agent_environment(row["agent_id"])
        return {
            "agent_name": row.get("agent_name"),
            "provider": row.get("provider"),
            "model": row.get("model"),
            "environment": env,
        }

    async def _agent_environment(self, agent_id: uuid.UUID) -> Optional[str]:
        from app.models.agent import Agent

        stmt = select(Agent.environment).where(Agent.id == agent_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _build_email_context(
        self,
        rule: AlertRule,
        current: float,
        message: str,
        *,
        is_test: bool,
    ) -> AlertEmailContext:
        ctx = await self._fetch_trace_context(rule)
        severity = compute_severity(rule.metric, current, rule.threshold)
        return AlertEmailContext(
            rule_name=rule.name,
            metric=rule.metric,
            operator=rule.operator,
            threshold=rule.threshold,
            current_value=current,
            message=message,
            severity=severity,
            triggered_at=datetime.now(timezone.utc),
            environment=ctx.get("environment"),
            agent_name=ctx.get("agent_name"),
            provider=ctx.get("provider"),
            model=ctx.get("model"),
            is_test=is_test,
            dashboard_url=f"{settings.FRONTEND_URL.rstrip('/')}/dashboard",
        )

    async def _dispatch_notifications(
        self,
        rule: AlertRule,
        current: float,
        message: str,
        context: AlertEmailContext,
    ) -> list[AlertDeliveryResult]:
        deliveries: list[AlertDeliveryResult] = []
        for channel in rule.channels or []:
            ch_type = channel.get("type", "")
            target = channel.get("target", "")
            if ch_type == "email":
                result = await self._send_email_alert(target, context)
                deliveries.append(result)
                await self._record_event(
                    rule=rule,
                    current=current,
                    message=message,
                    channel_type=ch_type,
                    channel_target=target,
                    success=result.success,
                    error=result.error,
                    resend_id=result.resend_id,
                    resend_response=result.resend_response,
                    context=context,
                    is_test=False,
                )
            else:
                logger.info(
                    "Skipping non-email channel type=%s target=%s (not yet implemented)",
                    ch_type,
                    target,
                )
        return deliveries

    async def _send_email_alert(
        self, to: str, context: AlertEmailContext
    ) -> AlertDeliveryResult:
        if not email_service.is_configured:
            return AlertDeliveryResult(
                channel_type="email",
                target=to,
                success=False,
                error="Resend is not configured — set RESEND_API_KEY in backend .env",
            )
        send_result = await email_service.send_email(
            to,
            context.subject,
            context.plain_text(),
            html=context.html(),
        )
        success = send_result.get("success", False)
        response = send_result.get("response") or {}
        resend_id = response.get("id") if isinstance(response, dict) else None
        if success:
            logger.info(
                "Alert email delivered to %s resend_id=%s rule=%s",
                to,
                resend_id,
                context.rule_name,
            )
        else:
            logger.error(
                "Alert email failed to %s rule=%s error=%s",
                to,
                context.rule_name,
                send_result.get("error"),
            )
        return AlertDeliveryResult(
            channel_type="email",
            target=to,
            success=success,
            error=send_result.get("error"),
            resend_id=resend_id,
            resend_response=response if isinstance(response, dict) else None,
        )

    async def _record_event(
        self,
        *,
        rule: AlertRule,
        current: float,
        message: str,
        channel_type: str,
        channel_target: str,
        success: bool,
        error: Optional[str],
        resend_id: Optional[str],
        resend_response: Optional[dict[str, Any]],
        context: AlertEmailContext,
        is_test: bool,
    ) -> None:
        event = AlertEvent(
            workspace_id=rule.workspace_id,
            rule_id=rule.id,
            rule_name=rule.name,
            metric=rule.metric,
            current_value=current,
            message=message,
            channel_type=channel_type,
            recipient=channel_target,
            status="sent" if success else "failed",
            resend_id=resend_id,
            error=error,
            resend_response=resend_response,
            severity=context.severity,
            agent_name=context.agent_name,
            provider=context.provider,
            model=context.model,
            environment=context.environment,
            is_test=is_test,
        )
        self.db.add(event)
        await self.db.commit()
        logger.info(
            "Alert event recorded rule_id=%s channel=%s success=%s resend_id=%s is_test=%s",
            rule.id,
            channel_type,
            success,
            resend_id,
            is_test,
        )
