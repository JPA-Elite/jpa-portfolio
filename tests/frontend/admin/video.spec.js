import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_VIDEO_FILE,
  openAdminPage,
  toastMessage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/video";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add Video/ }).click();
  await expect(page.locator("#addVideoModal")).toHaveClass(/show/);
}

async function fillAddForm(page, title = "Mock Added Video") {
  await page.locator("#addTitle").fill(title);
  await page.locator("#addTitleCeb").fill(title);
  await page.locator("#addTitleFr").fill(title);
  await page.locator("#addTitleFil").fill(title);
  await page.locator("#addDescription").fill("Added video description");
  await page.locator("#addDescriptionCeb").fill("Added video description");
  await page.locator("#addDescriptionFr").fill("Added video description");
  await page.locator("#addDescriptionFil").fill("Added video description");
  await page.locator("#addTags").fill("mock, video");
  await page.locator("#addVideoFile").setInputFiles(MOCK_VIDEO_FILE);
}

test.describe("Admin video", () => {
  test("lists and searches video records", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Video");
    await expect(page.locator("#videoTableBody tr")).toHaveCount(8);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#videoTableBody")).toContainText("Mock Video 08");

    await page.locator("#searchInput").fill("Mock Beacon Video");
    await expect(page.locator("#videoTableBody tr")).toHaveCount(1);
    await expect(page.locator("#videoTableBody")).toContainText(
      "Mock Beacon Video"
    );
    await expect(page.locator("#prevPage")).toBeDisabled();
    await expect(page.locator("#nextPage")).toBeDisabled();
  });

  test("validates file type and required fields when adding a video", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addVideoBtn").click();
    await expect(toastMessage(page)).toContainText(
      "All titles, descriptions, and a video file are required."
    );

    await fillAddForm(page);
    await page.locator("#addVideoFile").setInputFiles({
      name: "not-a-video.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("not a video"),
    });
    await page.locator("#addVideoBtn").click();
    await expect(toastMessage(page)).toContainText(
      "Please upload a valid video file."
    );
    await expect(page.locator("#addVideoModal")).toHaveClass(/show/);
  });

  test("adds a video record", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillAddForm(page);
    await page.locator("#addVideoBtn").click();

    await expect(toastMessage(page)).toContainText("video added successfully");
    await expect(page.locator("#addVideoModal")).not.toHaveClass(/show/);
    await expect(page.locator("#videoTableBody")).toContainText(
      "Mock Added Video"
    );
    expect(mockSite.admin.video).toHaveLength(9);
    expect(mockSite.admin.video.at(-1).tags).toEqual(["mock", "video"]);
  });

  test("edits a video record", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#videoTableBody tr").first().getByRole("button", { name: /Edit/ }).click();

    const modal = page.locator(".modal.show").last();
    await expect(modal).toBeVisible();
    await modal.locator("input[id^='editTitleEn']").fill("Mock Updated Video");
    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText("video updated successfully");
    await expect(page.locator("#videoTableBody")).toContainText(
      "Mock Updated Video"
    );
    expect(
      mockSite.admin.video.find((item) => item._id === "pw-admin-video-08").title.en
    ).toBe("Mock Updated Video");
  });

  test("deletes a video record after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#videoTableBody tr").first().getByRole("button", { name: /Delete/ }).click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("Video deleted successfully");
    expect(mockSite.admin.video).toHaveLength(7);
    await expect(page.locator("#videoTableBody")).not.toContainText("Mock Video 08");
  });

  test("opens and closes the video preview modal", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#videoTableBody").getByRole("button", { name: /Preview/ }).first().click();

    await expect(page.locator("#videoPreviewModal")).toHaveClass(/show/);
    await expect(page.locator("#previewSource")).toHaveAttribute(
      "src",
      "https://example.com/admin-video-08.mp4"
    );

    await page.locator("#videoPreviewModal [data-bs-dismiss='modal']").click();
    await expect(page.locator("#videoPreviewModal")).not.toHaveClass(/show/);
  });

  test("keeps the video table readable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator("#videoTableBody tr")).toHaveCount(8);
    await expect(page.locator(".admin-table-toolbar")).toBeVisible();
    await page.getByRole("button", { name: /Add Video/ }).click();
    await expect(page.locator("#addVideoModal")).toHaveClass(/show/);
    await expect(page.locator("#addVideoFile")).toBeVisible();
  });
});
