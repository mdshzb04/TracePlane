import { getTraceplaneSdkBaseUrl, buildTraceplaneEnvBlock } from "@/lib/traceplane-sdk"

export const SDK_PROVIDERS = [
  "OpenAI",
  "Claude",
  "Gemini",
  "DeepSeek",
  "Grok",
  "OpenRouter",
  "Cohere",
  "Perplexity",
  "Mistral",
  "MiniMax",
  "Cerebras",
  "DeepInfra",
  "Fireworks",
] as const

export type SdkProvider = (typeof SDK_PROVIDERS)[number]
export type SdkLanguage = "Python" | "TypeScript" | "JavaScript" | "cURL"

/** @deprecated Use SDK_PROVIDERS */
export const QUICKSTART_PROVIDERS = SDK_PROVIDERS
export type QuickstartProvider = SdkProvider

type SnippetOpts = { traceplaneApiKey?: string; ingestUrl?: string; agentName?: string }

type ClientKind = "openai" | "openai-compatible" | "anthropic" | "cohere" | "gemini" | "mistral"

type ProviderMeta = {
  providerId: string
  model: string
  providerKeyEnv: string
  client: ClientKind
  baseUrl?: string
  pyInstall: string
  tsInstall: string
  jsInstall: string
}

function resolve(opts?: SnippetOpts) {
  return {
    tpKey: opts?.traceplaneApiKey || "aoh_your_api_key",
    ingest: (opts?.ingestUrl || getTraceplaneSdkBaseUrl()).replace(/\/$/, ""),
    agent: opts?.agentName || "sdk-agent",
  }
}

function envPreamble(language: SdkLanguage, tpKey: string, ingest: string, providerKeyEnv?: string): string {
  if (language === "cURL") {
    return buildTraceplaneEnvBlock(tpKey, providerKeyEnv)
  }
  const lines = buildTraceplaneEnvBlock(tpKey, providerKeyEnv).split("\n")
  const prefix = language === "Python" ? "# " : "// "
  return lines.map((line) => `${prefix}${line}`).join("\n")
}

