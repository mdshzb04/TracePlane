import { expect, test } from "@playwright/test"

test.describe("onboarding", () => {
  test("quickstart page is reachable from marketing", async ({ page }) => {
    await page.goto("/")
    const link = page.getByRole("link", { name: /get started|open control plane/i }).first()
    await expect(link).toBeVisible()
  })
})
