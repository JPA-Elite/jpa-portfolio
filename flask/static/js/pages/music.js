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

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.documentElement;
    root.setAttribute("data-theme", "dark");
    try {
        const response = await fetch("/admin/api/music-list?per_page=999999");
        const result = await response.json();

        musicData = result?.music || [];
        if (musicData.length > 0) {
            selectFirstSong(); // Select the first song in the list
        }

        renderList(); // Render the music list
    } catch (err) {
        console.error("Failed to load music data:", err);
    }
});

function selectFirstSong() {
    currentSongIndex = Math.floor(Math.random() * musicData.length); // Randomly select an index
    const song = musicData[currentSongIndex];
    audioPlayer.src = song.url; // Set the audio source for the selected song
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

// Global functions
function playSong(index) {
    currentSongIndex = index;
    const song = musicData[index];
    audioPlayer.src = song.url;
    document.getElementById(
        "nowPlaying"
    ).textContent = `Now Playing: ${song.title}`;
    document.getElementById("coverImg").src = song.image;
    document.getElementById("playerNowPlaying").innerHTML = `
                <div class="title-artist">
                    <span class="title">${song.title}</span>
                    <span class="artist">${song.artist}</span>
                </div>
            `;
    document.getElementById("playerCoverImg").src = song.image;

    const albumSection = document.getElementById("albumSection");
    albumSection.style.backgroundImage = `url('${song.image}')`;

    coverImg.classList.add("spin");
    audioPlayer.play();
    playPauseBtn.textContent = "Pause";
    renderList(song.id); // Pass the active song id
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
    }
}

function prevSong() {
    currentSongIndex =
        (currentSongIndex - 1 + musicData.length) % musicData.length;
    playSong(currentSongIndex);
}

function nextSong() {
    currentSongIndex = (currentSongIndex + 1) % musicData.length;
    playSong(currentSongIndex);
}

function downloadSong() {
    const audio = document.getElementById("audioPlayer");
    const src = audio.getAttribute("src");
    if (!src) {
        alert("No song is currently loaded.");
        return;
    }
    window.open(`/api/download_song?url=${encodeURIComponent(src)}`, "_blank");
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

    return new Promise((resolve) => {
        const audio = new Audio(url);
        audio.addEventListener("loadedmetadata", () => {
            durationCache[url] = audio.duration;
            localStorage.setItem('audioDurationCache', JSON.stringify(durationCache));
            resolve(audio.duration);
        });

        audio.addEventListener("error", () => resolve(0));
    });
}

function updateVolume(value) {
    audioPlayer.volume = value / 100;
    document.getElementById("volumePercentage").textContent = `${value}%`;
}

function isMobileDevice() {
    return (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i).test(navigator.userAgent);
}

document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement) {
        document.getElementById("albumSection").classList.remove("fullscreen");
        document.getElementById("fullscreenBtn").textContent = "⛶";
    }
});

function toggleFullscreen() {
    const albumSection = document.getElementById("albumSection");
    const fullscreenBtn = document.getElementById("fullscreenBtn");

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

function updatePagination() {
    const totalPages = Math.ceil(musicData.length / itemsPerPage);
    document.getElementById(
        "pageInfo"
    ).textContent = `Page ${currentPage} of ${totalPages}`;
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        renderList();
        updatePagination();
    }
}

function nextPage() {
    const totalPages = Math.ceil(musicData.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderList();
        updatePagination();
    }
}

// Get DOM elements
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

async function renderList(activeSongId = null) {
    musicList.innerHTML = ""; // Clear the list before rendering
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = musicData.slice(start, end);

    for (const track of pageItems) {
        const div = document.createElement("div");
        div.className = "music-item" + (track.id === activeSongId ? " active" : "");

        // Get duration if not already cached
        if (!track.duration) {
            track.duration = await getDuration(track.url);
        }

        div.innerHTML = `
                        <div class="left-content">
                            <img src="${track.image}" alt="${track.title}" />
                            <div class="title-artist">
                                <span>${track.title}</span>
                                <span class="artist">${track.artist}</span>
                            </div>
                        </div>
                        <div class="share-section">
                            <span class="duration">${formatTime(
            track.duration
        )}</span>
                            <button class="copy-btn"><ion-icon name="copy-outline"></ion-icon></button>
                        </div>
                    `;
        div.addEventListener("click", () => playSong(musicData.indexOf(track)));
        const copyBtn = div.querySelector(".copy-btn");
        copyBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            copyLink(track.url);
        });
        musicList.appendChild(div);
    }

    updatePagination();
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
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60)
        .toString()
        .padStart(2, "0");
    return `${minutes}:${secs}`;
}

function seek(event) {
    const rect = progressBar.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const width = rect.width;
    const seekTime = (offsetX / width) * audioPlayer.duration;
    audioPlayer.currentTime = seekTime;
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
progressBar.addEventListener("click", seek);
progressBar.addEventListener("mousedown", (event) => {
    isDragging = true;
    seek(event);
});

document.addEventListener("mousemove", (event) => {
    if (isDragging) {
        seek(event);
    }
});

document.addEventListener("mouseup", () => {
    isDragging = false;
});

audioPlayer.addEventListener("ended", () => {
    coverImg.classList.remove("spin");
    if (autoplayEnabled) {
        nextSong();
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

renderList(); // Render the music list
