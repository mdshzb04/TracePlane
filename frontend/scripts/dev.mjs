#!/usr/bin/env node
/**
 * Reliable dev server startup:
 * - Clears .next when production build artifacts or stale routes are detected
 * - Restarts automatically when a build completes while dev is already running
 * - Frees port 3000 if occupied by a previous Next.js process
 * - Waits for the old process to exit before deleting .next (avoids corrupt webpack cache)
 */
import { spawn, spawnSync } from "node:child_process"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const nextDir = path.join(root, ".next")
const appDir = path.join(root, "app")
const cleanMarker = path.join(root, ".dev-needs-clean")
const legacyMarker = path.join(nextDir, ".requires-clean-dev")

let child = null
let restarting = false
let watchers = []

function pageExists(routeDir) {
  if (!routeDir) return fs.existsSync(path.join(appDir, "page.tsx"))
  return fs.existsSync(path.join(appDir, routeDir, "page.tsx"))
}

function markersPresent() {
  return fs.existsSync(cleanMarker) || fs.existsSync(legacyMarker)
}

function staleCacheDetected() {
  if (!fs.existsSync(nextDir)) return false
  if (process.env.FORCE_CLEAN === "1") return true
  if (markersPresent()) return true

  if (fs.existsSync(path.join(nextDir, "BUILD_ID"))) {
    console.log("[dev] production build cache detected — clearing for dev")
    return true
  }

  const typesDir = path.join(nextDir, "types/app")
  if (!fs.existsSync(typesDir)) return false

  for (const entry of fs.readdirSync(typesDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const route = entry.name === "page" ? "" : entry.name
    if (!pageExists(route)) {
      console.log(`[dev] stale cache for removed route: /${route || ""}`)
      return true
    }
  }
  return false
}

function clearCache(reason) {
  if (fs.existsSync(nextDir)) {
    fs.rmSync(nextDir, { recursive: true, force: true })
    console.log(`[dev] cleared .next cache${reason ? ` (${reason})` : ""}`)
  }
  for (const marker of [cleanMarker, legacyMarker]) {
    if (fs.existsSync(marker)) fs.rmSync(marker, { force: true })
  }
}

function freePort(port) {
  const result = spawnSync("fuser", [`${port}/tcp`], { encoding: "utf8" })
  if (result.status !== 0) return
  console.log(`[dev] freeing port ${port} (previous dev server)`)
  spawnSync("fuser", ["-k", `${port}/tcp`], { stdio: "ignore" })
}

function stopWatchers() {
  for (const watcher of watchers) {
    try {
      watcher.close()
    } catch {
      /* ignore */
    }
  }
  watchers = []
}

function watchForStaleCache() {
  stopWatchers()

  const onMarker = (reason) => {
    if (!markersPresent() && reason === "marker") return
    if (reason === "build-id" && !fs.existsSync(path.join(nextDir, "BUILD_ID"))) return
    scheduleCleanRestart(reason)
  }

  try {
    const rootWatcher = fs.watch(root, (_event, filename) => {
      if (filename === ".dev-needs-clean") onMarker("marker")
    })
    watchers.push(rootWatcher)
  } catch (err) {
    console.warn("[dev] could not watch clean marker:", err.message)
  }

  if (fs.existsSync(nextDir)) {
    try {
      const nextWatcher = fs.watch(nextDir, (_event, filename) => {
        if (filename === "BUILD_ID" || filename === ".requires-clean-dev") onMarker("build-id")
      })
      watchers.push(nextWatcher)
    } catch (err) {
      console.warn("[dev] could not watch .next:", err.message)
    }
  }
}

function scheduleCleanRestart(reason) {
  if (restarting) return
  restarting = true
  console.log(`[dev] cache invalidation triggered (${reason}) — restarting dev server`)

  stopWatchers()

  function afterChildStopped() {
    clearCache(reason)
    setTimeout(() => {
      restarting = false
      startDevServer()
    }, 500)
  }

  if (child && !child.killed) {
    const forceKill = setTimeout(() => {
      if (child && !child.killed) {
        console.log("[dev] force-stopping previous dev server")
        child.kill("SIGKILL")
      }
    }, 4000)

    child.once("exit", () => {
      clearTimeout(forceKill)
      child = null
      afterChildStopped()
    })

    child.kill("SIGTERM")
    return
  }

  afterChildStopped()
}

function startDevServer() {
  freePort(3000)

  child = spawn("npx", ["next", "dev", "-p", "3000"], {
    cwd: root,
    stdio: "inherit",
    shell: false,
  })

  child.on("exit", (code) => {
    if (restarting) return
    stopWatchers()
    process.exit(code ?? 0)
  })

  watchForStaleCache()
}

if (staleCacheDetected()) {
  clearCache("startup")
}

process.on("SIGINT", () => {
  stopWatchers()
  if (child && !child.killed) child.kill("SIGINT")
})
process.on("SIGTERM", () => {
  stopWatchers()
  if (child && !child.killed) child.kill("SIGTERM")
})

startDevServer()
