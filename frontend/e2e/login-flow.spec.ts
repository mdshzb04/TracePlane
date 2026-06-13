import { expect, test } from "@playwright/test"

test.skip("email login removed — GitHub OAuth required for authenticated e2e", async ({ page }) => {
  await page.goto("/login")
  await expect(page.getByRole("button", { name: /continue with github/i })).toBeVisible()
})
