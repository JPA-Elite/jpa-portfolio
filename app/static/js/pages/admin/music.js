import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminMusicService = new AdminCrudService("music");

let currentPage = 1;
let currentAudio = null;
let currentButton = null;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let searchDebounceTimer = null;

function escapeHtml(value = "") {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function setButtonLoading(button, isLoading) {
    if (!button) return;

    if (isLoading) {
        button.dataset.originalText = button.innerHTML; // Save original
        button.innerHTML = button.dataset.loadingText || "Loading...";
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || "Save";
        button.disabled = false;
    }
}

function initDropZone(dropZoneId, inputId) {
    const dropZone = document.getElementById(dropZoneId);
    const inputEl = document.getElementById(inputId);

    if (!dropZone || !inputEl) return;

    dropZone.addEventListener("click", () => inputEl.click());

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation(); // ✅ stop modal/backdrop from stealing event
            dropZone.classList.add("dragover");
        });
    });

    dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");

        if (e.dataTransfer.files.length > 0) {
            inputEl.files = e.dataTransfer.files;
            dropZone.querySelector("p").textContent = e.dataTransfer.files[0].name;
        }
    });

    inputEl.addEventListener("change", () => {
        if (inputEl.files.length > 0) {
            dropZone.querySelector("p").textContent = inputEl.files[0].name;
        }
    });
}

function togglePreview(musicId, musicUrl) {
    const audioEl = document.getElementById(`audio_${musicId}`);
    const buttonEl = document.getElementById(`previewBtn_${musicId}`);

    if (currentAudio && currentAudio !== audioEl) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio.style.display = "none";

        if (currentButton) {
            currentButton.innerHTML = `<i class="bi bi-music-note-beamed"></i> Play`;
            currentButton.classList.remove("btn-danger");
            currentButton.classList.add("btn-outline-primary");
        }
    }

    if (!audioEl.src) {
        audioEl.src = musicUrl;
    }

    if (audioEl.paused) {
        audioEl.style.display = "block";
        audioEl.play();

        buttonEl.innerHTML = `<i class="bi bi-stop-circle"></i> Stop`;
        buttonEl.classList.remove("btn-outline-primary");
        buttonEl.classList.add("btn-danger");

        currentAudio = audioEl;
        currentButton = buttonEl;
    } else {
        audioEl.pause();
        audioEl.currentTime = 0;
        audioEl.style.display = "none";

        buttonEl.innerHTML = `<i class="bi bi-music-note-beamed"></i> Play`;
        buttonEl.classList.remove("btn-danger");
        buttonEl.classList.add("btn-outline-primary");

        currentAudio = null;
        currentButton = null;
    }
}

