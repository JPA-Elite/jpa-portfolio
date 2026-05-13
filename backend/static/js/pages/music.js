import { MusicService } from "../services/MusicService.js";

const musicService = new MusicService();

// Declare global variables
let audioPlayer,
    playPauseBtn,
    currentSongIndex = 0;
let currentPage = 1;
const itemsPerPage = 10;
let musicList;
let musicData = [];
let autoplayEnabled = true;
let shuffleEnabled = false;
let shuffleQueueGlobal = [];
let shuffleQueueContextKey = "";
let shuffleHistoryGlobal = [];
let isDragging = false;
const durationCache = JSON.parse(localStorage.getItem('audioDurationCache') || '{}');
let filteredResults = null;
let musicDataLoaded = false;
const durationPromiseCache = new Map();
const MUSIC_DATA_CACHE_KEY = "musicPageDataCacheV3";
const MUSIC_DATA_CACHE_TTL_MS = 5 * 60 * 1000;
let activeSearchQuery = "";
let totalMusicCount = 0;
let totalPagesCount = 1;
let currentSongData = null;
musicList = document.getElementById("musicList");
audioPlayer = document.getElementById("audioPlayer");
const nowPlaying = document.getElementById("nowPlaying");
const coverImg = document.getElementById("coverImg");
const playerNowPlaying = document.getElementById("playerNowPlaying");
const playerCoverImg = document.getElementById("playerCoverImg");
const progressBar = document.getElementById("progressBar");
const progress = document.getElementById("progress");
const progressHandle = document.getElementById("progressHandle");
const currentTimeEl = document.getElementById("currentTime");
const totalDurationEl = document.getElementById("totalDuration");
playPauseBtn = document.getElementById("playPauseBtn");
const lyricsBtn = document.getElementById("lyricsBtn");
const lyricsModal = document.getElementById("lyricsModal");
const lyricsModalTitleEl = document.getElementById("lyricsModalTitle");
const lyricsModalArtistEl = document.getElementById("lyricsModalArtist");
const lyricsModalContentEl = document.getElementById("lyricsModalContent");
const lyricsCloseBtn = document.getElementById("lyricsCloseBtn");
const canvas = document.getElementById("beatVisualizer");
const ctx = canvas.getContext("2d");
let audioContext, analyser, source, dataArray, bufferLength, visualizerRunning;
const prevPageBtn = document.querySelector(".page-btn[onclick='prevPage()']");
const nextPageBtn = document.querySelector(".page-btn[onclick='nextPage()']");

const ACTIVE_SONG_STORAGE_KEY = "musicPageActiveSongId";

function getAudioSourceUrl(song) {
    if (!song || !song.url) return "";
    return isMobileDevice()
        ? song.url
        : `/api/proxy-audio?url=${encodeURIComponent(song.url)}`;
}

function setAudioSrcForSong(song) {
    if (!song) return;
    const source = getAudioSourceUrl(song);
    if (!source) return;
    audioPlayer.src = source;
}

function persistActiveSongId(songId) {
    if (!songId || typeof window === "undefined" || !window.localStorage) return;
    try {
        window.localStorage.setItem(ACTIVE_SONG_STORAGE_KEY, String(songId));
    } catch (error) {
        console.warn("Unable to persist active song:", error);
    }
}

function updateActiveSongDisplay(song, { prefix = "Now Playing:" } = {}) {
    if (!song) return;
    if (nowPlaying) {
        nowPlaying.textContent = `${prefix} ${song.title}`;
    }
    if (coverImg) {
        coverImg.src = song.image;
    }
    if (playerNowPlaying) {
        playerNowPlaying.innerHTML = `
            <div class="title-artist">
                <span class="title">${song.title}</span>
                <span class="artist">${song.artist}</span>
            </div>
        `;
    }
    if (playerCoverImg) {
        playerCoverImg.src = song.image;
    }
    const albumSection = document.getElementById("albumSection");
    if (albumSection) {
        albumSection.style.backgroundImage = `url('${song.image}')`;
    }
    syncLyricsPanel(song);
}

function restoreActiveSongFromStorage() {
    if (typeof window === "undefined" || !window.localStorage) return null;
    if (!Array.isArray(musicData) || !musicData.length) return null;
    try {
        const storedId = window.localStorage.getItem(ACTIVE_SONG_STORAGE_KEY);
        if (!storedId) return null;
        const index = musicData.findIndex((track) => String(track.id) === storedId);
        if (index === -1) return null;
        const track = musicData[index];
        currentSongIndex = index;
        currentSongData = track;
        setAudioSrcForSong(track);
        updateActiveSongDisplay(track);
        return track.id;
    } catch (error) {
        console.warn("Failed to restore active song:", error);
        return null;
    }
}

let pendingUrlHistoryPush = false;

function requestUrlHistoryPush() {
    pendingUrlHistoryPush = true;
}

function applyQueryParamsFromUrl() {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const pageParam = Number.parseInt(params.get("page") || "", 10);
    if (!Number.isNaN(pageParam) && pageParam >= 1) {
        currentPage = pageParam;
    } else {
        currentPage = 1;
    }

    const rawSearch = (params.get("search") || "").trim();
    activeSearchQuery = rawSearch ? rawSearch.toLowerCase() : "";

    const searchInput = document.getElementById("navbarSearch");
    if (searchInput) {
        searchInput.value = rawSearch;
    }
}

function updateMusicPageUrl({ push = false } = {}) {
    if (typeof window === "undefined") return;

    const url = new URL(window.location.href);
    const params = url.searchParams;

    if (activeSearchQuery) {
        params.set("search", activeSearchQuery);
    } else {
        params.delete("search");
    }

    if (currentPage > 1) {
        params.set("page", String(currentPage));
    } else {
        params.delete("page");
    }

    params.set("per_page", String(itemsPerPage));

    const hash = url.hash || "";
    const newSearch = params.toString();
    const newUrl = `${url.pathname}${newSearch ? `?${newSearch}` : ""}${hash}`;
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (newUrl === currentUrl) return;

    const historyState = window.history.state;
    const method = push ? "pushState" : "replaceState";
    window.history[method](historyState, "", newUrl);
}

