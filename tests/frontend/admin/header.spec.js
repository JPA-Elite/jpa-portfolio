import { expect, test } from "../support/test.js";
import { openAdminPage } from "../support/admin-page.js";

const PAGE_PATH = "/admin/dashboard";

async function expectTheme(page, theme) {
  await expect(page.locator("html")).toHaveAttribute("data-bs-theme", theme);
  await expect(page.locator("#adminSidebar")).toHaveAttribute(
    "data-bs-theme",
    theme
  );
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem("admin.theme")))
    .toBe(theme);
}

async function openProfilePanel(page) {
  const userMenu = page.locator(".user-menu");
  const toggle = userMenu.locator(".dropdown-toggle");
  const menu = userMenu.locator(".dropdown-menu");

  await expect(menu).not.toHaveClass(/show/);
  await toggle.click();
  await expect(menu).toHaveClass(/show/);
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(menu).toBeVisible();

  return { userMenu, toggle, menu };
}

test.describe("Admin header", () => {
  test("toggles the theme from the header and persists it", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    const toggle = page.locator("#adminThemeToggle");

    await expect(page.locator("html")).toHaveAttribute("data-bs-theme", "light");
    await expect(page.locator("#adminSidebar")).toHaveAttribute(
      "data-bs-theme",
      "light"
    );
    await expect(toggle).not.toBeChecked();

    await toggle.check({ force: true });

    await expectTheme(page, "dark");
    await expect(toggle).toBeChecked();

    await page.goto("/admin/gallery", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".app-content").first()).toBeVisible();
    await expectTheme(page, "dark");
    await expect(toggle).toBeChecked();

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.locator(".app-content").first()).toBeVisible();
    await expectTheme(page, "dark");
    await expect(toggle).toBeChecked();

    await toggle.uncheck({ force: true });

    await expectTheme(page, "light");
    await expect(toggle).not.toBeChecked();
  });

  test("opens and closes the profile panel from the header avatar", async ({
    page,
  }) => {
    await openAdminPage(page, PAGE_PATH);
    const { userMenu, toggle, menu } = await openProfilePanel(page);

    await expect(userMenu.locator(".user-image")).toHaveAttribute(
      "src",
      "/static/images/user.webp"
    );
    await expect(menu.locator(".user-header")).toContainText("Mock Admin");
    await expect(menu.locator(".user-header")).toContainText("Administrator");
    await expect(
      menu.getByRole("link", { name: "Settings" })
    ).toHaveAttribute("href", "/admin/settings");
    await expect(
      menu.getByRole("link", { name: "Sign out" })
    ).toHaveAttribute("href", "/admin/logout");

    await toggle.click();
    await expect(menu).not.toHaveClass(/show/);
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    await toggle.click();
    await expect(menu).toHaveClass(/show/);
    await page.keyboard.press("Escape");
    await expect(menu).not.toHaveClass(/show/);
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    await toggle.click();
    await expect(menu).toHaveClass(/show/);
    await page.locator(".app-content").first().click({ position: { x: 5, y: 5 } });
    await expect(menu).not.toHaveClass(/show/);
  });

  test("navigates to settings from the profile panel", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    const { menu } = await openProfilePanel(page);

    await menu.getByRole("link", { name: "Settings" }).click();

    await expect(page).toHaveURL(/\/admin\/settings$/);
    await expect(page.locator(".app-content-header h3")).toHaveText("Settings");
  });

  test("keeps the header theme and profile controls usable on mobile", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await page.locator("#adminThemeToggle").check({ force: true });
    await expectTheme(page, "dark");

    const { menu } = await openProfilePanel(page);
    await expect(menu.locator(".user-header")).toContainText("Mock Admin");
    await expect(
      menu.getByRole("link", { name: "Settings" })
    ).toBeVisible();
  });
});
