from dataclasses import dataclass
from datetime import datetime
from html import escape


SEVERITY_STYLES = {
    "INFO": {"bg": "#1e3a5f", "text": "#93c5fd", "label": "INFO"},
    "WARNING": {"bg": "#422006", "text": "#fcd34d", "label": "WARNING"},
    "CRITICAL": {"bg": "#450a0a", "text": "#fca5a5", "label": "CRITICAL"},
}


@dataclass(frozen=True)
class AlertEmailContext:
    rule_name: str
    metric: str
    operator: str
    threshold: float
    current_value: float
    message: str
    severity: str
    triggered_at: datetime
    environment: str | None
    agent_name: str | None
    provider: str | None
    model: str | None
    is_test: bool
    dashboard_url: str

    @property
    def subject(self) -> str:
        prefix = "[TEST] " if self.is_test else "🚨 "
        return f"{prefix}Traceplane Alert: {self.rule_name}"

    def plain_text(self) -> str:
        lines = [
            f"Traceplane Alert: {self.rule_name}",
            f"Severity: {self.severity}",
            f"Metric: {self.metric}",
            f"Current: {self.current_value:.4f}",
            f"Threshold: {self.operator} {self.threshold}",
            f"Triggered: {self.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]
        if self.environment:
            lines.append(f"Environment: {self.environment}")
        if self.agent_name:
            lines.append(f"Agent: {self.agent_name}")
        if self.provider:
            lines.append(f"Provider: {self.provider}")
        if self.model:
            lines.append(f"Model: {self.model}")
        lines.append("")
        lines.append(self.message)
        lines.append("")
        lines.append(f"View in Traceplane: {self.dashboard_url}")
        if self.is_test:
            lines.insert(0, "[TEST] This is a test alert email from Traceplane.")
        return "\n".join(lines)

    def html(self) -> str:
        sev = SEVERITY_STYLES.get(self.severity, SEVERITY_STYLES["INFO"])
        test_banner = ""
        if self.is_test:
            test_banner = (
                '<tr><td style="padding:0 24px 16px;">'
                '<div style="background:#1a1a2e;border:1px solid #3e3e44;border-radius:6px;'
                'padding:10px 14px;font-size:12px;color:#8a8f98;">'
                "[TEST] This is a test alert email from Traceplane."
                "</div></td></tr>"
            )

        def row(label: str, value: str) -> str:
            return (
                f'<tr><td style="padding:8px 0;color:#8a8f98;font-size:13px;width:140px;">{escape(label)}</td>'
                f'<td style="padding:8px 0;color:#f7f8f8;font-size:13px;font-weight:500;">{escape(value)}</td></tr>'
            )

        optional_rows = ""
        if self.environment:
            optional_rows += row("Environment", self.environment)
        if self.agent_name:
            optional_rows += row("Agent", self.agent_name)
        if self.provider:
            optional_rows += row("Provider", self.provider)
        if self.model:
            optional_rows += row("Model", self.model)

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#010102;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#010102;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" style="max-width:560px;background:#0f1011;border:1px solid #23252a;border-radius:8px;overflow:hidden;">
        <tr><td style="padding:24px 24px 16px;border-bottom:1px solid #23252a;">
          <table width="100%"><tr>
            <td><span style="font-size:18px;font-weight:600;color:#f7f8f8;letter-spacing:-0.3px;">Traceplane</span></td>
            <td align="right"><span style="display:inline-block;padding:4px 10px;border-radius:999px;background:{sev['bg']};color:{sev['text']};font-size:11px;font-weight:600;letter-spacing:0.5px;">{sev['label']}</span></td>
          </tr></table>
        </td></tr>
        {test_banner}
        <tr><td style="padding:20px 24px 8px;">
          <h1 style="margin:0;font-size:20px;font-weight:600;color:#f7f8f8;letter-spacing:-0.4px;">{escape(self.rule_name)}</h1>
          <p style="margin:8px 0 0;font-size:13px;color:#8a8f98;">{escape(self.message)}</p>
        </td></tr>
        <tr><td style="padding:8px 24px 20px;">
          <table width="100%" style="border-top:1px solid #23252a;padding-top:12px;">
            {row("Metric", self.metric.replace("_", " "))}
            {row("Current value", f"{self.current_value:.4f}")}
            {row("Threshold", f"{self.operator} {self.threshold}")}
            {row("Triggered", self.triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC"))}
            {optional_rows}
          </table>
        </td></tr>
        <tr><td style="padding:0 24px 24px;">
          <a href="{escape(self.dashboard_url)}" style="display:inline-block;background:#5e6ad2;color:#ffffff;text-decoration:none;padding:10px 18px;border-radius:6px;font-size:14px;font-weight:500;">View in Traceplane</a>
        </td></tr>
        <tr><td style="padding:16px 24px;border-top:1px solid #23252a;">
          <p style="margin:0;font-size:11px;color:#62666d;">Traceplane · AI agent observability</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def compute_severity(metric: str, current: float, threshold: float) -> str:
    if metric == "provider_outage" and current >= 1:
        return "CRITICAL"
    if threshold <= 0:
        return "INFO"
    ratio = current / threshold
    if metric == "error_rate":
        if current >= 50 or ratio >= 3:
            return "CRITICAL"
        if ratio >= 1.5:
            return "WARNING"
        return "INFO"
    if ratio >= 3:
        return "CRITICAL"
    if ratio >= 1.5:
        return "WARNING"
    return "INFO"