function getCurrentSong() {
    if (currentSongData && typeof currentSongData === "object") {
        return currentSongData;
    }

    const source = filteredResults !== null ? filteredResults : musicData;
    if (!Array.isArray(source) || !source.length) return null;
    if (currentSongIndex < 0 || currentSongIndex >= source.length) return null;
    return source[currentSongIndex] || null;
}

function renderLyricsContent(text = "", { isEmptyState = false } = {}) {
    if (!lyricsModalContentEl) return;

    lyricsModalContentEl.innerHTML = "";
    lyricsModalContentEl.classList.toggle("is-empty", Boolean(isEmptyState));

    if (isEmptyState) {
        const emptyLine = document.createElement("div");
        emptyLine.className = "lyrics-modal__line lyrics-modal__line--empty-state";
        emptyLine.textContent = text || "No lyrics available.";
        lyricsModalContentEl.appendChild(emptyLine);
        return;
    }

    const lines = String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");

    lines.forEach((lineText) => {
        const lineEl = document.createElement("div");
        lineEl.className = "lyrics-modal__line";

        if (!lineText.trim()) {
            lineEl.classList.add("lyrics-modal__line--blank");
            lineEl.innerHTML = "&nbsp;";
        } else {
            lineEl.textContent = lineText;
        }

        lyricsModalContentEl.appendChild(lineEl);
    });
}

function syncLyricsPanel(song = getCurrentSong()) {
    if (lyricsBtn) {
        const disabled = !song;
        lyricsBtn.disabled = disabled;
        lyricsBtn.classList.toggle("is-disabled", disabled);
        lyricsBtn.setAttribute("aria-disabled", String(disabled));
        lyricsBtn.title = disabled ? "Lyrics unavailable" : "Lyrics";
    }

    if (!lyricsModalTitleEl || !lyricsModalArtistEl || !lyricsModalContentEl) return;

    if (!song) {
        lyricsModalTitleEl.textContent = "Select a song";
        lyricsModalArtistEl.textContent = "";
        renderLyricsContent("Select a song to view lyrics.", { isEmptyState: true });
        return;
    }

    const lyrics = typeof song.lyrics === "string" ? song.lyrics.trim() : "";
    lyricsModalTitleEl.textContent = song.title || "Lyrics";
    lyricsModalArtistEl.textContent = song.artist || "";
    if (!lyrics) {
        renderLyricsContent("No lyrics added for this song yet.", { isEmptyState: true });
        return;
    }

    renderLyricsContent(lyrics, { isEmptyState: false });
}

function openLyricsModal() {
    if (!lyricsModal) return;
    const song = getCurrentSong();
    if (!song) return;

    syncLyricsPanel(song);
    lyricsModal.classList.add("is-open");
    lyricsModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("lyrics-modal-open");
}

function closeLyricsModal() {
    if (!lyricsModal) return;
    lyricsModal.classList.remove("is-open");
    lyricsModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lyrics-modal-open");
}

function toggleLyricsModal() {
    if (!lyricsModal) return;
    if (lyricsModal.classList.contains("is-open")) {
        closeLyricsModal();
    } else {
        openLyricsModal();
    }
}

function setControlButtonIcon(button, iconName, label) {
    if (!button) return;
    button.innerHTML = `<ion-icon name="${iconName}"></ion-icon>`;
    if (label) {
        button.title = label;
        button.setAttribute("aria-label", label);
    }
}

function syncPlayPauseButton() {
    const isPlaying = !!audioPlayer?.src && !audioPlayer.paused;
    setControlButtonIcon(
        playPauseBtn,
        isPlaying ? "pause-outline" : "play-outline",
        isPlaying ? "Pause" : "Play"
    );
}

function syncAutoplayButton() {
    const btn = document.getElementById("autoplayBtn");
    if (!btn) return;
    btn.classList.add("icon-btn");
    setControlButtonIcon(
        btn,
        autoplayEnabled ? "repeat" : "repeat-outline",
        `Autoplay: ${autoplayEnabled ? "On" : "Off"}`
    );
    btn.classList.toggle("is-off", !autoplayEnabled);
    btn.setAttribute("aria-pressed", String(autoplayEnabled));
}

function syncShuffleButton() {
    const btn = document.getElementById("shuffleBtn");
    if (!btn) return;
    btn.classList.add("icon-btn");
    setControlButtonIcon(
        btn,
        shuffleEnabled ? "shuffle" : "shuffle-outline",
        `Shuffle: ${shuffleEnabled ? "On" : "Off"}`
    );
    btn.classList.toggle("is-off", !shuffleEnabled);
    btn.classList.toggle("is-on", shuffleEnabled);
    btn.setAttribute("aria-pressed", String(shuffleEnabled));
}

function syncFullscreenButton(isExpanded) {
    const btn = document.getElementById("fullscreenBtn");
    if (!btn) return;
    btn.classList.add("icon-btn");
    setControlButtonIcon(
        btn,
        isExpanded ? "contract-outline" : "expand-outline",
        isExpanded ? "Exit fullscreen" : "Enter fullscreen"
    );
    btn.setAttribute("aria-pressed", String(!!isExpanded));
}

