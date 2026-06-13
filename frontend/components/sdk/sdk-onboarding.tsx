"use client"

import { useEffect, useMemo, useState, type ReactNode } from "react"
import Link from "next/link"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Copy, ExternalLink, Loader2, Send } from "lucide-react"
import { PageHeader } from "@/components/shared"
import { CopyToast } from "@/components/sdk/sdk-copy-toast"
import { SdkProviderStrip } from "@/components/sdk/sdk-provider-strip"
import { SdkSetupProgress } from "@/components/sdk/sdk-setup-progress"
import { apiKeysService, analyticsService, providersService } from "@/services/api"
import { useOnboarding } from "@/hooks/useOnboarding"
import {
  buildSdkProviderSnippet,
  getSdkInstallCommand,
  SDK_PROVIDERS,
  type SdkLanguage,
  type SdkProvider,
} from "@/lib/sdk-provider-snippets"
import {
  DEFAULT_AGENT_NAME,
  DEFAULT_PROMPT,
  PROVIDER_MODELS,
  defaultModelFor,
  providerIdFor,
  type QuickstartProviderId,
} from "@/lib/quickstart-providers"
import { invalidateTelemetryCaches } from "@/lib/invalidate-telemetry"
import { getStoredApiKey, markSdkInstalled, setStoredApiKey } from "@/lib/onboarding-storage"
import { mergeProviderCatalog, staticProviderCatalog } from "@/lib/provider-catalog"
import { friendlyErrorMessage } from "@/lib/friendly-error"
import { cn } from "@/lib/utils"

const LANGUAGES: SdkLanguage[] = ["Python", "TypeScript", "JavaScript", "cURL"]

function formatTimestamp(iso: string | undefined): string {
  if (!iso) return "—"
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

function SectionCard({
  title,
  description,
  children,
  className,
}: {
  title: string
  description?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn("panel-lift rounded-lg overflow-hidden", className)}>
      <div className="border-b border-hairline px-4 py-3.5 sm:px-5">
        <h2 className="text-body-sm font-medium text-ink">{title}</h2>
        {description && (
          <p className="text-caption text-ink-subtle mt-1 leading-relaxed max-w-prose">{description}</p>
        )}
      </div>
      <div className="px-4 py-4 sm:px-5">{children}</div>
    </section>
  )
}

function Chip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "shrink-0 rounded-md px-2.5 py-1 text-caption font-medium border transition-colors duration-150",
        active
          ? "bg-primary/15 border-primary/40 text-ink"
          : "border-hairline text-ink-subtle hover:text-ink hover:border-hairline-strong hover:bg-surface-2/50"
      )}
    >
      {label}
    </button>
  )
}

function highlightLine(line: string, lang: SdkLanguage): ReactNode {
  if (lang === "cURL" && line.startsWith("#")) {
    return <span className="text-ink-tertiary">{line}</span>
  }
  const parts: ReactNode[] = []
  const re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|#.*$|\b(?:import|from|const|await|async|new|curl)\b)/g
  let last = 0
  let match: RegExpExecArray | null
  while ((match = re.exec(line)) !== null) {
    if (match.index > last) parts.push(line.slice(last, match.index))
    const token = match[0]
    if (token.startsWith("#")) {
      parts.push(<span key={match.index} className="text-ink-tertiary">{token}</span>)
    } else if (token.startsWith('"') || token.startsWith("'")) {
      parts.push(<span key={match.index} className="text-success/80">{token}</span>)
    } else {
      parts.push(<span key={match.index} className="text-primary/90">{token}</span>)
    }
    last = match.index + token.length
  }
  if (last < line.length) parts.push(line.slice(last))
  return parts.length ? parts : line
}

function NavButtons({ className }: { className?: string }) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      <Link
        href="/dashboard"
        className="btn-primary inline-flex items-center gap-2 text-body-sm transition-colors duration-150"
      >
        View Dashboard <ExternalLink className="w-3.5 h-3.5" />
      </Link>
      <Link href="/analytics" className="btn-secondary text-body-sm transition-colors duration-150">
        View Analytics
      </Link>
      <Link href="/traces" className="btn-secondary text-body-sm transition-colors duration-150">
        View Trace Explorer
      </Link>
    </div>
  )
}

