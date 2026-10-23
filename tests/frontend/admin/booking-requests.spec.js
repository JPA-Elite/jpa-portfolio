import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  openAdminPage,
  toastMessage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/booking-requests";

test.describe("Admin booking requests", () => {
  test("lists booking requests with pagination controls", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText(
      "Booking Requests"
    );
    await expect(page.locator("#bookingRequestsTableBody tr")).toHaveCount(8);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#clearBookingRequestsBtn")).toBeEnabled();
    await expect(page.locator("#bookingRequestsTableBody")).toContainText(
      "client8@example.com"
    );
  });

  test("paginates booking requests", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#perPageSelect").selectOption("5");

    await expect(page.locator("#bookingRequestsTableBody tr")).toHaveCount(5);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 2");
    await expect(page.locator("#prevPage")).toBeDisabled();

    await page.locator("#nextPage").click();
    await expect(page.locator("#bookingRequestsTableBody tr")).toHaveCount(3);
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 | 2");
    await expect(page.locator("#nextPage")).toBeDisabled();
  });

  test("expands and collapses a long booking message", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#searchInput").fill("Alice Client");

    const row = page.locator("#bookingRequestsTableBody tr").filter({
      hasText: "Alice Client",
    });
    await expect(row).toHaveCount(1);
    await expect(row.locator(".msg-text")).toContainText("...");
    await expect(row.getByText("Show more")).toBeVisible();

    await row.getByText("Show more").click();
    await expect(row.locator(".msg-text")).toContainText(
      "expandable message control"
    );
    await expect(row.getByText("Show less")).toBeVisible();

    await row.getByText("Show less").click();
    await expect(row.locator(".msg-text")).toContainText("...");
    await expect(row.getByText("Show more")).toBeVisible();
  });

  test("sorts booking requests oldest first", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#bookingRequestsTableBody tr").first()).not.toContainText(
      "Alice Client"
    );

    await page.locator("#orderSelect").selectOption("asc");
    await expect(page.locator("#bookingRequestsTableBody tr").first()).toContainText(
      "Alice Client"
    );
  });

  test("deletes a booking request after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#bookingRequestsTableBody .booking-delete-btn")
      .first()
      .click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete this booking request?"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText(
      "Booking request deleted successfully"
    );
    expect(mockSite.admin.bookings).toHaveLength(7);
    await expect(page.locator("#bookingRequestsTableBody tr")).toHaveCount(7);
  });

  test("clears all booking requests after confirmation", async ({
    page,
    mockSite,
  }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#clearBookingRequestsBtn").click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete all booking requests?"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText(
      "All booking requests cleared successfully"
    );
    expect(mockSite.admin.bookings).toHaveLength(0);
    await expect(page.locator("#bookingRequestsTableBody")).toContainText(
      "No booking requests found"
    );
    await expect(page.locator("#clearBookingRequestsBtn")).toBeDisabled();
  });

  test("keeps booking request controls accessible on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator("#searchInput")).toBeVisible();
    await expect(page.locator("#clearBookingRequestsBtn")).toBeVisible();
    await expect(page.locator("#bookingRequestsTableBody tr")).toHaveCount(8);
  });
});
