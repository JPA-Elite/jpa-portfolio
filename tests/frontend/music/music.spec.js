import { expect, test } from "../support/test.js";
import {
  MUSIC_CONFIG,
  activeTrackId,
  openMusicPage,
  selectTrack,
  stubMusicEnvironment,
  waitForMusicCounts,
  waitForMusicList,
  waitForMusicVote,
} from "../support/music-page.js";

const nextSongButton = '[onclick="nextSong()"]';
const prevSongButton = '[onclick="prevSong()"]';
const nextPageButton = '.page-btn[onclick="nextPage()"]';
const prevPageButton = '.page-btn[onclick="prevPage()"]';

test.describe("Music page", () => {
  test.beforeEach(async ({ page }) => {
    await stubMusicEnvironment(page);
  });

  test("renders the first page of tracks, categories, votes and pagination", async ({
    page,
  }) => {
    await openMusicPage(page);

    const items = page.locator(".music-item");
    await expect(page.locator("#music-header")).toHaveText(MUSIC_CONFIG.header);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 3");
    await expect(items).toHaveCount(MUSIC_CONFIG.perPage);
    await expect(items.nth(0).locator(".title")).toHaveText("Mock Track 01");
    await expect(items.nth(0).locator(".artist")).toHaveText("Mock Artist 01");
    await expect(items.nth(0).locator(".duration")).toHaveText("3:10");
    await expect(items.nth(1).locator(".like-btn .vote-count")).toHaveText("8");
    await expect(page.locator(prevPageButton)).toBeDisabled();
    await expect(page.locator(nextPageButton)).toBeEnabled();

    await page.locator("#categoryToggle").click();
    await expect(page.locator("#categoryTabs")).not.toHaveClass(
      /category-tabs--collapsed/
    );

    const tags = page.locator(".category-tag");
    await expect(tags).toHaveCount(11);
    await expect(tags.filter({ hasText: "All" })).toHaveClass(/active/);
    await expect(tags.filter({ hasText: "All" })).toContainText("25");
    await expect(tags.filter({ hasText: "Rap" })).toContainText("7");

    await page.locator("#categoryToggle").click();
    await expect(page.locator("#categoryTabs")).toHaveClass(
      /category-tabs--collapsed/
    );
  });

  test("toggles like and dislike votes and updates the counts", async ({
    page,
  }) => {
    await openMusicPage(page);
    await selectTrack(page, 0);

    const item = page.locator(".music-item").first();
    const like = item.locator(".like-btn");
    const dislike = item.locator(".dislike-btn");

    await expect(like.locator(".vote-count")).toHaveText("7");
    await expect(dislike.locator(".vote-count")).toHaveText("2");
    await expect(like).not.toHaveClass(/voted/);
    await expect(dislike).not.toHaveClass(/voted/);

    let voteResponse = waitForMusicVote(page);
    let countsResponse = waitForMusicCounts(page);
    await like.click();
    await voteResponse;
    await countsResponse;

    await expect(like).toHaveClass(/voted/);
    await expect(like.locator(".vote-count")).toHaveText("8");
    await expect(dislike).not.toHaveClass(/voted/);
    await expect(dislike.locator(".vote-count")).toHaveText("2");

    voteResponse = waitForMusicVote(page);
    countsResponse = waitForMusicCounts(page);
    await dislike.click();
    await voteResponse;
    await countsResponse;

    await expect(like).not.toHaveClass(/voted/);
    await expect(like.locator(".vote-count")).toHaveText("7");
    await expect(dislike).toHaveClass(/voted/);
    await expect(dislike.locator(".vote-count")).toHaveText("3");

    voteResponse = waitForMusicVote(page);
    countsResponse = waitForMusicCounts(page);
    await dislike.click();
    await voteResponse;
    await countsResponse;

    await expect(like).not.toHaveClass(/voted/);
    await expect(like.locator(".vote-count")).toHaveText("7");
    await expect(dislike).not.toHaveClass(/voted/);
    await expect(dislike.locator(".vote-count")).toHaveText("2");
  });

  test("filters tracks by category and shows an empty category state", async ({
    page,
  }) => {
    await openMusicPage(page);

    await page.locator("#categoryToggle").click();
    const response = waitForMusicList(
      page,
      (url) => url.searchParams.get("category") === MUSIC_CONFIG.tag
    );
    await page
      .locator(`.category-tag[data-category="${MUSIC_CONFIG.tag}"]`)
      .click();
    await response;

    const items = page.locator(".music-item");
    await expect(items).toHaveCount(MUSIC_CONFIG.tagCount);
    await expect(page.locator("#music-header")).toHaveText("My Tracks (7 songs)");
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 1");
    await expect(
      page.locator(`.category-tag[data-category="${MUSIC_CONFIG.tag}"]`)
    ).toHaveClass(/active/);
    await expect(page.locator("#categoryTabs")).toHaveClass(
      /category-tabs--collapsed/
    );

    await page.locator("#categoryToggle").click();
    const emptyResponse = waitForMusicList(
      page,
      (url) => url.searchParams.get("category") === MUSIC_CONFIG.emptyTag
    );
    await page
      .locator(`.category-tag[data-category="${MUSIC_CONFIG.emptyTag}"]`)
      .click();
    await emptyResponse;

    await expect(items).toHaveCount(0);
    await expect(page.locator(".empty-category-state")).toContainText(
      `There is no music in ${MUSIC_CONFIG.emptyTag}`
    );
    await expect(page.locator("#music-header")).toHaveText("My Tracks (0 songs)");
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 1");
  });

  test("searches titles and artists, handles no results and clears the query", async ({
    page,
  }) => {
    await openMusicPage(page);

    const search = page.locator("#navbarSearch");
    const items = page.locator(".music-item");

    const titleResponse = waitForMusicList(
      page,
      (url) => url.searchParams.get("search") === "mock track 12"
    );
    await search.fill(MUSIC_CONFIG.searchTitle);
    await titleResponse;

    await expect(items).toHaveCount(1);
    await expect(items.locator(".title")).toHaveText(MUSIC_CONFIG.searchTitle);
    await expect(page.locator("#music-header")).toHaveText("My Tracks (1 song)");
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 1");
    await expect(page).toHaveURL(
      (url) => url.searchParams.get("search") === "mock track 12"
    );

    const artistResponse = waitForMusicList(
      page,
      (url) => url.searchParams.get("search") === "mock artist 12"
    );
    await search.fill(MUSIC_CONFIG.searchArtist);
    await artistResponse;

    await expect(items).toHaveCount(1);
    await expect(items.locator(".title")).toHaveText(MUSIC_CONFIG.searchTitle);

    const targetResponse = waitForMusicList(
      page,
      (url) => url.searchParams.get("search") === "mock aurora nights"
    );
    await search.fill(MUSIC_CONFIG.searchTarget);
    await targetResponse;

    await expect(items).toHaveCount(1);
    await expect(items.locator(".title")).toHaveText(MUSIC_CONFIG.searchTarget);

    const emptyResponse = waitForMusicList(
      page,
      (url) => url.searchParams.get("search") === MUSIC_CONFIG.emptySearch
    );
    await search.fill(MUSIC_CONFIG.emptySearch);
    await emptyResponse;

    await expect(items).toHaveCount(0);
    await expect(page.locator(".no-results")).toHaveText("No songs found.");
    await expect(page.locator("#music-header")).toHaveText("My Tracks (0 songs)");

    const clearResponse = waitForMusicList(
      page,
      (url) => !url.searchParams.has("search")
    );
    await page.locator(".clear-icon").click();
    await clearResponse;

    await expect(search).toHaveValue("");
    await expect(items).toHaveCount(MUSIC_CONFIG.perPage);
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 3");
  });

  test("hydrates the page and search from the URL", async ({ page }) => {
    await openMusicPage(page, "/music?page=2");

    await expect(page.locator(".music-item")).toHaveCount(MUSIC_CONFIG.perPage);
    await expect(page.locator(".music-item .title").first()).toHaveText(
      "Mock Track 11"
    );
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 of 3");

    await page.goto("/music?search=mock+track+12", {
      waitUntil: "domcontentloaded",
    });

    await expect(page.locator(".music-item")).toHaveCount(1);
    await expect(page.locator("#navbarSearch")).toHaveValue("mock track 12");
    await expect(page.locator(".music-item .title")).toHaveText(
      MUSIC_CONFIG.searchTitle
    );
  });

  test("navigates through the music pagination", async ({ page }) => {
    await openMusicPage(page);

    const items = page.locator(".music-item");
    const nextPage = page.locator(nextPageButton);
    const prevPage = page.locator(prevPageButton);

    const secondPage = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "2"
    );
    await nextPage.click();
    await secondPage;

    await expect(items).toHaveCount(MUSIC_CONFIG.perPage);
    await expect(items.locator(".title").first()).toHaveText("Mock Track 11");
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 of 3");
    await expect(prevPage).toBeEnabled();
    await expect(nextPage).toBeEnabled();
    await expect(page).toHaveURL((url) => url.searchParams.get("page") === "2");

    const thirdPage = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "3"
    );
    await nextPage.click();
    await thirdPage;

    await expect(items).toHaveCount(5);
    await expect(items.locator(".title").first()).toHaveText("Mock Track 21");
    await expect(page.locator("#pageInfo")).toHaveText("Page 3 of 3");
    await expect(nextPage).toBeDisabled();

    const previousPage = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "2"
    );
    await prevPage.click();
    await previousPage;

    await expect(items).toHaveCount(MUSIC_CONFIG.perPage);
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 of 3");
  });

  test("selects a track and toggles playback controls", async ({ page }) => {
    await openMusicPage(page);
    const item = await selectTrack(page, 0);

    await expect(page.locator(".music-item.active")).toHaveCount(1);
    await expect(page.locator("#nowPlaying")).toContainText("Mock Track 01");
    await expect(page.locator("#playerNowPlaying .title")).toHaveText(
      "Mock Track 01"
    );
    await expect(page.locator("#playerNowPlaying .artist")).toHaveText(
      "Mock Artist 01"
    );
    await expect(page.locator("#coverImg")).toHaveAttribute(
      "src",
      /cert1\.webp/
    );
    await expect(page.locator("#playerCoverImg")).toHaveAttribute(
      "src",
      /cert1\.webp/
    );
    await expect(page.locator("#vinylDisc")).toHaveClass(/spinning/);
    await expect(page.locator("#tonearm")).toHaveClass(/playing/);
    await expect(page.locator("#playPauseBtn")).toHaveAttribute(
      "aria-label",
      "Pause"
    );
    await expect(page.locator("#playPauseBtn ion-icon")).toHaveAttribute(
      "name",
      "pause-outline"
    );
    await expect(page.locator("#audioPlayer")).toHaveAttribute(
      "src",
      /api\/proxy-audio\?url=.*mock-music-01\.mp3/
    );
    await expect(page.locator("#categoryTabs")).toHaveClass(
      /category-tabs--collapsed/
    );
    await expect(item).toHaveClass(/active/);

    await page.locator("#playPauseBtn").click();
    await expect(page.locator("#playPauseBtn")).toHaveAttribute(
      "aria-label",
      "Play"
    );
    await expect(page.locator("#playPauseBtn ion-icon")).toHaveAttribute(
      "name",
      "play-outline"
    );
    await expect(page.locator("#vinylDisc")).not.toHaveClass(/spinning/);
    await expect(page.locator("#tonearm")).not.toHaveClass(/playing/);

    await page.locator("#playPauseBtn").click();
    await expect(page.locator("#playPauseBtn")).toHaveAttribute(
      "aria-label",
      "Pause"
    );
    await expect(page.locator("#vinylDisc")).toHaveClass(/spinning/);
    await expect(page.locator("#tonearm")).toHaveClass(/playing/);
  });

  test("moves between tracks and across pages with next and previous", async ({
    page,
  }) => {
    await openMusicPage(page);
    await selectTrack(page, 9);

    let response = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "2"
    );
    await page.locator(nextSongButton).click();
    await response;

    await expect(page.locator(".music-item.active .title")).toHaveText(
      "Mock Track 11"
    );
    await expect(page.locator("#playerNowPlaying .title")).toHaveText(
      "Mock Track 11"
    );
    await expect(page.locator("#pageInfo")).toHaveText("Page 2 of 3");

    response = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "1"
    );
    await page.locator(prevSongButton).click();
    await response;

    await expect(page.locator(".music-item.active .title")).toHaveText(
      "Mock Track 10"
    );
    await expect(page.locator("#pageInfo")).toHaveText("Page 1 of 3");

    await selectTrack(page, 0);
    response = waitForMusicList(
      page,
      (url) => url.searchParams.get("page") === "3"
    );
    await page.locator(prevSongButton).click();
    await response;

    await expect(page.locator(".music-item.active .title")).toHaveText(
      "Mock Track 25"
    );
    await expect(page.locator("#pageInfo")).toHaveText("Page 3 of 3");
  });

  test("toggles shuffle, plays a shuffled track and returns through history", async ({
    page,
  }) => {
    await openMusicPage(page);

    const shuffle = page.locator("#shuffleBtn");
    await expect(shuffle).toHaveAttribute("aria-pressed", "false");
    await expect(shuffle).not.toHaveClass(/is-on/);

    await shuffle.click();
    await expect(shuffle).toHaveAttribute("aria-pressed", "true");
    await expect(shuffle).toHaveClass(/is-on/);
    await expect(shuffle).toHaveAttribute("title", "Shuffle: On");
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("musicShuffle")))
      .toBe("true");

    await selectTrack(page, 0);
    const firstId = await activeTrackId(page);
    expect(firstId).toBe("pw-music-01");

    await page.locator(nextSongButton).click();
    await expect
      .poll(async () => {
        const id = await activeTrackId(page);
        return id && id !== firstId ? id : "";
      })
      .not.toBe("");

    await page.locator(prevSongButton).click();
    await expect.poll(() => activeTrackId(page)).toBe(firstId);

    await shuffle.click();
    await expect(shuffle).toHaveAttribute("aria-pressed", "false");
    await expect(shuffle).not.toHaveClass(/is-on/);
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("musicShuffle")))
      .toBe("false");
  });

  test("toggles autoplay and advances when a track ends", async ({ page }) => {
    await openMusicPage(page);

    const autoplay = page.locator("#autoplayBtn");
    await expect(autoplay).toHaveAttribute("aria-pressed", "true");
    await expect(autoplay).toHaveAttribute("title", "Autoplay: On");
    await expect(autoplay.locator("ion-icon")).toHaveAttribute("name", "repeat");

    await autoplay.click();
    await expect(autoplay).toHaveAttribute("aria-pressed", "false");
    await expect(autoplay).toHaveAttribute("title", "Autoplay: Off");
    await expect(autoplay.locator("ion-icon")).toHaveAttribute(
      "name",
      "repeat-outline"
    );
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("autoplay")))
      .toBe("false");

    await autoplay.click();
    await expect(autoplay).toHaveAttribute("aria-pressed", "true");

    await selectTrack(page, 0);
    await expect(page.locator("#playerNowPlaying .title")).toHaveText(
      "Mock Track 01"
    );

    await page.evaluate(() => {
      document
        .getElementById("audioPlayer")
        .dispatchEvent(new Event("ended"));
    });

    await expect(page.locator("#playerNowPlaying .title")).toHaveText(
      "Mock Track 02"
    );
    await expect.poll(() => activeTrackId(page)).toBe("pw-music-02");
  });

  test("changes the volume and seeks through the progress bar", async ({
    page,
  }) => {
    await openMusicPage(page);
    await selectTrack(page, 0);

    await page.locator("#volumeSlider").evaluate((element) => {
      element.value = "40";
      element.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await expect(page.locator("#volumePercentage")).toHaveText("40%");
    const volume = await page.evaluate(
      () => document.getElementById("audioPlayer").volume
    );
    expect(volume).toBeCloseTo(0.4, 5);

    const progressBar = page.locator("#progressBar");
    const box = await progressBar.boundingBox();
    expect(box).not.toBeNull();
    expect(box.width).toBeGreaterThan(0);

    await progressBar.click({
      position: { x: box.width / 2, y: box.height / 2 },
    });

    const progressState = await page.evaluate(() => {
      const audio = document.getElementById("audioPlayer");
      const seconds = Math.floor(audio.currentTime);
      return {
        time: audio.currentTime,
        width: Number.parseFloat(
          document.getElementById("progress").style.width
        ),
        label: `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`,
      };
    });

    expect(progressState.time).toBeGreaterThan(90);
    expect(progressState.time).toBeLessThan(110);
    expect(progressState.width).toBeGreaterThan(40);
    expect(progressState.width).toBeLessThan(60);
    await expect(page.locator("#currentTime")).toHaveText(progressState.label);
  });

  test("opens lyrics, highlights LRC lines, seeks and closes the modal", async ({
    page,
  }) => {
    await openMusicPage(page);
    await selectTrack(page, 0);

    await page.locator("#lyricsBtn").click();
    const modal = page.locator("#lyricsModal");
    await expect(modal).toHaveClass(/is-open/);
    await expect(modal).toHaveAttribute("aria-hidden", "false");
    await expect(page.locator("body")).toHaveClass(/lyrics-modal-open/);
    await expect(page.locator("#lyricsModalTitle")).toHaveText("Mock Track 01");
    await expect(page.locator("#lyricsModalArtist")).toHaveText("Mock Artist 01");

    const lines = page.locator("#lyricsModalContent .lyrics-modal__line");
    await expect(lines).toHaveCount(3);
    await expect(lines.nth(0)).toHaveText("Mock opening line");
    await expect(lines.nth(0)).toHaveClass(/is-active/);

    await lines.nth(1).click();
    await expect(lines.nth(1)).toHaveClass(/is-active/);
    const currentTime = await page.evaluate(
      () => document.getElementById("audioPlayer").currentTime
    );
    expect(currentTime).toBe(5);

    await page.keyboard.press("Escape");
    await expect(modal).not.toHaveClass(/is-open/);
    await expect(modal).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator("body")).not.toHaveClass(/lyrics-modal-open/);

    await page.locator("#lyricsBtn").click();
    await expect(modal).toHaveClass(/is-open/);
    await page.locator("#lyricsCloseBtn").click();
    await expect(modal).not.toHaveClass(/is-open/);

    await page.locator("#lyricsBtn").click();
    await expect(modal).toHaveClass(/is-open/);
    await page
      .locator(".lyrics-modal__backdrop")
      .click({ position: { x: 10, y: 10 }, force: true });
    await expect(modal).not.toHaveClass(/is-open/);

    await selectTrack(page, 1);
    await page.locator("#lyricsBtn").click();
    await expect(lines).toHaveCount(2);
    await expect(lines.nth(0)).toHaveText("Plain mock lyric line one");
    await page.keyboard.press("Escape");

    await selectTrack(page, 2);
    await page.locator("#lyricsBtn").click();
    await expect(
      page.locator("#lyricsModalContent .lyrics-modal__line--empty-state")
    ).toHaveText("No lyrics added for this song yet.");
  });

  test("downloads the current track and copies its link", async ({ page }) => {
    await openMusicPage(page);
    await selectTrack(page, 0);

    await page.locator("#downloadBtn").click();
    const confirm = page.locator("#confirmModal");
    await expect(confirm).toHaveClass(/is-open/);
    await expect(page.locator("#confirmModalTitle")).toHaveText("Download Song");
    await expect(page.locator("#confirmModalBody")).toContainText(
      "Do you want to download this song?"
    );

    await page.locator("#confirmModalConfirmBtn").click();
    await expect(confirm).not.toHaveClass(/is-open/);

    const openedUrls = await page.evaluate(() => window.__openedMusicUrls);
    expect(openedUrls).toHaveLength(1);
    expect(openedUrls[0]).toContain("/api/download_song?url=");
    expect(openedUrls[0]).toContain(
      encodeURIComponent("https://example.com/mock-music-01.mp3")
    );

    await page.locator("#copyLinkBtn").click();
    const popup = page.locator("#copyPopup");
    await expect(popup).toBeVisible();
    await expect(popup).toHaveText("Copied to clipboard!");

    const copied = await page.evaluate(() => window.__copiedMusicLink);
    expect(copied).toContain("/api/proxy-audio?url=");
    expect(copied).toContain("mock-music-01.mp3");
    await expect(popup).toBeHidden({ timeout: 4000 });
  });

  test("opens the visualizer settings and applies presets and custom values", async ({
    page,
  }) => {
    await openMusicPage(page);
    await selectTrack(page, 0);

    await page.locator("#visualizerSettingsBtn").click();
    const panel = page.locator("#visualizerSettingsPanel");
    const backdrop = page.locator("#visualizerSettingsBackdrop");
    await expect(panel).toHaveClass(/open/);
    await expect(panel).toHaveAttribute("aria-hidden", "false");
    await expect(backdrop).toHaveClass(/open/);

    await page.locator('#visualizerModes button[data-mode="Cyberpunk"]').click();
    await expect(
      page.locator('#visualizerModes button[data-mode="Cyberpunk"]')
    ).toHaveClass(/active/);
    await expect(page.locator("#vizBars")).toHaveValue("110");
    await expect(page.locator("#vizSpeed")).toHaveValue("18");
    await expect(page.locator("#vizGlow")).toHaveValue("24");
    await expect(page.locator("#vizSensitivity")).toHaveValue("105");
    await expect(page.locator("#vizSmooth")).toHaveValue("56");
    await expect(page.locator("#vizBass")).toHaveValue("18");
    await expect(page.locator("#vizTreble")).toHaveValue("16");

    await page.locator("#vizBars").evaluate((element) => {
      element.value = "42";
      element.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await expect(
      page.locator('#visualizerModes button[data-mode="Custom"]')
    ).toHaveClass(/active/);
    await expect(page.locator("#vizBars")).toHaveValue("42");

    const vizToggle = page.locator("#vizOffToggle");
    const vizSwitch = page.locator(".visualizer-off-toggle .switch .slider");
    await expect(vizToggle).toBeChecked();
    await vizSwitch.click();
    await expect(vizToggle).not.toBeChecked();
    await vizSwitch.click();
    await expect(vizToggle).toBeChecked();

    await page.locator("#visualizerCloseBtn").click();
    await expect(panel).not.toHaveClass(/open/);
    await expect(panel).toHaveAttribute("aria-hidden", "true");
    await expect(backdrop).not.toHaveClass(/open/);

    await page.locator("#visualizerSettingsBtn").click();
    await expect(panel).toHaveClass(/open/);
    await backdrop.click({ position: { x: 10, y: 10 }, force: true });
    await expect(panel).not.toHaveClass(/open/);
  });

  test("minimizes the track list and toggles the navbar dropdowns", async ({
    page,
  }) => {
    await openMusicPage(page);

    const listTab = page.locator("#musicListTab");
    const main = page.locator("#musicMain");

    await listTab.click();
    await expect(main).toHaveClass(/music-list-hidden/);
    await expect(listTab).toHaveAttribute("aria-expanded", "false");
    await expect(listTab).toHaveAttribute("title", "Maximize sidebar");

    await listTab.click();
    await expect(main).not.toHaveClass(/music-list-hidden/);
    await expect(listTab).toHaveAttribute("aria-expanded", "true");
    await expect(listTab).toHaveAttribute("title", "Minimize sidebar");

    const social = page.locator(".social-dropdown");
    await page.locator(".social-dropdown-btn").click();
    await expect(social).toHaveClass(/active/);
    await page.locator("#nowPlaying").click({ force: true });
    await expect(social).not.toHaveClass(/active/);

    const media = page.locator(".media-dropdown");
    await page.locator(".media-dropdown-trigger").click();
    await expect(media).toHaveClass(/is-open/);
    await page.locator("#nowPlaying").click({ force: true });
    await expect(media).not.toHaveClass(/is-open/);
  });
});

test.describe("Music page mobile", () => {
  test.use({ viewport: { width: 480, height: 900 } });

  test("toggles the mobile sidebar, media submenu, categories and fullscreen", async ({
    page,
  }) => {
    await stubMusicEnvironment(page);
    await openMusicPage(page);

    const sidebarToggle = page.locator("#navbarToggle");
    const sidebar = page.locator("#sidebar");
    await expect(sidebarToggle).toBeVisible();

    await sidebarToggle.click();
    await expect(sidebar).toHaveClass(/active/);
    await expect(sidebarToggle).toHaveClass(/active/);

    await page.locator(".mobile-media-toggle").click();
    await expect(page.locator(".mobile-media-dropdown")).toHaveClass(/is-open/);

    await sidebarToggle.click();
    await expect(sidebar).not.toHaveClass(/active/);
    await expect(sidebarToggle).not.toHaveClass(/active/);

    await page.locator("#categoryToggle").click();
    await expect(page.locator("#categoryTabs")).not.toHaveClass(
      /category-tabs--collapsed/
    );

    const response = waitForMusicList(
      page,
      (url) => url.searchParams.get("category") === MUSIC_CONFIG.tag
    );
    await page
      .locator(`.category-tag[data-category="${MUSIC_CONFIG.tag}"]`)
      .click();
    await response;
    await expect(page.locator(".music-item")).toHaveCount(MUSIC_CONFIG.tagCount);

    const fullscreen = page.locator("#fullscreenBtn");
    await fullscreen.click();
    await expect(page.locator("body")).toHaveClass(/music-mobile-fullscreen/);
    await expect(page.locator("#albumSection")).toHaveClass(/fullscreen-mobile/);
    await expect(fullscreen).toHaveAttribute("aria-pressed", "true");

    await fullscreen.click();
    await expect(page.locator("body")).not.toHaveClass(
      /music-mobile-fullscreen/
    );
    await expect(page.locator("#albumSection")).not.toHaveClass(
      /fullscreen-mobile/
    );
    await expect(fullscreen).toHaveAttribute("aria-pressed", "false");
  });
});
