"use client"

import { useState, useEffect } from "react"
import { Bell, Check, Clock, History, Loader2, Mail, Plus, Trash2 } from "lucide-react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { AppLayout } from "@/components/layout/app-layout"
import { Badge, Modal, PageHeader, StatusBadge, Table, TableCell, TableHead, TableHeader, TableRow } from "@/components/shared"
import { alertsService } from "@/services/api"
import { friendlyErrorMessage } from "@/lib/friendly-error"
import type { AlertEvent, AlertRule, AlertChannelConfig } from "@/types"

const METRICS = [
  { id: "cost_spike", label: "Cost spike" },
  { id: "error_rate", label: "Error rate (%)" },
  { id: "latency_threshold", label: "Avg latency (ms)" },
  { id: "token_threshold", label: "Token usage" },
  { id: "provider_outage", label: "Provider outages" },
]

const ALERT_EMAIL_KEY = "traceplane_alert_email"

function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "Never"
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function channelLabel(channels: AlertChannelConfig[]): string {
  if (!channels.length) return "None"
  const types = [...new Set(channels.map((c) => c.type))]
  return types.join(", ")
}

function severityVariant(severity?: string | null): "default" | "primary" | "warning" | "danger" {
  const s = severity?.toUpperCase()
  if (s === "CRITICAL") return "danger"
  if (s === "WARNING") return "warning"
  if (s === "INFO") return "primary"
  return "default"
}

