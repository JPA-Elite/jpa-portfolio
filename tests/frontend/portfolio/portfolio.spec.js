import { expect, test } from "../support/test.js";

async function openPortfolio(page) {
  await page.goto("/portfolio", { waitUntil: "domcontentloaded" });
}

async function revealSection(page, selector) {
  const section = page.locator(selector);
  await section.scrollIntoViewIfNeeded();
  await expect(section).toHaveClass(/is-revealed/);
}

async function expectBlankTargetPopup(page, locator) {
  await expect(locator).toHaveAttribute("target", "_blank");
  const [popup] = await Promise.all([page.waitForEvent("popup"), locator.click()]);
  await expect.poll(() => popup.url()).toMatch(/^https?:\/\//);
  await popup.close();
}

test.describe("Portfolio", () => {
  test("opens the profile image modal from the available for work avatar", async ({ page }) => {
    await openPortfolio(page);

    const badge = page.locator(".summary-badge", { hasText: /available for work/i });
    await expect(badge).toBeVisible();

    const avatar = page.locator('.summary-avatar img[alt="Profile Image"]');
    await expect(avatar).toBeVisible();
    await avatar.click({ force: true });

    const modal = page.locator("#imageModal");
    await expect(modal).toBeVisible();
    await expect(page.locator("#modalImage")).toBeVisible();
    await expect(page.locator("#caption")).toContainText("My Profile");
  });

  test("opens activity snapshots modal and navigates multiple contents", async ({ page }) => {
    await openPortfolio(page);

    const activity = page.locator(".career-roadmap__activity-card").first();
    await activity.scrollIntoViewIfNeeded();
    await activity.click({ force: true });

    const modal = page.locator("#imageModal");
    const counter = page.locator("#imageModalGalleryCounter");
    const modalImage = page.locator("#modalImage");
    const next = page.locator("#imageModalNext");
    const prev = page.locator("#imageModalPrev");

    await expect(modal).toBeVisible();
    await expect(modalImage).toBeVisible();
    await expect(counter).toHaveText(/^1 \/ \d+$/);
    const firstSource = await modalImage.getAttribute("src");

    await expect(next).toBeVisible();
    await expect(prev).toBeVisible();
    await next.click();
    await expect(counter).toHaveText(/^2 \/ \d+$/);
    await expect.poll(() => modalImage.getAttribute("src")).not.toBe(firstSource);

    await prev.click();
    await expect(counter).toHaveText(/^1 \/ \d+$/);
    await expect(modalImage).toHaveAttribute("src", firstSource);
  });

  test("opens a key project modal", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#key-projects");

    const project = page.locator(".kanban-project-card").first();
    const title = (await project.locator("h4").innerText()).trim();
    const media = project.locator(".kanban-project-card__media");
    await media.scrollIntoViewIfNeeded();
    await media.click({ force: true });

    await expect(page.locator("#imageModal")).toBeVisible();
    await expect(page.locator("#modalImage")).toBeVisible();
    await expect(page.locator("#caption")).toContainText(title);
  });

  test("opens the key project preview modal", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#key-projects");

    const preview = page.locator(".kanban-action-link--ghost").first();
    await preview.scrollIntoViewIfNeeded();
    await preview.click();

    await expect(page.locator("#imageModal")).toBeVisible();
    await expect(page.locator("#modalImage")).toBeVisible();
  });

  test("opens a built app details page from view details", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#key-projects");

    const card = page.locator(".store-card").first();
    const appName = (await card.locator(".store-card__name").innerText()).trim();
    const viewDetails = card.locator(".store-card__view");

    await expect(viewDetails).toContainText(/view details/i);
    await viewDetails.scrollIntoViewIfNeeded();
    await viewDetails.click();

    await expect(page).toHaveURL(/\/apps\/[^/]+$/);
    await expect(page.locator(".app-details h1")).toHaveText(appName);
  });

  test("opens key project demo and repo links in new tabs", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#key-projects");

    const project = page.locator(".kanban-project-card").first();
    const demo = project.locator("a.kanban-action-link--view", { hasText: "Demo" });
    const repo = project.locator("a.kanban-action-link--view", { hasText: "Repo" });

    await expect(demo).toBeVisible();
    await expect(repo).toBeVisible();
    await expectBlankTargetPopup(page, demo);
    await expectBlankTargetPopup(page, repo);
  });

  test("switches between technical skills, frameworks, and tools tabs", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#key-projects");

    const targets = ["technical", "frameworks", "tools"];

    for (const target of targets) {
      const tab = page.locator(`.skills-tabs .tab[data-target="${target}"]`);
      await tab.scrollIntoViewIfNeeded();
      await tab.click();

      await expect(tab).toHaveClass(/active/);
      await expect(page.locator(`#${target}`)).toHaveClass(/active/);
      await expect(page.locator(`#${target}`)).toBeVisible();

      for (const other of targets.filter((value) => value !== target)) {
        await expect(page.locator(`#${other}`)).toBeHidden();
      }
    }
  });

  test("opens the certifications modal", async ({ page }) => {
    await openPortfolio(page);
    await revealSection(page, "#certifications");

    const card = page.locator(".cert-polaroid__card").first();
    const title = (await card.locator(".cert-polaroid__caption").textContent()).trim();
    await card.scrollIntoViewIfNeeded();
    await card.click();

    await expect(page.locator("#imageModal")).toBeVisible();
    await expect(page.locator("#modalImage")).toBeVisible();
    await expect(page.locator("#caption")).toContainText(title);
    await expect(page.locator("#imageModalGalleryCounter")).toHaveText(/^1 \/ \d+$/);
  });

  test("toggles the footer theme", async ({ page }) => {
    await openPortfolio(page);

    const html = page.locator("html");
    const toggle = page.locator("#themeToggle");
    const initialTheme = (await html.getAttribute("data-theme")) || "light";
    const expectedTheme = initialTheme === "light" ? "dark" : "light";

    await toggle.scrollIntoViewIfNeeded();
    await toggle.click();

    await expect(html).toHaveAttribute("data-theme", expectedTheme);
    await expect.poll(() => page.evaluate(() => localStorage.getItem("theme"))).toBe(expectedTheme);
  });

  test("opens footer co-developer links in new tabs", async ({ page }) => {
    await openPortfolio(page);

    const links = page.locator(".social-footer__collab");
    const count = await links.count();
    expect(count).toBeGreaterThan(0);

    for (let index = 0; index < count; index += 1) {
      await expectBlankTargetPopup(page, links.nth(index));
    }
  });

  test("switches from professional mode to social mode", async ({ page }) => {
    await openPortfolio(page);

    const modeButton = page.locator("#modeToggleBtn");
    await expect(modeButton).toBeVisible();
    await expect(page.locator("#modeToggleLabel")).toContainText(/social/i);

    await Promise.all([
      page.waitForURL((url) => url.hostname === "jpastack.local"),
      modeButton.click(),
    ]);

    await expect(page).toHaveURL(/^http:\/\/jpastack\.local(?::\d+)?\/portfolio$/);
  });

  test("does not render the admin panel in professional mode", async ({ page }) => {
    await openPortfolio(page);
    await expect(page.locator("#adminFloat")).toHaveCount(0);
  });

  test("expands and minimizes the admin panel in social mode", async ({
    page,
    baseURL,
  }) => {
    const socialUrl = new URL(baseURL);
    socialUrl.hostname = "jpastack.local";
    socialUrl.pathname = "/portfolio";
    socialUrl.search = "";
    socialUrl.hash = "";

    await page.goto(socialUrl.toString(), { waitUntil: "domcontentloaded" });

    const adminFloat = page.locator("#adminFloat");
    const toggle = adminFloat.locator(".admin-float-toggle");

    await expect(adminFloat).toBeVisible();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(toggle).toHaveAttribute("aria-label", "Maximize Admin Panel");

    await toggle.click();
    await expect(adminFloat).toHaveClass(/is-maximized/);
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(toggle).toHaveAttribute("aria-label", "Minimize Admin Panel");

    await toggle.click();
    await expect(adminFloat).not.toHaveClass(/is-maximized/);
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(toggle).toHaveAttribute("aria-label", "Maximize Admin Panel");
  });
});
