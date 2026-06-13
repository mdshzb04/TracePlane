import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


AlertMetric = Literal[
    "cost_spike",
    "error_rate",
    "latency_threshold",
    "token_threshold",
    "provider_outage",
]

AlertOperator = Literal["gt", "gte", "lt", "lte"]

AlertChannelType = Literal["slack", "discord", "webhook", "email"]


class AlertChannelConfig(BaseModel):
    type: AlertChannelType
    target: str = Field(description="Webhook URL, email address, or channel ID")
    name: Optional[str] = None


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    metric: AlertMetric
    operator: AlertOperator = "gt"
    threshold: float = Field(gt=0)
    window_minutes: int = Field(default=60, ge=5, le=1440)
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)
    channels: list[AlertChannelConfig] = Field(min_length=1)
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    metric: Optional[AlertMetric] = None
    operator: Optional[AlertOperator] = None
    threshold: Optional[float] = Field(default=None, gt=0)
    window_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    cooldown_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    channels: Optional[list[AlertChannelConfig]] = None
    is_active: Optional[bool] = None


class AlertRuleRead(BaseModel):
    id: uuid.UUID
    name: str
    metric: str
    operator: str
    threshold: float
    window_minutes: int
    cooldown_minutes: int
    channels: list[dict[str, Any]]
    is_active: bool
    trigger_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertDeliveryResult(BaseModel):
    channel_type: str
    target: str
    success: bool
    error: Optional[str] = None
    resend_id: Optional[str] = None
    resend_response: Optional[dict[str, Any]] = None


class AlertEvaluationResult(BaseModel):
    rule_id: uuid.UUID
    triggered: bool
    current_value: float
    message: str
    deliveries: list[AlertDeliveryResult] = Field(default_factory=list)


class AlertTestEmailRequest(BaseModel):
    recipient: str = Field(min_length=3, max_length=320)


class AlertTestEmailResponse(BaseModel):
    success: bool
    recipient: str
    message: str
    resend_id: Optional[str] = None
    resend_response: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class AlertEventRead(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    rule_name: str
    metric: str
    operator: str
    threshold: float
    current_value: float
    message: str
    channel_type: str
    channel_target: str
    delivery_success: bool
    delivery_error: Optional[str] = None
    resend_id: Optional[str] = None
    severity: Optional[str] = None
    agent_name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    environment: Optional[str] = None
    is_test: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
