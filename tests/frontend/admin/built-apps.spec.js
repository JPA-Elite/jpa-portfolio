import { expect, test } from "../support/test.js";
import {
  confirmDelete,
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/built-apps";

async function openAddModal(page) {
  await page.getByRole("button", { name: /Add App/ }).click();
  await expect(page.locator("#addAppModal")).toHaveClass(/show/);
}

async function fillAppForm(page, name = "Mock Added App") {
  await page.locator("#addNameEn").fill(name);
  await page.locator("#addNameCeb").fill(name);
  await page.locator("#addNameFr").fill(name);
  await page.locator("#addNameFil").fill(name);
  await page.locator("#addShortEn").fill("Added app short description");
  await page.locator("#addFullEn").fill("Added app full description paragraph.");
  await page.locator("#addPlatform").selectOption("Desktop");
  await page.locator("#addVersion").fill("2.0.0");
  await page.locator("#addIcon").fill("bi-window");
  await page.locator("#addDownloadUrl").fill("https://example.com/mock-added-app.zip");
  await page.locator("#addSortOrder").fill("9");
  await page.locator("#addTechnologiesContainer [data-tech-value]").fill("Flask");
  await uploadImage(page.locator("#addIconImage"));
  await uploadImage(page.locator("#addSnapshotFiles"));
}

test.describe("Admin built apps", () => {
  test("lists and filters built apps", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Built Apps");
    await expect(page.locator("#builtAppsTableBody tr")).toHaveCount(6);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 | 1");
    await expect(page.locator("#builtAppsTableBody tr").first()).toContainText(
      "Mock App One"
    );

    await page.locator("#platformFilterSelect").selectOption("mobile");
    await expect(page.locator("#builtAppsTableBody tr")).toHaveCount(3);

    await page.locator("#platformFilterSelect").selectOption("");
    await page.locator("#activeFilterSelect").selectOption("false");
    await expect(page.locator("#builtAppsTableBody tr")).toHaveCount(1);

    await page.locator("#activeFilterSelect").selectOption("");
    await page.locator("#searchInput").fill("Mock App One");
    await expect(page.locator("#builtAppsTableBody tr")).toHaveCount(1);
    await expect(page.locator("#builtAppsTableBody")).toContainText("Mock App One");
  });

  test("selects and accumulates files through the dropzone picker", async ({
    page,
  }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    const modal = page.locator("#addAppModal");
    const iconZone = modal.locator("#addIconImage + .ba-dropzone");
    const snapshotZone = modal.locator("#addSnapshotFiles + .ba-dropzone");

    const iconChooserPromise = page.waitForEvent("filechooser");
    await iconZone.click();
    const iconChooser = await iconChooserPromise;
    await iconChooser.setFiles(MOCK_IMAGE);

    await expect(modal.locator("#addIconImagePreview .ba-dropthumb")).toHaveCount(
      1
    );
    await expect
      .poll(() =>
        page.locator("#addIconImage").evaluate((input) => input.files.length)
      )
      .toBe(1);

    const firstSnapshotChooserPromise = page.waitForEvent("filechooser");
    await snapshotZone.click();
    const firstSnapshotChooser = await firstSnapshotChooserPromise;
    await firstSnapshotChooser.setFiles(MOCK_IMAGE);

    const secondSnapshotChooserPromise = page.waitForEvent("filechooser");
    await snapshotZone.click();
    const secondSnapshotChooser = await secondSnapshotChooserPromise;
    await secondSnapshotChooser.setFiles({
      ...MOCK_IMAGE,
      name: "mock-admin-image-2.png",
    });

    await expect(
      modal.locator("#addSnapshotFilesPreview .ba-dropthumb")
    ).toHaveCount(2);
    await expect
      .poll(() =>
        page
          .locator("#addSnapshotFiles")
          .evaluate((input) => input.files.length)
      )
      .toBe(2);

    await modal
      .locator("#addSnapshotFilesPreview .ba-dropthumb")
      .first()
      .getByRole("button", { name: "Remove photo" })
      .click();

    await expect(
      modal.locator("#addSnapshotFilesPreview .ba-dropthumb")
    ).toHaveCount(1);
    await expect
      .poll(() =>
        page
          .locator("#addSnapshotFiles")
          .evaluate((input) => input.files.length)
      )
      .toBe(1);
  });

  test("requires an English app name before adding", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await page.locator("#addAppBtn").click();
    await expect(toastMessage(page)).toContainText("English name is required.");
    await expect(page.locator("#addAppModal")).toHaveClass(/show/);
  });

  test("adds a built app with technology and snapshot data", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);
    await fillAppForm(page);

    await page.locator("#addAppBtn").click();

    await expect(toastMessage(page)).toContainText("Built app added successfully");
    await expect(page.locator("#addAppModal")).not.toHaveClass(/show/);
    await expect(page.locator("#builtAppsTableBody")).toContainText("Mock Added App");

    expect(mockSite.admin.builtApps).toHaveLength(7);
    const added = mockSite.admin.builtApps.at(-1);
    expect(added.slug).toBe("mock-added-app");
    expect(added.platform).toBe("Desktop");
    expect(added.technologies[0].value).toBe("Flask");
    expect(added.snapshots).toHaveLength(1);
  });

  test("edits an app and adds a snapshot row", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#builtAppsTableBody tr")
      .first()
      .getByRole("button", { name: /Edit/ })
      .click();

    const modal = page.locator(".modal.show").last();
    await expect(modal).toBeVisible();
    await modal.locator("input[id^='editNameEn']").fill("Mock Updated App");
    await modal.locator("select[id^='editPlatform']").selectOption("Desktop");

    await modal.locator("[data-add-snapshot-row]").click();
    const snapshots = modal.locator("[data-snapshot-row]");
    await expect(snapshots).toHaveCount(2);
    await uploadImage(snapshots.last().locator("[data-snapshot-file]"));

    await modal.getByRole("button", { name: "Save changes" }).click();

    await expect(toastMessage(page)).toContainText("Built app updated successfully");
    await expect(page.locator("#builtAppsTableBody")).toContainText("Mock Updated App");

    const updated = mockSite.admin.builtApps.find(
      (item) => item._id === "pw-admin-app-01"
    );
    expect(updated.name.en).toBe("Mock Updated App");
    expect(updated.platform).toBe("Desktop");
    expect(updated.snapshots).toHaveLength(2);
  });

  test("deletes a built app after confirmation", async ({ page, mockSite }) => {
    await openAdminPage(page, PAGE_PATH);
    await page
      .locator("#builtAppsTableBody tr")
      .first()
      .getByRole("button", { name: /Delete/ })
      .click();
    await expect(page.locator("#deleteConfirmModalBody")).toContainText(
      "Its snapshots will also be removed."
    );
    await confirmDelete(page);

    await expect(toastMessage(page)).toContainText("Built app deleted successfully");
    expect(mockSite.admin.builtApps).toHaveLength(5);
    await expect(page.locator("#builtAppsTableBody")).not.toContainText(
      "Mock App One"
    );
  });

  test("keeps the add app form usable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);
    await openAddModal(page);

    await expect(page.locator("#addNameEn")).toBeVisible();
    await expect(page.locator("#addPlatform")).toBeVisible();
    await expect(page.locator("#addAppModal .ba-dropzone")).toHaveCount(2);
    await expect(page.locator("#addAppModal .ba-dropzone").first()).toBeVisible();
    await expect(page.locator("#addTechnologiesContainer [data-tech-row]")).toHaveCount(1);
  });
});
