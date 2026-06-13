"""Tests for alert email delivery via Resend."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.schemas.alert import AlertChannelConfig, AlertRuleCreate, AlertTestEmailRequest
from app.services.alert_email_template import AlertEmailContext, compute_severity
from app.services.alert_service import AlertService
from app.services.email_service import EmailService, validate_recipient_email


def test_validate_recipient_email():
    assert validate_recipient_email("User@Example.com") == "user@example.com"
    with pytest.raises(ValueError):
        validate_recipient_email("not-an-email")


def test_resend_configured_from_settings():
    assert isinstance(settings.resend_configured, bool)


def test_compute_severity():
    assert compute_severity("provider_outage", 1, 1) == "CRITICAL"
    assert compute_severity("error_rate", 10, 5) == "WARNING"
    assert compute_severity("token_threshold", 100, 200) == "INFO"


def test_alert_email_context_subjects():
    ctx = AlertEmailContext(
        rule_name="High errors",
        metric="error_rate",
        operator="gt",
        threshold=5,
        current_value=12,
        message="Error rate is high",
        severity="WARNING",
        triggered_at=datetime.now(timezone.utc),
        environment="production",
        agent_name="Support Bot",
        provider="openai",
        model="gpt-4o",
        is_test=False,
        dashboard_url="http://localhost:3000/dashboard",
    )
    assert ctx.subject.startswith("🚨 ")
    assert "Traceplane Alert" in ctx.subject
    assert "View in Traceplane" in ctx.plain_text()
    assert "Traceplane" in ctx.html()
    assert "WARNING" in ctx.html()

    test_ctx = AlertEmailContext(
        rule_name="High errors",
        metric="error_rate",
        operator="gt",
        threshold=5,
        current_value=12,
        message="Error rate is high",
        severity="WARNING",
        triggered_at=datetime.now(timezone.utc),
        environment=None,
        agent_name=None,
        provider=None,
        model=None,
        is_test=True,
        dashboard_url="http://localhost:3000/dashboard",
    )
    assert test_ctx.subject.startswith("[TEST] ")


@pytest.mark.asyncio
async def test_send_test_email_success():
    session = MagicMock()
    mock_rule = MagicMock()
    mock_rule.id = uuid.uuid4()
    mock_rule.workspace_id = uuid.uuid4()
    mock_rule.name = "High errors"
    mock_rule.metric = "error_rate"
    mock_rule.operator = "gt"
    mock_rule.threshold = 5.0
    mock_rule.window_minutes = 60

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_rule
    session.execute = AsyncMock(return_value=mock_result)
    session.add = MagicMock()
    session.commit = AsyncMock()

    alert_svc = AlertService(session)
    with (
        patch.object(alert_svc, "_compute_metric", AsyncMock(return_value=(3.5, "Error rate is 3.5%"))),
        patch.object(
            alert_svc,
            "_fetch_trace_context",
            AsyncMock(return_value={"agent_name": None, "provider": None, "model": None, "environment": None}),
        ),
        patch("app.services.alert_service.email_service") as mock_email,
    ):
        mock_email.is_configured = True
        mock_email.send_email = AsyncMock(
            return_value={
                "success": True,
                "recipient": "test@gmail.com",
                "response": {"id": "re_123"},
            }
        )
        result = await alert_svc.send_test_email(uuid.uuid4(), "test@gmail.com")
        assert result.success is True
        assert result.resend_id == "re_123"
        call_kwargs = mock_email.send_email.await_args.kwargs
        assert call_kwargs.get("html") is not None or len(mock_email.send_email.await_args.args) >= 3
        subject = mock_email.send_email.await_args.args[1]
        assert subject.startswith("[TEST] ")
        sent_body = mock_email.send_email.await_args.args[2]
        assert "Traceplane Alert:" in sent_body
        assert "Severity:" in sent_body


@pytest.mark.asyncio
async def test_send_test_email_failure_surfaces_error():
    session = MagicMock()
    mock_rule = MagicMock()
    mock_rule.id = uuid.uuid4()
    mock_rule.workspace_id = uuid.uuid4()
    mock_rule.name = "High errors"
    mock_rule.metric = "error_rate"
    mock_rule.operator = "gt"
    mock_rule.threshold = 5.0
    mock_rule.window_minutes = 60

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_rule
    session.execute = AsyncMock(return_value=mock_result)
    session.add = MagicMock()
    session.commit = AsyncMock()

    alert_svc = AlertService(session)
    with (
        patch.object(alert_svc, "_compute_metric", AsyncMock(return_value=(3.5, "Error rate is 3.5%"))),
        patch.object(
            alert_svc,
            "_fetch_trace_context",
            AsyncMock(return_value={"agent_name": None, "provider": None, "model": None, "environment": None}),
        ),
        patch("app.services.alert_service.email_service") as mock_email,
    ):
        mock_email.is_configured = True
        mock_email.send_email = AsyncMock(
            return_value={
                "success": False,
                "recipient": "test@gmail.com",
                "error": "API error",
            }
        )
        result = await alert_svc.send_test_email(uuid.uuid4(), "test@gmail.com")
        assert result.success is False
        assert "API error" in (result.error or "")


@pytest.mark.asyncio
async def test_email_service_retries_then_succeeds():
    svc = EmailService()
    svc._configured = True
    calls = {"n": 0}

    def flaky_send(to, subject, text, html=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("temporary")
        return {"id": "re_retry_ok"}

    with patch.object(svc, "_send_sync", side_effect=flaky_send):
        result = await svc.send_email("retry@gmail.com", "subj", "body", html="<p>hi</p>")
        assert result["success"] is True
        assert calls["n"] == 2


def test_alert_rule_create_schema():
    data = AlertRuleCreate(
        name="High errors",
        metric="error_rate",
        threshold=5,
        channels=[AlertChannelConfig(type="email", target="ops@gmail.com")],
    )
    assert data.channels[0].type == "email"
    assert data.cooldown_minutes == 15


def test_alert_compare_operators():
    assert AlertService._compare("gt", 10, 5) is True
    assert AlertService._compare("gt", 5, 5) is False
    assert AlertService._compare("gte", 5, 5) is True


def test_alert_test_email_request_schema():
    req = AlertTestEmailRequest(recipient="alert@gmail.com")
    assert req.recipient == "alert@gmail.com"
