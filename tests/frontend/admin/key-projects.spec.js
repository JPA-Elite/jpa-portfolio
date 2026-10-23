import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/key-projects";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add Project/ }).click();
  await expect(page.locator("#addProjectModal")).toHaveClass(/show/);
}

async function fillProjectForm(page, title = "Mock Added Project") {
  await page.locator("#addTitleEn").fill(title);
  await page.locator("#addTitleCeb").fill(title);
  await page.locator("#addTitleFr").fill(title);
  await page.locator("#addTitleFil").fill(title);
  await page.locator("#addDescEn").fill("Added project description");
  await page.locator("#addDescCeb").fill("Added project description");
  await page.locator("#addDescFr").fill("Added project description");
  await page.locator("#addDescFil").fill("Added project description");
  await page.locator("#addStack").fill("Flask • MongoDB");
  await page.locator("#addStatus").selectOption("building");
  await page.locator("#addSortOrder").fill("9");
  await page.locator("#addDemoUrl").fill("https://example.com/added-demo");
  await page.locator("#addRepoUrl").fill("https://example.com/added-repo");
  await uploadImage(page.locator("#addImageFile"));
}

test.describe("Admin key projects", () => {
  test("lists and filters key projects", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText(
      "Key Projects"
    );
    await expect(page.locator("#keyProjectsTableBody tr")).toHaveCount(7);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#keyProjectsTableBody tr").first()).toContainText(
      "Mock Atlas Platform"
    );

    await page.locator("#statusFilterSelect").selectOption("shipped");
    await expect(page.locator("#keyProjectsTableBody tr")).toHaveCount(3);
    await expect(page.locator("#keyProjectsTableBody")).toContainText("Shipped");

    await page.locator("#statusFilterSelect").selectOption("");
    await page.locator("#activeFilterSelect").selectOption("false");
    await expect(page.locator("#keyProjectsTableBody tr")).toHaveCount(1);
    await expect(page.locator("#keyProjectsTableBody")).toContainText("No");

    await page.locator("#activeFilterSelect").selectOption("");
    await page.locator("#searchInput").fill("Atlas");
    await expect(page.locator("#keyProjectsTableBody tr")).toHaveCount(1);
    await expect(page.locator("#keyProjectsTableBody")).toContainText(
      "Mock Atlas Platform"
    );
  });

  test("requires an image when adding a project", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addProjectBtn").click();
    await expect(toastMessage(page)).toContainText("Image is required.");
    await expect(page.locator("#addProjectModal")).toHaveClass(/show/);
  });

  test("adds a key project with an extra slide", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillProjectForm(page);

    await page.locator("#addProjectModal").getByRole("button", { name: /Add Slide/ }).click();
    const slide = page.locator("#addProjectSlidesContainer [data-slide-row]").first();
    await uploadImage(slide.locator("[data-slide-file]"));
    await slide.locator("[data-slide-title]").fill("Added slide title");
    await slide.locator("[data-slide-description]").fill("Added slide description");

    await page.locator("#addProjectBtn").click();

    await expect(toastMessage(page)).toContainText("Key project added successfully");
    await expect(page.locator("#addProjectModal")).not.toHaveClass(/show/);
    await expect(page.locator("#keyProjectsTableBody")).toContainText(
      "Mock Added Project"
    );
    expect(mockSite.admin.keyProjects).toHaveLength(8);
    expect(mockSite.admin.keyProjects.at(-1).slides).toHaveLength(1);
    expect(mockSite.admin.keyProjects.at(-1).slides[0].title.en).toBe(
      "Added slide title"
    );
  });

  test("edits a key project", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#keyProjectsTableBody tr").first().getByRole("button", { name: /Edit/ }).click();

    const modal = page.locator(".modal.show").last();
    await expect(modal).toBeVisible();
    await modal.locator("input[id^='editTitleEn']").fill("Mock Updated Project");
    await modal.locator("select[id^='editStatus']").selectOption("planned");
    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText("Key project updated successfully");
    await expect(page.locator("#keyProjectsTableBody")).toContainText(
      "Mock Updated Project"
    );
    const updated = mockSite.admin.keyProjects.find(
      (item) => item._id === "pw-admin-project-01"
    );
    expect(updated.title.en).toBe("Mock Updated Project");
    expect(updated.status).toBe("planned");
  });

  test("deletes a key project after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#keyProjectsTableBody tr").first().getByRole("button", { name: /Delete/ }).click();
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText(
      "Key project deleted successfully"
    );
    expect(mockSite.admin.keyProjects).toHaveLength(6);
    await expect(page.locator("#keyProjectsTableBody")).not.toContainText(
      "Mock Atlas Platform"
    );
  });

  test("opens a key project image preview", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#keyProjectsTableBody img").first().click();

    await expect(page.locator("#adminImagePreviewModal")).toHaveClass(/show/);
    await expect(page.locator("#adminImagePreviewTitle")).toHaveText(
      "Mock Atlas Platform"
    );
  });

  test("keeps key project controls visible on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addImageFile")).toBeVisible();
    await expect(page.locator("#addStatus")).toBeVisible();
    await expect(page.locator("#addIsActive")).toBeVisible();
  });
});
