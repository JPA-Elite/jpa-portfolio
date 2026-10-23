import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  openAdminPage,
  toastMessage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/login-attempts";

test.describe("Admin login attempts", () => {
  test("lists and paginates login attempts", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText(
      "Login Attempts"
    );
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(7);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");

    await page.locator("#perPageSelect").selectOption("5");
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(5);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 2");
    await expect(page.locator("#prevPage")).toBeDisabled();
    await expect(page.locator("#nextPage")).toBeEnabled();

    await page.locator("#nextPage").click();
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(2);
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 | 2");
    await expect(page.locator("#nextPage")).toBeDisabled();
  });

  test("marks the current device and prevents deleting it", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    const currentRow = page
      .locator("#loginAttemptsTableBody tr")
      .filter({ hasText: "mock-playwright-ip" });

    await expect(currentRow).toHaveClass(/table-success/);
    await expect(currentRow).toContainText("(Current Device)");
    await expect(currentRow.getByRole("button", { name: /Delete/ })).toBeDisabled();
  });

  test("searches login attempts by IP and device", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await page.locator("#searchInput").fill("mock-ip-03");
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(1);
    await expect(page.locator("#loginAttemptsTableBody")).toContainText(
      "mock-ip-03"
    );

    await page.locator("#searchInput").fill("Mock Device 5");
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(1);
    await expect(page.locator("#loginAttemptsTableBody")).toContainText(
      "Mock Device 5"
    );
  });

  test("sorts login attempts oldest first", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#loginAttemptsTableBody tr").first()).not.toContainText(
      "mock-playwright-ip"
    );

    await page.locator("#orderSelect").selectOption("asc");

    await expect(page.locator("#loginAttemptsTableBody tr").first()).toContainText(
      "mock-playwright-ip"
    );
    await expect(
      page
        .locator("#loginAttemptsTableBody tr")
        .first()
        .getByRole("button", { name: /Delete/ })
    ).toBeDisabled();
  });

  test("deletes a non-current login attempt after confirmation", async ({
    page,
    mockSite,
  }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#loginAttemptsTableBody .login-attempt-delete-btn:not([disabled])")
      .first()
      .click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete login attempts from"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText(
      "Login Attempt deleted successfully"
    );
    expect(mockSite.admin.loginAttempts).toHaveLength(6);
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(6);
  });

  test("keeps login attempt controls accessible on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator("#searchInput")).toBeVisible();
    await expect(page.locator("#perPageSelect")).toBeVisible();
    await expect(page.locator("#loginAttemptsTableBody tr")).toHaveCount(7);
  });
});
