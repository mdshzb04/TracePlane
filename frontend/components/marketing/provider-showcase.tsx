"use client"

import { useEffect, useMemo, useState } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"
import { apiKeysService } from "@/services/api"
import { markSdkInstalled, getStoredApiKey } from "@/lib/onboarding-storage"
import {
  buildSdkProviderSnippet,
  SDK_PROVIDERS,
  type SdkProvider,
  type SdkLanguage,
} from "@/lib/sdk-provider-snippets"
import { ProviderLogoStrip } from "./provider-logo-strip"

const FEATURED: SdkProvider[] = ["OpenAI", "Claude", "Gemini", "DeepSeek", "Grok", "OpenRouter"]
const LANGS: SdkLanguage[] = ["TypeScript", "Python", "cURL"]

type ProviderShowcaseProps = {
  variant?: "marketing" | "page"
}

function SdkCodeBlock({
  provider,
  language,
  code,
  onCopy,
  copied,
  onProviderChange,
  onLanguageChange,
  providers,
}: {
  provider: SdkProvider
  language: SdkLanguage
  code: string
  onCopy: () => void
  copied: boolean
  onProviderChange: (p: SdkProvider) => void
  onLanguageChange: (l: SdkLanguage) => void
  providers: SdkProvider[]
}) {
  return (
    <div
      key={`${provider}-${language}`}
      className="rounded-xl overflow-hidden border border-[#2a2a2a] bg-[#171717] shadow-[0_20px_60px_rgba(0,0,0,0.25)]"
    >
      <div className="flex flex-wrap gap-1 px-4 pt-3 pb-2 border-b border-[#2a2a2a]">
        {providers.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => onProviderChange(name)}
            className={cn(
              "px-3 py-1.5 text-[13px] font-medium rounded-md transition-colors duration-200",
              provider === name
                ? "text-white border-b-2 border-white rounded-none pb-1"
                : "text-[#9ca3af] hover:text-[#e5e7eb]"
            )}
          >
            {name}
          </button>
        ))}
      </div>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-4">
          {LANGS.map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => onLanguageChange(lang)}
              className={cn(
                "text-[12px] font-medium pb-0.5 border-b-2 transition-colors duration-200",
                language === lang
                  ? "text-white border-white"
                  : "text-[#9ca3af] border-transparent hover:text-[#e5e7eb]"
              )}
            >
              {lang}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={onCopy}
          className="p-1.5 text-[#9ca3af] hover:text-white transition-colors"
          aria-label="Copy code"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
        </button>
      </div>
      <pre className="font-mono overflow-x-auto whitespace-pre text-[#e5e7eb] text-[12px] sm:text-[13px] leading-[1.6] p-5 sm:p-6 min-h-[260px] max-h-[400px]">
        {code}
      </pre>
    </div>
  )
}

export function ProviderShowcase({ variant = "marketing" }: ProviderShowcaseProps) {
  const [provider, setProvider] = useState<SdkProvider>("OpenAI")
  const [language, setLanguage] = useState<SdkLanguage>("TypeScript")
  const [copied, setCopied] = useState(false)
  const [apiKey, setApiKey] = useState("aoh_your_api_key")

  useEffect(() => {
    if (variant !== "page") return
    const stored = getStoredApiKey()
    if (stored?.startsWith("aoh_")) setApiKey(stored)
    else apiKeysService.list().catch(() => {})
  }, [variant])

  const fullCode = useMemo(
    () => buildSdkProviderSnippet(provider, language, { traceplaneApiKey: apiKey }),
    [provider, language, apiKey]
  )

  const code = useMemo(() => {
    const lines = fullCode.split("\n")
    return lines.length > 22 ? lines.slice(0, 22).join("\n") : fullCode
  }, [fullCode])

  const activeProviders = useMemo(() => SDK_PROVIDERS, [])

  function handleCopy() {
    void navigator.clipboard.writeText(fullCode)
    markSdkInstalled()
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function selectProvider(p: SdkProvider) {
    setProvider(p)
    setCopied(false)
  }

  function selectLanguage(l: SdkLanguage) {
    setLanguage(l)
    setCopied(false)
  }

  if (variant === "page") {
    return (
      <div className="max-w-5xl mx-auto px-5 pt-4 pb-6">
        <h1 className="text-headline md:text-display-md font-display font-semibold text-ink tracking-tight">
          One SDK for 13+ AI Providers
        </h1>
        <p className="text-body text-ink-muted mt-2 max-w-2xl">
          Monitor OpenAI, Claude, Gemini, DeepSeek, Grok, OpenRouter and more with Traceplane SDK.
        </p>
        <div className="mt-4">
          <SdkCodeBlock
            key={`${provider}-${language}`}
            provider={provider}
            language={language}
            code={code}
            onCopy={handleCopy}
            copied={copied}
            onProviderChange={selectProvider}
            onLanguageChange={selectLanguage}
            providers={FEATURED}
          />
        </div>
      </div>
    )
  }

  return (
    <section id="sdk" className="border-t border-hairline bg-canvas scroll-mt-24">
      <div className="max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 py-16">
        <h2 className="text-[28px] sm:text-[32px] font-semibold text-ink tracking-tight">
          One SDK for <span className="text-primary">13+ providers</span>
        </h2>
        <p className="text-[15px] text-ink-muted mt-3 max-w-xl">
          Instrument any major AI provider with Traceplane. Switch models without rewriting your telemetry.
        </p>

        <ProviderLogoStrip />

        <SdkCodeBlock
          key={`${provider}-${language}`}
          provider={provider}
          language={language}
          code={code}
          onCopy={handleCopy}
          copied={copied}
          onProviderChange={selectProvider}
          onLanguageChange={selectLanguage}
          providers={activeProviders}
        />
      </div>
    </section>
  )
}
