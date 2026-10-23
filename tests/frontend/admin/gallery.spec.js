import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/gallery";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add Gallery/ }).click();
  await expect(page.locator("#addGalleryModal")).toHaveClass(/show/);
}

async function fillAddForm(page, title = "Mock Added Gallery") {
  await page.locator("#addTitle").fill(title);
  await page.locator("#addTitleCeb").fill(title);
  await page.locator("#addTitleFr").fill(title);
  await page.locator("#addTitleFil").fill(title);
  await page.locator("#addDescription").fill("Added gallery description");
  await page.locator("#addDescriptionCeb").fill("Added gallery description");
  await page.locator("#addDescriptionFr").fill("Added gallery description");
  await page.locator("#addDescriptionFil").fill("Added gallery description");
  await page.locator("#addTags").fill("mock, added");
  await uploadImage(page.locator("#addImageFile"));
}

test.describe("Admin gallery", () => {
  test("lists, paginates, and searches gallery records", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Gallery");
    await expect(page.locator("#galleryTableBody tr")).toHaveCount(10);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 2");
    await expect(page.locator("#galleryTableBody")).toContainText(
      "Mock Studio Frame 12"
    );

    await page.locator("#nextPage").click();
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 | 2");
    await expect(page.locator("#galleryTableBody tr")).toHaveCount(2);

    await page.locator("#searchInput").fill("Aurora Frame 01");
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#galleryTableBody")).toContainText(
      "Mock Aurora Frame 01"
    );
    await expect(page.locator("#prevPage")).toBeDisabled();
    await expect(page.locator("#nextPage")).toBeDisabled();
  });

  test("validates the add gallery form", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addGalleryBtn").click();
    await expect(toastMessage(page)).toContainText(
      "All titles, descriptions, and a gallery file are required."
    );

    await fillAddForm(page);
    await page.locator("#addTags").fill("bad tag!");
    await page.locator("#addGalleryBtn").click();
    await expect(toastMessage(page)).toContainText("Invalid tag(s): bad tag!");
    await expect(page.locator("#addGalleryModal")).toHaveClass(/show/);
  });

  test("adds a gallery record with an uploaded image", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillAddForm(page);

    await page.locator("#addGalleryBtn").click();

    await expect(toastMessage(page)).toContainText("gallery added successfully");
    await expect(page.locator("#addGalleryModal")).not.toHaveClass(/show/);
    await expect(page.locator("#galleryTableBody")).toContainText(
      "Mock Added Gallery"
    );
    expect(mockSite.admin.gallery).toHaveLength(13);
    expect(mockSite.admin.gallery.at(-1).tags).toEqual(["mock", "added"]);
  });

  test("edits a gallery record", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#galleryTableBody tr").first().getByRole("button", { name: /Edit/ }).click();
    await expect(page.locator(".modal.show").last()).toBeVisible();

    const modal = page.locator(".modal.show").last();
    await modal.locator("input[id^='editTitleEn']").fill("Mock Updated Aurora");
    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText("gallery updated successfully");
    await expect(page.locator("#galleryTableBody")).toContainText(
      "Mock Updated Aurora"
    );
    const updated = mockSite.admin.gallery.find(
      (item) => item._id === "pw-admin-gallery-12"
    );
    expect(updated.title.en).toBe("Mock Updated Aurora");
  });

  test("deletes a gallery record after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#galleryTableBody tr").first().getByRole("button", { name: /Delete/ }).click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("Gallery deleted successfully");
    await expect(page.locator("#galleryTableBody")).not.toContainText(
      "Mock Studio Frame 12"
    );
    expect(mockSite.admin.gallery).toHaveLength(11);
  });

  test("opens the image preview from a gallery thumbnail", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#galleryTableBody img").first().click();

    await expect(page.locator("#adminImagePreviewModal")).toHaveClass(/show/);
    await expect(page.locator("#adminImagePreviewTitle")).toHaveText("Gallery Image");
    await expect(page.locator("#adminImagePreviewSource")).toHaveAttribute(
      "src",
      /\/static\/images\//
    );
  });

  test("shows mobile-specific upload controls in the add modal", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addImageFileMobile")).toBeVisible();
    await expect(page.locator("#addImageFile")).toBeHidden();
    await expect(page.locator("#addTitle")).toBeVisible();
    await uploadImage(page.locator("#addImageFileMobile"), MOCK_IMAGE);
    await expect(page.locator("#addImageFileMobile")).toHaveValue(/mock-admin-image/);
  });
});