syncPlayPauseButton();
syncShuffleButton();
syncFullscreenButton(false);

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.documentElement;
    // Always force dark theme on the music page, regardless of saved preference from other pages
    root.setAttribute("data-theme", "dark");

    applyQueryParamsFromUrl();

    if (lyricsBtn) {
        lyricsBtn.addEventListener("click", toggleLyricsModal);
    }
    if (lyricsCloseBtn) {
        lyricsCloseBtn.addEventListener("click", closeLyricsModal);
    }
    if (lyricsModal) {
        lyricsModal.addEventListener("click", (event) => {
            if (event.target === lyricsModal || event.target.closest("[data-lyrics-close]")) {
                closeLyricsModal();
            }
        });
    }

    showTripleLoading?.();
    try {
        await loadAndRenderMusicPage({ resetSelection: true });
        musicDataLoaded = true;
    } catch (err) {
        console.error("Failed to load music data:", err);
        musicList.innerHTML = `<p class="no-results">Failed to load songs.</p>`;
    } finally {
        hideTripleLoading?.();
    }
    syncPlayPauseButton();
    markGlobalSongAsPlayed(getCurrentGlobalSongIndex());
    syncAutoplayButton();
    syncShuffleButton();
    syncFullscreenButton(false);
    syncLyricsPanel();
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && lyricsModal?.classList.contains("is-open")) {
        closeLyricsModal();
    }
});

function getRandomTrackIndex(source = [], excludeIndex = -1) {
    const count = Array.isArray(source) ? source.length : 0;
    if (count <= 1) return 0;

    let nextIndex = excludeIndex;
    let safety = 0;
    while (nextIndex === excludeIndex && safety < 12) {
        nextIndex = Math.floor(Math.random() * count);
        safety++;
    }
    return nextIndex === excludeIndex ? (excludeIndex + 1) % count : nextIndex;
}

function getShuffleContextKey() {
    return `${activeSearchQuery}::${Number(totalMusicCount || 0)}`;
}

function getCurrentGlobalSongIndex() {
    if (!Array.isArray(musicData) || !musicData.length || currentSongIndex < 0) return -1;
    return ((Math.max(1, currentPage) - 1) * itemsPerPage) + currentSongIndex;
}

function resetShuffleQueue(excludeGlobalIndex = -1) {
    const total = Number(totalMusicCount || 0);
    shuffleQueueContextKey = getShuffleContextKey();
    shuffleQueueGlobal = [];
    if (total <= 0) return;

    for (let i = 0; i < total; i++) {
        if (i !== excludeGlobalIndex) {
            shuffleQueueGlobal.push(i);
        }
    }

    for (let i = shuffleQueueGlobal.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffleQueueGlobal[i], shuffleQueueGlobal[j]] = [shuffleQueueGlobal[j], shuffleQueueGlobal[i]];
    }
}

function ensureShuffleQueue(excludeGlobalIndex = -1) {
    if (shuffleQueueContextKey !== getShuffleContextKey()) {
        shuffleHistoryGlobal = [];
    }
    if (shuffleQueueContextKey !== getShuffleContextKey() || !shuffleQueueGlobal.length) {
        resetShuffleQueue(excludeGlobalIndex);
    }
}

function markGlobalSongAsPlayed(globalIndex) {
    if (globalIndex < 0) return;
    if (shuffleQueueContextKey !== getShuffleContextKey()) return;
    if (!shuffleQueueGlobal.length) return;
    shuffleQueueGlobal = shuffleQueueGlobal.filter((idx) => idx !== globalIndex);
}

function getNextShuffleGlobalIndex() {
    const currentGlobalIndex = getCurrentGlobalSongIndex();
    ensureShuffleQueue(currentGlobalIndex);
    if (!shuffleQueueGlobal.length) return currentGlobalIndex;
    return shuffleQueueGlobal.shift();
}

async function playSongByGlobalIndex(globalIndex, { recordShuffleHistory = false } = {}) {
    const total = Number(totalMusicCount || 0);
    if (globalIndex < 0 || globalIndex >= total) return;

    if (recordShuffleHistory && shuffleEnabled) {
        const currentGlobalIndex = getCurrentGlobalSongIndex();
        if (currentGlobalIndex >= 0 && currentGlobalIndex !== globalIndex) {
            const lastHistory = shuffleHistoryGlobal[shuffleHistoryGlobal.length - 1];
            if (lastHistory !== currentGlobalIndex) {
                shuffleHistoryGlobal.push(currentGlobalIndex);
            }
        }
    }

    const targetPage = Math.floor(globalIndex / itemsPerPage) + 1;
    const targetLocalIndex = globalIndex % itemsPerPage;

    if (targetPage !== currentPage) {
        currentPage = targetPage;
        showTripleLoading?.();
        try {
            await loadAndRenderMusicPage();
        } finally {
            hideTripleLoading?.();
        }
    }

    if (!Array.isArray(musicData) || !musicData.length) return;
    playSong(Math.min(targetLocalIndex, musicData.length - 1));
}

async function loadMusicData() {
    const cacheKey = `${MUSIC_DATA_CACHE_KEY}:${currentPage}:${itemsPerPage}:${activeSearchQuery}`;
    try {
        const cachedRaw = sessionStorage.getItem(cacheKey);
        if (cachedRaw) {
            const cached = JSON.parse(cachedRaw);
            if (
                cached &&
                Array.isArray(cached.music) &&
                typeof cached.savedAt === "number" &&
                Date.now() - cached.savedAt < MUSIC_DATA_CACHE_TTL_MS
            ) {
                totalMusicCount = Number(cached.totalMusic || cached.music.length || 0);
                totalPagesCount = Math.max(1, Number(cached.totalPages || 1));
                currentPage = Math.max(1, Number(cached.page || currentPage));
                return cached.music;
            }
        }
    } catch (error) {
        console.warn("Music cache read failed:", error);
    }

    const params = new URLSearchParams();
    params.set("page", String(currentPage));
    params.set("per_page", String(itemsPerPage));
    if (activeSearchQuery) {
        params.set("search", activeSearchQuery);
    }

    const result = await musicService.fetchMusicList(params);
    const items = result?.music || [];
    totalMusicCount = Number(result?.total_music || 0);
    totalPagesCount = Math.max(1, Number(result?.total_pages || 1));
    currentPage = Math.max(1, Number(result?.page || currentPage));

    try {
        sessionStorage.setItem(
            cacheKey,
            JSON.stringify({
                savedAt: Date.now(),
                music: items,
                totalMusic: totalMusicCount,
                totalPages: totalPagesCount,
                page: currentPage,
            })
        );
    } catch (error) {
        console.warn("Music cache write failed:", error);
    }

    return items;
}

