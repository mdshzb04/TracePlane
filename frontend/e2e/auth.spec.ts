import { expect, test } from "@playwright/test"

test.describe("authentication", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login")
    await expect(page.locator("form").getByRole("button", { name: /sign in/i })).toBeVisible()
  })

  test("redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/agents")
    await expect(page).toHaveURL(/\/login/)
  })
})
