import { expect } from "@playwright/test";

export const ADMIN_USERNAME = "admin";
export const ADMIN_PASSWORD = "admin-pass";
export const ADMIN_OTP = "123456";

export const MOCK_IMAGE = {
  name: "mock-admin-image.png",
  mimeType: "image/png",
  buffer: Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Z0X8AAAAASUVORK5CYII=",
    "base64"
  ),
};

export const MOCK_VIDEO_FILE = {
  name: "mock-admin-video.mp4",
  mimeType: "video/mp4",
  buffer: Buffer.from("mock-video-content"),
};

export async function loginAsAdmin(page, { faceVerified = true } = {}) {
  const response = await page.request.get(
    `/__playwright/admin-session?face_verified=${faceVerified ? "1" : "0"}`
  );
  expect(response.status()).toBe(204);
}

export async function openAdminPage(page, path, options = {}) {
  await loginAsAdmin(page, options);
  await page.goto(path, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".app-content").first()).toBeVisible();
}

export async function uploadImage(locator, file = MOCK_IMAGE) {
  await locator.setInputFiles(file);
}

export async function closeToast(page) {
  const close = page.locator(".toast-item .toast-close").last();
  if (await close.isVisible().catch(() => false)) {
    await close.click();
  }
}

export function toastMessage(page) {
  return page.locator(".toast-item .toast-message").last();
}

export async function confirmDelete(page) {
  const modal = page.locator("#deleteConfirmModal");
  await expect(modal).toHaveClass(/show/);
  await page.locator("#confirmDeleteBtn").click();
  await expect(modal).not.toHaveClass(/show/);
}

export async function expectNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

export async function waitForTable(page, selector, minimumRows = 1) {
  const table = page.locator(selector);
  await expect
    .poll(async () => table.locator("tr").count())
    .toBeGreaterThanOrEqual(minimumRows);
  return table;
}