async function loadAndRenderMusicPage({ resetSelection = false, activeSongId = null } = {}) {
    const pushUrlState = pendingUrlHistoryPush;
    pendingUrlHistoryPush = false;

    musicData = await loadMusicData();

    let activeSongIdToRender = activeSongId ?? null;
    if (!activeSongIdToRender) {
        const restoredId = restoreActiveSongFromStorage();
        if (restoredId) {
            activeSongIdToRender = restoredId;
        }
    }

    if (!activeSongIdToRender && resetSelection && musicData.length > 0) {
        selectFirstSong();
        activeSongIdToRender = currentSongData?.id ?? null;
    }

    renderList(activeSongIdToRender);
    updateMusicPageUrl({ push: pushUrlState });
}

function selectFirstSong() {
    if (!Array.isArray(musicData) || !musicData.length) {
        currentSongData = null;
        syncLyricsPanel(null);
        return;
    }

    currentSongIndex = Math.floor(Math.random() * musicData.length); // Randomly select an index
    const song = musicData[currentSongIndex];
    currentSongData = song;
    setAudioSrcForSong(song);
    updateActiveSongDisplay(song, { prefix: "Selected:" });
    persistActiveSongId(song.id);
}

function playSong(index) {
    if (index < 0) return;

    const source = filteredResults !== null ? filteredResults : musicData;
    const song = source[index];
    if (!song) {
        console.warn("No valid song found for index:", index);
        return;
    }

    currentSongIndex = index;
    currentSongData = song;
    setAudioSrcForSong(song);
    updateActiveSongDisplay(song);
    persistActiveSongId(song.id);

    coverImg.classList.add("spin");
    audioPlayer.play();
    if (!isMobileDevice()) startVisualizer();
    syncPlayPauseButton();
    markGlobalSongAsPlayed(getCurrentGlobalSongIndex());

    // ✅ Re-render the current page only
    renderList(song.id);
}

function togglePlay() {
    if (audioPlayer.src) {
        if (audioPlayer.paused) {
            coverImg.classList.add("spin");
            audioPlayer.play();
            syncPlayPauseButton();
        } else {
            coverImg.classList.remove("spin");
            audioPlayer.pause();
            syncPlayPauseButton();
        }
        if (!isMobileDevice()) startVisualizer();
    }
}

async function prevSong() {
    const source = musicData || [];
    if (!source.length) return;

    if (shuffleEnabled) {
        const previousGlobalIndex = shuffleHistoryGlobal.pop();
        if (typeof previousGlobalIndex === "number" && previousGlobalIndex >= 0) {
            await playSongByGlobalIndex(previousGlobalIndex, { recordShuffleHistory: false });
            scrollToActiveSong();
        }
        return;
    }

    const total = Number(totalMusicCount || 0);
    if (total <= 0) return;
    const currentGlobalIndex = getCurrentGlobalSongIndex();
    const prevGlobalIndex = currentGlobalIndex <= 0 ? total - 1 : currentGlobalIndex - 1;
    await playSongByGlobalIndex(prevGlobalIndex, { recordShuffleHistory: false });
    scrollToActiveSong();
}

async function nextSong() {
    const source = musicData || [];
    if (!source.length) return;
    if (shuffleEnabled) {
        await playSongByGlobalIndex(getNextShuffleGlobalIndex(), { recordShuffleHistory: true });
        scrollToActiveSong();
        return;
    }
    const total = Number(totalMusicCount || 0);
    if (total <= 0) return;
    const currentGlobalIndex = getCurrentGlobalSongIndex();
    const nextGlobalIndex = currentGlobalIndex >= total - 1 ? 0 : currentGlobalIndex + 1;
    await playSongByGlobalIndex(nextGlobalIndex, { recordShuffleHistory: false });
    scrollToActiveSong();
}

async function playNextSongOrNextPage() {
    const source = musicData || [];
    if (!source.length) return;

    if (shuffleEnabled) {
        await playSongByGlobalIndex(getNextShuffleGlobalIndex(), { recordShuffleHistory: true });
        scrollToActiveSong();
        return;
    }

    if (currentSongIndex >= source.length - 1) {
        if (currentPage < totalPagesCount) {
            currentPage++;
            showTripleLoading?.();
            await loadAndRenderMusicPage();
            hideTripleLoading?.();

            const musicListContainer = document.getElementById("musicList");
            if (musicListContainer) {
                musicListContainer.scrollTo({
                    top: 0,
                    behavior: "smooth",
                });
            }

            playSong(0);

            scrollToActiveSong();
        }
    } else {
        nextSong();
        scrollToActiveSong();
    }
}

function scrollToActiveSong(behavior = "smooth") {
    const activeItem = document.querySelector(".music-item.active");
    if (activeItem) {
        activeItem.scrollIntoView({
            behavior: behavior,
            block: "center",
        });
    }
}

function downloadSong() {
    const audio = document.getElementById("audioPlayer");
    const src = audio.getAttribute("src");
    if (!src) {
        window.notify("No song is currently loaded.", "warning");
        return;
    }

    let actualUrl = src;
    const urlParamMatch = src.match(/[?&]url=([^&]+)/);
    if (urlParamMatch) {
        actualUrl = decodeURIComponent(urlParamMatch[1]);
    }

    window.open(`/api/download_song?url=${encodeURIComponent(actualUrl)}`, "_blank");
}

