import { expect } from "./test.js";

export const CONTENT_CONFIG = {
  gallery: {
    path: "/gallery",
    itemSelector: ".gallery-item",
    titleSelector: ".gallery-title",
    cardOpenSelector: ".gallery-image",
    commentOpenSelector: ".comment-btn",
    statSelector: ".gallery-stat-card__value",
    commentBasePath: "/api/gallery-comments",
    likeBasePath: "/api/gallery-like",
    idAttr: "data-gallery-id",
    idParam: "gallery_id",
    perPage: 6,
    totalItems: 8,
    totalPages: 2,
    tag: "alpha",
    tagItemCount: 2,
    searchTerm: "Aurora",
    searchDescription: "phosphorescent",
  },
  vlog: {
    path: "/vlog",
    itemSelector: ".video-item",
    titleSelector: ".video-title",
    cardOpenSelector: ".comment-btn",
    commentOpenSelector: ".comment-btn",
    statSelector: ".vlog-stat-card__value",
    commentBasePath: "/api/vlog-comments",
    likeBasePath: "/api/vlog-like",
    idAttr: "data-vlog-id",
    idParam: "vlog_id",
    perPage: 3,
    totalItems: 5,
    totalPages: 2,
    tag: "alpha",
    tagItemCount: 2,
    searchTerm: "Aurora",
    searchDescription: "phosphorescent",
  },
};

export async function openContentPage(page, kind) {
  const config = CONTENT_CONFIG[kind];
  await page.goto(config.path, { waitUntil: "domcontentloaded" });
  await expect(page.locator(config.itemSelector).first()).toBeVisible();
  return config;
}

export async function expectContentStats(page, config, currentPage, totalPages) {
  const stats = page.locator(config.statSelector);
  await expect(stats.nth(0)).toHaveText(String(currentPage));
  await expect(stats.nth(1)).toHaveText(String(totalPages));
  await expect(page.locator(".pagination-count")).toHaveText(
    `Page ${currentPage} of ${totalPages}`
  );
}

export async function openCommentModal(page, kind, cardIndex = 0) {
  const config = CONTENT_CONFIG[kind];
  await openContentPage(page, kind);

  const card = page.locator(config.itemSelector).nth(cardIndex);
  await card.scrollIntoViewIfNeeded();
  const title = (await card.locator(config.titleSelector).innerText()).trim();

  await card.locator(config.commentOpenSelector).click();

  await expect(page.locator("#imageModal")).toBeVisible();
  await expect(page.locator(".comment-section")).toBeVisible();
  await expect(page.locator(".comment-item").first()).toBeVisible();
  await expect(page.locator(".comment-skeleton-list")).toHaveCount(0);

  return { card, title };
}

export async function clickWithoutOverlay(locator) {
  await locator.evaluate((element) => element.click());
}

export async function openEditProfile(page) {
  await clickWithoutOverlay(page.locator("#commentHeaderEditBtn"));

  const modal = page.locator("#nameEditModal");
  await expect(modal).toHaveClass(/is-open/);
  await expect(modal).toHaveAttribute("aria-hidden", "false");
  await expect(page.locator("#avatarPreview")).toBeVisible();

  return modal;
}

export async function closeEditProfile(page) {
  await page.locator("#nameEditModal .name-edit-modal__close").click();
  await expect(page.locator("#nameEditModal")).not.toHaveClass(/is-open/);
}

export async function clickConfirm(page) {
  const modal = page.locator("#confirmModal");
  await expect(modal).toHaveClass(/is-open/);
  await page.locator("#confirmModalConfirmBtn").click();
}

export async function stubShareClipboard(page) {
  await page.addInitScript(() => {
    window.__copiedShareText = "";

    window.prompt = function (message, value) {
      window.__copiedShareText = value || "";
      return value || "";
    };

    try {
      Object.defineProperty(navigator, "share", {
        value: undefined,
        configurable: true,
      });
      Object.defineProperty(navigator, "clipboard", {
        value: {
          writeText: async (text) => {
            window.__copiedShareText = text;
          },
        },
        configurable: true,
      });
    } catch {
      window.__copiedShareText = "";
    }
  });
}

export async function stubSpeechRecognition(page) {
  await page.addInitScript(() => {
    class MockSpeechRecognition {
      constructor() {
        this.lang = "en-US";
        this.interimResults = false;
        this.maxAlternatives = 1;
        this.onresult = null;
        this.onend = null;
        this.onerror = null;
      }

      start() {
        setTimeout(() => {
          if (this.onresult) {
            this.onresult({
              results: [[{ transcript: "Mock voice transcript" }]],
            });
          }
          if (this.onend) {
            this.onend();
          }
        }, 0);
      }

      stop() {
        if (this.onend) {
          this.onend();
        }
      }
    }

    Object.defineProperty(window, "SpeechRecognition", {
      value: MockSpeechRecognition,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      value: MockSpeechRecognition,
      configurable: true,
      writable: true,
    });
    window.__mockSpeechRecognitionInstalled = true;
  });
}