export function SdkOnboarding() {
  const queryClient = useQueryClient()
  const { status: onboarding, refresh: refreshOnboarding } = useOnboarding()

  const [provider, setProvider] = useState<SdkProvider>("OpenAI")
  const [providerId, setProviderId] = useState<QuickstartProviderId>("openai")
  const [language, setLanguage] = useState<SdkLanguage>("Python")
  const [model, setModel] = useState(defaultModelFor("openai"))

  const [keyName, setKeyName] = useState("Default")
  const [creating, setCreating] = useState(false)
  const [traceplaneApiKey, setTraceplaneApiKey] = useState("")
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedSnippet, setCopiedSnippet] = useState(false)
  const [copiedInstall, setCopiedInstall] = useState<string | null>(null)

  const [testing, setTesting] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)
  const [lastTraceId, setLastTraceId] = useState<string | null>(null)
  const [traceVerified, setTraceVerified] = useState(false)
  const [showSuccessBanner, setShowSuccessBanner] = useState(false)

  const { data: providers = [] } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => mergeProviderCatalog(await providersService.list()),
    placeholderData: staticProviderCatalog(),
    retry: 0,
    staleTime: 30_000,
  })

  const hasFirstTrace = Boolean(onboarding?.has_first_trace || lastTraceId)
  const connectedCount = providers.filter((p) => p.status === "connected").length
  const providerConnected = providers.some((p) => p.status === "connected")
  const selectedProviderConnected = providers.find((p) => p.provider_id === providerId)?.status === "connected"

  const { data: traceBounds } = useQuery({
    queryKey: ["sdk-trace-bounds"],
    queryFn: async () => {
      const latest = await analyticsService.traces({ page: 1, page_size: 1 })
      if (!latest.total) return null
      const lastPage = Math.max(1, Math.ceil(latest.total / 1))
      const earliest =
        lastPage === 1 ? latest : await analyticsService.traces({ page: lastPage, page_size: 1 })
      return {
        firstSeen: earliest.traces[earliest.traces.length - 1]?.timestamp,
        lastTrace: latest.traces[0]?.timestamp,
        total: latest.total,
      }
    },
    enabled: hasFirstTrace,
    staleTime: 30_000,
  })

  useEffect(() => {
    const stored = getStoredApiKey()
    if (stored?.startsWith("aoh_")) setTraceplaneApiKey(stored)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => void refreshOnboarding(), 10_000)
    return () => clearInterval(interval)
  }, [refreshOnboarding])

  useEffect(() => {
    if (onboarding?.has_first_trace) setShowSuccessBanner(true)
  }, [onboarding?.has_first_trace])

  const hasTraceplaneKey = Boolean(traceplaneApiKey?.startsWith("aoh_"))
  const sdkInstalled = hasTraceplaneKey || Boolean(onboarding?.has_api_key)

  const snippet = useMemo(
    () =>
      buildSdkProviderSnippet(provider, language, {
        traceplaneApiKey: traceplaneApiKey || undefined,
        agentName: DEFAULT_AGENT_NAME,
      }),
    [provider, language, traceplaneApiKey]
  )

  const progressItems = [
    { label: "Provider Connected", complete: providerConnected },
    { label: "SDK Installed", complete: sdkInstalled },
    { label: "First Trace Received", complete: hasFirstTrace },
  ]

  function selectProvider(p: SdkProvider) {
    setProvider(p)
    const id = providerIdFor(p)
    setProviderId(id)
    setModel(defaultModelFor(id))
    setTestError(null)
  }

  function selectFromStrip(id: string, sdkName: SdkProvider) {
    selectProvider(sdkName)
  }

  async function handleCreateKey() {
    setCreating(true)
    setTestError(null)
    try {
      const created = await apiKeysService.create(keyName.trim() || "Default")
      setTraceplaneApiKey(created.key)
      setStoredApiKey(created.key)
      markSdkInstalled()
    } finally {
      setCreating(false)
    }
  }

  function copyText(text: string, kind: "snippet" | "key" | "install", installId?: string) {
    navigator.clipboard.writeText(text)
    if (kind === "snippet") {
      setCopiedSnippet(true)
      markSdkInstalled()
      setTimeout(() => setCopiedSnippet(false), 2500)
    } else if (kind === "key") {
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2500)
    } else if (kind === "install" && installId) {
      setCopiedInstall(installId)
      markSdkInstalled()
      setTimeout(() => setCopiedInstall(null), 2500)
    }
  }

  async function handleVerifyIntegration() {
    if (!hasTraceplaneKey || !selectedProviderConnected) return
    setTesting(true)
    setTestError(null)
    setTraceVerified(false)
    try {
      const response = await providersService.testTrace(providerId, {
        traceplane_api_key: traceplaneApiKey,
        model,
        prompt: DEFAULT_PROMPT,
        agent_name: DEFAULT_AGENT_NAME,
      })
      setLastTraceId(response.trace_id)
      setTraceVerified(true)
      setShowSuccessBanner(true)
      await invalidateTelemetryCaches(queryClient)
      await refreshOnboarding()
    } catch (err) {
      setTestError(friendlyErrorMessage(err instanceof Error ? err.message : String(err)))
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="page-container max-w-3xl space-y-6 pb-12">
      <PageHeader
        title="SDK"
        subtitle="Connect your provider, install the SDK, and send your first trace in minutes."
      />

      {/* 1. Setup Progress */}
      <SdkSetupProgress items={progressItems} />

      {showSuccessBanner && hasFirstTrace && (
        <div className="rounded-lg border border-success/30 bg-success/5 px-4 py-3 text-body-sm text-ink transition-all duration-300">
          🎉 Traceplane is successfully receiving telemetry.
        </div>
      )}

      {/* 2. Supported Providers */}
      <div className="space-y-2.5">
        <p className="text-caption font-medium text-ink-subtle uppercase tracking-wide">Supported Providers</p>
        <SdkProviderStrip
          providers={providers}
          selectedId={providerId}
          onSelect={selectFromStrip}
        />
      </div>

      {/* 3. Connect Provider */}
      <SectionCard title="Connect Provider" description="Connect your LLM provider.">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
          <span className="text-caption text-ink-muted">
            Connected Providers: <span className="text-ink font-medium">{connectedCount}</span>
          </span>
          <Link
            href="/settings/providers"
            className="btn-primary text-body-sm transition-colors duration-150"
          >
            Manage Providers
          </Link>
        </div>
      </SectionCard>

      {/* 4. Workspace SDK Key */}
      <section className="panel-lift rounded-lg p-4 sm:p-5 space-y-3">
        <div>
          <h2 className="text-body-sm font-medium text-ink">Workspace SDK Key</h2>
          <p className="text-caption text-ink-subtle mt-1 leading-relaxed">
            Use this key in your application.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            className="input flex-1 min-w-[200px] text-body-sm font-mono"
            placeholder="aoh_..."
            value={traceplaneApiKey}
            onChange={(e) => {
              setTraceplaneApiKey(e.target.value)
              if (e.target.value.startsWith("aoh_")) {
                setStoredApiKey(e.target.value)
                markSdkInstalled()
              }
            }}
          />
          {hasTraceplaneKey && (
            <button
              type="button"
              className="btn-secondary text-body-sm transition-colors duration-150"
              onClick={() => copyText(traceplaneApiKey, "key")}
              aria-label="Copy SDK key"
            >
              {copiedKey ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
        </div>
        <CopyToast message="SDK key copied" visible={copiedKey} />
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <input
            className="input w-40 text-body-sm"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            placeholder="Key name"
          />
          <button
            type="button"
            className="btn-secondary text-body-sm transition-colors duration-150"
            disabled={creating}
            onClick={() => void handleCreateKey()}
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate key"}
          </button>
        </div>
      </section>

      {/* 5. Install SDK */}
      <SectionCard title="Install SDK">
        <div className="space-y-3">
          {[
            { id: "pip", label: "Python", cmd: "pip install traceplane" },
            { id: "npm", label: "Node.js", cmd: "npm install traceplane" },
          ].map(({ id, label, cmd }) => (
            <div key={id} className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-caption text-ink-tertiary w-14 shrink-0">{label}</span>
                <code className="flex-1 min-w-0 rounded-md border border-hairline bg-canvas px-3 py-2.5 text-caption font-mono text-ink">
                  {cmd}
                </code>
                <button
                  type="button"
                  className="btn-secondary text-caption shrink-0 transition-colors duration-150"
                  onClick={() => copyText(cmd, "install", id)}
                >
                  Copy
                </button>
              </div>
              {copiedInstall === id && <CopyToast message="Command copied" visible />}
            </div>
          ))}
        </div>
      </SectionCard>

      {/* 6. Copy Integration Code */}
      <SectionCard title="Copy Integration Code" description="Paste this snippet into your app.">
        <div className="flex flex-wrap gap-1.5 mb-3">
          {SDK_PROVIDERS.map((p) => (
            <Chip key={p} label={p} active={provider === p} onClick={() => selectProvider(p)} />
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5 mb-4">
          {LANGUAGES.map((lang) => (
            <Chip key={lang} label={lang} active={language === lang} onClick={() => setLanguage(lang)} />
          ))}
        </div>
        <p className="text-caption text-ink-tertiary mb-3">{getSdkInstallCommand(provider, language)}</p>
        <div className="relative rounded-md border border-hairline bg-canvas overflow-hidden">
          <button
            type="button"
            onClick={() => copyText(snippet, "snippet")}
            className="absolute right-2 top-2 btn-secondary text-caption z-10 transition-colors duration-150"
          >
            Copy
          </button>
          <pre className="overflow-x-auto p-4 pt-11 text-[13px] font-mono leading-[1.65] text-ink-muted max-h-[380px]">
            {snippet.split("\n").map((line, i) => (
              <div key={i}>{highlightLine(line, language)}</div>
            ))}
          </pre>
        </div>
        <div className="mt-2">
          <CopyToast message="Snippet copied" visible={copiedSnippet} />
        </div>
      </SectionCard>

      {/* 7. Verify Integration */}
      <SectionCard
        title="Verify Integration"
        description="Send a sample request and verify telemetry reaches Traceplane."
      >
        <select
          className="input text-body-sm mb-4 w-full max-w-md"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          {(PROVIDER_MODELS[providerId] ?? [defaultModelFor(providerId)]).map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        {testError && <p className="text-caption text-danger mb-3">{testError}</p>}
        {(traceVerified || lastTraceId) && (
          <p className="text-caption text-success mb-3 inline-flex items-center gap-1.5 transition-opacity duration-200">
            <Check className="w-3.5 h-3.5 shrink-0" strokeWidth={2.5} />
            Trace received successfully
            {lastTraceId && (
              <>
                {" "}
                ·{" "}
                <Link href={`/traces/${lastTraceId}`} className="text-primary hover:underline">
                  View trace
                </Link>
              </>
            )}
          </p>
        )}
        <button
          type="button"
          className="btn-primary inline-flex items-center gap-2 text-body-sm transition-colors duration-150"
          disabled={testing || !hasTraceplaneKey || !selectedProviderConnected}
          onClick={() => void handleVerifyIntegration()}
        >
          {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Send Test Trace
        </button>
        {!selectedProviderConnected && (
          <p className="caption-text text-ink-tertiary mt-3">
            Connect {provider} on the{" "}
            <Link href="/settings/providers" className="text-primary hover:underline">
              Providers
            </Link>{" "}
            page first.
          </p>
        )}
        {!hasTraceplaneKey && (
          <p className="caption-text text-ink-tertiary mt-2">Generate a Workspace SDK Key above first.</p>
        )}
      </SectionCard>

      {/* 8. SDK Connected — bottom success state */}
      {hasFirstTrace && onboarding && (
        <section className="panel-lift rounded-lg p-4 sm:p-5 space-y-5 transition-all duration-300">
          <div>
            <h2 className="text-body-sm font-medium text-ink">SDK Connected</h2>
            <p className="text-caption text-ink-subtle mt-1 leading-relaxed">
              Your workspace is actively receiving telemetry.
            </p>
          </div>
          <dl className="grid gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-caption text-ink-tertiary">First Trace</dt>
              <dd className="text-body-sm text-ink mt-1 font-medium">{formatTimestamp(traceBounds?.firstSeen)}</dd>
            </div>
            <div>
              <dt className="text-caption text-ink-tertiary">Last Trace</dt>
              <dd className="text-body-sm text-ink mt-1 font-medium">{formatTimestamp(traceBounds?.lastTrace)}</dd>
            </div>
            <div>
              <dt className="text-caption text-ink-tertiary">Total Traces</dt>
              <dd className="text-body-sm text-ink mt-1 font-medium">
                {traceBounds?.total ?? onboarding.execution_count}
              </dd>
            </div>
          </dl>
          <NavButtons />
        </section>
      )}
    </div>
  )
}
