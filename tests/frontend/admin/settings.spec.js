import { expect, test } from "../support/test.js";
import {
  MOCK_IMAGE,
  openAdminPage,
  toastMessage,
  uploadImage,
} from "../support/admin-page.js";

const PAGE_PATH = "/admin/settings";

async function waitForOtpEmail(page) {
  await expect(page.locator("#otpEmailContent")).toBeVisible();
  await expect(page.locator("#otpEmailInput")).not.toHaveValue("");
}

test.describe("Admin settings", () => {
  test("renders profile details and loads the OTP email", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator(".app-content-header h3")).toHaveText("Settings");
    await expect(page.locator("#username")).toHaveValue("Mock Admin");
    await expect(page.locator("#profileImagePreview")).toHaveAttribute(
      "src",
      "/static/images/user.webp"
    );
    await expect(page.locator("#password")).toHaveValue("");
    await expect(page.locator("#confirmPassword")).toHaveValue("");

    await expect(page.locator("#otpEmailSkeleton")).toBeVisible();
    await waitForOtpEmail(page);
    await expect(page.locator("#otpEmailInput")).toHaveValue(
      /@example\.com$/
    );
    await expect(page.locator("#saveOtpEmailBtn")).toBeEnabled();
  });

  test("validates username, password, and profile image fields", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);

    await page.locator("#username").fill("");
    await page.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.locator("#usernameError")).toHaveText(
      "Username is required."
    );

    await page.locator("#username").fill("abc");
    await page.locator("#password").fill("123");
    await page.locator("#confirmPassword").fill("456");
    await page.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.locator("#usernameError")).toHaveText(
      "Username must be at least 5 characters."
    );
    await expect(page.locator("#passwordError")).toHaveText(
      "Password must be at least 5 characters."
    );
    await expect(page.locator("#confirmPasswordError")).toHaveText(
      "Passwords do not match."
    );

    await page.locator("#username").fill("Mock Admin");
    await page.locator("#password").fill("");
    await page.locator("#confirmPassword").fill("12345");
    await page.locator("#profileImage").setInputFiles({
      name: "not-an-image.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("not an image"),
    });
    await page.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.locator("#confirmPasswordError")).toHaveText(
      "Enter password first."
    );
    await expect(page.locator("#profileImageError")).toHaveText(
      "Please upload a valid image file."
    );
  });

  test("previews the selected profile image", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await uploadImage(page.locator("#profileImage"));

    await expect(page.locator("#profileImagePreview")).toHaveAttribute(
      "src",
      /^data:image\/png;base64,/
    );
  });

  test("updates the profile and refreshes the preview", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#username").fill("Mock Admin Updated");
    await uploadImage(page.locator("#profileImage"));
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(toastMessage(page)).toContainText("Profile updated successfully!");
    await expect(page.locator("#profileImagePreview")).toHaveAttribute(
      "src",
      "/static/images/avatars/avatar_orange.svg"
    );
    await page.waitForURL(/\/admin\/settings$/);
  });

  test("logs out after changing the password", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await page.locator("#username").fill("Mock Admin");
    await page.locator("#password").fill("new-password");
    await page.locator("#confirmPassword").fill("new-password");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(toastMessage(page)).toContainText("Profile updated successfully!");
    await expect(page).toHaveURL(/\/admin\/login$/, { timeout: 7000 });
    await expect(page.locator(".alert-success")).toContainText(
      "You have been logged out successfully."
    );
  });

  test("validates and saves the OTP email", async ({ page }) => {
    await openAdminPage(page, PAGE_PATH);
    await waitForOtpEmail(page);

    await page.locator("#otpEmailInput").fill("invalid-email");
    await page.locator("#saveOtpEmailBtn").click();
    await expect(page.locator("#otpEmailError")).toHaveText(
      "Please enter a valid email address."
    );
    await expect(page.locator("#otpEmailStatus")).toHaveText("Invalid email.");

    await page.locator("#otpEmailInput").fill("updated-admin@example.com");
    await page.locator("#saveOtpEmailBtn").click();

    await expect(toastMessage(page)).toContainText("OTP email updated successfully.");
    const response = await page.request.get("/admin/api/otp/email");
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.email).toBe("updated-admin@example.com");
  });

  test("keeps settings forms usable on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdminPage(page, PAGE_PATH);

    await expect(page.locator("#username")).toBeVisible();
    await expect(page.locator("#profileImagePreview")).toBeVisible();
    await expect(page.getByRole("button", { name: "Save Changes" })).toBeVisible();
    await expect(page.locator("#saveOtpEmailBtn")).toBeVisible();
  });
});
