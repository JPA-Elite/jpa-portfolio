let currentPage = 1;
let currentAudio = null;
let currentButton = null;
let perPage = 10;

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

function togglePreview(projectId, projectUrl) {
    const audioEl = document.getElementById(`audio_${projectId}`);
    const buttonEl = document.getElementById(`previewBtn_${projectId}`);

    if (currentAudio && currentAudio !== audioEl) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio.style.display = "none";

        if (currentButton) {
            currentButton.innerHTML = `<i class="bi bi-project-note-beamed"></i> Preview`;
            currentButton.classList.remove("btn-danger");
            currentButton.classList.add("btn-outline-primary");
        }
    }

    if (!audioEl.src) {
        audioEl.src = projectUrl;
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

        buttonEl.innerHTML = `<i class="bi bi-project-note-beamed"></i> Preview`;
        buttonEl.classList.remove("btn-danger");
        buttonEl.classList.add("btn-outline-primary");

        currentAudio = null;
        currentButton = null;
    }
}

async function loadProject(page = 1) {
    const tbody = document.getElementById("projectTableBody");
    const modalContainer = document.getElementById("projectModals");
    const pageInfo = document.getElementById("pageInfo");

    // ✅ Show loading row
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const response = await fetch(
            `/admin/api/music-list?page=${page}&per_page=${perPage}&order=desc`
        );
        const data = await response.json();

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.music || data.music.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No project found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.music.forEach((project, index) => {
            const modalIdEdit = `editModal${page}_${index}`;
            const modalIdDelete = `deleteModal${page}_${index}`;

            // ✅ Add table row
            tbody.innerHTML += `
        <tr>
            <td>${(page - 1) * perPage + (index + 1)}</td>
            <td>${project.title}</td>
            <td>${project.artist}</td>
            <td>
                <button
                id="previewBtn_${project._id}"
                class="btn btn-sm btn-outline-primary"
                onclick="togglePreview('${project._id}', '${project.url}')">
                <i class="bi bi-project-note-beamed"></i> Preview
                </button>
                <audio id="audio_${
                project._id
                }" style="display:none; width:100%; margin-top:5px;"></audio>
            </td>
            <td>
                <img src="${project.image}" onclick="window.location.href='${project.image}'" alt="${
                project.title}" style="width: 60px; height: auto; border-radius:4px;">
            </td>
            <td>
                <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${modalIdEdit}">
                <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#${modalIdDelete}">
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
                    <h5 class="modal-title" id="${modalIdEdit}Label">Edit Project</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="editForm${page}_${index}">
                    <div class="mb-3">
                        <label for="editTitle${page}_${index}" class="form-label">Title <span class="text-danger">*</label>
                        <input type="text" class="form-control" id="editTitle${page}_${index}" value="${project.title}">
                    </div>
                    <div class="mb-3">
                        <label for="editArtist${page}_${index}" class="form-label">Artist <span class="text-danger">*</label>
                        <input type="text" class="form-control" id="editArtist${page}_${index}" value="${project.artist}">
                    </div>
                    <div class="mb-3">
                    <label class="form-label">Project File (leave blank to keep current)</label>
                    <input type="file" class="form-control" id="editProjectFile${page}_${index}" accept="audio/*">
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
                    id="editProjectBtn_${project._id}"
                    data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
                    onclick="updateProject('${project._id}', 'editForm${page}_${index}')">Save changes</button>
                </div>
                </div>
            </div>
            </div>
            `;

            // ✅ Add Delete modal
            modalContainer.innerHTML += `
            <div class="modal fade" id="${modalIdDelete}" tabindex="-1" aria-labelledby="${modalIdDelete}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${modalIdDelete}Label">Delete Project</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    Are you sure you want to delete <strong>${project.title}</strong> by <em>${project.artist}</em>?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="deleteProject('${project._id}', '${modalIdDelete}')">Delete</button>
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
            }, 0);
        });

        // ✅ Update page info
        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;
    } catch (error) {
        console.error("Error fetching project list:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

async function addProject() {
    const btn = document.getElementById("addProjectBtn");
    setButtonLoading(btn, true);

    const title = document.getElementById("addTitle").value.trim();
    const artist = document.getElementById("addArtist").value.trim();
    const projectFile = document.getElementById("addProjectFile").files[0];
    const imageFileDesktop = document.getElementById("addImageFile").files[0];
    const imageFileMobile =
        document.getElementById("addImageFileMobile").files[0];
    const imageFile = imageFileDesktop || imageFileMobile;

    // ✅ Required field checks
    if (!title || !artist || !projectFile || !imageFile) {
        alert("All fields are required.");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ File type validation
    if (!projectFile.type.startsWith("audio/")) {
        alert("Please upload a valid project file.");
        setButtonLoading(btn, false);
        return;
    }
    if (!imageFile.type.startsWith("image/")) {
        alert("Please upload a valid image file.");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("artist", artist);
    formData.append("project_file", projectFile);
    formData.append("image_file", imageFile);

    try {
        const res = await fetch("/admin/api/add-music", {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById("addProjectModal")
            ).hide();
            const data = await res.json();
            loadProject(currentPage);
            alert(data.message);
        } else {
            alert("Failed to add project.");
        }
    } catch (err) {
        console.error(err);
        alert("Error adding project.");
    } finally {
        setButtonLoading(btn, false);
    }
}

async function updateProject(projectId, formId) {
    const btn = document.getElementById(`editProjectBtn_${projectId}`);
    setButtonLoading(btn, true);

    const form = document.getElementById(formId);
    const title = form
        .querySelector(`#${formId} input[id^='editTitle']`)
        .value.trim();
    const artist = form
        .querySelector(`#${formId} input[id^='editArtist']`)
        .value.trim();
    const projectFile = form.querySelector(`#${formId} input[id^='editProjectFile']`)
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
        alert("Title and Artist are required.");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ File type validation (only if provided)
    if (projectFile && !projectFile.type.startsWith("audio/")) {
        alert("Please upload a valid project file.");
        setButtonLoading(btn, false);
        return;
    }
    if (imageFile && !imageFile.type.startsWith("image/")) {
        alert("Please upload a valid image file.");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("artist", artist);
    if (projectFile) formData.append("project_file", projectFile);
    if (imageFile) formData.append("image_file", imageFile);

    try {
        const res = await fetch(`/admin/api/update-music/${projectId}`, {
            method: "PUT",
            body: formData,
        });

        if (res.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById(form.closest(".modal").id)
            ).hide();

            const data = await res.json();
            loadProject(currentPage);
            alert(data.message);
        } else {
            alert("Failed to update project.");
        }
    } catch (err) {
        console.error(err);
        alert("Error updating project.");
    } finally {
        // 🔹 Restore button
        setButtonLoading(btn, false);
    }
}

async function deleteProject(projectId, modalId) {
    const res = await fetch(`/admin/api/delete-music/${projectId}`, {
        method: "DELETE",
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById(modalId)).hide();
        const data = await res.json();
        loadProject(currentPage);
        alert(data.message);
    } else {
        alert("Failed to delete project.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadProject(currentPage);
    initDropZone("addDropZone", "addImageFile");

    const addProjectModal = document.getElementById("addProjectModal");
    addProjectModal.addEventListener("show.bs.modal", () => {
        document.getElementById("addProjectForm").reset();

        // reset dropzone text
        const addDropZone = document.getElementById("addDropZone");
        if (addDropZone) {
            const p = addDropZone.querySelector("p");
            if (p) p.textContent = "Drag & Drop image here, or click to select";
        }
    });

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadProject(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        currentPage++;
        loadProject(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", (e) => {
        perPage = parseInt(e.target.value);
        currentPage = 1; // reset to first page when perPage changes
        loadProject(currentPage);
    });
});