async function loadMusic(page = 1) {
    const tbody = document.getElementById("musicTableBody");
    const modalContainer = document.getElementById("musicModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="7" class="text-center">Loading...</td></tr>`;

    try {
        const data = await adminMusicService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
        });

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.music || data.music.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">No music found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.music.forEach((music, index) => {
            const modalIdEdit = `editModal${page}_${index}`;
            const safeTitle = escapeHtml(music.title || "");
            const safeArtist = escapeHtml(music.artist || "");
            const safeLyrics = escapeHtml(music.lyrics || "");

            // ✅ Add table row
            tbody.innerHTML += `
        <tr>
            <td>${(page - 1) * perPage + (index + 1)}</td>
            <td>${safeTitle}</td>
            <td>${safeArtist}</td>
            <td>${music.category || "All"}</td>
            <td>
                <button
                id="previewBtn_${music._id}"
                class="btn btn-sm btn-outline-primary"
                onclick="togglePreview('${music._id}', '${music.url}')">
                <i class="bi bi-music-note-beamed"></i> Play
                </button>
                <audio id="audio_${music._id
                }" style="display:none; width:100%; margin-top:5px;"></audio>
            </td>
            <td>
                <img src="${music.image}" onclick="playMusicPreview('${music.image}')" alt="${safeTitle}" style="cursor: pointer; width: 60px; height: auto; border-radius:4px;">
            </td>
            <td>
                <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${modalIdEdit}">
                <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger music-delete-btn" data-record-id="${music._id}" data-title="${safeTitle}" data-artist="${safeArtist}">
                <i class="bi bi-trash"></i> Delete
                </button>
            </td>
            </tr>
            `;

            // ✅ Add Edit modal
            modalContainer.innerHTML += `
            <div class="modal fade" id="${modalIdEdit}" tabindex="-1" aria-labelledby="${modalIdEdit}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title me-auto" id="${modalIdEdit}Label">Edit Music</h5>
                    <div class="d-flex align-items-center gap-1">
                        <button type="button" class="btn p-1 preview-header-btn edit-maximize-btn" data-target-modal="${modalIdEdit}" aria-label="Maximize" title="Maximize">
                            <i class="bi bi-arrows-fullscreen"></i>
                        </button>
                        <button type="button" class="btn p-1 preview-header-btn" data-bs-dismiss="modal" aria-label="Close">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                </div>
                <div class="modal-body">
                    <form id="editForm${page}_${index}">
                    <div class="mb-3">
                        <label for="editTitle${page}_${index}" class="form-label">Title <span class="text-danger">*</label>
                        <input type="text" class="form-control" id="editTitle${page}_${index}" value="${safeTitle}">
                    </div>
                    <div class="mb-3">
                        <label for="editArtist${page}_${index}" class="form-label">Artist <span class="text-danger">*</label>
                        <input type="text" class="form-control" id="editArtist${page}_${index}" value="${safeArtist}">
                    </div>
                    <div class="mb-3">
                        <label for="editCategory${page}_${index}" class="form-label">Category</label>
                        <select class="form-select" id="editCategory${page}_${index}">
                            <option value="All" ${music.category === "All" ? "selected" : ""}>All</option>
                            <option value="Rap" ${music.category === "Rap" ? "selected" : ""}>Rap</option>
                            <option value="Love Song" ${music.category === "Love Song" ? "selected" : ""}>Love Song</option>
                            <option value="Pop" ${music.category === "Pop" ? "selected" : ""}>Pop</option>
                            <option value="R&B" ${music.category === "R&B" ? "selected" : ""}>R&B</option>
                            <option value="Rock" ${music.category === "Rock" ? "selected" : ""}>Rock</option>
                            <option value="Chill" ${music.category === "Chill" ? "selected" : ""}>Chill</option>
                            <option value="Party" ${music.category === "Party" ? "selected" : ""}>Party</option>
                            <option value="Workout" ${music.category === "Workout" ? "selected" : ""}>Workout</option>
                            <option value="Mood" ${music.category === "Mood" ? "selected" : ""}>Mood</option>
                            <option value="Focus" ${music.category === "Focus" ? "selected" : ""}>Focus</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="editLyrics${page}_${index}" class="form-label d-flex justify-content-between align-items-center gap-2">
                            <span>Lyrics <small class="text-muted fw-normal">(supports LRC timestamps)</small></span>
                            <button type="button" class="btn btn-sm btn-outline-secondary" id="lyricsSyncToggle_${page}_${index}" onclick="toggleLyricsSync('${page}_${index}')">
                                <i class="bi bi-stopwatch"></i> Sync timestamps
                            </button>
                        </label>
                        <textarea class="form-control" id="editLyrics${page}_${index}" rows="6"
                            placeholder="Enter song lyrics or LRC, e.g. [00:12.00] Line one">${safeLyrics}</textarea>
                        <div class="lyrics-sync-toolbar d-none mt-2" id="lyricsSyncToolbar_${page}_${index}">
                            <div class="d-flex flex-wrap align-items-center gap-2">
                                <button type="button" class="btn btn-sm btn-outline-primary" id="lyricsSyncPreview_${page}_${index}" onclick="toggleSyncPreview('${page}_${index}')">
                                    <i class="bi bi-play-circle"></i> Preview
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="stampNextEditorLine('${page}_${index}')">
                                    <i class="bi bi-bookmark"></i> Stamp next
                                </button>
                                <span class="text-muted small">Play the song, then click a line's clock to stamp the current time.</span>
                            </div>
                            <audio id="lyricsSyncAudio_${page}_${index}" data-music-url="${music.url}" style="display:none; width:100%; margin-top:6px;"></audio>
                        </div>
                        <div class="lyrics-sync-editor d-none mt-2" id="lyricsEditor_${page}_${index}"></div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Music Source</label>
                        <div class="form-check form-switch mb-2">
                            <input class="form-check-input" type="checkbox" role="switch" id="editMusicSourceToggle${page}_${index}">
                            <label class="form-check-label" for="editMusicSourceToggle${page}_${index}" id="editMusicSourceLabel${page}_${index}">Upload MP3 File</label>
                        </div>
                    </div>
                    <div class="mb-3" id="editMusicFileGroup${page}_${index}">
                        <label class="form-label">Music File (leave blank to keep current)</label>
                        <input type="file" class="form-control" id="editMusicFile${page}_${index}" accept="audio/*">
                    </div>
                    <div class="mb-3 d-none" id="editMusicUrlGroup${page}_${index}">
                        <label class="form-label">Music URL (leave blank to keep current)</label>
                        <input type="url" class="form-control" id="editMusicUrl${page}_${index}" placeholder="https://example.com/song.mp3 or YouTube/SoundCloud link">
                        <div class="form-text">Paste a direct audio URL or a YouTube/SoundCloud link. yt-dlp will convert it to MP3.</div>
                    </div>
                    <!-- Desktop (Drag & Drop) -->
                    <div class="mb-3 d-none d-md-block">
                    <label class="form-label">Image File (leave blank to keep current)</label>
                    <div id="editDropZone${page}_${index}" class="dropzone">
                        <p>Drag & Drop image here, or click to select</p>
                        <input type="file" id="editImageFile${page}_${index}" accept="image/*" hidden>
                    </div>
                    </div>

                    <!-- Mobile (Normal Input) -->
                    <div class="mb-3 d-md-none">
                    <label class="form-label">Image File (leave blank to keep current)</label>
                    <input type="file" class="form-control" id="editImageFileMobile${page}_${index}" accept="image/*">
                    </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button
                    type="button"
                    class="btn btn-primary"
                    id="editMusicBtn_${music._id}"
                    data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
                    onclick="updateMusic('${music._id}', 'editForm${page}_${index}')">Save changes</button>
                </div>
                </div>
            </div>
            </div>
            `;

            setTimeout(() => {
                initDropZone(
                    `editDropZone${page}_${index}`,
                    `editImageFile${page}_${index}`
                );
                initMusicSourceToggle(
                    `editMusicSourceToggle${page}_${index}`,
                    `editMusicFileGroup${page}_${index}`,
                    `editMusicUrlGroup${page}_${index}`,
                    `editMusicSourceLabel${page}_${index}`
                );
            }, 0);
        });

        // ✅ Update page info
        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;

        // Attach delete handlers via delegation
        tbody.querySelectorAll(".music-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                const title = this.dataset.title;
                const artist = this.dataset.artist;
                window.confirmDelete(
                    `Are you sure you want to delete <strong>${title}</strong> by <em>${artist}</em>?`,
                    async () => {
                        const result = await adminMusicService.remove(recordId);
                        if (result.ok) {
                            bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                            window.notify(result.data?.message || "Music deleted.", "success");
                            loadMusic(currentPage);
                        } else {
                            window.notify("Failed to delete music.", "error");
                        }
                    }
                );
            });
        });
    } catch (error) {
        console.error("Error fetching music list:", error);
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

function playMusicPreview(url) {
    if (typeof window.openAdminImagePreview !== "function") {
        console.error("openAdminImagePreview is not available.");
        return;
    }
    window.openAdminImagePreview(url, "Music Image");
}

const LRC_TIME_RE = /\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]/g;

function formatLrcTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) seconds = 0;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const centis = Math.floor((seconds - Math.floor(seconds)) * 100);
    return `[${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${String(centis).padStart(2, "0")}]`;
}

function parseLrc(raw) {
    if (typeof raw !== "string" || !raw.trim()) return { isLrc: false, lines: [] };
    if (!/\[\d{1,2}:\d{1,2}/.test(raw)) return { isLrc: false, lines: [] };

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
        for (const time of times) lines.push({ time, text });
    }
    lines.sort((a, b) => a.time - b.time);
    return { isLrc: true, lines };
}

function buildEditorLinesFromLyrics(raw) {
    const parsed = parseLrc(raw);
    if (parsed.isLrc) {
        return parsed.lines.map((line) => ({ time: line.time, text: line.text }));
    }
    return String(raw)
        .replace(/\r\n/g, "\n")
        .replace(/\r/g, "\n")
        .split("\n")
        .map((text) => ({ time: null, text }));
}

function getSyncAudio(prefix) {
    return document.getElementById(`lyricsSyncAudio_${prefix}`);
}

function getMusicUrl(prefix) {
    const audioEl = getSyncAudio(prefix);
    return audioEl?.dataset.musicUrl || "";
}

let lyricsSyncState = null;

function renderLyricsEditor(prefix) {
    const state = lyricsSyncState;
    const container = document.getElementById(`lyricsEditor_${prefix}`);
    if (!state || !container) return;

    container.innerHTML = "";

    state.lines.forEach((line, index) => {
        const row = document.createElement("div");
        row.className = "lyrics-sync-row";

        const timeBtn = document.createElement("button");
        timeBtn.type = "button";
        timeBtn.className = "lyrics-sync-time";
        timeBtn.textContent =
            line.time != null ? formatLrcTime(line.time).replace(/[\[\]]/g, "") : "--:--.--";
        timeBtn.title = "Stamp current playback time";
        timeBtn.addEventListener("click", () => stampEditorLine(prefix, index));

        const textEl = document.createElement("div");
        textEl.className = "lyrics-sync-text";
        textEl.contentEditable = "true";
        textEl.spellcheck = false;
        textEl.textContent = line.text;
        textEl.addEventListener("input", () => {
            state.lines[index].text = textEl.textContent;
        });

        row.appendChild(timeBtn);
        row.appendChild(textEl);
        container.appendChild(row);
    });
}