export const PROVIDER_META: Record<SdkProvider, ProviderMeta> = {
  OpenAI: {
    providerId: "openai",
    model: "gpt-4o-mini",
    providerKeyEnv: "OPENAI_API_KEY",
    client: "openai",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Claude: {
    providerId: "anthropic",
    model: "claude-3-5-haiku-latest",
    providerKeyEnv: "ANTHROPIC_API_KEY",
    client: "anthropic",
    pyInstall: "traceplane anthropic",
    tsInstall: "traceplane @anthropic-ai/sdk",
    jsInstall: "traceplane @anthropic-ai/sdk",
  },
  Gemini: {
    providerId: "google",
    model: "gemini-2.0-flash",
    providerKeyEnv: "GEMINI_API_KEY",
    client: "gemini",
    pyInstall: "traceplane google-genai",
    tsInstall: "traceplane @google/genai",
    jsInstall: "traceplane @google/genai",
  },
  DeepSeek: {
    providerId: "deepseek",
    model: "deepseek-chat",
    providerKeyEnv: "DEEPSEEK_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.deepseek.com",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Grok: {
    providerId: "xai",
    model: "grok-2-1212",
    providerKeyEnv: "XAI_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.x.ai/v1",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  OpenRouter: {
    providerId: "openrouter",
    model: "google/gemini-2.0-flash-001",
    providerKeyEnv: "OPENROUTER_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://openrouter.ai/api/v1",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Cohere: {
    providerId: "cohere",
    model: "command-r-plus-08-2024",
    providerKeyEnv: "COHERE_API_KEY",
    client: "cohere",
    pyInstall: "traceplane cohere",
    tsInstall: "traceplane cohere-ai",
    jsInstall: "traceplane cohere-ai",
  },
  Perplexity: {
    providerId: "perplexity",
    model: "sonar",
    providerKeyEnv: "PERPLEXITY_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.perplexity.ai",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Mistral: {
    providerId: "mistral",
    model: "mistral-small-latest",
    providerKeyEnv: "MISTRAL_API_KEY",
    client: "mistral",
    pyInstall: "traceplane mistralai",
    tsInstall: "traceplane @mistralai/mistralai",
    jsInstall: "traceplane @mistralai/mistralai",
  },
  MiniMax: {
    providerId: "minimax",
    model: "abab6.5-chat",
    providerKeyEnv: "MINIMAX_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.minimax.chat/v1",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Cerebras: {
    providerId: "cerebras",
    model: "llama-3.3-70b",
    providerKeyEnv: "CEREBRAS_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.cerebras.ai/v1",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  DeepInfra: {
    providerId: "deepinfra",
    model: "meta-llama/Meta-Llama-3.1-8B-Instruct",
    providerKeyEnv: "DEEPINFRA_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.deepinfra.com/v1/openai",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
  Fireworks: {
    providerId: "fireworks",
    model: "accounts/fireworks/models/llama-v3p1-8b-instruct",
    providerKeyEnv: "FIREWORKS_API_KEY",
    client: "openai-compatible",
    baseUrl: "https://api.fireworks.ai/inference/v1",
    pyInstall: "traceplane openai",
    tsInstall: "traceplane openai",
    jsInstall: "traceplane openai",
  },
}

export function getSdkInstallCommand(provider: SdkProvider, lang: SdkLanguage): string {
  const m = PROVIDER_META[provider]
  if (lang === "Python") return `pip install ${m.pyInstall}`
  if (lang === "TypeScript" || lang === "JavaScript") return `npm install ${m.tsInstall}`
  return `export TRACEPLANE_API_KEY=...\nexport TRACEPLANE_BASE_URL=${getTraceplaneSdkBaseUrl()}  export ${m.providerKeyEnv}=...`
}

export function getTraceplaneInstallCommand(lang: SdkLanguage): string {
  if (lang === "Python") return "pip install traceplane"
  if (lang === "TypeScript" || lang === "JavaScript") return "npm install traceplane"
  return `export TRACEPLANE_API_KEY=...\nexport TRACEPLANE_BASE_URL=${getTraceplaneSdkBaseUrl()}`
}

function pyTraceHeader(ingest: string, agent: string, model: string, providerId: string): string {
  return `import os
import traceplane

traceplane.init(
    api_key=os.environ["TRACEPLANE_API_KEY"],
    base_url=os.environ.get("TRACEPLANE_BASE_URL", "${ingest}"),
)

with traceplane.trace("${agent}", model="${model}", provider="${providerId}") as span:
    prompt = "Hello!"
    span.set_input(prompt)`
}

function openAiPython(ingest: string, agent: string, model: string, providerId: string, keyEnv: string): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["${keyEnv}"])
    response = client.chat.completions.create(
        model="${model}",
        messages=[{"role": "user", "content": prompt}],
    )`
}

function openAiCompatiblePython(
  ingest: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  baseUrl: string
): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["${keyEnv}"], base_url="${baseUrl}")
    response = client.chat.completions.create(
        model="${model}",
        messages=[{"role": "user", "content": prompt}],
    )`
}

function anthropicPython(ingest: string, agent: string, model: string, providerId: string, keyEnv: string): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["${keyEnv}"])
    response = client.messages.create(
        model="${model}",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )`
}

function geminiPython(ingest: string, agent: string, model: string, providerId: string, keyEnv: string): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    from google import genai

    client = genai.Client(api_key=os.environ["${keyEnv}"])
    response = client.models.generate_content(model="${model}", contents=prompt)`
}

function coherePython(ingest: string, agent: string, model: string, providerId: string, keyEnv: string): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    import cohere

    client = cohere.ClientV2(api_key=os.environ["${keyEnv}"])
    response = client.chat(model="${model}", messages=[{"role": "user", "content": prompt}])`
}

function mistralPython(ingest: string, agent: string, model: string, providerId: string, keyEnv: string): string {
  return `${pyTraceHeader(ingest, agent, model, providerId)}
    from mistralai import Mistral

    client = Mistral(api_key=os.environ["${keyEnv}"])
    response = client.chat.complete(
        model="${model}",
        messages=[{"role": "user", "content": prompt}],
    )`
}

function tsInitBlock(ingest: string, extraImports: string): string {
  return `import { init, trace } from "traceplane";
${extraImports}

init({
  apiKey: process.env.TRACEPLANE_API_KEY!,
  baseUrl: process.env.TRACEPLANE_BASE_URL ?? "${ingest}",
});`
}

function openAiTypeScript(
  ingest: string,
  _tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import OpenAI from "openai";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new OpenAI({ apiKey: process.env.${keyEnv}! });
    const response = await client.chat.completions.create({
      model: "${model}",
      messages: [{ role: "user", content: prompt }],
    });
    return response.choices[0]?.message?.content ?? "";
  },
);`
}

function openAiCompatibleTypeScript(
  ingest: string,
  tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  baseUrl: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import OpenAI from "openai";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new OpenAI({
      apiKey: process.env.${keyEnv}!,
      baseURL: "${baseUrl}",
    });
    const response = await client.chat.completions.create({
      model: "${model}",
      messages: [{ role: "user", content: prompt }],
    });
    return response.choices[0]?.message?.content ?? "";
  },
);`
}

function anthropicTypeScript(
  ingest: string,
  tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import Anthropic from "@anthropic-ai/sdk";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new Anthropic({ apiKey: process.env.${keyEnv}! });
    const response = await client.messages.create({
      model: "${model}",
      max_tokens: 256,
      messages: [{ role: "user", content: prompt }],
    });
    return response.content[0]?.type === "text" ? response.content[0].text : "";
  },
);`
}

function geminiTypeScript(
  ingest: string,
  tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import { GoogleGenAI } from "@google/genai";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new GoogleGenAI({ apiKey: process.env.${keyEnv}! });
    const response = await client.models.generateContent({ model: "${model}", contents: prompt });
    return response.text ?? "";
  },
);`
}

function cohereTypeScript(
  ingest: string,
  tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import { CohereClientV2 } from "cohere-ai";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new CohereClientV2({ token: process.env.${keyEnv}! });
    const response = await client.chat({
      model: "${model}",
      messages: [{ role: "user", content: prompt }],
    });
    return (response.message?.content ?? [])
      .map((p) => ("text" in p ? p.text : ""))
      .join("");
  },
);`
}

