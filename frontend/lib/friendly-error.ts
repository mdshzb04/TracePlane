export function friendlyErrorMessage(raw: string | null | undefined): string {
  if (!raw) return "Something went wrong. Please try again."
  const lower = raw.toLowerCase()
  if (lower.includes("failed to fetch") || lower.includes("cannot reach")) {
    return "Unable to connect. Check your network and ensure the API is running."
  }
  if (lower.includes("session expired") || lower.includes("401")) {
    return "Your session expired. Please sign in again."
  }
  if (lower.includes("server error") || lower.includes("internal server")) {
    return "We couldn't load this data right now. Please try again in a moment."
  }
  if (lower.includes("403") || lower.includes("permission")) {
    return "You don't have permission to view this resource."
  }
  if (lower.includes("404") || lower.includes("not found")) {
    return "The requested resource was not found."
  }
  return raw.replace(/^Server error:\s*/i, "").replace(/\.\s*Check backend logs.*$/i, ".")
}
