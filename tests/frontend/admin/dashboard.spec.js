import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  openAdminPage,
  toastMessage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/dashboard";

test.describe("Admin dashboard", () => {
  test("renders summary cards, activity, and visit tables", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
    await expect(page.locator("#visitorCount")).toHaveText("128");
    await expect(page.locator("#botCount")).toHaveText("12");
    await expect(page.locator("#musicCount")).toHaveText("12");
    await expect(page.locator("#galleryCount")).toHaveText("12");
    await expect(page.locator("#videoCount")).toHaveText("8");
    await expect(page.locator("#keyProjectCount")).toHaveText("7");
    await expect(page.locator("#companyRoadmapCount")).toHaveText("6");

    await expect(page.locator("#recentActivityTableBody tr")).toHaveCount(10);
    await expect(page.locator("#recentActivityTableBody")).toContainText(
      "/admin/api/add-gallery"
    );
    await expect(page.locator("#activityPageInfo")).toHaveText("1-10 of 13");
    await expect(page.locator("#visitsTableBody tr")).toHaveCount(10);
    await expect(page.locator("#visitsPageInfo")).toHaveText("1-10 of 13");
    await expect(page.locator("#deviceBreakdownTotalCount")).toHaveText("128");
    await expect(page.locator("#deviceBreakdownLegend")).toContainText("Windows");
    await expect(page.locator("#deviceBreakdownLegend")).toContainText("iOS");
    await expect(page.locator("#deviceDonutSegments circle")).toHaveCount(6);
  });

  test("paginates recent activity records", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#activityPageInfo")).toHaveText("1-10 of 13");
    await expect(page.locator("#activityPrevPage")).toBeDisabled();

    await page.locator("#activityNextPage").click();

    await expect(page.locator("#activityPageInfo")).toHaveText("11-13 of 13");
    await expect(page.locator("#recentActivityTableBody tr")).toHaveCount(3);
    await expect(page.locator("#activityPrevPage")).toBeEnabled();
    await expect(page.locator("#activityNextPage")).toBeDisabled();

    await page.locator("#activityPrevPage").click();
    await expect(page.locator("#activityPageInfo")).toHaveText("1-10 of 13");
  });

  test("filters and deletes a recent activity record", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#activitySearchInput").fill("add-gallery");

    await expect(page.locator("#activityPageInfo")).toHaveText("1-1 of 1");
    await expect(page.locator("#recentActivityTableBody")).toContainText(
      "/admin/api/add-gallery"
    );

    await page.locator("#recentActivityTableBody .activity-delete-btn").click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete this activity record?"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("Activity selected records deleted");
    await expect(page.locator("#recentActivityTableBody")).toContainText(
      "No recent activity."
    );
    expect(mockSite.admin.activity).toHaveLength(12);
  });

  test("clears all recent activity after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#activityPageInfo")).toHaveText("1-10 of 13");

    await page.locator("#clearActivityBtn").click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Clear all recent activity records?"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("All recent activity cleared");
    await expect(page.locator("#recentActivityTableBody")).toContainText(
      "No recent activity."
    );
    await expect(page.locator("#activityPageInfo")).toHaveText("");
    expect(mockSite.admin.activity).toHaveLength(0);
  });

  test("filters, paginates, and deletes visit records", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#visitsPageInfo")).toHaveText("1-10 of 13");

    await page.locator("#visitsSearchInput").fill("/mock/page/2");
    await expect(page.locator("#visitsPageInfo")).toHaveText("1-1 of 1");
    await expect(page.locator("#visitsTableBody")).toContainText("/mock/page/2");

    await page.locator("#visitsTableBody .visit-delete-btn").click();
    await confirmDelete(page);
    await expect(toastMessage(page)).toContainText("Record deleted.");
    await expect(page.locator("#visitsTableBody")).toContainText(
      "No visit records found."
    );
    expect(mockSite.admin.visits).toHaveLength(12);
  });

  test("clears all visitor records after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await expect(page.locator("#visitsPageInfo")).toHaveText("1-10 of 13");

    await page.locator("#clearVisitsBtn").click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Clear all visitor records?"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("All visitor records cleared");
    await expect(page.locator("#visitsTableBody")).toContainText(
      "No visit records found."
    );
    expect(mockSite.admin.visits).toHaveLength(0);
  });

  test("keeps dashboard cards usable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator("#visitorCount")).toHaveText("128");
    await expect(page.locator("#recentActivityTableBody tr")).toHaveCount(10);
    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
  });
});
