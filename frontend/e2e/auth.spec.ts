import { expect, test } from "@playwright/test"

test.describe("authentication", () => {
  test("login page renders GitHub sign-in", async ({ page }) => {
    await page.goto("/login")
    await expect(page.getByRole("button", { name: /continue with github/i })).toBeVisible()
  })

  test("redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/agents")
    await expect(page).toHaveURL(/\/login/)
  })
})