function copyLink(url = null) {
    const textToCopy = url || audioPlayer?.src;
    if (!textToCopy) {
        window.notify("No song is currently loaded.", "warning");
        return;
    }

    // ✅ Modern secure method
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard
            .writeText(textToCopy)
            .then(showCopyPopup)
            .catch((err) => {
                console.error("Clipboard error:", err);
                fallbackCopy(textToCopy);
            });
    } else {
        // ✅ Fallback method for HTTP or unsupported browsers
        fallbackCopy(textToCopy);
    }
}

// Fallback using <textarea> + execCommand
function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);

    textarea.select();
    try {
        document.execCommand("copy");
        showCopyPopup();
    } catch (err) {
        console.error("Fallback copy failed:", err);
        window.notify("Failed to copy the link.", "error");
    }
    document.body.removeChild(textarea);
}

function showCopyPopup() {
    if (!isMobileDevice()) {
        const popup = document.getElementById("copyPopup");
        popup.style.display = "block";
        setTimeout(() => {
            popup.style.display = "none";
        }, 1500);
    }
}

async function getDuration(url) {
    if (durationCache[url]) {
        return durationCache[url];
    }

    if (durationPromiseCache.has(url)) {
        return durationPromiseCache.get(url);
    }

    const durationPromise = new Promise((resolve) => {
        const audio = new Audio(url);
        audio.preload = "metadata";

        let settled = false;
        const finish = (value) => {
            if (settled) return;
            settled = true;
            durationPromiseCache.delete(url);
            resolve(value);
            audio.removeAttribute("src");
            audio.load?.();
        };

        audio.addEventListener("loadedmetadata", () => {
            durationCache[url] = audio.duration;
            localStorage.setItem('audioDurationCache', JSON.stringify(durationCache));
            finish(audio.duration);
        });

        audio.addEventListener("error", () => finish(0));
        setTimeout(() => finish(0), 5000);
    });

    durationPromiseCache.set(url, durationPromise);
    return durationPromise;
}

function updateVolume(value) {
    audioPlayer.volume = value / 100;
    document.getElementById("volumePercentage").textContent = `${value}%`;
}

function isMobileDevice() {
    return window.innerWidth <= 768;
}

const MUSIC_MOBILE_FULLSCREEN_STATE_KEY = "__musicMobileFullscreen";

function isMusicMobileFullscreenHistoryState(state = window.history.state) {
    return Boolean(
        state &&
        typeof state === "object" &&
        state[MUSIC_MOBILE_FULLSCREEN_STATE_KEY] === true
    );
}

function setMusicMobileFullscreenMode(isActive) {
    const albumSection = document.getElementById("albumSection");
    const fullscreenBtn = document.getElementById("fullscreenBtn");

    document.body.classList.toggle("music-mobile-fullscreen", Boolean(isActive));
    if (albumSection) {
        albumSection.classList.toggle("fullscreen-mobile", Boolean(isActive));
    }

    if (fullscreenBtn) {
        // Legacy text fallback; syncFullscreenButton will render icon markup.
        fullscreenBtn.textContent = isActive ? "â®Œ" : "â›¶";
    }

    syncFullscreenButton(Boolean(isActive));
}

document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement && !document.body.classList.contains("music-mobile-fullscreen")) {
        document.getElementById("albumSection").classList.remove("fullscreen");
        document.getElementById("fullscreenBtn").textContent = "⛶";
    }
});

document.addEventListener("fullscreenchange", () => {
    const isExpanded = !!document.fullscreenElement || document.body.classList.contains("music-mobile-fullscreen");
    syncFullscreenButton(isExpanded);
});

window.addEventListener("popstate", () => {
    if (document.body.classList.contains("music-mobile-fullscreen")) {
        setMusicMobileFullscreenMode(false);
    }
});

function toggleFullscreen() {
    const albumSection = document.getElementById("albumSection");
    const fullscreenBtn = document.getElementById("fullscreenBtn");
    if (isMobileDevice()) {
        const entering = !document.body.classList.contains("music-mobile-fullscreen");

        if (entering) {
            setMusicMobileFullscreenMode(true);

            if (!isMusicMobileFullscreenHistoryState()) {
                const currentState =
                    window.history.state && typeof window.history.state === "object"
                        ? window.history.state
                        : {};

                window.history.pushState(
                    {
                        ...currentState,
                        [MUSIC_MOBILE_FULLSCREEN_STATE_KEY]: true,
                    },
                    "",
                    window.location.href
                );
            }
        } else {
            setMusicMobileFullscreenMode(false);

            if (isMusicMobileFullscreenHistoryState()) {
                window.history.back();
            }
        }

        if (entering) {
            window.scrollTo({ top: 0, behavior: "auto" });
        }
        return;
    }

    if (!document.fullscreenElement) {
        albumSection.classList.add("fullscreen");
        fullscreenBtn.textContent = "⮌";
        albumSection.requestFullscreen().catch((err) => {
            console.error("Fullscreen failed:", err);
        });
        syncFullscreenButton(true);
    } else {
        document.exitFullscreen();
    }
}

function updatePagination(source = null) {
    const totalPages = Math.max(1, totalPagesCount || 1);
    const current = Math.min(currentPage, totalPages) || 1;

    const pageInfo = document.getElementById("pageInfo");
    if (pageInfo) {
        pageInfo.textContent = `Page ${current} of ${totalPages || 1}`;
    }

    if (prevPageBtn) prevPageBtn.disabled = current <= 1;
    if (nextPageBtn) nextPageBtn.disabled = current >= totalPages;
}

async function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        requestUrlHistoryPush();
        showTripleLoading?.();
        await loadAndRenderMusicPage();
        hideTripleLoading?.();
    }
}

