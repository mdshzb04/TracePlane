import { expect, test } from "@playwright/test"

test("login stays on dashboard", async ({ page }) => {
  await page.goto("/login")
  await page.fill('input[type="email"]', "fixtest@gmail.com")
  await page.fill('input[type="password"]', "password123")
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL(/\/agents/, { timeout: 30000 })
  await page.waitForTimeout(3000)
  await expect(page).toHaveURL(/\/agents/)
})
