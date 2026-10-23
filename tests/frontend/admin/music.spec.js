import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/music";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add Music/ }).click();
  await expect(page.locator("#addMusicModal")).toHaveClass(/show/);
}

async function fillBasics(page, title = "Mock Added Track") {
  await page.locator("#addTitle").fill(title);
  await page.locator("#addArtist").fill("Mock Added Artist");
  await page.locator("#addCategory").selectOption("Pop");
  await page.locator("#addLyrics").fill("[00:00.00]Added lyric line");
  await uploadImage(page.locator("#addImageFile"), MOCK_IMAGE);
}

test.describe("Admin music", () => {
  test("lists, paginates, and searches music records", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Music");
    await expect(page.locator("#musicTableBody tr")).toHaveCount(10);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 2");
    await expect(page.locator("#musicTableBody")).toContainText(
      "Mock Admin Track 12"
    );

    await page.locator("#nextPage").click();
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 | 2");
    await expect(page.locator("#musicTableBody tr")).toHaveCount(2);

    await page.locator("#searchInput").fill("Mock Aurora Theme");
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#musicTableBody")).toContainText(
      "Mock Aurora Theme"
    );
  });

  test("toggles between upload and URL music sources", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addMusicFileGroup")).toBeVisible();
    await expect(page.locator("#addMusicUrlGroup")).toBeHidden();
    await expect(page.locator("#addMusicSourceLabel")).toHaveText(
      "Upload MP3 File"
    );

    await page.locator("#addMusicSourceToggle").check();
    await expect(page.locator("#addMusicFileGroup")).toBeHidden();
    await expect(page.locator("#addMusicUrlGroup")).toBeVisible();
    await expect(page.locator("#addMusicSourceLabel")).toHaveText(
      "From URL (convert to MP3)"
    );

    await page.locator("#addMusicSourceToggle").uncheck();
    await expect(page.locator("#addMusicFileGroup")).toBeVisible();
    await expect(page.locator("#addMusicUrlGroup")).toBeHidden();
  });

  test("validates required fields and the selected source", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addMusicBtn").click();
    await expect(toastMessage(page)).toContainText("All fields are required.");

    await fillBasics(page);
    await page.locator("#addMusicBtn").click();
    await expect(toastMessage(page)).toContainText(
      "Please select a music file."
    );

    await page.locator("#addMusicSourceToggle").check();
    await page.locator("#addMusicBtn").click();
    await expect(toastMessage(page)).toContainText(
      "Please enter a music URL."
    );
    await expect(page.locator("#addMusicModal")).toHaveClass(/show/);
  });

  test("adds a music record from a URL", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillBasics(page);
    await page.locator("#addMusicSourceToggle").check();
    await page.locator("#addMusicUrl").fill("https://example.com/mock-added.mp3");
    await page.locator("#addMusicBtn").click();

    await expect(toastMessage(page)).toContainText("music added successfully");
    await expect(page.locator("#addMusicModal")).not.toHaveClass(/show/);
    await expect(page.locator("#musicTableBody")).toContainText(
      "Mock Added Track"
    );
    expect(mockSite.admin.music).toHaveLength(13);
    expect(mockSite.admin.music.at(-1).url).toBe(
      "https://example.com/mock-added.mp3"
    );
    expect(mockSite.admin.music.at(-1).category).toBe("Pop");
  });

  test("edits a music record", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#musicTableBody tr").first().getByRole("button", { name: /Edit/ }).click();

    const modal = page.locator(".modal.show").last();
    await expect(modal).toBeVisible();
    await modal.locator("input[id^='editTitle']").fill("Mock Updated Track");
    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText("music updated successfully");
    await expect(page.locator("#musicTableBody")).toContainText(
      "Mock Updated Track"
    );
    expect(
      mockSite.admin.music.find((item) => item._id === "pw-admin-music-12").title
    ).toBe("Mock Updated Track");
  });

  test("deletes a music record after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#musicTableBody tr").first().getByRole("button", { name: /Delete/ }).click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Are you sure you want to delete"
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("Music deleted successfully");
    expect(mockSite.admin.music).toHaveLength(11);
    await expect(page.locator("#musicTableBody")).not.toContainText(
      "Mock Admin Track 12"
    );
  });

  test("opens the music image preview", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#musicTableBody img").first().click();

    await expect(page.locator("#adminImagePreviewModal")).toHaveClass(/show/);
    await expect(page.locator("#adminImagePreviewTitle")).toHaveText("Music Image");
  });

  test("uses mobile image upload controls", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addImageFileMobile")).toBeVisible();
    await expect(page.locator("#addImageFile")).toBeHidden();
    await expect(page.locator("#addMusicSourceToggle")).toBeVisible();
  });
});
