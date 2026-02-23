// Declare global variables
let audioPlayer,
    playPauseBtn,
    currentSongIndex = 0;
let currentPage = 1;
const itemsPerPage = 10;
let musicList;
let musicData = [];
let autoplayEnabled = true;
let isDragging = false;
const durationCache = JSON.parse(localStorage.getItem('audioDurationCache') || '{}');
let filteredResults = null;
let musicDataLoaded = false;
const durationPromiseCache = new Map();
const MUSIC_DATA_CACHE_KEY = "musicPageDataCacheV2";
const MUSIC_DATA_CACHE_TTL_MS = 5 * 60 * 1000;
let activeSearchQuery = "";
let totalMusicCount = 0;
let totalPagesCount = 1;
musicList = document.getElementById("musicList");
audioPlayer = document.getElementById("audioPlayer");
const nowPlaying = document.getElementById("nowPlaying");
const coverImg = document.getElementById("coverImg");
const playerNowPlaying = document.getElementById("playerNowPlaying");
const playerCoverImg = document.getElementById("playerCoverImg");
const progressBar = document.getElementById("progressBar");
const progress = document.getElementById("progress");
const currentTimeEl = document.getElementById("currentTime");
const totalDurationEl = document.getElementById("totalDuration");
playPauseBtn = document.getElementById("playPauseBtn");
const canvas = document.getElementById("beatVisualizer");
const ctx = canvas.getContext("2d");
let audioContext, analyser, source, dataArray, bufferLength, visualizerRunning;
const prevPageBtn = document.querySelector(".page-btn[onclick='prevPage()']");
const nextPageBtn = document.querySelector(".page-btn[onclick='nextPage()']");

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.documentElement;
    root.setAttribute("data-theme", "dark");
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
});

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

    const response = await fetch(`/api/music-list?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch music list: ${response.status}`);
    }

    const result = await response.json();
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
    musicData = await loadMusicData();

    if (resetSelection && musicData.length > 0) {
        selectFirstSong();
    }

    renderList(activeSongId);
}

function selectFirstSong() {
    currentSongIndex = Math.floor(Math.random() * musicData.length); // Randomly select an index
    const song = musicData[currentSongIndex];
    audioPlayer.src = isMobileDevice()
        ? song.url : `/api/proxy-audio?url=${encodeURIComponent(song.url)}`; // Set the audio source for the selected song
    let nowPlaying = document.getElementById("nowPlaying");
    let coverImg = document.getElementById("coverImg");
    let playerNowPlaying = document.getElementById("playerNowPlaying");
    let playerCoverImg = document.getElementById("playerCoverImg");
    let albumSection = document.getElementById("albumSection");

    if (nowPlaying) {
        nowPlaying.textContent = `Selected: ${song.title}`;
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
    if (albumSection) {
        albumSection.style.backgroundImage = `url('${song.image}')`;
    }
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
    audioPlayer.src = isMobileDevice()
        ? song.url : `/api/proxy-audio?url=${encodeURIComponent(song.url)}`;

    document.getElementById("nowPlaying").textContent = `Now Playing: ${song.title}`;
    document.getElementById("coverImg").src = song.image;
    document.getElementById("playerNowPlaying").innerHTML = `
        <div class="title-artist">
            <span class="title">${song.title}</span>
            <span class="artist">${song.artist}</span>
        </div>`;
    document.getElementById("playerCoverImg").src = song.image;
    document.getElementById("albumSection").style.backgroundImage = `url('${song.image}')`;

    coverImg.classList.add("spin");
    audioPlayer.play();
    if (!isMobileDevice()) startVisualizer();
    playPauseBtn.textContent = "Pause";

    // ✅ Re-render the current page only
    renderList(song.id);
}

function togglePlay() {
    if (audioPlayer.src) {
        if (audioPlayer.paused) {
            coverImg.classList.add("spin");
            audioPlayer.play();
            playPauseBtn.textContent = "Pause";
        } else {
            coverImg.classList.remove("spin");
            audioPlayer.pause();
            playPauseBtn.textContent = "Play";
        }
        if (!isMobileDevice()) startVisualizer();
    }
}

function prevSong() {
    const source = musicData || [];
    if (!source.length) return;
    currentSongIndex = (currentSongIndex - 1 + source.length) % source.length;
    playSong(currentSongIndex);
}

function nextSong() {
    const source = musicData || [];
    if (!source.length) return;
    currentSongIndex = (currentSongIndex + 1) % source.length;
    playSong(currentSongIndex);
}

async function playNextSongOrNextPage() {
    const source = musicData || [];
    if (!source.length) return;

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
        alert("No song is currently loaded.");
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
        alert("No song is currently loaded.");
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
        alert("Failed to copy the link.");
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

document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement && !document.body.classList.contains("music-mobile-fullscreen")) {
        document.getElementById("albumSection").classList.remove("fullscreen");
        document.getElementById("fullscreenBtn").textContent = "⛶";
    }
});

