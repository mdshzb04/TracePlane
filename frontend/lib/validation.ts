const ALLOWED_EMAIL_DOMAINS = ["gmail.com", "company.com"] as const

export function isAllowedEmail(email: string): boolean {
  const normalized = email.trim().toLowerCase()
  const parts = normalized.split("@")
  if (parts.length !== 2 || !parts[0] || !parts[1]) return false
  return (ALLOWED_EMAIL_DOMAINS as readonly string[]).includes(parts[1])
}

export function getEmailValidationError(email: string): string | null {
  const trimmed = email.trim()
  if (!trimmed) return "Email is required"
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return "Enter a valid email address"
  }
  if (!isAllowedEmail(trimmed)) {
    return "Use an email ending with @gmail.com or @company.com"
  }
  return null
}
