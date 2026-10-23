import { expect, test } from "./test.js";
import {
  CONTENT_CONFIG,
  clickConfirm,
  clickWithoutOverlay,
  closeEditProfile,
  expectContentStats,
  openCommentModal,
  openContentPage,
  openEditProfile,
  stubShareClipboard,
  stubSpeechRecognition,
} from "./content-page.js";

function cardLikeResponse(page, config) {
  return page.waitForResponse(
    (response) =>
      response.url().includes(config.likeBasePath) &&
      response.request().method() === "POST"
  );
}

function commentApiResponse(page, config, suffix, method) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === `${config.commentBasePath}${suffix}` &&
      response.request().method() === method
    );
  });
}

export function registerContentPageTests(kind) {
  const config = CONTENT_CONFIG[kind];
  const label = kind === "gallery" ? "gallery" : "vlog";

  test("matches search text in titles and descriptions", async ({ page }) => {
    await openContentPage(page, kind);

    const search = page.locator("#search-input");
    const items = page.locator(config.itemSelector);

    await search.fill(config.searchTerm);
    await Promise.all([
      page.waitForURL(
        (url) => url.searchParams.get("search") === config.searchTerm
      ),
      search.press("Enter"),
    ]);

    await expect(items).toHaveCount(1);
    await expect(items.locator(config.titleSelector)).toContainText(
      config.searchTerm
    );
    await expectContentStats(page, config, 1, 1);

    await search.fill(config.searchDescription);
    await Promise.all([
      page.waitForURL(
        (url) => url.searchParams.get("search") === config.searchDescription
      ),
      search.press("Enter"),
    ]);

    await expect(items).toHaveCount(1);
    await expect(items.locator(config.titleSelector)).toContainText(
      kind === "gallery" ? "Mock Gallery Forest" : "Mock Vlog Second"
    );
    await expectContentStats(page, config, 1, 1);
  });

  test(`filters ${label} cards using a tag`, async ({ page }) => {
    await openContentPage(page, kind);

    await page.locator("#search-input").focus();
    const tagButton = page.locator(".tag-button", { hasText: config.tag }).first();
    await expect(tagButton).toBeVisible();
    await tagButton.click();
    await expect(page.locator("#tags-input")).toHaveValue(config.tag);

    await Promise.all([
      page.waitForURL(
        (url) => url.searchParams.get("tags") === config.tag
      ),
      page.locator(".search-next").click(),
    ]);

    const items = page.locator(config.itemSelector);
    await expect(items).toHaveCount(config.tagItemCount);
    await expectContentStats(page, config, 1, 1);

    for (let index = 0; index < config.tagItemCount; index += 1) {
      await expect(
        items.nth(index).locator(".tag").filter({ hasText: `#${config.tag}` })
      ).toHaveCount(1);
    }
  });

  test("matches the page statistics with pagination and navigates pages", async ({
    page,
  }) => {
    await openContentPage(page, kind);

    const items = page.locator(config.itemSelector);
    await expect(items).toHaveCount(config.perPage);
    await expectContentStats(page, config, 1, config.totalPages);

    const next = page.locator('.pagination a[href*="page=2"]');
    await Promise.all([
      page.waitForURL((url) => url.searchParams.get("page") === "2"),
      next.click(),
    ]);

    await expect(items).toHaveCount(config.totalItems - config.perPage);
    await expectContentStats(page, config, 2, config.totalPages);

    const previous = page.locator('.pagination a[href*="page=1"]');
    await Promise.all([
      page.waitForURL((url) => url.searchParams.get("page") === "1"),
      previous.click(),
    ]);

    await expect(items).toHaveCount(config.perPage);
    await expectContentStats(page, config, 1, config.totalPages);
  });

  test(`opens every ${label} card in its modal`, async ({ page }) => {
    await openContentPage(page, kind);

    const cards = page.locator(config.itemSelector);
    const count = await cards.count();
    expect(count).toBe(config.perPage);

    const modal = page.locator("#imageModal");
    const modalImage = page.locator("#modalImage");
    const modalVideo = page.locator("#modalVideo");
    const caption = page.locator("#caption");

    for (let index = 0; index < count; index += 1) {
      const card = cards.nth(index);
      const title = (await card.locator(config.titleSelector).innerText()).trim();
      const opener = card.locator(config.cardOpenSelector);
      const imageSource =
        kind === "gallery" ? await opener.getAttribute("src") : null;

      await card.scrollIntoViewIfNeeded();
      await opener.click({ force: true });

      await expect(modal).toBeVisible();
      await expect(caption).toContainText(title);
      await expect(page.locator(".comment-section")).toBeVisible();

      if (kind === "gallery") {
        await expect(modalImage).toBeVisible();
        await expect(modalImage).toHaveAttribute("src", imageSource);
      } else {
        await expect(modalVideo).toHaveCSS("display", "block");
      }

      await page.locator("#imageModal .close").click();
      await expect(modal).toBeHidden();
    }
  });

  test("toggles the card like button and updates the count", async ({ page }) => {
    await openContentPage(page, kind);

    const card = page.locator(config.itemSelector).first();
    const likeButton = card.locator(".like-btn");
    const likeCount = card.locator(".like-count");
    const commentCount = card.locator(".comment-count");

    await expect(likeCount).toHaveText("12");
    await expect(commentCount).toHaveText("3");

    const baseCount = Number((await likeCount.innerText()).trim());

    const firstResponse = cardLikeResponse(page, config);
    await likeButton.click();
    await firstResponse;

    await expect(likeButton).toHaveClass(/liked/);
    await expect(likeCount).toHaveText(String(baseCount + 1));

    const secondResponse = cardLikeResponse(page, config);
    await likeButton.click();
    await secondResponse;

    await expect(likeButton).not.toHaveClass(/liked/);
    await expect(likeCount).toHaveText(String(baseCount));
  });

  test("copies the card share link", async ({ page }) => {
    await stubShareClipboard(page);
    await openContentPage(page, kind);

    const card = page.locator(config.itemSelector).first();
    const shareButton = card.locator(".relay-btn");
    const label = shareButton.locator(".action-state-label");

    await expect(label).toHaveText(/^share$/i);
    await shareButton.click();

    await expect(label).toHaveText(/copied/i);

    const copied = await page.evaluate(() => window.__copiedShareText);
    expect(copied).toMatch(/^https?:\/\//);
    expect(copied).toContain(
      kind === "gallery" ? "/static/images/" : "example.com/mock-vlog"
    );

    await expect(label).toHaveText(/^share$/i, { timeout: 5000 });
  });

  test("likes and unlikes a comment", async ({ page }) => {
    await openCommentModal(page, kind);

    const comment = page.locator(".comment-item").first();
    const likeButton = comment.locator(".like-btn");
    const likeCount = comment.locator(".like-count");

    await expect(likeCount).toHaveText("0");

    const likedResponse = commentApiResponse(page, config, "/like", "POST");
    await likeButton.click();
    await likedResponse;

    await expect(likeButton).toHaveClass(/liked/);
    await expect(likeCount).toHaveText("1");

    const unlikedResponse = commentApiResponse(page, config, "/like", "POST");
    await likeButton.click();
    await unlikedResponse;

    await expect(likeButton).not.toHaveClass(/liked/);
    await expect(likeCount).toHaveText("0");
  });

  test("removes each own comment through the confirmation modal", async ({
    page,
  }) => {
    await openCommentModal(page, kind);

    const ownSelector = '.comment-item[data-is-own="true"]';
    const ownCount = await page.locator(ownSelector).count();
    const totalBefore = await page.locator(".comment-item").count();
    expect(ownCount).toBeGreaterThan(0);

    for (let index = 0; index < ownCount; index += 1) {
      const comment = page.locator(ownSelector).first();
      const commentId = await comment.getAttribute("data-comment-id");
      expect(commentId).toBeTruthy();

      await comment.locator(".comment-remove-btn").click();
      const deleteResponse = commentApiResponse(
        page,
        config,
        `/${commentId}`,
        "DELETE"
      );
      await clickConfirm(page);
      await deleteResponse;

      await expect(
        page.locator(`.comment-item[data-comment-id="${commentId}"]`)
      ).toHaveCount(0);
    }

    await expect(page.locator(ownSelector)).toHaveCount(0);
    await expect(page.locator(".comment-item")).toHaveCount(
      totalBefore - ownCount
    );
    await expect(page.locator("#commentCount")).toHaveText(
      String(totalBefore - ownCount)
    );
  });

  test("opens the edit profile modal and posts the saved name and comment text", async ({
    page,
  }) => {
    await openCommentModal(page, kind);

    await openEditProfile(page);
    const editModal = page.locator("#nameEditModal");
    await closeEditProfile(page);

    await clickWithoutOverlay(page.locator("#commenterEditBtn"));
    await expect(editModal).toHaveClass(/is-open/);

    await page.fill("#nameEditInput", "Playwright Tester");
    const saveResponse = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/comment-username" &&
        response.request().method() === "POST"
    );

    await page.locator("#nameEditSaveBtn").click();
    await saveResponse;
    await expect(editModal).not.toHaveClass(/is-open/);

    const ownAuthor = page.locator(
      '.comment-item[data-is-own="true"] .comment-author'
    );
    await expect(ownAuthor.first()).toHaveText("Playwright Tester");

    const text = `Rendered ${kind} comment from Playwright`;
    const countBefore = Number(
      (await page.locator("#commentCount").innerText()).trim()
    );
    await page.fill("#commentBox", text);

    const createResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname === config.commentBasePath &&
        response.request().method() === "POST"
      );
    });

    await page.locator(".send-btn").click();
    await createResponse;

    const lastComment = page.locator(".comment-item").last();
    await expect(lastComment).toHaveAttribute("data-is-own", "true");
    await expect(lastComment.locator(".comment-author")).toHaveText(
      "Playwright Tester"
    );
    await expect(lastComment.locator(".comment-text")).toHaveText(text);
    await expect(page.locator("#commentCount")).toHaveText(
      String(countBefore + 1)
    );
  });

  test("uploads, removes and selects an avatar", async ({ page }) => {
    await openCommentModal(page, kind);
    await openEditProfile(page);

    const preview = page.locator("#avatarPreview");
    await expect(preview).toHaveAttribute("src", /avatar_pink\.svg/);

    const upload = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/comment-avatar/upload" &&
        response.request().method() === "POST"
    );

    await page.setInputFiles("#avatarUploadInput", {
      name: "mock-avatar.png",
      mimeType: "image/png",
      buffer: Buffer.from("mock-avatar"),
    });
    await upload;

    await expect(preview).toHaveAttribute("src", /avatar_orange\.svg/);

    const ownAvatar = page.locator(
      '.comment-item[data-is-own="true"] .comment-avatar'
    );
    await expect(ownAvatar.first()).toHaveAttribute(
      "src",
      /avatar_orange\.svg/
    );

    const removeResponse = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/comment-avatar" &&
        response.request().method() === "DELETE"
    );
    await page.locator("#avatarRemoveBtn").click();
    await removeResponse;

    await expect(preview).toHaveAttribute("src", /user\.webp/);

    const preset = page.locator(
      '.avatar-presets__item[data-avatar-url$="avatar_blue.svg"]'
    );
    const presetResponse = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/comment-avatar" &&
        response.request().method() === "POST"
    );
    await preset.click();
    await presetResponse;

    await expect(preview).toHaveAttribute("src", /avatar_blue\.svg/);
    await expect(preset).toHaveClass(/is-selected/);
  });

  test("inserts an emoji and a speech transcript into the comment box", async ({
    page,
  }) => {
    await stubSpeechRecognition(page);
    await openCommentModal(page, kind);

    const commentBox = page.locator("#commentBox");
    const emojiToggle = page.locator("#commentEmojiToggle");
    const emojiPicker = page.locator("#commentEmojiPicker");
    const micToggle = page.locator("#commentMicToggle");

    await emojiToggle.click();
    await expect(emojiPicker).toBeVisible();
    await emojiPicker.locator("button", { hasText: "😍" }).click();
    await expect(commentBox).toHaveValue(/😍/);

    await expect(micToggle).toBeVisible();
    await micToggle.click();
    await expect(commentBox).toHaveValue(/😍 Mock voice transcript/);
  });

  test("deletes all own comments from the edit profile modal", async ({
    page,
  }) => {
    await openCommentModal(page, kind);

    const ownSelector = '.comment-item[data-is-own="true"]';
    const ownCount = await page.locator(ownSelector).count();
    const totalCount = await page.locator(".comment-item").count();
    const otherCount = totalCount - ownCount;
    expect(ownCount).toBeGreaterThan(0);

    await openEditProfile(page);

    const deleteResponse = commentApiResponse(
      page,
      config,
      "/delete-all",
      "DELETE"
    );
    const reloadResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname === config.commentBasePath &&
        url.searchParams.has(config.idParam) &&
        response.request().method() === "GET"
      );
    });

    await page.locator("#deleteAllCommentsBtn").click();
    await clickConfirm(page);
    await deleteResponse;
    await reloadResponse;

    await expect(page.locator("#nameEditModal")).not.toHaveClass(/is-open/);
    await expect(page.locator(ownSelector)).toHaveCount(0);
    await expect(page.locator(".comment-item")).toHaveCount(otherCount);
    await expect(page.locator("#commentCount")).toHaveText(String(otherCount));
  });
}
