import { expect } from "./test.js";

export const MUSIC_CONFIG = {
  path: "/music",
  header: "My Tracks (25 songs)",
  totalTracks: 25,
  perPage: 10,
  totalPages: 3,
  searchTitle: "Mock Track 12",
  searchArtist: "Mock Artist 12",
  searchTarget: "Mock Aurora Nights",
  emptySearch: "not-a-real-track",
  tag: "Rap",
  tagCount: 7,
  emptyTag: "Rock",
};

const MUSIC_MEDIA_STUB = () => {
  window.__copiedMusicLink = "";
  window.__openedMusicUrls = [];

  Object.defineProperty(HTMLMediaElement.prototype, "paused", {
    configurable: true,
    get() {
      return this.__mockPaused !== false;
    },
  });

  Object.defineProperty(HTMLMediaElement.prototype, "duration", {
    configurable: true,
    get() {
      return this.__mockDuration ?? 200;
    },
  });

  Object.defineProperty(HTMLMediaElement.prototype, "currentTime", {
    configurable: true,
    get() {
      return this.__mockCurrentTime ?? 0;
    },
    set(value) {
      this.__mockCurrentTime = Number(value) || 0;
      this.dispatchEvent(new Event("timeupdate"));
    },
  });

  HTMLMediaElement.prototype.play = function () {
    this.__mockPaused = false;
    this.dispatchEvent(new Event("play"));
    return Promise.resolve();
  };

  HTMLMediaElement.prototype.pause = function () {
    this.__mockPaused = true;
    this.dispatchEvent(new Event("pause"));
  };

  HTMLMediaElement.prototype.load = function () {};

  class MockAnalyserNode {
    constructor() {
      this.fftSize = 2048;
      this.frequencyBinCount = 1024;
      this.smoothingTimeConstant = 0.8;
    }

    connect() {
      return this;
    }

    getByteFrequencyData(array) {
      array.fill(0);
    }
  }

  class MockBiquadFilterNode {
    constructor() {
      this.type = "";
      this.frequency = { value: 0 };
      this.gain = { value: 0 };
    }

    connect() {
      return this;
    }
  }

  class MockMediaElementSourceNode {
    connect() {
      return this;
    }
  }

  class MockAudioContext {
    constructor() {
      this.state = "running";
      this.destination = {};
    }

    createMediaElementSource() {
      return new MockMediaElementSourceNode();
    }

    createAnalyser() {
      return new MockAnalyserNode();
    }

    createBiquadFilter() {
      return new MockBiquadFilterNode();
    }

    resume() {
      this.state = "running";
      return Promise.resolve();
    }
  }

  Object.defineProperty(window, "AudioContext", {
    configurable: true,
    value: MockAudioContext,
  });
  Object.defineProperty(window, "webkitAudioContext", {
    configurable: true,
    value: MockAudioContext,
  });

  window.open = function (url) {
    window.__openedMusicUrls.push(String(url));
    return null;
  };

  Object.defineProperty(window, "isSecureContext", {
    configurable: true,
    value: true,
  });

  try {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (text) => {
          window.__copiedMusicLink = String(text);
        },
      },
    });
  } catch {
    window.__copiedMusicLink = "";
  }
};

export async function stubMusicEnvironment(page) {
  await page.addInitScript(MUSIC_MEDIA_STUB);
}

export async function openMusicPage(page, path = MUSIC_CONFIG.path) {
  await page.goto(path, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".music-item").first()).toBeVisible();
  await expect(page.locator("#music-header")).toContainText("My Tracks");
}

export function waitForMusicList(page, predicate) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === "/api/music-list" && predicate(url);
  });
}

export function waitForMusicCounts(page) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/music-like/counts" &&
      url.searchParams.has("music_id") &&
      response.request().method() === "GET"
    );
  });
}

export function waitForMusicVote(page) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/music-like/vote" &&
      response.request().method() === "POST"
    );
  });
}

export async function selectTrack(page, index) {
  const item = page.locator(".music-item").nth(index);
  await item.scrollIntoViewIfNeeded();
  await item.click();
  await expect(item).toHaveClass(/active/);
  return item;
}

export function activeTrackId(page) {
  return page.evaluate(() => {
    const button = document.querySelector(".music-item.active .like-btn");
    return button?.dataset.musicId || null;
  });
}