export default function AlertsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [testEmail, setTestEmail] = useState("")
  const [testDone, setTestDone] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)
  const [sendingTest, setSendingTest] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [historyRule, setHistoryRule] = useState<AlertRule | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem(ALERT_EMAIL_KEY)
    if (saved) setTestEmail(saved)
  }, [])

  const { data: rules = [], isLoading, error, refetch } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => alertsService.list(),
  })

  const { data: recentEvents = [], isLoading: eventsLoading } = useQuery({
    queryKey: ["alert-events"],
    queryFn: () => alertsService.listEvents(undefined, 20),
  })

  const { data: ruleEvents = [], isLoading: ruleEventsLoading } = useQuery({
    queryKey: ["alert-events", historyRule?.id],
    queryFn: () => alertsService.listRuleEvents(historyRule!.id, 50),
    enabled: !!historyRule,
  })

  async function handleDelete(id: string) {
    setBusy(true)
    setDeleteError(null)
    try {
      await alertsService.delete(id)
      await queryClient.invalidateQueries({ queryKey: ["alerts"] })
      await queryClient.invalidateQueries({ queryKey: ["alert-events"] })
    } catch (err) {
      setDeleteError(friendlyErrorMessage(err instanceof Error ? err.message : String(err)))
    } finally {
      setBusy(false)
    }
  }

  function handleTestEmailChange(value: string) {
    setTestEmail(value)
    if (value.trim()) localStorage.setItem(ALERT_EMAIL_KEY, value.trim())
  }

  async function handleTestEmail() {
    const recipient = testEmail.trim()
    if (!recipient) return
    setSendingTest(true)
    setTestDone(false)
    setTestError(null)
    try {
      await alertsService.testEmail(recipient)
      setTestDone(true)
      await queryClient.invalidateQueries({ queryKey: ["alert-events"] })
    } catch (err) {
      setTestError(friendlyErrorMessage(err instanceof Error ? err.message : String(err)))
    } finally {
      setSendingTest(false)
    }
  }

  return (
    <AppLayout>
      <div className="page-container max-w-5xl">
        <PageHeader title="Alerts" subtitle="Production-grade monitoring for cost, errors, latency, tokens, and provider health">
          <button type="button" className="btn-primary inline-flex items-center gap-1.5" onClick={() => setShowForm((v) => !v)}>
            <Plus className="w-4 h-4" /> New rule
          </button>
        </PageHeader>

        <div className="rounded-lg border border-hairline bg-surface-1 p-4 mb-4">
          <h3 className="text-body-sm font-medium text-ink mb-1">Send test email</h3>
          <p className="text-caption text-ink-subtle mb-3">Sends a sample HTML alert marked [TEST] via Resend.</p>
          <div className="flex flex-wrap gap-2">
            <input
              className="input flex-1 min-w-[220px] text-body-sm"
              type="email"
              placeholder="you@example.com"
              value={testEmail}
              onChange={(e) => handleTestEmailChange(e.target.value)}
            />
            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-1.5 text-body-sm"
              disabled={sendingTest || !testEmail.trim()}
              onClick={() => void handleTestEmail()}
            >
              {sendingTest ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
              Send test email
            </button>
          </div>
          {testDone && (
            <p className="text-caption text-success mt-2 inline-flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5" /> Done
            </p>
          )}
          {testError && <p className="text-caption text-danger mt-2">{testError}</p>}
        </div>

        {showForm && (
          <AlertForm
            alertEmail={testEmail.trim()}
            onClose={() => setShowForm(false)}
            onCreated={async () => {
              setShowForm(false)
              await queryClient.invalidateQueries({ queryKey: ["alerts"] })
            }}
          />
        )}

        {deleteError && <p className="text-caption text-danger mb-3">{deleteError}</p>}

        {isLoading && <p className="text-body-sm text-ink-subtle py-8">Loading alert rules…</p>}
        {error && (
          <div className="panel-lift rounded-lg p-6 text-center">
            <p className="text-body-sm text-ink-muted">{friendlyErrorMessage(error instanceof Error ? error.message : String(error))}</p>
            <button type="button" className="btn-secondary mt-3" onClick={() => void refetch()}>Retry</button>
          </div>
        )}

        {!isLoading && !error && rules.length === 0 && (
          <div className="panel-lift rounded-lg p-10 text-center">
            <Bell className="w-8 h-8 text-ink-tertiary mx-auto mb-3" />
            <p className="text-body text-ink-muted mb-1">No alert rules configured</p>
            <p className="text-body-sm text-ink-subtle mb-4">Rules evaluate automatically when SDK telemetry is ingested.</p>
            <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>Create your first alert</button>
          </div>
        )}

        <div className="space-y-3 mt-4">
          {rules.map((rule: AlertRule) => {
            const isTriggered = rule.trigger_count > 0
            const recentlyTriggered =
              rule.last_triggered_at &&
              Date.now() - new Date(rule.last_triggered_at).getTime() < rule.cooldown_minutes * 60_000

            return (
              <div key={rule.id} className="panel-lift rounded-lg p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-body font-medium text-ink">{rule.name}</h3>
                      {!rule.is_active && (
                        <span className="text-[11px] text-ink-tertiary border border-hairline rounded-full px-2 py-0.5">
                          Paused
                        </span>
                      )}
                      {isTriggered && <Badge variant="warning">Triggered</Badge>}
                      {recentlyTriggered && rule.is_active && (
                        <Badge variant="default">Cooldown</Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2 mt-3">
                      <div>
                        <p className="caption-text text-ink-tertiary">Metric</p>
                        <p className="text-body-sm text-ink-muted">{rule.metric.replace(/_/g, " ")}</p>
                      </div>
                      <div>
                        <p className="caption-text text-ink-tertiary">Threshold</p>
                        <p className="text-body-sm text-ink-muted">{rule.operator} {rule.threshold}</p>
                      </div>
                      <div>
                        <p className="caption-text text-ink-tertiary">Notification</p>
                        <p className="text-body-sm text-ink-muted capitalize">{channelLabel(rule.channels)}</p>
                      </div>
                      <div>
                        <p className="caption-text text-ink-tertiary">Last triggered</p>
                        <p className="text-body-sm text-ink-muted inline-flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(rule.last_triggered_at)}
                        </p>
                      </div>
                    </div>
                    <p className="caption-text text-ink-tertiary mt-2">
                      {rule.window_minutes}m window · {rule.cooldown_minutes}m cooldown · fired {rule.trigger_count} times
                    </p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      type="button"
                      className="btn-secondary text-caption inline-flex items-center gap-1"
                      onClick={() => setHistoryRule(rule)}
                    >
                      <History className="w-3.5 h-3.5" /> History
                    </button>
                    <button
                      type="button"
                      className="btn-secondary text-caption inline-flex items-center gap-1"
                      disabled={busy}
                      onClick={() => void handleDelete(rule.id)}
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Delete
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {(recentEvents.length > 0 || eventsLoading) && (
          <div className="mt-8">
            <h2 className="text-body font-medium text-ink mb-3">Recent alert events</h2>
            {eventsLoading ? (
              <p className="text-body-sm text-ink-subtle">Loading events…</p>
            ) : (
              <div className="panel-lift rounded-lg overflow-hidden">
                <Table>
                  <TableHead>
                    <TableHeader>Time</TableHeader>
                    <TableHeader>Rule</TableHeader>
                    <TableHeader>Severity</TableHeader>
                    <TableHeader>Value</TableHeader>
                    <TableHeader>Channel</TableHeader>
                    <TableHeader>Status</TableHeader>
                  </TableHead>
                  <tbody>
                    {recentEvents.map((event: AlertEvent) => (
                      <TableRow key={event.id}>
                        <TableCell>{formatRelativeTime(event.created_at)}</TableCell>
                        <TableCell>
                          <span className="text-ink">{event.rule_name}</span>
                          {event.is_test && <span className="ml-2"><Badge variant="default">TEST</Badge></span>}
                        </TableCell>
                        <TableCell>
                          {event.severity ? (
                            <Badge variant={severityVariant(event.severity)}>{event.severity}</Badge>
                          ) : (
                            "—"
                          )}
                        </TableCell>
                        <TableCell>{event.current_value.toFixed(2)}</TableCell>
                        <TableCell className="capitalize">{event.channel_type}</TableCell>
                        <TableCell>
                          <StatusBadge status={event.delivery_success ? "success" : "failed"} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </tbody>
                </Table>
              </div>
            )}
          </div>
        )}

        <Modal
          open={!!historyRule}
          onClose={() => setHistoryRule(null)}
          title={historyRule ? `Alert history — ${historyRule.name}` : "Alert history"}
        >
          {ruleEventsLoading ? (
            <p className="text-body-sm text-ink-subtle">Loading history…</p>
          ) : ruleEvents.length === 0 ? (
            <p className="text-body-sm text-ink-subtle">No events recorded for this rule yet.</p>
          ) : (
            <div className="space-y-3 max-h-[60vh] overflow-y-auto">
              {ruleEvents.map((event: AlertEvent) => (
                <div key={event.id} className="rounded-lg border border-hairline p-3 bg-surface-2/30">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-body-sm font-medium text-ink">
                      {formatRelativeTime(event.created_at)}
                    </span>
                    <div className="flex items-center gap-2">
                      {event.is_test && <Badge variant="default">TEST</Badge>}
                      {event.severity && <Badge variant={severityVariant(event.severity)}>{event.severity}</Badge>}
                      <StatusBadge status={event.delivery_success ? "success" : "failed"} />
                    </div>
                  </div>
                  <p className="text-caption text-ink-subtle mt-1">{event.message}</p>
                  <p className="caption-text text-ink-tertiary mt-2">
                    {event.metric.replace(/_/g, " ")} · current {event.current_value.toFixed(4)} · threshold {event.operator} {event.threshold}
                  </p>
                  {(event.agent_name || event.provider || event.model) && (
                    <p className="caption-text text-ink-tertiary mt-1">
                      {[event.agent_name, event.provider, event.model].filter(Boolean).join(" · ")}
                    </p>
                  )}
                  {!event.delivery_success && event.delivery_error && (
                    <p className="caption-text text-danger mt-1">{event.delivery_error}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Modal>
      </div>
    </AppLayout>
  )
}

function AlertForm({
  alertEmail,
  onClose,
  onCreated,
}: {
  alertEmail: string
  onClose: () => void
  onCreated: () => Promise<void>
}) {
  const [name, setName] = useState("")
  const [metric, setMetric] = useState("error_rate")
  const [threshold, setThreshold] = useState("5")
  const [windowMinutes, setWindowMinutes] = useState("60")
  const [cooldownMinutes, setCooldownMinutes] = useState("15")
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!alertEmail) {
      setError("Set a notification email in Send test email above first.")
      return
    }
    setBusy(true)
    setError(null)
    const channels: AlertChannelConfig[] = [{ type: "email", target: alertEmail }]
    try {
      await alertsService.create({
        name: name.trim(),
        metric: metric as AlertRule["metric"],
        operator: "gt",
        threshold: parseFloat(threshold),
        window_minutes: parseInt(windowMinutes, 10),
        cooldown_minutes: parseInt(cooldownMinutes, 10),
        channels,
        is_active: true,
      })
      await onCreated()
    } catch (err) {
      setError(friendlyErrorMessage(err instanceof Error ? err.message : String(err)))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="panel-lift rounded-lg p-5 mb-4 space-y-3">
      <h3 className="text-body font-medium text-ink">New alert rule</h3>
      <p className="text-caption text-ink-subtle">
        Notifications send to <span className="text-ink-muted">{alertEmail || "— set email above"}</span> via email.
      </p>
      <input className="input w-full" placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} required />
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <select className="input" value={metric} onChange={(e) => setMetric(e.target.value)}>
          {METRICS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
        </select>
        <input className="input" type="number" step="any" placeholder="Threshold" value={threshold} onChange={(e) => setThreshold(e.target.value)} required />
        <input className="input" type="number" placeholder="Window (min)" value={windowMinutes} onChange={(e) => setWindowMinutes(e.target.value)} required />
        <input className="input" type="number" placeholder="Cooldown (min)" value={cooldownMinutes} onChange={(e) => setCooldownMinutes(e.target.value)} required />
      </div>
      {error && <p className="caption-text text-danger">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" className="btn-primary inline-flex items-center gap-1.5" disabled={busy}>
          {busy && <Loader2 className="w-4 h-4 animate-spin" />} Create rule
        </button>
        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
      </div>
    </form>
  )
}