function stampEditorLine(prefix, index) {
    const state = lyricsSyncState;
    const audioEl = getSyncAudio(prefix);
    if (!state || !state.lines[index] || !audioEl) return;
    state.lines[index].time = audioEl.currentTime || 0;
    renderLyricsEditor(prefix);
}

function stampNextEditorLine(prefix) {
    const state = lyricsSyncState;
    if (!state) return;
    const target = state.lines.findIndex((line) => line.time == null);
    if (target === -1) {
        window.notify?.("All lines already have a timestamp.", "info");
        return;
    }
    stampEditorLine(prefix, target);
    const rows = document.getElementById(`lyricsEditor_${prefix}`)?.querySelectorAll(".lyrics-sync-row");
    if (rows && rows[target]) {
        rows[target].scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function toggleLyricsSync(prefix) {
    const textarea = document.getElementById(`editLyrics${prefix}`);
    const editor = document.getElementById(`lyricsEditor_${prefix}`);
    const toolbar = document.getElementById(`lyricsSyncToolbar_${prefix}`);
    const toggleBtn = document.getElementById(`lyricsSyncToggle_${prefix}`);
    if (!textarea || !editor || !toolbar || !toggleBtn) return;

    if (!lyricsSyncState || lyricsSyncState.prefix !== prefix) {
        const audioEl = getSyncAudio(prefix);
        if (audioEl && !audioEl.src) audioEl.src = getMusicUrl(prefix);

        lyricsSyncState = {
            prefix,
            lines: buildEditorLinesFromLyrics(textarea.value),
            audioEl,
        };

        editor.classList.remove("d-none");
        toolbar.classList.remove("d-none");
        textarea.classList.add("d-none");
        toggleBtn.classList.add("active");
        renderLyricsEditor(prefix);
    } else {
        const lrc = lyricsSyncState.lines
            .map((line) => `${line.time != null ? formatLrcTime(line.time) : ""}${line.text}`)
            .join("\n");
        textarea.value = lrc;

        editor.classList.add("d-none");
        toolbar.classList.add("d-none");
        textarea.classList.remove("d-none");
        toggleBtn.classList.remove("active");
        lyricsSyncState = null;
    }
}

function toggleSyncPreview(prefix) {
    const audioEl = getSyncAudio(prefix);
    const btn = document.getElementById(`lyricsSyncPreview_${prefix}`);
    if (!audioEl || !btn) return;
    if (!audioEl.src) audioEl.src = getMusicUrl(prefix);

    if (audioEl.paused) {
        audioEl.play();
        btn.innerHTML = '<i class="bi bi-stop-circle"></i> Stop';
    } else {
        audioEl.pause();
        audioEl.currentTime = 0;
        btn.innerHTML = '<i class="bi bi-play-circle"></i> Preview';
    }
}

async function addMusic() {
    const btn = document.getElementById("addMusicBtn");
    setButtonLoading(btn, true);

    const title = document.getElementById("addTitle").value.trim();
    const artist = document.getElementById("addArtist").value.trim();
    const category = document.getElementById("addCategory").value;
    const lyrics = document.getElementById("addLyrics").value;
    const isUrlMode = document.getElementById("addMusicSourceToggle").checked;
    const musicUrl = document.getElementById("addMusicUrl").value.trim();
    const musicFile = document.getElementById("addMusicFile").files[0];
    const imageFileDesktop = document.getElementById("addImageFile").files[0];
    const imageFileMobile =
        document.getElementById("addImageFileMobile").files[0];
    const imageFile = imageFileDesktop || imageFileMobile;

    // ✅ Required field checks
    if (!title || !artist || !imageFile) {
        window.notify("All fields are required.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    if (isUrlMode) {
        if (!musicUrl) {
            window.notify("Please enter a music URL.", "warning");
            setButtonLoading(btn, false);
            return;
        }
    } else {
        if (!musicFile) {
            window.notify("Please select a music file.", "warning");
            setButtonLoading(btn, false);
            return;
        }
        if (!musicFile.type.startsWith("audio/")) {
            window.notify("Please upload a valid music file.", "warning");
            setButtonLoading(btn, false);
            return;
        }
    }

    if (!imageFile.type.startsWith("image/")) {
        window.notify("Please upload a valid image file.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("artist", artist);
    formData.append("category", category);
    formData.append("lyrics", lyrics);
    formData.append("music_source_type", isUrlMode ? "url" : "file");
    if (isUrlMode) {
        formData.append("music_url_input", musicUrl);
    } else {
        formData.append("music_file", musicFile);
    }
    formData.append("image_file", imageFile);

    try {
        const result = await adminMusicService.add(formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById("addMusicModal")
            ).hide();
            loadMusic(currentPage);
            window.notify(result.data?.message || "Music added.", "success");
        } else {
            window.notify("Failed to add music.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error adding music.", "error");
    } finally {
        setButtonLoading(btn, false);
    }
}

function initMusicSourceToggle(toggleId, fileGroupId, urlGroupId, labelId) {
    const toggle = document.getElementById(toggleId);
    if (!toggle) return;
    toggle.addEventListener("change", function () {
        const isUrl = this.checked;
        document.getElementById(fileGroupId)?.classList.toggle("d-none", isUrl);
        document.getElementById(urlGroupId)?.classList.toggle("d-none", !isUrl);
        const label = document.getElementById(labelId);
        if (label) label.textContent = isUrl ? "From URL (convert to MP3)" : "Upload MP3 File";
    });
}

async function updateMusic(musicId, formId) {
    const btn = document.getElementById(`editMusicBtn_${musicId}`);
    setButtonLoading(btn, true);

    const form = document.getElementById(formId);
    const prefix = formId.replace("editForm", "");

    // If the lyrics sync editor is still open, flush the generated LRC
    // into the textarea so the timestamps are saved to the database.
    if (lyricsSyncState && lyricsSyncState.prefix === prefix) {
        const textarea = document.getElementById(`editLyrics${prefix}`);
        if (textarea) {
            textarea.value = lyricsSyncState.lines
                .map((line) => `${line.time != null ? formatLrcTime(line.time) : ""}${line.text}`)
                .join("\n");
        }
        lyricsSyncState = null;
    }

    const title = form
        .querySelector(`#${formId} input[id^='editTitle']`)
        .value.trim();
    const artist = form
        .querySelector(`#${formId} input[id^='editArtist']`)
        .value.trim();
    const category = form
        .querySelector(`#${formId} select[id^='editCategory']`)
        .value;
    const lyrics = form
        .querySelector(`#${formId} textarea[id^='editLyrics']`)
        .value;

    const toggle = document.getElementById(`editMusicSourceToggle${prefix}`);
    const isUrlMode = toggle ? toggle.checked : false;
    const musicUrl = form.querySelector(`#editMusicUrl${prefix}`)?.value.trim();
    const musicFile = form.querySelector(`#${formId} input[id^='editMusicFile']`)
        .files[0];
    const imageFileDesktop = form.querySelector(
        `#${formId} input[id^='editImageFile']`
    ).files[0];
    const imageFileMobile = form.querySelector(
        `#${formId} input[id^='editImageFileMobile']`
    ).files[0];
    const imageFile = imageFileDesktop || imageFileMobile;

    // ✅ Required checks
    if (!title || !artist) {
        window.notify("Title and Artist are required.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ File type validation (only if provided)
    if (!isUrlMode && musicFile && !musicFile.type.startsWith("audio/")) {
        window.notify("Please upload a valid music file.", "warning");
        setButtonLoading(btn, false);
        return;
    }
    if (imageFile && !imageFile.type.startsWith("image/")) {
        window.notify("Please upload a valid image file.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("artist", artist);
    formData.append("category", category);
    formData.append("lyrics", lyrics);
    formData.append("music_source_type", isUrlMode ? "url" : "file");
    if (isUrlMode) {
        if (musicUrl) formData.append("music_url_input", musicUrl);
    } else {
        if (musicFile) formData.append("music_file", musicFile);
    }
    if (imageFile) formData.append("image_file", imageFile);

    try {
        const result = await adminMusicService.update(musicId, formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById(form.closest(".modal").id)
            ).hide();

            loadMusic(currentPage);
            window.notify(result.data?.message || "Music updated.", "success");
        } else {
            window.notify("Failed to update music.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error updating music.", "error");
    } finally {
        // 🔹 Restore button
        setButtonLoading(btn, false);
    }
}

async function deleteMusic(musicId) {
    const result = await adminMusicService.remove(musicId);
    if (result.ok) {
        loadMusic(currentPage);
        window.notify(result.data?.message || "Music deleted.", "success");
    } else {
        window.notify("Failed to delete music.", "error");
    }
}

function toggleMusicModalMaximize(btn) {
    const modalId = btn.dataset.targetModal || btn.closest(".modal")?.id;
    if (!modalId) return;
    const dialog = document.querySelector("#" + modalId + " .modal-dialog");
    const modalBody = dialog?.querySelector(".modal-body");
    if (!dialog) return;
    dialog.classList.toggle("modal-fullscreen");
    const isFull = dialog.classList.contains("modal-fullscreen");

    // Adjust modal-body max-height for better fullscreen experience
    if (modalBody) {
        modalBody.style.maxHeight = isFull ? "calc(100vh - 120px)" : "";
    }

    btn.innerHTML = isFull
        ? '<i class="bi bi-fullscreen-exit"></i>'
        : '<i class="bi bi-arrows-fullscreen"></i>';
    btn.setAttribute("title", isFull ? "Restore" : "Maximize");
    btn.setAttribute("aria-label", isFull ? "Restore" : "Maximize");
}

document.addEventListener("DOMContentLoaded", () => {
    // Add Music maximize handler
    const addMaxBtn = document.getElementById("addMusicMaximizeBtn");
    if (addMaxBtn) {
        addMaxBtn.dataset.targetModal = "addMusicModal";
        addMaxBtn.addEventListener("click", function () {
            toggleMusicModalMaximize(this);
        });
    }

    // Delegated handler for edit maximize buttons (dynamically created)
    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".edit-maximize-btn");
        if (btn) {
            const modalId = btn.dataset.targetModal;
            if (modalId) {
                toggleMusicModalMaximize(btn);
            }
        }
    });
    loadMusic(currentPage);
    initDropZone("addDropZone", "addImageFile");
    initMusicSourceToggle("addMusicSourceToggle", "addMusicFileGroup", "addMusicUrlGroup", "addMusicSourceLabel");

    const addMusicModal = document.getElementById("addMusicModal");
    addMusicModal.addEventListener("show.bs.modal", () => {
        document.getElementById("addMusicForm").reset();

        // reset dropzone text
        const addDropZone = document.getElementById("addDropZone");
        if (addDropZone) {
            const p = addDropZone.querySelector("p");
            if (p) p.textContent = "Drag & Drop image here, or click to select";
        }
    });

    document.addEventListener("show.bs.modal", (e) => {
        const modal = e.target;
        if (!modal.id || !modal.id.startsWith("editModal")) return;

        const form = modal.querySelector("form");
        if (form) {
            form.reset();
            form.querySelectorAll('input[type="file"]').forEach((input) => {
                input.value = "";
            });
        }

        const dropZone = modal.querySelector(".dropzone p");
        if (dropZone) {
            dropZone.textContent = "Drag & Drop image here, or click to select";
        }

        const toggle = modal.querySelector('input[type="checkbox"][role="switch"]');
        if (toggle) {
            toggle.checked = false;
            const prefix = toggle.id.replace("editMusicSourceToggle", "");
            const fileGroup = document.getElementById(`editMusicFileGroup${prefix}`);
            const urlGroup = document.getElementById(`editMusicUrlGroup${prefix}`);
            const label = document.getElementById(`editMusicSourceLabel${prefix}`);
            if (fileGroup) fileGroup.classList.remove("d-none");
            if (urlGroup) urlGroup.classList.add("d-none");
            if (label) label.textContent = "Upload MP3 File";
        }
    });

    document.addEventListener("hide.bs.modal", (e) => {
        const modal = e.target;
        if (!modal.id || !modal.id.startsWith("editModal")) return;

        const syncAudio = modal.querySelector("audio[id^='lyricsSyncAudio_']");
        if (syncAudio) {
            syncAudio.pause();
            syncAudio.currentTime = 0;
        }

        const previewBtn = modal.querySelector("[id^='lyricsSyncPreview_']");
        if (previewBtn) {
            previewBtn.innerHTML = '<i class="bi bi-play-circle"></i> Preview';
        }

        const prefix = modal.id.replace("editModal", "");
        if (lyricsSyncState && lyricsSyncState.prefix === prefix) {
            lyricsSyncState = null;
        }

        const editor = modal.querySelector("[id^='lyricsEditor_']");
        const toolbar = modal.querySelector("[id^='lyricsSyncToolbar_']");
        const textarea = modal.querySelector("textarea[id^='editLyrics']");
        const syncToggle = modal.querySelector("[id^='lyricsSyncToggle_']");
        if (editor) editor.classList.add("d-none");
        if (toolbar) toolbar.classList.add("d-none");
        if (textarea) textarea.classList.remove("d-none");
        if (syncToggle) syncToggle.classList.remove("active");
    });

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadMusic(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        currentPage++;
        loadMusic(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", (e) => {
        perPage = parseInt(e.target.value);
        currentPage = 1; // reset to first page when perPage changes
        loadMusic(currentPage);
    });

    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadMusic(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadMusic(currentPage);
    });
});

window.addMusic = addMusic;
window.updateMusic = updateMusic;
window.deleteMusic = deleteMusic;
window.togglePreview = togglePreview;
window.playMusicPreview = playMusicPreview;
window.toggleLyricsSync = toggleLyricsSync;
window.toggleSyncPreview = toggleSyncPreview;
window.stampNextEditorLine = stampNextEditorLine;
window.stampEditorLine = stampEditorLine;