async function nextPage() {
    if (currentPage < totalPagesCount) {
        currentPage++;
        requestUrlHistoryPush();
        showTripleLoading?.();
        await loadAndRenderMusicPage();
        hideTripleLoading?.();
    }
}

function renderTracks(tracks, activeSongId = null) {
    musicList.innerHTML = "";

    if (tracks.length === 0) {
        musicList.innerHTML = `<p class="no-results">No songs found.</p>`;
        return;
    }

    const fragment = document.createDocumentFragment();
    const durationTargets = [];

    for (let i = 0; i < tracks.length; i++) {
        const track = tracks[i];

        // ✅ Detect whether this song is active (either by ID or index)
        const isActive =
            track.id === activeSongId ||
            (filteredResults
                ? i === currentSongIndex // use filtered index
                : musicData.indexOf(track) === currentSongIndex);

        const div = document.createElement("div");
        div.className = "music-item" + (isActive ? " active" : "");

        const cachedDuration = track.duration || durationCache[track.url] || 0;

        div.innerHTML = `
            <div class="left-content">
                <div class="image-wrapper ${isActive ? "active" : ""}">
                    <img src="${track.image}" alt="${track.title}" loading="lazy" decoding="async" />
                    <ion-icon name="play-circle-outline" class="hover-play-icon"></ion-icon>
                </div>
                <div class="title-artist">
                    <span class="title">${track.title}</span>
                    <span class="artist">${track.artist}</span>
                </div>
            </div>
            <div class="share-section">
                <span class="duration">${cachedDuration ? formatTime(cachedDuration) : "--:--"}</span>
                <button class="copy-btn"><ion-icon name="copy-outline"></ion-icon></button>
            </div>
        `;

        div.addEventListener("click", () => {
            playSong(i);
        });

        const copyBtn = div.querySelector(".copy-btn");
        copyBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            copyLink(track.url);
        });

        const durationEl = div.querySelector(".duration");
        if (durationEl && !cachedDuration) {
            durationTargets.push({ track, el: durationEl });
        }

        fragment.appendChild(div);
    }

    musicList.appendChild(fragment);
    hydrateTrackDurations(durationTargets);
}

function renderList(activeSongId = null) {
    const source = musicData || [];

    if (!source || source.length === 0) {
        musicList.innerHTML = `<p class="no-results">No songs found.</p>`;
        currentSongData = null;
        syncLyricsPanel(null);
        closeLyricsModal();
        updatePagination();
        updateMusicHeader();
        return;
    }

    renderTracks(source, activeSongId);

    updatePagination();
    scrollToActiveSong();
    updateMusicHeader();
}

function hydrateTrackDurations(targets = []) {
    if (!targets.length) return;

    const run = async () => {
        for (const { track, el } of targets) {
            if (!track?.url || !el?.isConnected) continue;
            if (!track.duration) {
                track.duration = await getDuration(track.url);
            }
            if (el.isConnected) {
                el.textContent = formatTime(track.duration);
            }
        }
    };

    if (typeof window.requestIdleCallback === "function") {
        window.requestIdleCallback(() => run().catch(console.error), { timeout: 1200 });
    } else {
        setTimeout(() => run().catch(console.error), 0);
    }
}

function updateProgress() {
    if (audioPlayer && progress) {
        const currentTime = audioPlayer.currentTime;
        const duration = audioPlayer.duration;
        const progressPercent = (currentTime / duration) * 100;
        const handlePercent =
            Number.isFinite(progressPercent) && !Number.isNaN(progressPercent)
                ? Math.min(Math.max(progressPercent, 0), 100)
                : 0;
        progress.style.width = handlePercent + "%";
        if (progressHandle) {
            progressHandle.style.left = handlePercent + "%";
        }
        currentTimeEl.textContent = formatTime(currentTime);
    }
}

function updateDuration() {
    if (audioPlayer && totalDurationEl) {
        totalDurationEl.textContent = formatTime(audioPlayer.duration);
    }
}

function formatTime(seconds) {
    if (typeof seconds === "string" && /^\d{1,2}:\d{2}$/.test(seconds)) {
        return seconds;
    }

    if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) {
        return "0:00";
    }

    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60)
        .toString()
        .padStart(2, "0");
    return `${minutes}:${secs}`;
}

function seek(event) {
    if (!audioPlayer.duration) return;

    const rect = progressBar.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const width = rect.width;
    const seekTime = (offsetX / width) * audioPlayer.duration;

    const wasPaused = audioPlayer.paused;
    audioPlayer.currentTime = seekTime;

    // ✅ Only play if it was already playing
    if (wasPaused) {
        audioPlayer.pause();
    }
}

function toggleAutoplay() {
    autoplayEnabled = !autoplayEnabled;
    const btn = document.getElementById("autoplayBtn");
    btn.textContent = autoplayEnabled ? "♬" : "⏹️";
    btn.title = `Autoplay: ${autoplayEnabled ? "On" : "Off"}`;
    syncAutoplayButton();
    localStorage.setItem("autoplay", autoplayEnabled);
}

function toggleShuffle() {
    shuffleEnabled = !shuffleEnabled;
    shuffleHistoryGlobal = [];
    if (shuffleEnabled) {
        resetShuffleQueue(getCurrentGlobalSongIndex());
    } else {
        shuffleQueueGlobal = [];
        shuffleQueueContextKey = "";
    }
    syncShuffleButton();
    localStorage.setItem("musicShuffle", shuffleEnabled);
}

audioPlayer.addEventListener("timeupdate", updateProgress);
audioPlayer.addEventListener("loadedmetadata", updateDuration);
audioPlayer.addEventListener("play", syncPlayPauseButton);
audioPlayer.addEventListener("pause", syncPlayPauseButton);
progressBar.addEventListener("click", (event) => seek(event));
progressBar.addEventListener("mousedown", (event) => {
    isDragging = true;
    if (!isMobileDevice()) stopVisualizer();
    seek(event);
});

