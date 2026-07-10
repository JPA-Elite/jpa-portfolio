import { MusicService } from "../services/MusicService.js";

const musicService = new MusicService();

const CATEGORY_ICONS = {
    "All": "🎵",
    "Rap": "🎤",
    "Love Song": "💖",
    "Pop": "🎧",
    "R&B": "🕺",
    "Rock": "🎸",
    "Chill": "🌊",
    "Party": "🎉",
    "Workout": "💪",
    "Mood": "😌",
    "Focus": "🎯"
};

const CATEGORY_COLORS = {
    "All": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "Rap": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    "Love Song": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
    "Pop": "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
    "R&B": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
    "Rock": "linear-gradient(135deg, #ff0844 0%, #ffb199 100%)",
    "Chill": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "Party": "linear-gradient(135deg, #f6d365 0%, #fda085 100%)",
    "Workout": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    "Mood": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
    "Focus": "linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%)"
};

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
let activeSearchQuery = "";
let currentCategory = "All";
let availableCategories = [];
let totalMusicCount = 0;
let totalPagesCount = 1;
let currentSongData = null;
const voteStateCache = {};
window.voteStateCache = voteStateCache;
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

function updateActiveSongDisplay(song, { prefix = "" } = {}) {
    if (!song) return;
    if (nowPlaying) {
        nowPlaying.innerHTML = `<ion-icon name="musical-notes-outline"></ion-icon> ${song.title}`;
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
        const sameSongAlreadyLoaded = audioPlayer?.src && currentSongData && String(currentSongData.id) === storedId;
        if (!sameSongAlreadyLoaded) {
            setAudioSrcForSong(track);
        }
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

const LRC_TIME_RE = /\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]/g;

let currentLyrics = { isLrc: false, lines: [] };
let activeLyricIndex = -1;
let isLyricsModalOpen = false;

function parseLrc(raw) {
    if (typeof raw !== "string" || !raw.trim()) {
        return { isLrc: false, lines: [] };
    }
    if (!/\[\d{1,2}:\d{1,2}/.test(raw)) {
        return { isLrc: false, lines: [] };
    }

    const rows = raw.split(/\r\n|\r|\n/);
    const lines = [];

    for (const row of rows) {
        const times = [];
        let match;
        LRC_TIME_RE.lastIndex = 0;
        while ((match = LRC_TIME_RE.exec(row)) !== null) {
            const minutes = Number(match[1]);
            const seconds = Number(match[2]);
            const fractionRaw = match[3] ? match[3].padEnd(3, "0") : "0";
            const fraction = Number(fractionRaw) / 1000;
            times.push(minutes * 60 + seconds + fraction);
        }

        const text = row.replace(LRC_TIME_RE, "").trim();
        if (!times.length) continue;

        for (const time of times) {
            lines.push({ time, text });
        }
    }

    lines.sort((a, b) => a.time - b.time);
    return { isLrc: true, lines };
}

function renderLrcLyrics(lines) {
    if (!lyricsModalContentEl) return;

    lyricsModalContentEl.innerHTML = "";
    lyricsModalContentEl.classList.remove("is-empty");

    if (!lines.length) {
        renderLyricsContent("No lyrics added for this song yet.", { isEmptyState: true });
        return;
    }

    lines.forEach((line, index) => {
        const lineEl = document.createElement("div");
        lineEl.className = "lyrics-modal__line";
        lineEl.dataset.index = String(index);
        lineEl.dataset.time = String(line.time);
        lineEl.setAttribute("role", "button");
        lineEl.setAttribute("tabindex", "0");

        if (!line.text) {
            lineEl.classList.add("lyrics-modal__line--blank");
            lineEl.innerHTML = "&nbsp;";
        } else {
            lineEl.textContent = line.text;
        }

        const seekToLine = () => {
            if (!audioPlayer || Number.isNaN(line.time)) return;
            audioPlayer.currentTime = line.time;
            updateActiveLyric(line.time, true);
        };

        lineEl.addEventListener("click", seekToLine);
        lineEl.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                seekToLine();
            }
        });

        lyricsModalContentEl.appendChild(lineEl);
    });
}

function findActiveLyricIndex(time) {
    const lines = currentLyrics.lines;
    if (!lines.length || Number.isNaN(time)) return -1;

    let index = -1;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].time <= time) {
            index = i;
        } else {
            break;
        }
    }
    return index;
}

