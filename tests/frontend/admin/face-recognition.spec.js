import { expect, test } from "../support/test.js";
import { openAdminPage } from "../support/admin-page.js";

const PAGE_PATH = "/admin/face-recognition";

async function stubFaceCamera(page, { deny = false } = {}) {
  await page.addInitScript(
    ({ denied }) => {
      if (!navigator.mediaDevices) {
        Object.defineProperty(navigator, "mediaDevices", {
          configurable: true,
          value: {},
        });
      }

      navigator.mediaDevices.getUserMedia = async () => {
        if (denied) {
          throw new DOMException("Permission denied", "NotAllowedError");
        }
        return new MediaStream();
      };

      Object.defineProperty(HTMLVideoElement.prototype, "videoWidth", {
        configurable: true,
        get() {
          return 640;
        },
      });
      Object.defineProperty(HTMLVideoElement.prototype, "videoHeight", {
        configurable: true,
        get() {
          return 480;
        },
      });

      const originalGetContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (type, ...args) {
        if (type === "2d") {
          return { drawImage() {} };
        }
        return originalGetContext.call(this, type, ...args);
      };
      HTMLCanvasElement.prototype.toDataURL = function () {
        return "data:image/jpeg;base64,bW9jaw==";
      };
    },
    { denied: deny }
  );
}

async function waitForCamera(page) {
  await expect(page.locator("#faceStatus")).toHaveText(
    "Camera ready. Register your face, then verify."
  );
}

test.describe("Admin face recognition", () => {
  test("redirects face-verified admins to the dashboard", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
  });

  test("starts the camera and enables both actions", async ({ page }) => {
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });

    await expect(page.locator(".app-content-header h3")).toHaveText(
      "Face Recognition"
    );
    await waitForCamera(page);
    await expect(page.locator("#registerBtn")).toBeEnabled();
    await expect(page.locator("#verifyBtn")).toBeEnabled();
  });

  test("registers a face and keeps verification available", async ({
    page,
    mockSite,
  }) => {
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });
    await waitForCamera(page);

    await page.locator("#registerBtn").click();

    await expect(page.locator("#faceStatus")).toHaveText(
      "Face registered successfully."
    );
    await expect(page.locator("#registerBtn")).toBeEnabled();
    await expect(page.locator("#verifyBtn")).toBeEnabled();
    expect(mockSite.admin.face.registered).toBe(1);
  });

  test("reports a failed registration and restores the actions", async ({
    page,
    mockSite,
  }) => {
    mockSite.admin.face.failRegister = true;
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });
    await waitForCamera(page);

    await page.locator("#registerBtn").click();

    await expect(page.locator("#faceStatus")).toHaveText("No face detected.");
    await expect(page.locator("#registerBtn")).toBeEnabled();
    await expect(page.locator("#verifyBtn")).toBeEnabled();
    expect(mockSite.admin.face.registered).toBe(0);
  });

  test("reports a failed verification and allows retrying", async ({
    page,
    mockSite,
  }) => {
    mockSite.admin.face.failVerify = true;
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });
    await waitForCamera(page);

    await page.locator("#verifyBtn").click();

    await expect(page.locator("#faceStatus")).toHaveText("Face did not match.");
    await expect(page.locator("#registerBtn")).toBeEnabled();
    await expect(page.locator("#verifyBtn")).toBeEnabled();
    await expect(page).toHaveURL(/\/admin\/face-recognition$/);
  });

  test("verifies a face and unlocks the dashboard session", async ({
    page,
    mockSite,
  }) => {
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });
    await waitForCamera(page);

    await page.locator("#verifyBtn").click();

    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
    expect(mockSite.admin.face.verified).toBe(1);

    await page.goto(PAGE_PATH, { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\/admin\/dashboard$/);
  });

  test("handles denied camera access with disabled actions", async ({ page }) => {
    await stubFaceCamera(page, { deny: true });
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });

    await expect(page.locator("#faceStatus")).toContainText("Camera error:");
    await expect(page.locator("#registerBtn")).toBeDisabled();
    await expect(page.locator("#verifyBtn")).toBeDisabled();
  });

  test("keeps the face recognition actions usable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await stubFaceCamera(page);
    await openAdminPage(page, PAGE_PATH, { faceVerified: false });
    await waitForCamera(page);

    await expect(page.locator("#faceVideo")).toBeVisible();
    await expect(page.locator("#registerBtn")).toBeVisible();
    await expect(page.locator("#verifyBtn")).toBeVisible();
  });
});
