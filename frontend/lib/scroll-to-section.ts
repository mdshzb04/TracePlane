export const SECTION_SCROLL_OFFSET = 96

export function scrollToSection(id: string, behavior: ScrollBehavior = "smooth"): boolean {
  const el = document.getElementById(id)
  if (!el) return false

  const top = el.getBoundingClientRect().top + window.scrollY - SECTION_SCROLL_OFFSET
  window.scrollTo({ top: Math.max(0, top), behavior })
  return true
}

/** Retry until the target exists (client-hydrated sections). */
export function scrollToSectionWithRetry(
  id: string,
  behavior: ScrollBehavior = "smooth",
  maxAttempts = 12,
): Promise<boolean> {
  return new Promise((resolve) => {
    let attempt = 0

    const run = () => {
      if (scrollToSection(id, behavior)) {
        resolve(true)
        return
      }
      attempt++
      if (attempt >= maxAttempts) {
        resolve(false)
        return
      }
      requestAnimationFrame(run)
    }

    run()
  })
}
