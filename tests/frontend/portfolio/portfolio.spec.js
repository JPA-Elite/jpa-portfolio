import { expect, test } from "@playwright/test";

test.describe("Portfolio available for work", () => {
  test("opens the profile image modal from the available for work avatar", async ({ page }) => {
    await page.goto("/portfolio", { waitUntil: "domcontentloaded" });

    const badge = page.locator(".summary-badge", { hasText: /available for work/i });
    await expect(badge).toBeVisible();

    const avatar = page.locator('.summary-avatar img[alt="Profile Image"]');
    await expect(avatar).toBeVisible();
    await avatar.click({ force: true });

    const modal = page.locator("#imageModal");
    await expect(modal).toBeVisible();
    await expect(page.locator("#modalImage")).toBeVisible();
    await expect(page.locator("#caption")).toContainText("My Profile");
  });
});
