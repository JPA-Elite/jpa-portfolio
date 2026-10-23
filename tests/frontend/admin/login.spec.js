import { expect, test } from "../support/test.js";
import {
  ADMIN_OTP,
  ADMIN_PASSWORD,
  ADMIN_USERNAME,
  loginAsAdmin,
} from "../support/admin-page.js";

const LOGIN_PATH = "/admin/login";

async function submitCredentials(page, { username = ADMIN_USERNAME, password = ADMIN_PASSWORD, remember = false } = {}) {
  await page.locator("#username").fill(username);
  await page.locator("#password").fill(password);
  if (remember) {
    await page.locator("#remember").check();
  }
  await page.getByRole("button", { name: "Sign In" }).click();
}

async function completeOtpGate(page) {
  await expect(page.locator("#otpVerifyModal")).toHaveClass(/show/);
  await expect(page.locator("#otpModalStatus")).toContainText("OTP is ready");
  await page.locator("#sendOtpBtn").click();
  await expect(page.locator("#otpModalStatus")).toContainText("OTP sent to your email.");
  await page.locator("#otpCodeInput").fill(ADMIN_OTP);
  await page.locator("#verifyOtpBtn").click();
  await expect(page).toHaveURL(/\/admin\/dashboard$/);
}

test.describe("Admin login", () => {
  test("redirects unauthenticated admin pages to the login form", async ({ page }) => {
    await page.goto("/admin/dashboard", { waitUntil: "domcontentloaded" });

    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.locator(".alert-warning")).toContainText(
      "Please log in to access this page."
    );
    await expect(page.getByPlaceholder("Username")).toBeVisible();
  });

  test("renders the login form without opening the OTP modal", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });

    await expect(page.getByText("JPA-Admin")).toBeVisible();
    await expect(page.getByText("Sign in to start your session")).toBeVisible();
    await expect(page.locator("#username")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.locator("#remember")).not.toBeChecked();
    await expect(page.getByRole("link", { name: /Back/ })).toHaveAttribute(
      "href",
      "/portfolio"
    );
    await expect(page.locator("#otpVerifyModal")).toHaveAttribute(
      "data-show-face-modal",
      "0"
    );
    await expect(page.locator("#otpVerifyModal")).not.toHaveClass(/show/);
  });

  test("shows client-side validation errors before submitting", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.locator(".invalid-feedback-custom")).toHaveCount(2);
    await expect(page.getByText("Username is required.")).toBeVisible();
    await expect(page.getByText("Password is required.")).toBeVisible();
    await expect(page).toHaveURL(/\/admin\/login$/);
  });

  test("clears client validation errors while typing", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page.locator(".invalid-feedback-custom")).toHaveCount(2);

    await page.locator("#username").fill(ADMIN_USERNAME);
    await page.locator("#password").fill(ADMIN_PASSWORD);

    await expect(page.locator(".invalid-feedback-custom")).toHaveCount(0);
  });

  test("rejects invalid admin credentials", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await submitCredentials(page, { password: "wrong-password" });

    await expect(page.locator(".alert-warning")).toContainText(
      "Invalid username or password."
    );
    await expect(page).toHaveURL(/\/admin\/login$/);
    await expect(page.locator("#otpVerifyModal")).not.toHaveClass(/show/);
  });

  test("opens the OTP gate after a successful password login", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await submitCredentials(page);

    await expect(page.locator(".alert-success")).toContainText(
      "Welcome back, Admin!"
    );
    await expect(page.locator("#otpVerifyModal")).toHaveClass(/show/);
    await expect(page.locator("#otpVerifyModal")).toHaveAttribute(
      "data-show-face-modal",
      "1"
    );
    await expect(page.locator("#otpModalStatus")).toContainText("OTP is ready");
    await expect(page.locator("#otpSavedEmail")).toContainText(
      "OTP will be sent to the authorized email"
    );
    await expect(page.locator("#sendOtpBtn")).toBeEnabled();
    await expect(page.locator("#otpCodeInput")).toBeDisabled();
  });

  test("validates the OTP and redirects to the dashboard", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await submitCredentials(page);
    await expect(page.locator("#otpVerifyModal")).toHaveClass(/show/);

    await page.locator("#sendOtpBtn").click();
    await expect(page.locator("#otpModalStatus")).toContainText(
      "OTP sent to your email."
    );
    await expect(page.locator("#otpCodeInput")).toBeEnabled();

    await page.locator("#otpCodeInput").fill("000000");
    await page.locator("#verifyOtpBtn").click();
    await expect(page.locator("#otpModalStatus")).toContainText("Invalid OTP.");
    await expect(page).toHaveURL(/\/admin\/login$/);

    await page.locator("#otpCodeInput").fill(ADMIN_OTP);
    await page.locator("#verifyOtpBtn").click();
    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
  });

  test("keeps the session when remember me is checked", async ({ page }) => {
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });
    await submitCredentials(page, { remember: true });
    await completeOtpGate(page);

    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((cookie) => cookie.name === "session");
    expect(sessionCookie).toBeTruthy();
    expect(sessionCookie.expires).toBeGreaterThan(0);
  });

  test("redirects an authenticated admin away from the login page", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto(LOGIN_PATH, { waitUntil: "domcontentloaded" });

    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    await expect(page.locator(".app-content-header h3")).toHaveText("Dashboard");
  });
});