// --- Desktop Mouse Events ---
document.addEventListener("mousemove", (event) => {
    if (isDragging) {
        seek(event);
    }
});

document.addEventListener("mouseup", () => {
    isDragging = false;
    if (!isMobileDevice()) startVisualizer();
});

// --- Mobile Touch Events ---
progressBar.addEventListener("touchstart", (event) => {
    isDragging = true;
    if (!isMobileDevice()) stopVisualizer();
    seek(event.touches[0]); // First touch point
});

document.addEventListener("touchmove", (event) => {
    if (isDragging) {
        seek(event.touches[0]);
    }
});

document.addEventListener("touchend", () => {
    isDragging = false;
    if (!isMobileDevice()) startVisualizer();
});

audioPlayer.addEventListener("ended", () => {
    coverImg.classList.remove("spin");
    if (autoplayEnabled) {
        playNextSongOrNextPage();
    }
});
// Add volume control
const volumeSlider = document.getElementById("volumeSlider");
volumeSlider.addEventListener("input", (e) => updateVolume(e.target.value));


// Toggle navbar menu visibility
document.getElementById("navbarToggle").addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    const toggleButton = document.getElementById("navbarToggle");
    sidebar.classList.toggle("active");
    toggleButton.classList.toggle("active");
});

// Close sidebar when clicking outside
document.addEventListener("click", function (e) {
    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("navbarToggle");
    if (
        !sidebar.contains(e.target) &&
        !toggle.contains(e.target) &&
        sidebar.classList.contains("active")
    ) {
        sidebar.classList.remove("active");
        toggle.classList.remove("active");
    }
});

// Initialize autoplay from localStorage
autoplayEnabled = localStorage.getItem("autoplay") !== "false";
shuffleEnabled = localStorage.getItem("musicShuffle") === "true";
const autoplayBtn = document.getElementById("autoplayBtn");
if (autoplayBtn) {
    autoplayBtn.textContent = autoplayEnabled ? "♬" : "⏹️";
    autoplayBtn.title = `Autoplay: ${autoplayEnabled ? "On" : "Off"}`;
    syncAutoplayButton();
}
syncShuffleButton();

async function handleSearch(query) {
    if (!musicDataLoaded) return;
    query = query.trim().toLowerCase();

    activeSearchQuery = query;
    filteredResults = null; // server-side filtering now
    currentPage = 1;
    requestUrlHistoryPush();
    showTripleLoading?.();
    await loadAndRenderMusicPage();
    hideTripleLoading?.();
}

async function clearSearch() {
    const input = document.getElementById('navbarSearch');
    input.value = '';
    filteredResults = null;
    activeSearchQuery = "";
    currentPage = 1;
    requestUrlHistoryPush();
    showTripleLoading?.();
    await loadAndRenderMusicPage();
    hideTripleLoading?.();
}

const dropdownBtn = document.querySelector('.social-dropdown-btn');
const dropdown = document.querySelector('.social-dropdown');

dropdownBtn.addEventListener('click', () => {
    dropdown.classList.toggle('active');
});

document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

function updateMusicHeader() {
    const header = document.getElementById("music-header");
    if (!header) return;

    const total = Number(totalMusicCount || 0);

    header.textContent = `My Music List (${total} ${total === 1 ? "song" : "songs"})`;
}

function initVisualizer() {
    if (!audioPlayer || !canvas || !ctx) return;
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (!source) source = audioContext.createMediaElementSource(audioPlayer);
    if (!analyser) analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.72;
    bufferLength = analyser.frequencyBinCount;
    dataArray = new Uint8Array(bufferLength);
    source.connect(analyser);

    if (!window.__vizGain) {
        window.__vizGain = audioContext.createGain();
        window.__vizBass = audioContext.createBiquadFilter();
        window.__vizBass.type = 'lowshelf';
        window.__vizBass.frequency.value = 200;
        analyser.connect(window.__vizBass);
        window.__vizBass.connect(window.__vizGain);
        window.__vizGain.connect(audioContext.destination);
    }
    setupVisualizerControls();
    resizeCanvas();
}

function resizeCanvas() { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }
window.addEventListener("resize", resizeCanvas);

const vizState = { mode:'Neon Wave', style:'Vertical Bars', theme:'Dark', barCount:96, barWidth:4, sensitivity:120, smoothness:72, waveSpeed:10, glowIntensity:16, particleAmount:85, barColor:'#28d7ff', bgColor:'#130a25', beat:0, t:0 };
const particles = [];
let micStream;

