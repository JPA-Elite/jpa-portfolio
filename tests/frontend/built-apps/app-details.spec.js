import { expect, test } from "../support/test.js";

const APP_PATH = "/apps/mock-app";

async function openAppDetails(page, waitForVotes = false) {
  const countsResponse = waitForVotes
    ? page.waitForResponse(
        (response) =>
          response.url().includes("/api/built-app-like/counts") && response.ok()
      )
    : null;

  await page.goto(APP_PATH, { waitUntil: "domcontentloaded" });

  if (countsResponse) {
    await countsResponse;
  }
}

function voteCount(value) {
  return Number(String(value).trim());
}

async function toggleVote(page, button) {
  const voteResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/built-app-like/vote") &&
      response.request().method() === "POST"
  );
  const countsResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/built-app-like/counts") && response.ok()
  );

  await button.click();
  await voteResponse;
  await countsResponse;
}

test.describe("Built app details", () => {
  test("opens the app download link in a new tab", async ({ page }) => {
    await openAppDetails(page);

    const download = page.locator(".app-details__download");
    await expect(download).toContainText(/download/i);
    await expect(download).toHaveAttribute("target", "_blank");
    await expect(download).toHaveAttribute("href", /^https?:\/\//);

    const [popup] = await Promise.all([page.waitForEvent("popup"), download.click()]);
    await expect.poll(() => popup.url()).toMatch(/^https?:\/\//);
    await popup.close();
  });

  test("toggles like and dislike votes", async ({ page }) => {
    await openAppDetails(page, true);

    const actions = page.locator("[data-app-actions]");
    const like = actions.locator('[data-app-vote="1"]');
    const dislike = actions.locator('[data-app-vote="0"]');
    const likeCount = actions.locator("[data-app-like-count]");
    const dislikeCount = actions.locator("[data-app-dislike-count]");

    await expect(like).not.toHaveClass(/is-voted/);
    await expect(dislike).not.toHaveClass(/is-voted/);

    const baseLike = voteCount(await likeCount.innerText());
    const baseDislike = voteCount(await dislikeCount.innerText());

    await toggleVote(page, like);
    await expect(like).toHaveClass(/is-voted/);
    await expect(dislike).not.toHaveClass(/is-voted/);
    await expect(likeCount).toHaveText(String(baseLike + 1));
    await expect(dislikeCount).toHaveText(String(baseDislike));

    await toggleVote(page, like);
    await expect(like).not.toHaveClass(/is-voted/);
    await expect(likeCount).toHaveText(String(baseLike));
    await expect(dislikeCount).toHaveText(String(baseDislike));

    await toggleVote(page, dislike);
    await expect(dislike).toHaveClass(/is-voted/);
    await expect(like).not.toHaveClass(/is-voted/);
    await expect(dislikeCount).toHaveText(String(baseDislike + 1));
    await expect(likeCount).toHaveText(String(baseLike));

    await toggleVote(page, dislike);
    await expect(dislike).not.toHaveClass(/is-voted/);
    await expect(dislikeCount).toHaveText(String(baseDislike));
    await expect(likeCount).toHaveText(String(baseLike));
  });

  test("copies the app URL from the share button", async ({ page }) => {
    await page.addInitScript(() => {
      const originalExecCommand = document.execCommand.bind(document);
      document.execCommand = function (command) {
        if (command === "copy") {
          const area = document.querySelector("textarea[readonly]");
          window.__copiedShareText = area ? area.value : "";
        }
        return originalExecCommand.apply(document, arguments);
      };
    });

    await openAppDetails(page);

    const share = page.locator("[data-app-share]");
    const label = share.locator(".action-state-label");

    await expect(label).toHaveText(/^share$/i);
    await share.click();

    await expect(share).toHaveClass(/is-shared/);
    await expect(label).toHaveText(/^(copied|shared)$/i);
    await expect
      .poll(() => page.evaluate(() => window.__copiedShareText))
      .toContain("/apps/mock-app");
    await expect(label).toHaveText(/^share$/i, { timeout: 5000 });
    await expect(share).not.toHaveClass(/is-shared/);
  });

  test("opens every snapshot in a modal with the matching image", async ({ page }) => {
    await openAppDetails(page);

    const previews = page.locator("[data-app-slide] img");
    const count = await previews.count();
    const modal = page.locator("#imageModal");
    const modalImage = page.locator("#modalImage");
    const counter = page.locator("#imageModalGalleryCounter");

    expect(count).toBeGreaterThan(0);

    for (let index = 0; index < count; index += 1) {
      const preview = previews.nth(index);
      const source = await preview.getAttribute("src");

      await preview.scrollIntoViewIfNeeded();
      await preview.click({ force: true });

      await expect(modal).toBeVisible();
      await expect(modalImage).toHaveAttribute("src", source);
      await expect(counter).toHaveText(`${index + 1} / ${count}`);
      await expect(page.locator("#caption")).toContainText(
        new RegExp(`Snapshots?\\s+${index + 1}\\b`)
      );

      await page.locator("#imageModal .close").click();
      await expect(modal).toBeHidden();
    }
  });

  test("matches the technology count to the technology rows", async ({ page }) => {
    await openAppDetails(page);

    const techList = page.locator("[data-tech-reveal]");
    const countLabel = page.locator(".app-details__tech-count");

    await techList.scrollIntoViewIfNeeded();
    await expect(techList).toHaveClass(/is-visible/);

    const labelText = (await countLabel.innerText()).trim();
    const declaredCount = Number(labelText.match(/\d+/)?.[0]);
    const rowCount = await page.locator("[data-tech-row]").count();

    expect(Number.isNaN(declaredCount)).toBe(false);
    expect(declaredCount).toBe(rowCount);
    expect(rowCount).toBeGreaterThan(0);
  });
});