function updateActiveLyric(time = audioPlayer?.currentTime || 0, scroll = false) {
    if (!currentLyrics.isLrc || !lyricsModalContentEl) return;

    const index = findActiveLyricIndex(time);
    if (index === activeLyricIndex) return;
    activeLyricIndex = index;

    const allLines = lyricsModalContentEl.querySelectorAll(".lyrics-modal__line");
    allLines.forEach((el, i) => el.classList.toggle("is-active", i === index));

    const activeEl = index >= 0 ? allLines[index] : null;
    if (activeEl && (scroll || isLyricsModalOpen)) {
        activeEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
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

    const lyrics = (typeof song.lyrics === "string" ? song.lyrics : "").trim();
    lyricsModalTitleEl.textContent = song.title || "Lyrics";
    lyricsModalArtistEl.textContent = song.artist || "";
    if (!lyrics) {
        currentLyrics = { isLrc: false, lines: [] };
        activeLyricIndex = -1;
        renderLyricsContent("No lyrics added for this song yet.", { isEmptyState: true });
        return;
    }

    const parsed = parseLrc(lyrics);
    currentLyrics = parsed;
    activeLyricIndex = -1;

    if (parsed.isLrc) {
        renderLrcLyrics(parsed.lines);
        updateActiveLyric(audioPlayer?.currentTime || 0, isLyricsModalOpen);
    } else {
        renderLyricsContent(lyrics, { isEmptyState: false });
    }
}

function openLyricsModal() {
    if (!lyricsModal) return;
    const song = getCurrentSong();
    if (!song) return;

    syncLyricsPanel(song);
    isLyricsModalOpen = true;
    lyricsModal.classList.add("is-open");
    lyricsModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("lyrics-modal-open");
    updateActiveLyric(audioPlayer?.currentTime || 0, true);
}

function closeLyricsModal() {
    if (!lyricsModal) return;
    isLyricsModalOpen = false;
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

    const categoryToggleBtn = document.getElementById("categoryToggle");
    if (categoryToggleBtn) {
        categoryToggleBtn.addEventListener("click", toggleCategories);
    }

    showTripleLoading?.();
    try {
        await loadCategories();
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
    const params = new URLSearchParams();
    params.set("page", String(currentPage));
    params.set("per_page", String(itemsPerPage));
    if (activeSearchQuery) {
        params.set("search", activeSearchQuery);
    }
    if (currentCategory && currentCategory !== "All") {
        params.set("category", currentCategory);
    }

    const result = await musicService.fetchMusicList(params);
    const items = result?.music || [];
    totalMusicCount = Number(result?.total_music || 0);
    totalPagesCount = Math.max(1, Number(result?.total_pages || 1));
    currentPage = Math.max(1, Number(result?.page || currentPage));

    return items;
}

async function loadCategories() {
    try {
        const result = await musicService.fetchCategories();
        const categories = result?.categories || ["All"];
        const counts = result?.counts || {};

        availableCategories = categories;

        const container = document.getElementById("categoryTabs");
        if (!container || categories.length === 0) return;

        const row = document.createElement("div");
        row.className = "category-tag-row";

        categories.forEach((cat) => {
            const count = counts[cat] || 0;
            const isActive = cat === currentCategory;
            const icon = CATEGORY_ICONS[cat] || "🎵";

            const tag = document.createElement("button");
            tag.type = "button";
            tag.className = `category-tag${isActive ? " active" : ""}`;
            tag.setAttribute("data-category", cat);
            tag.setAttribute("aria-pressed", String(isActive));
            tag.innerHTML = `${icon} ${cat} <span class="category-tag__count">${count}</span>`;
            tag.addEventListener("click", () => filterByCategory(cat));
            row.appendChild(tag);
        });

        container.innerHTML = "";
        container.appendChild(row);
    } catch (err) {
        console.error("Failed to load categories:", err);
    }
}

function filterByCategory(category) {
    currentCategory = category || "All";
    currentPage = 1;

    document.querySelectorAll(".category-tag").forEach((tag) => {
        const cat = tag.getAttribute("data-category");
        const isActive = cat === currentCategory;
        tag.classList.toggle("active", isActive);
        tag.setAttribute("aria-pressed", String(isActive));
    });

    showTripleLoading?.();
    loadAndRenderMusicPage({ resetSelection: false }).finally(() => {
        hideTripleLoading?.();
    });
    toggleCategories();
}

function setCategoriesCollapsed(collapsed) {
    const container = document.getElementById("categoryTabs");
    const btn = document.getElementById("categoryToggle");
    if (!container || !btn) return;

    const expanded = btn.getAttribute("aria-expanded") !== "false";
    if (expanded === !collapsed) return;

    btn.setAttribute("aria-expanded", String(!collapsed));
    container.classList.toggle("category-tabs--collapsed", collapsed);
    btn.querySelector(".category-toggle__icon").setAttribute("name", collapsed ? "chevron-up-outline" : "chevron-down-outline");
}

function toggleCategories() {
    const btn = document.getElementById("categoryToggle");
    if (!btn) return;
    setCategoriesCollapsed(btn.getAttribute("aria-expanded") === "true");
}

window.toggleCategories = toggleCategories;

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

    currentSongIndex = Math.floor(Math.random() * musicData.length);
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

    setCategoriesCollapsed(true);

    coverImg.classList.add("spin");
    audioPlayer.play();
    if (!isMobileDevice()) startVisualizer();
    syncPlayPauseButton();
    markGlobalSongAsPlayed(getCurrentGlobalSongIndex());

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

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard
            .writeText(textToCopy)
            .then(showCopyPopup)
            .catch((err) => {
                console.error("Clipboard error:", err);
                fallbackCopy(textToCopy);
            });
    } else {
        fallbackCopy(textToCopy);
    }
}

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
        fullscreenBtn.textContent = isActive ? "⮌" : "⛶";
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
        const cachedVote = voteStateCache[track.id];

        const isActive =
            track.id === activeSongId ||
            (currentSongData && track.id === currentSongData.id);

        const div = document.createElement("div");
        div.className = "music-item" + (isActive ? " active" : "");

        const cachedDuration = track.duration || durationCache[track.url] || 0;
        const likeCount = cachedVote ? cachedVote.like_counts : 0;
        const dislikeCount = cachedVote ? cachedVote.dislike_counts : 0;
        const likeVoted = cachedVote && cachedVote.user_vote === true;
        const dislikeVoted = cachedVote && cachedVote.user_vote === false;

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
            <div class="music-item-actions">
                <div class="vote-group">
                    <button class="vote-btn like-btn${likeVoted ? " voted" : ""}" data-music-id="${track.id}" data-vote="1" type="button" aria-label="Like">
                        <ion-icon name="thumbs-up-outline"></ion-icon>
                        <span class="vote-count">${likeCount}</span>
                    </button>
                    <button class="vote-btn dislike-btn${dislikeVoted ? " voted" : ""}" data-music-id="${track.id}" data-vote="0" type="button" aria-label="Dislike">
                        <ion-icon name="thumbs-down-outline"></ion-icon>
                        <span class="vote-count">${dislikeCount}</span>
                    </button>
                </div>
                <div class="duration-row">
                    <span class="duration">${cachedDuration ? formatTime(cachedDuration) : "--:--"}</span>
                </div>
            </div>
        `;

        div.addEventListener("click", () => {
            playSong(i);
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
        musicList.innerHTML = currentCategory !== "All"
            ? `<div class="empty-category-state"><span class="empty-category-state__icon">${CATEGORY_ICONS[currentCategory] || "🎵"}</span><p class="empty-category-state__text">There is no music in <strong>${currentCategory}</strong></p></div>`
            : `<p class="no-results">No songs found.</p>`;
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
audioPlayer.addEventListener("timeupdate", () => updateActiveLyric());
audioPlayer.addEventListener("loadedmetadata", updateDuration);
audioPlayer.addEventListener("play", syncPlayPauseButton);
audioPlayer.addEventListener("pause", syncPlayPauseButton);
progressBar.addEventListener("click", (event) => seek(event));
progressBar.addEventListener("mousedown", (event) => {
    isDragging = true;
    if (!isMobileDevice()) stopVisualizer();
    seek(event);
});

document.addEventListener("mousemove", (event) => {
    if (isDragging) {
        seek(event);
    }
});

document.addEventListener("mouseup", () => {
    isDragging = false;
    if (!isMobileDevice()) startVisualizer();
});

progressBar.addEventListener("touchstart", (event) => {
    isDragging = true;
    if (!isMobileDevice()) stopVisualizer();
    seek(event.touches[0]);
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

const volumeSlider = document.getElementById("volumeSlider");
volumeSlider.addEventListener("input", (e) => updateVolume(e.target.value));


document.getElementById("navbarToggle").addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    const toggleButton = document.getElementById("navbarToggle");
    const navIcon = toggleButton.querySelector(".navbar-toggle-icon");
    const isOpen = !sidebar.classList.contains("active");
    sidebar.classList.toggle("active");
    toggleButton.classList.toggle("active");
    if (navIcon) {
        navIcon.setAttribute("name", isOpen ? "close-outline" : "menu-outline");
    }
});



const mobileMediaDropdown = document.querySelector(".mobile-media-dropdown");
const mobileMediaToggle = document.querySelector(".mobile-media-toggle");
if (mobileMediaDropdown && mobileMediaToggle) {
    mobileMediaToggle.addEventListener("click", (event) => {
        event.preventDefault();
        mobileMediaDropdown.classList.toggle("is-open");
    });
}


const desktopMediaDropdown = document.querySelector(".media-dropdown");
const desktopMediaTrigger = document.querySelector(".media-dropdown-trigger");
if (desktopMediaDropdown && desktopMediaTrigger) {
    desktopMediaTrigger.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        desktopMediaDropdown.classList.toggle("is-open");
    });

    document.addEventListener("click", (event) => {
        if (!desktopMediaDropdown.contains(event.target)) {
            desktopMediaDropdown.classList.remove("is-open");
        }
    });
}

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
        const navIcon = toggle.querySelector(".navbar-toggle-icon");
        if (navIcon) {
            navIcon.setAttribute("name", "menu-outline");
        }
    }
});

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
    filteredResults = null;
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

    header.textContent = `My Tracks (${total} ${total === 1 ? "song" : "songs"})`;
}

const vizConfig = { mode: 'Neon Wave', freq: 196, bass: 10, treble: 8, sensitivity: 125, bars: 72, speed: 10, glow: 14, smooth: 70, phase: 0, off: false };

function toNearestValidFftSize(value) {
    const min = 32; const max = 32768;
    const clamped = Math.min(max, Math.max(min, Number(value) || 256));
    const pow = Math.round(Math.log2(clamped));
    return 2 ** pow;
}

function initVisualizer() {
    if (!audioPlayer || !canvas || !ctx) return;
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        source = audioContext.createMediaElementSource(audioPlayer);
        analyser = audioContext.createAnalyser();
        window.__vizBass = audioContext.createBiquadFilter(); window.__vizBass.type = 'lowshelf'; window.__vizBass.frequency.value = 200;
        window.__vizTreble = audioContext.createBiquadFilter(); window.__vizTreble.type = 'highshelf'; window.__vizTreble.frequency.value = 2200;
        source.connect(analyser); analyser.connect(window.__vizBass); window.__vizBass.connect(window.__vizTreble); window.__vizTreble.connect(audioContext.destination);
        applyMode(vizConfig.mode);
        bindVisualizerSettings();
        resizeCanvas();
    }
}

function applyMode(mode) {
    vizConfig.mode = mode;
    const presets = {
        Disco:{bars:80,speed:16,glow:20,sensitivity:115,smooth:65,bass:16,treble:11}, Jazz:{bars:56,speed:7,glow:8,sensitivity:135,smooth:82,bass:8,treble:9}, 'Neon Wave':{bars:72,speed:10,glow:14,sensitivity:125,smooth:70,bass:10,treble:8}, Cyberpunk:{bars:110,speed:18,glow:24,sensitivity:105,smooth:56,bass:18,treble:16}, 'Lo-fi':{bars:48,speed:4,glow:6,sensitivity:140,smooth:88,bass:6,treble:4}, EDM:{bars:96,speed:20,glow:26,sensitivity:95,smooth:52,bass:22,treble:12}, Chill:{bars:60,speed:6,glow:10,sensitivity:130,smooth:84,bass:9,treble:6}
    };
    if (mode !== 'Custom' && presets[mode]) Object.assign(vizConfig, presets[mode]);
    syncVisualizerUI();
}

function bindVisualizerSettings() {
    const panel=document.getElementById('visualizerSettingsPanel'), openBtn=document.getElementById('visualizerSettingsBtn'), closeBtn=document.getElementById('visualizerCloseBtn'), backdrop=document.getElementById('visualizerSettingsBackdrop');
    const offToggle = document.getElementById('vizOffToggle');
    const openPanel = ()=>{ panel?.classList.add('open'); backdrop?.classList.add('open'); panel?.setAttribute('aria-hidden','false'); backdrop?.setAttribute('aria-hidden','false'); };
    const closePanel = ()=>{ panel?.classList.remove('open'); backdrop?.classList.remove('open'); panel?.setAttribute('aria-hidden','true'); backdrop?.setAttribute('aria-hidden','true'); };
    const togglePanel = ()=>{ if (panel?.classList.contains('open')) closePanel(); else openPanel(); };
    if (openBtn && !openBtn.dataset.bound) { openBtn.dataset.bound='1'; openBtn.addEventListener('click', togglePanel); }
    if (closeBtn && !closeBtn.dataset.bound) { closeBtn.dataset.bound='1'; closeBtn.addEventListener('click', closePanel); }
    if (backdrop && !backdrop.dataset.bound) { backdrop.dataset.bound='1'; backdrop.addEventListener('click', closePanel); }
    if (offToggle && !offToggle.dataset.bound) { offToggle.dataset.bound='1'; offToggle.addEventListener('change',()=>{ const shouldBeOn = offToggle.checked; vizConfig.off = !shouldBeOn; if(!shouldBeOn){ stopVisualizer(); ctx.clearRect(0,0,canvas.width,canvas.height); } else { visualizerRunning = false; startVisualizer(); } syncVisualizerUI(); }); }
    const modes=document.getElementById('visualizerModes'); if (modes && !modes.dataset.bound) { modes.dataset.bound='1'; modes.addEventListener('click',(e)=>{ const m=e.target?.dataset?.mode; if(!m) return; applyMode(m); }); }
    [['vizFreq','freq'],['vizBass','bass'],['vizTreble','treble'],['vizSensitivity','sensitivity'],['vizBars','bars'],['vizSpeed','speed'],['vizGlow','glow'],['vizSmooth','smooth']].forEach(([id,k])=>{ const el=document.getElementById(id); if(!el||el.dataset.bound) return; el.dataset.bound='1'; el.addEventListener('input',()=>{ vizConfig[k]=Number(el.value); vizConfig.mode='Custom'; syncVisualizerUI(); }); });
    syncVisualizerUI();
}

function syncVisualizerUI(){
    const ids={vizFreq:'freq',vizBass:'bass',vizTreble:'treble',vizSensitivity:'sensitivity',vizBars:'bars',vizSpeed:'speed',vizGlow:'glow',vizSmooth:'smooth'};
    Object.entries(ids).forEach(([id,k])=>{const el=document.getElementById(id); if(el && Number(el.value)!==Number(vizConfig[k])) el.value=vizConfig[k];});
    document.querySelectorAll('#visualizerModes button').forEach(b=>b.classList.toggle('active', b.dataset.mode===vizConfig.mode));
    const offToggle=document.getElementById('vizOffToggle'); if(offToggle) offToggle.checked=!vizConfig.off;
    if (analyser) analyser.smoothingTimeConstant = vizConfig.smooth/100;
    if (window.__vizBass) window.__vizBass.gain.value = vizConfig.bass;
    if (window.__vizTreble) window.__vizTreble.gain.value = vizConfig.treble;
}

function resizeCanvas() { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }
window.addEventListener('resize', resizeCanvas);

function drawVisualizer() {
    if (!visualizerRunning || !analyser) return;
    if (vizConfig.off) { requestAnimationFrame(drawVisualizer); return; }
    requestAnimationFrame(drawVisualizer);
    const nextFftSize = toNearestValidFftSize(vizConfig.freq * 2);
    if (analyser.fftSize !== nextFftSize) analyser.fftSize = nextFftSize;
    bufferLength = analyser.frequencyBinCount;
    if (!dataArray || dataArray.length !== bufferLength) dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);
    const w=canvas.width,h=canvas.height; vizConfig.phase += vizConfig.speed*0.012;
    const beat = dataArray.slice(0,20).reduce((a,b)=>a+b,0)/20;
    ctx.clearRect(0,0,w,h); ctx.fillStyle='rgba(7,9,22,0.18)'; ctx.fillRect(0,0,w,h);
    ctx.shadowBlur = vizConfig.glow + beat/20;
    const modeColor = {Disco:'#ff2ad4',Jazz:'#f3d59e','Neon Wave':'#27d9ff',Cyberpunk:'#8e63ff','Lo-fi':'#90b0c5',EDM:'#26ff7f',Chill:'#7fd0ff',Custom:'#ffffff'};
    ctx.fillStyle=modeColor[vizConfig.mode]||'#27d9ff'; ctx.shadowColor=ctx.fillStyle;
    const count=Math.max(8,vizConfig.bars), step=Math.max(1,Math.floor(bufferLength/count)), bw=Math.max(2,w/count-2);
    for(let i=0;i<count;i++){ const v=(dataArray[i*step]/255)*(h*0.74)*(vizConfig.sensitivity/100); const wave=Math.sin(vizConfig.phase+i*0.24)*(vizConfig.speed*0.6); ctx.fillRect(i*(bw+2), h-v-wave, bw, v+Math.max(0,wave)); }
}

function startVisualizer() { if (!audioContext) initVisualizer(); else if (audioContext?.state==='suspended') audioContext.resume(); resizeCanvas(); if (!visualizerRunning) { visualizerRunning=true; drawVisualizer(); } }
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
