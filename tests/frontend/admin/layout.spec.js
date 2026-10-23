import { expect, test } from "../support/test.js";
import { openAdminPage } from "../support/admin-page.js";

const NAV_PAGES = [
  ["/admin/dashboard", "/admin/dashboard"],
  ["/admin/gallery", "/admin/gallery"],
  ["/admin/video", "/admin/video"],
  ["/admin/music", "/admin/music"],
  ["/admin/key-projects", "/admin/key-projects"],
  ["/admin/company-roadmaps", "/admin/company-roadmaps"],
  ["/admin/built-apps", "/admin/built-apps"],
  ["/admin/settings", "/admin/settings"],
  ["/admin/login-attempts", "/admin/login-attempts"],
  ["/admin/booking-requests", "/admin/booking-requests"],
];

test.describe("Admin layout", () => {
  test("highlights the active navigation link on every admin page", async ({
    page,
  }) => {
    await openAdminPage(page, "/admin/dashboard");

    for (const [path, href] of NAV_PAGES) {
      if (!page.url().endsWith(path)) {
        await page.goto(path, { waitUntil: "domcontentloaded" });
      }
      await expect(page.locator(".app-content").first()).toBeVisible();

      const link = page.locator(
        `#navigation a.nav-link[href="${href}"][data-sidebar-tooltip]`
      );
      await expect(link).toHaveClass(/active/);
      await expect(
        page.locator("#navigation a.nav-link.active")
      ).toHaveCount(1);
    }
  });

  test("collapses the sidebar and remembers the collapsed state", async ({
    page,
  }) => {
    await openAdminPage(page, "/admin/dashboard");
    const body = page.locator("body");

    await expect(body).toHaveClass(/sidebar-open/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText(
      "Collapse Sidebar"
    );

    await page.locator("#sidebarCollapseButton").click();

    await expect(body).toHaveClass(/sidebar-collapse/);
    await expect(body).not.toHaveClass(/sidebar-open/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText(
      "Expand Sidebar"
    );
    await expect
      .poll(() =>
        page.evaluate(() => localStorage.getItem("admin.sidebar.collapsed"))
      )
      .toBe("true");

    await page.goto("/admin/gallery", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".app-content").first()).toBeVisible();
    await expect(body).toHaveClass(/sidebar-collapse/);

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.locator(".app-content").first()).toBeVisible();
    await expect(body).toHaveClass(/sidebar-collapse/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText(
      "Expand Sidebar"
    );
  });

  test("expands a collapsed sidebar and clears the stored state", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("admin.sidebar.collapsed", "true");
    });
    await openAdminPage(page, "/admin/dashboard");
    const body = page.locator("body");

    await expect(body).toHaveClass(/sidebar-collapse/);
    await page.locator("#sidebarCollapseButton").click();

    await expect(body).toHaveClass(/sidebar-open/);
    await expect(body).not.toHaveClass(/sidebar-collapse/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText(
      "Collapse Sidebar"
    );
    await expect
      .poll(() =>
        page.evaluate(() => localStorage.getItem("admin.sidebar.collapsed"))
      )
      .toBe("false");
  });

  test("applies the theme immediately and persists it after reload", async ({
    page,
  }) => {
    await openAdminPage(page, "/admin/dashboard");
    const html = page.locator("html");
    const toggle = page.locator("#adminThemeToggle");

    await expect(html).toHaveAttribute("data-bs-theme", "light");
    await expect(toggle).not.toBeChecked();

    await toggle.check({ force: true });

    await expect(html).toHaveAttribute("data-bs-theme", "dark");
    await expect(page.locator("#adminSidebar")).toHaveAttribute(
      "data-bs-theme",
      "dark"
    );
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("admin.theme")))
      .toBe("dark");

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(html).toHaveAttribute("data-bs-theme", "dark");
    await expect(toggle).toBeChecked();

    await toggle.uncheck({ force: true });
    await expect(html).toHaveAttribute("data-bs-theme", "light");
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("admin.theme")))
      .toBe("light");
  });

  test("opens the user menu and logs out", async ({ page }) => {
    await openAdminPage(page, "/admin/dashboard");
    const userMenu = page.locator(".user-menu");

    await expect(userMenu).toContainText("Mock Admin");
    await userMenu.locator(".dropdown-toggle").click();
    await expect(userMenu.locator(".dropdown-menu")).toHaveClass(/show/);
    await expect(
      userMenu.getByRole("link", { name: "Settings" })
    ).toHaveAttribute("href", "/admin/settings");

    await userMenu.getByRole("link", { name: "Sign out" }).click();

    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.locator(".alert-success")).toContainText(
      "You have been logged out successfully."
    );
    await expect(page.locator("#username")).toBeVisible();
  });

  test("opens and closes the sidebar on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, "/admin/dashboard");
    const body = page.locator("body");
    const headerToggle = page.locator(
      '.app-header a[data-lte-toggle="sidebar"]'
    );

    await expect(body).toHaveClass(/sidebar-collapse/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText("Open Menu");

    await headerToggle.click();

    await expect(body).toHaveClass(/sidebar-open/);
    await expect(body).not.toHaveClass(/sidebar-collapse/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText(
      "Close Menu"
    );

    await page.locator('#navigation a[href="/admin/gallery"]').click();

    await expect(page).toHaveURL(/\/admin\/gallery$/);
    await expect(body).toHaveClass(/sidebar-collapse/);
    await expect(page.locator("#sidebarCollapseLabel")).toHaveText("Open Menu");
  });
});
