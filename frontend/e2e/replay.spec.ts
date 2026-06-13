import { expect, test } from "@playwright/test"

test.describe("auth gates", () => {
  test("traces route requires auth", async ({ page }) => {
    await page.goto("/traces")
    await expect(page).toHaveURL(/\/login/)
  })
})
