import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/company-roadmaps";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add Roadmap Entry/ }).click();
  await expect(page.locator("#addRoadmapModal")).toHaveClass(/show/);
}

async function fillRoadmapBasics(page, company = "Mock Added Company") {
  await page.locator("#addCompanyName").fill(company);
  await page.locator("#addRoleTitle").fill("Mock Added Role");
  await page.locator("#addPeriod").fill("2026 - Present");
  await page.locator("#addEmploymentType").selectOption("Contract");
  await page.locator("#addLocation").fill("Remote");
  await page.locator("#addDefinition").fill("Added roadmap definition");
  await page.locator("#addSummary").fill("Added roadmap summary");
  await page.locator("#addHighlights").fill("Built the platform\nImproved reliability");
  await uploadImage(page.locator("#addCoverImageFile"));
}

test.describe("Admin company roadmaps", () => {
  test("lists and filters company roadmap entries", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText(
      "Company Roadmaps"
    );
    await expect(page.locator("#companyRoadmapsTableBody tr")).toHaveCount(6);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(
      page.locator("#companyRoadmapsTableBody tr").first()
    ).toContainText("Northwind Labs");

    await page.locator("#employmentTypeFilterSelect").selectOption("Full-time");
    await expect(page.locator("#companyRoadmapsTableBody tr")).toHaveCount(3);

    await page.locator("#employmentTypeFilterSelect").selectOption("");
    await page.locator("#activeFilterSelect").selectOption("false");
    await expect(page.locator("#companyRoadmapsTableBody tr")).toHaveCount(1);

    await page.locator("#activeFilterSelect").selectOption("");
    await page.locator("#searchInput").fill("Northwind");
    await expect(page.locator("#companyRoadmapsTableBody tr")).toHaveCount(2);
  });

  test("validates the cover image and required roadmap fields", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addRoadmapBtn").click();
    await expect(toastMessage(page)).toContainText("Cover image is required.");

    await uploadImage(page.locator("#addCoverImageFile"));
    await page.locator("#addRoadmapBtn").click();
    await expect(toastMessage(page)).toContainText(
      "Company Name, Role Title, and Period are required."
    );
    await expect(page.locator("#addRoadmapModal")).toHaveClass(/show/);
  });

  test("adds a roadmap entry with an activity image", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillRoadmapBasics(page);

    await page.getByRole("button", { name: /Add Activity Image/ }).click();
    const activity = page.locator("#addActivityRows [data-activity-row]").first();
    await uploadImage(activity.locator("[data-activity-file]"));
    await activity.locator("[data-activity-title]").fill("Added activity title");
    await activity
      .locator("[data-activity-caption]")
      .fill("Added activity caption");

    await page.locator("#addRoadmapBtn").click();

    await expect(toastMessage(page)).toContainText(
      "Company roadmap added successfully"
    );
    await expect(page.locator("#addRoadmapModal")).not.toHaveClass(/show/);
    await expect(page.locator("#companyRoadmapsTableBody")).toContainText(
      "Mock Added Company"
    );
    expect(mockSite.admin.roadmaps).toHaveLength(7);
    expect(mockSite.admin.roadmaps.at(-1).activities).toHaveLength(1);
    expect(mockSite.admin.roadmaps.at(-1).activities[0].title.en).toBe(
      "Added activity title"
    );
  });

  test("edits a company roadmap entry", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#companyRoadmapsTableBody tr")
      .first()
      .getByRole("button", { name: /Edit/ })
      .click();

    const modal = page.locator(".modal.show").last();
    await expect(modal).toBeVisible();
    await modal.locator("input[id^='editCompanyName']").fill("Mock Updated Company");
    await modal.locator("select[id^='editEmploymentType']").selectOption("Contract");
    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText(
      "Company roadmap updated successfully"
    );
    await expect(page.locator("#companyRoadmapsTableBody")).toContainText(
      "Mock Updated Company"
    );
    const updated = mockSite.admin.roadmaps.find(
      (item) => item._id === "pw-admin-roadmap-01"
    );
    expect(updated.company_name).toBe("Mock Updated Company");
    expect(updated.employment_type).toBe("Contract");
  });

  test("deletes a company roadmap entry after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#companyRoadmapsTableBody tr")
      .first()
      .getByRole("button", { name: /Delete/ })
      .click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText(
      "Company roadmap deleted successfully"
    );
    expect(mockSite.admin.roadmaps).toHaveLength(5);
    await expect(page.locator("#companyRoadmapsTableBody")).not.toContainText(
      "Mock Engineer 1"
    );
  });

  test("opens the roadmap cover preview", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#companyRoadmapsTableBody img").first().click();

    await expect(page.locator("#adminImagePreviewModal")).toHaveClass(/show/);
    await expect(page.locator("#adminImagePreviewTitle")).toHaveText(
      "Northwind Labs"
    );
  });

  test("keeps roadmap controls usable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addCompanyName")).toBeVisible();
    await expect(page.locator("#addCoverImageFile")).toBeVisible();
    await expect(page.locator("#addIsActive")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Add Activity Image/ })
    ).toBeVisible();
  });
});
