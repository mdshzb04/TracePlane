import { Suspense } from "react"
import { LoginForm } from "./login-form"

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-canvas flex items-center justify-center">
          <p className="text-body-sm text-ink-muted">Loading…</p>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  )
}