function toggleFullscreen() {
    const albumSection = document.getElementById("albumSection");
    const fullscreenBtn = document.getElementById("fullscreenBtn");

    if (isMobileDevice()) {
        const body = document.body;
        const entering = !body.classList.contains("music-mobile-fullscreen");

        body.classList.toggle("music-mobile-fullscreen", entering);
        albumSection.classList.toggle("fullscreen-mobile", entering);
        fullscreenBtn.textContent = entering ? "⮌" : "⛶";

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
        showTripleLoading?.();
        await loadAndRenderMusicPage();
        hideTripleLoading?.();
    }
}

async function nextPage() {
    if (currentPage < totalPagesCount) {
        currentPage++;
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
                    <span>${track.title}</span>
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
        progress.style.width = progressPercent + "%";
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
    localStorage.setItem("autoplay", autoplayEnabled);
}

audioPlayer.addEventListener("timeupdate", updateProgress);
audioPlayer.addEventListener("loadedmetadata", updateDuration);
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
const autoplayBtn = document.getElementById("autoplayBtn");
if (autoplayBtn) {
    autoplayBtn.textContent = autoplayEnabled ? "♬" : "⏹️";
    autoplayBtn.title = `Autoplay: ${autoplayEnabled ? "On" : "Off"}`;
}

async function handleSearch(query) {
    if (!musicDataLoaded) return;
    query = query.trim().toLowerCase();

    activeSearchQuery = query;
    filteredResults = null; // server-side filtering now
    currentPage = 1;
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
    if (!audioPlayer) return;

    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256; // Adjust smoothness/detail
        bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        source = audioContext.createMediaElementSource(audioPlayer);
        source.connect(analyser);
        analyser.connect(audioContext.destination);
    }

    resizeCanvas();
    drawVisualizer();
}

function resizeCanvas() {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
}

window.addEventListener("resize", resizeCanvas);

function drawVisualizer() {
    if (!visualizerRunning || !analyser) return; // stop cleanly

    requestAnimationFrame(drawVisualizer);
    analyser.getByteFrequencyData(dataArray);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 2.5;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] * 0.6;
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
        gradient.addColorStop(0, "#00b4ff");
        gradient.addColorStop(0.5, "#009dff");
        gradient.addColorStop(1, "#80eaff");
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
    }
}

function startVisualizer() {
    if (!audioPlayer) return;

    // 🔒 Initialize audio context and analyser only once
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        source = audioContext.createMediaElementSource(audioPlayer);
        source.connect(analyser);
        analyser.connect(audioContext.destination);
    }

    // ✅ Resume context if paused (required on Chrome mobile sometimes)
    if (audioContext.state === "suspended") {
        audioContext.resume();
    }

    // ✅ Only start drawing if not already running
    if (!visualizerRunning) {
        visualizerRunning = true;
        resizeCanvas();
        drawVisualizer();
    }
}

function stopVisualizer() {
    // 🚫 Do NOT touch audio context or source, only pause animation
    visualizerRunning = false;
}