function setupVisualizerControls() {
    const map = [['vizMode','mode'],['vizStyle','style'],['vizTheme','theme'],['barCount','barCount'],['barWidth','barWidth'],['sensitivity','sensitivity'],['smoothness','smoothness'],['waveSpeed','waveSpeed'],['glowIntensity','glowIntensity'],['particleAmount','particleAmount'],['barColor','barColor'],['bgColor','bgColor']];
    map.forEach(([id,key])=>{ const el=document.getElementById(id); if(!el||el.dataset.bound) return; el.dataset.bound='1'; el.addEventListener('input',()=>{ vizState[key]=el.type==='range'?Number(el.value):el.value; if(key==='smoothness'&&analyser) analyser.smoothingTimeConstant=vizState.smoothness/100; });});
    const volume = document.getElementById('vizVolume'); if(volume && !volume.dataset.bound){ volume.dataset.bound='1'; volume.addEventListener('input', ()=>{audioPlayer.volume=Number(volume.value)/100; if(window.__vizGain) window.__vizGain.gain.value=audioPlayer.volume;});}
    const bass = document.getElementById('bassBoost'); if(bass && !bass.dataset.bound){ bass.dataset.bound='1'; bass.addEventListener('input', ()=>{ if(window.__vizBass) window.__vizBass.gain.value=Number(bass.value);});}
    const upBtn=document.getElementById('uploadAudioBtn'), upInput=document.getElementById('uploadAudioInput'); if(upBtn && upInput && !upBtn.dataset.bound){ upBtn.dataset.bound='1'; upBtn.onclick=()=>upInput.click(); upInput.onchange=(e)=>{ const f=e.target.files?.[0]; if(f){ audioPlayer.src=URL.createObjectURL(f); audioPlayer.play(); startVisualizer(); } }; }
    const micBtn=document.getElementById('micInputBtn'); if(micBtn && !micBtn.dataset.bound){ micBtn.dataset.bound='1'; micBtn.onclick=async()=>{ try{ if(micStream){ micStream.getTracks().forEach(t=>t.stop()); micStream=null; micBtn.classList.remove('active'); return;} micStream=await navigator.mediaDevices.getUserMedia({audio:true}); const micSource=audioContext.createMediaStreamSource(micStream); micSource.connect(analyser); micBtn.classList.add('active'); startVisualizer(); }catch(err){ console.error(err);} }; }
    const fsBtn=document.getElementById('fullscreenVizBtn'); if(fsBtn && !fsBtn.dataset.bound){ fsBtn.dataset.bound='1'; fsBtn.onclick=()=>toggleFullscreen(); }
    const saveBtn=document.getElementById('savePresetBtn'); if(saveBtn && !saveBtn.dataset.bound){ saveBtn.dataset.bound='1'; saveBtn.onclick=()=>localStorage.setItem('vizCustomPreset',JSON.stringify(vizState)); }
    const loadBtn=document.getElementById('loadPresetBtn'); if(loadBtn && !loadBtn.dataset.bound){ loadBtn.dataset.bound='1'; loadBtn.onclick=()=>{ const raw=localStorage.getItem('vizCustomPreset'); if(!raw) return; Object.assign(vizState, JSON.parse(raw)); Object.entries(vizState).forEach(([k,v])=>{ const el=document.getElementById(k==='mode'?'vizMode':k==='style'?'vizStyle':k==='theme'?'vizTheme':k); if(el) el.value=v;}); }; }
}

function drawVisualizer() {
    if (!visualizerRunning || !analyser) return;
    requestAnimationFrame(drawVisualizer);
    analyser.getByteFrequencyData(dataArray);
    const wave = new Uint8Array(bufferLength); analyser.getByteTimeDomainData(wave);
    const w=canvas.width, h=canvas.height, cX=w/2, cY=h/2;
    vizState.t += 0.01*vizState.waveSpeed;
    const bassEnergy = dataArray.slice(0, 24).reduce((a,b)=>a+b,0)/24;
    vizState.beat = bassEnergy > vizState.sensitivity ? 1 : Math.max(0, vizState.beat - 0.06);
    ctx.fillStyle = vizState.bgColor; ctx.globalAlpha=0.17; ctx.fillRect(0,0,w,h); ctx.globalAlpha=1;
    ctx.shadowBlur = vizState.glowIntensity; ctx.shadowColor = vizState.barColor; ctx.strokeStyle = vizState.barColor; ctx.fillStyle = vizState.barColor;
    const count = Math.max(8, vizState.barCount); const step=Math.floor(bufferLength/count);
    if (vizState.style === 'Waveform') { ctx.beginPath(); for(let i=0;i<count;i++){ const x=(i/(count-1))*w; const y=(wave[i*step]/255)*h; i?ctx.lineTo(x,y):ctx.moveTo(x,y);} ctx.stroke(); }
    else if (vizState.style === 'Circular Spectrum' || vizState.style === 'Radial Pulse') { for(let i=0;i<count;i++){ const a=(i/count)*Math.PI*2; const v=(dataArray[i*step]/255)*vizState.sensitivity; const r=(vizState.style==='Radial Pulse'?80:130)+(v*0.8)+(vizState.beat*24); ctx.fillRect(cX+Math.cos(a)*r, cY+Math.sin(a)*r, vizState.barWidth, vizState.barWidth+v*0.2);} }
    else { let x=0; const bw=vizState.barWidth; for(let i=0;i<count;i++){ const v=(dataArray[i*step]/255)*h*0.7*(vizState.sensitivity/100); if(vizState.style==='3D Tunnel Bars'){ const p=i/count; const z=(Math.sin(vizState.t+p*8)+1)*0.5; ctx.globalAlpha=0.3+z*0.7; } ctx.fillRect(x,h-v,bw,v); x+=bw+2; } ctx.globalAlpha=1; }
    for(let i=particles.length;i<vizState.particleAmount;i++) particles.push({x:Math.random()*w,y:Math.random()*h,v:0.4+Math.random()*1.6,s:1+Math.random()*2});
    particles.length = vizState.particleAmount;
    particles.forEach(p=>{ p.y-=p.v + vizState.beat*1.3; if(p.y<0){p.y=h; p.x=Math.random()*w;} ctx.globalAlpha=0.2+Math.random()*0.6; ctx.fillRect(p.x,p.y,p.s,p.s);});
    ctx.globalAlpha=1;
}

function startVisualizer() { initVisualizer(); if (audioContext?.state === 'suspended') audioContext.resume(); if (!visualizerRunning) { visualizerRunning = true; drawVisualizer(); } }
function stopVisualizer() { visualizerRunning = false; }


window.handleSearch = handleSearch;
window.clearSearch = clearSearch;
window.prevPage = prevPage;
window.nextPage = nextPage;
window.downloadSong = downloadSong;
window.copyLink = copyLink;
window.prevSong = prevSong;
window.togglePlay = togglePlay;
window.nextSong = nextSong;
window.toggleShuffle = toggleShuffle;
window.toggleAutoplay = toggleAutoplay;
window.toggleFullscreen = toggleFullscreen;

