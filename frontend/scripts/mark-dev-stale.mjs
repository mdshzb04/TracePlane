#!/usr/bin/env node
/**
 * Written after `next build`.
 * Signals a running dev server (dev.mjs) to clear .next and restart so chunk/CSS
 * hashes never drift mid-session (prevents unstyled / blank pages).
 */
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const nextDir = path.join(root, ".next")

fs.writeFileSync(path.join(root, ".dev-needs-clean"), String(Date.now()))

// Legacy marker for dev servers started before this change
if (fs.existsSync(nextDir)) {
  fs.writeFileSync(path.join(nextDir, ".requires-clean-dev"), String(Date.now()))
}

console.log("[build] dev cache invalidation marker written — running dev server will auto-restart")