function mistralTypeScript(
  ingest: string,
  tpKey: string,
  agent: string,
  model: string,
  providerId: string,
  keyEnv: string,
  typed: boolean
): string {
  const t = typed ? ": string" : ""
  return `${tsInitBlock(ingest, 'import { Mistral } from "@mistralai/mistralai";')}

await trace(
  { agent: "${agent}", model: "${model}", provider: "${providerId}" },
  async (run) => {
    const prompt${t} = "Hello!";
    run.setInput(prompt);
    const client = new Mistral({ apiKey: process.env.${keyEnv}! });
    const response = await client.chat.complete({
      model: "${model}",
      messages: [{ role: "user", content: prompt }],
    });
    return response.choices?.[0]?.message?.content ?? "";
  },
);`
}

function providerCurl(model: string, keyEnv: string, client: ClientKind, baseUrl?: string): string {
  if (client === "anthropic") {
    return `curl https://api.anthropic.com/v1/messages \\
  -H "x-api-key: $${keyEnv}" \\
  -H "anthropic-version: 2023-06-01" \\
  -H "content-type: application/json" \\
  -d '{"model":"${model}","max_tokens":256,"messages":[{"role":"user","content":"Hello!"}]}'`
  }
  if (client === "cohere") {
    return `curl https://api.cohere.com/v2/chat \\
  -H "Authorization: Bearer $${keyEnv}" \\
  -H "content-type: application/json" \\
  -d '{"model":"${model}","messages":[{"role":"user","content":"Hello!"}]}'`
  }
  if (client === "gemini") {
    return `curl "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent" \\
  -H "x-goog-api-key: $${keyEnv}" \\
  -H "content-type: application/json" \\
  -d '{"contents":[{"parts":[{"text":"Hello!"}]}]}'`
  }
  if (client === "mistral") {
    return `curl https://api.mistral.ai/v1/chat/completions \\
  -H "Authorization: Bearer $${keyEnv}" \\
  -H "content-type: application/json" \\
  -d '{"model":"${model}","messages":[{"role":"user","content":"Hello!"}]}'`
  }
  const url =
    client === "openai"
      ? "https://api.openai.com/v1/chat/completions"
      : `${baseUrl}/chat/completions`
  return `curl ${url} \\
  -H "Authorization: Bearer $${keyEnv}" \\
  -H "content-type: application/json" \\
  -d '{"model":"${model}","messages":[{"role":"user","content":"Hello!"}]}'`
}


export function buildSdkProviderSnippet(
  provider: SdkProvider,
  language: SdkLanguage,
  snippetOpts?: SnippetOpts
): string {
  const { tpKey, ingest, agent } = resolve(snippetOpts)
  const m = PROVIDER_META[provider]
  const typed = language === "TypeScript"
  const preamble = envPreamble(language, tpKey, ingest, m.providerKeyEnv)

  let body: string
  if (language === "Python") {
    if (m.client === "anthropic") body = anthropicPython(ingest, agent, m.model, m.providerId, m.providerKeyEnv)
    else if (m.client === "gemini") body = geminiPython(ingest, agent, m.model, m.providerId, m.providerKeyEnv)
    else if (m.client === "cohere") body = coherePython(ingest, agent, m.model, m.providerId, m.providerKeyEnv)
    else if (m.client === "mistral") body = mistralPython(ingest, agent, m.model, m.providerId, m.providerKeyEnv)
    else if (m.client === "openai-compatible")
      body = openAiCompatiblePython(ingest, agent, m.model, m.providerId, m.providerKeyEnv, m.baseUrl!)
    else body = openAiPython(ingest, agent, m.model, m.providerId, m.providerKeyEnv)
  } else if (language === "TypeScript" || language === "JavaScript") {
    if (m.client === "anthropic")
      body = anthropicTypeScript(ingest, tpKey, agent, m.model, m.providerId, m.providerKeyEnv, typed)
    else if (m.client === "gemini")
      body = geminiTypeScript(ingest, tpKey, agent, m.model, m.providerId, m.providerKeyEnv, typed)
    else if (m.client === "cohere")
      body = cohereTypeScript(ingest, tpKey, agent, m.model, m.providerId, m.providerKeyEnv, typed)
    else if (m.client === "mistral")
      body = mistralTypeScript(ingest, tpKey, agent, m.model, m.providerId, m.providerKeyEnv, typed)
    else if (m.client === "openai-compatible")
      body = openAiCompatibleTypeScript(
        ingest,
        tpKey,
        agent,
        m.model,
        m.providerId,
        m.providerKeyEnv,
        m.baseUrl!,
        typed
      )
    else body = openAiTypeScript(ingest, tpKey, agent, m.model, m.providerId, m.providerKeyEnv, typed)
  } else {
    body = providerCurl(m.model, m.providerKeyEnv, m.client, m.baseUrl)
  }

  return `${preamble}\n\n${body}`
}
