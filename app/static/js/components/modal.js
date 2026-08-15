if (!window.__modal_js_loaded__) {
    window.__modal_js_loaded__ = true;
    const ModalType = {
        IMAGE: 'imageModal',
        BOX: 'boxModal'
    };
    let currentSlide = 0;
    const currentLocale = window.pageLocale || "en";
    const tm = (key, fallback, vars = {}) => {
        let text = (window.modalI18n || {})[key] || fallback;
        Object.entries(vars).forEach(([name, value]) => {
            const safe = String(value);
            text = text
                .replaceAll(`{${name}}`, safe)
                .replaceAll(`%(${name})s`, safe);
        });
        return text;
    };
    const baseUrl = window.baseUrl;
    const idType = window.idType;
    let slideData = [];
    let currentSelectedId = null;
    let currentCommentPage = 1;
    const COMMENTS_PER_PAGE = 100;
    const MAX_COMMENT_LENGTH = 1000;
    const MAX_AVATAR_BYTES = 2 * 1024 * 1024;
    let imageGalleryData = [];
    let imageGalleryIndex = 0;
    let currentDisplayName = null;
    let remainingNameChanges = 5;
    const DEFAULT_AVATAR = "/static/images/user.webp";
    let currentAvatarUrl = null;
    let remainingAvatarChanges = 5;

    fetch("/static/json/project.json")
        .then(response => response.json())
        .then(data => {
            slideData = normalizeSlides(data);
            updateCarousel();
        })
        .catch(error => {
            console.error('Error fetching slide data:', error);
        });

    function normalizeLocaleMap(value, fallback = "") {
        if (value && typeof value === "object") {
            return {
                en: value.en || fallback || "",
                ceb: value.ceb || value.en || fallback || "",
                fr: value.fr || value.en || fallback || "",
                fil_PH: value.fil_PH || value.en || fallback || "",
            };
        }

        const text = typeof value === "string" ? value : (fallback || "");
        return {
            en: text,
            ceb: text,
            fr: text,
            fil_PH: text,
        };
    }

    function normalizeSlides(slides) {
        if (!Array.isArray(slides)) return [];

        return slides
            .map((slide) => {
                if (!slide) return null;
                const src = slide.src || slide.image_url || "";
                if (!src) return null;
                return {
                    src,
                    titles: normalizeLocaleMap(
                        slide.titles || slide.title,
                        tm("modalProjectPreview", "Project Preview")
                    ),
                    descriptions: normalizeLocaleMap(slide.descriptions || slide.description, ""),
                };
            })
            .filter(Boolean);
    }


    function updateCarousel() {
        const carouselInner = document.getElementById('carouselInner');
        const carouselIndicators = document.getElementById('carouselIndicators');
        const boxContainer = document.querySelector(".box-modal-container");
        const carouselInnerQuery = document.querySelector(".carousel-inner");

        if (!carouselInner || !carouselIndicators || !boxContainer || !carouselInnerQuery) {
            return;
        }

        carouselIndicators.innerHTML = '';
        carouselInner.innerHTML = '';

        if (!slideData.length) {
            boxContainer.style.display = "none";
            return;
        }

        slideData.forEach((slide, index) => {
            const indicator = document.createElement('span');
            indicator.classList.add('indicator');
            indicator.dataset.slideTo = index;
            if (index === 0) indicator.classList.add('active');
            carouselIndicators.appendChild(indicator);

            const carouselItem = document.createElement('div');
            carouselItem.classList.add('carousel-item');
            if (index === 0) carouselItem.classList.add('active');

            const img = document.createElement('img');
            img.classList.add('d-block', 'w-100');
            img.src = slide.src;
            carouselItem.appendChild(img);

            carouselInner.appendChild(carouselItem);
        });

        const indicators = document.querySelectorAll('.indicator');
        const slides = document.querySelectorAll('.carousel-item');

        function setActiveSlide() {
            slides.forEach((slide, index) => {
                slide.classList.toggle("active", index === currentSlide);
            });

            indicators.forEach((indicator, index) => {
                indicator.classList.toggle("active", index === currentSlide);
            });

            const offset = -currentSlide * 100;
            carouselInnerQuery.style.transform = `translateX(${offset}%)`;

            const currentSlideTitle = slideData[currentSlide].titles;
            const currentSlideDescription = slideData[currentSlide].descriptions;

            const titleText = currentSlideTitle[currentLocale] || currentSlideTitle["en"];
            const descriptionText = currentSlideDescription[currentLocale] || currentSlideDescription["en"];

            const descriptionTitle = document.getElementById("descriptionTitle");
            const descriptionTextEl = document.getElementById("descriptionText");

            if (descriptionTitle) descriptionTitle.textContent = titleText;
            if (descriptionTextEl) descriptionTextEl.textContent = descriptionText;

            boxContainer.style.display = "block";
        }

        setActiveSlide();
    }

    function moveSlide(direction) {
        if (!slideData.length) return;
        currentSlide = (currentSlide + direction + slideData.length) % slideData.length;
        updateCarousel();
    }

    function isVideoFile(fileSrc) {
        if (!fileSrc) return false;

        // Common video file extensions
        const videoExtensions = [
            "mp4", "mov", "avi", "mkv", "webm",
            "flv", "wmv", "mpeg", "mpg", "3gp"
        ];

        // Extract extension from URL or filename
        const ext = fileSrc.split('.').pop().toLowerCase();

        return videoExtensions.includes(ext);
    }

    function getImageGalleryNavElements() {
        return {
            prevBtn: document.getElementById("imageModalPrev"),
            nextBtn: document.getElementById("imageModalNext"),
            counter: document.getElementById("imageModalGalleryCounter"),
            imageModal: document.getElementById("imageModal"),
            boxContainer: document.querySelector(".box-modal-container"),
            modalImage: document.getElementById("modalImage"),
        };
    }

    function normalizeImageGalleryItems(items) {
        if (!Array.isArray(items)) return [];
        return items
            .map((item) => {
                if (!item || typeof item !== "object") return null;
                const src = String(item.image_url || item.src || "").trim();
                if (!src) return null;
                return {
                    src,
                    title: String(item.title || "").trim(),
                    description: String(item.caption || item.description || "").trim(),
                };
            })
            .filter(Boolean);
    }

    function syncImageGalleryNav(isImageView = null) {
        const { prevBtn, nextBtn, counter, imageModal, boxContainer, modalImage } = getImageGalleryNavElements();
        if (!prevBtn || !nextBtn || !counter || !imageModal) return;

        const modalOpen = imageModal.style.display === "flex";
        const boxOpen = boxContainer && boxContainer.style.display === "block";
        const imageShown = modalImage && modalImage.style.display !== "none";
        const shouldShow = modalOpen && !boxOpen && (isImageView ?? imageShown) && imageGalleryData.length > 1;

        prevBtn.hidden = !shouldShow;
        nextBtn.hidden = !shouldShow;
        counter.hidden = !shouldShow;

        if (!shouldShow) {
            counter.textContent = "";
            return;
        }

        counter.textContent = `${imageGalleryIndex + 1} / ${imageGalleryData.length}`;
    }

    function clearImageGalleryNav() {
        imageGalleryData = [];
        imageGalleryIndex = 0;
        syncImageGalleryNav(false);
    }

    function renderActiveImageGallerySlide() {
        if (!imageGalleryData.length) return;
        const total = imageGalleryData.length;
        imageGalleryIndex = (imageGalleryIndex + total) % total;
        const item = imageGalleryData[imageGalleryIndex];
        openModal(
            item.src,
            item.title,
            item.description,
            ModalType.IMAGE,
            false,
            null,
            { keepImageGallery: true }
        );
    }

    function pauseAllVideos() {
        const videos = document.querySelectorAll("video");
        videos.forEach(v => {
            v.pause();
            v.currentTime = 0; // optional reset
        });
    }

    function getCommentComposerElements() {
        return {
            commentBox: document.getElementById("commentBox"),
            emojiPicker: document.getElementById("commentEmojiPicker"),
            emojiToggle: document.getElementById("commentEmojiToggle"),
        };
    }

    function getCommentPanelElements() {
        return {
            commentSection: document.querySelector(".comment-section"),
            commentPanelToggle: document.getElementById("commentPanelToggle"),
            commentPanelToggleLabel: document.querySelector(".comment-panel-toggle__label"),
        };
    }

    function isMobileViewport() {
        return window.innerWidth <= 768;
    }

    function getCollapsedCommentPanelHeight() {
        return "64px";
    }

    function getMobileHalfModalHeight() {
        const safeHalf = Math.floor(window.innerHeight * 0.5);
        return `${Math.max(240, safeHalf)}px`;
    }

    function getCollapsedCommentPanelPixels() {
        const raw = getCollapsedCommentPanelHeight();
        const parsed = Number.parseInt(raw, 10);
        return Number.isFinite(parsed) ? parsed : 64;
    }

    function setMobileModalContentHeight(expanded) {
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (!modalContentContainer) return;

        if (!isMobileViewport()) {
            modalContentContainer.style.height = "";
            modalContentContainer.style.minHeight = "";
            modalContentContainer.style.maxHeight = "";
            modalContentContainer.style.paddingBottom = "";
            return;
        }

        if (expanded) {
            const halfHeight = getMobileHalfModalHeight();
            modalContentContainer.style.height = halfHeight;
            modalContentContainer.style.minHeight = halfHeight;
            modalContentContainer.style.maxHeight = halfHeight;
            modalContentContainer.style.paddingBottom = "0";
            return;
        }

        const collapsedHeight = getCollapsedCommentPanelPixels();
        const availableHeight = Math.max(220, window.innerHeight - collapsedHeight - 12);
        const availableHeightPx = `${availableHeight}px`;
        modalContentContainer.style.height = availableHeightPx;
        modalContentContainer.style.minHeight = availableHeightPx;
        modalContentContainer.style.maxHeight = availableHeightPx;
        modalContentContainer.style.paddingBottom = "0";
    }

    function getExpandedCommentPanelHeight() {
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (isMobileViewport() && modalContentContainer) {
            const containerHeight = Math.round(modalContentContainer.getBoundingClientRect().height);
            if (containerHeight > 0) {
                return `${containerHeight}px`;
            }
            return getMobileHalfModalHeight();
        }
        return "50vh";
    }

    function setCommentPanelExpanded(expanded) {
        const { commentSection, commentPanelToggle, commentPanelToggleLabel } = getCommentPanelElements();
        if (!commentSection || !commentPanelToggle) return;

        const isExpanded = Boolean(expanded) && isMobileViewport() && commentSection.style.display !== "none";
        const isCollapsed = !isExpanded && isMobileViewport() && commentSection.style.display !== "none";
        setMobileModalContentHeight(isExpanded);
        commentSection.classList.toggle("comment-section--expanded", isExpanded);
        commentSection.classList.toggle("comment-section--collapsed", isCollapsed);
        commentPanelToggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
        if (isMobileViewport()) {
            const targetHeight = isExpanded
                ? getExpandedCommentPanelHeight()
                : getCollapsedCommentPanelHeight();
            commentSection.style.height = targetHeight;
            commentSection.style.maxHeight = targetHeight;
        } else {
            commentSection.style.height = "";
            commentSection.style.maxHeight = "";
        }

        if (commentPanelToggleLabel) {
            commentPanelToggleLabel.textContent = isExpanded
                ? tm("commentPanelCollapse", "Collapse")
                : tm("commentPanelExpand", "Expand");
        }
    }

    function syncCommentPanelToggleVisibility(enableComments = false) {
        const { commentPanelToggle } = getCommentPanelElements();
        if (!commentPanelToggle) return;
        const shouldShow = Boolean(enableComments) && isMobileViewport();
        commentPanelToggle.hidden = !shouldShow;
        if (!shouldShow) {
            commentPanelToggle.setAttribute("aria-expanded", "false");
        }
    }

    function resetCommentPanelState(enableComments = false) {
        const { commentSection } = getCommentPanelElements();
        if (commentSection) {
            commentSection.classList.remove("comment-section--expanded");
            commentSection.classList.remove("comment-section--collapsed");
        }
        syncCommentPanelToggleVisibility(enableComments);
        setCommentPanelExpanded(Boolean(enableComments) && isMobileViewport());
    }

    function toggleCommentPanel(event) {
        event?.preventDefault?.();
        event?.stopPropagation?.();
        const { commentPanelToggle } = getCommentPanelElements();
        if (!commentPanelToggle) return;
        const expanded = commentPanelToggle.getAttribute("aria-expanded") === "true";
        setCommentPanelExpanded(!expanded);
    }

    function closeCommentEmojiPicker() {
        const { emojiPicker, emojiToggle } = getCommentComposerElements();
        if (emojiPicker) emojiPicker.hidden = true;
        if (emojiToggle) emojiToggle.setAttribute("aria-expanded", "false");
    }

    function toggleCommentEmojiPicker(event) {
        event?.preventDefault?.();
        event?.stopPropagation?.();

        const { emojiPicker, emojiToggle } = getCommentComposerElements();
        if (!emojiPicker) return;

        const willOpen = emojiPicker.hidden;
        emojiPicker.hidden = !willOpen;
        if (emojiToggle) emojiToggle.setAttribute("aria-expanded", willOpen ? "true" : "false");
    }

    function insertCommentEmoji(emoji) {
        const { commentBox } = getCommentComposerElements();
        if (!commentBox) return;

        const value = commentBox.value || "";
        const start = Number.isInteger(commentBox.selectionStart) ? commentBox.selectionStart : value.length;
        const end = Number.isInteger(commentBox.selectionEnd) ? commentBox.selectionEnd : value.length;
        const nextValue = value.slice(0, start) + emoji + value.slice(end);

        commentBox.value = nextValue;
        commentBox.dispatchEvent(new Event("input", { bubbles: true }));

        const nextPos = start + emoji.length;
        try {
            commentBox.setSelectionRange(nextPos, nextPos);
        } catch (_) {
            // Ignore if browser/input type doesn't support selection range.
        }

        commentBox.focus();
        closeCommentEmojiPicker();
    }

    window.openProjectSlidesModal = function (slides, startIndex = 0) {
        const normalized = normalizeSlides(slides);
        if (!normalized.length) {
            return;
        }
        const localizedSlides = normalized.map((slide) => ({
            src: slide.src,
            title: (slide.titles && (slide.titles[currentLocale] || slide.titles.en)) || "",
            description: (slide.descriptions && (slide.descriptions[currentLocale] || slide.descriptions.en)) || "",
        }));
        window.openImageGalleryModal(localizedSlides, startIndex);
    };

    window.openImageGalleryModal = function (items, startIndex = 0) {
        const normalized = normalizeImageGalleryItems(items);
        if (!normalized.length) return;

        imageGalleryData = normalized;
        imageGalleryIndex = Math.max(0, Math.min(Number(startIndex) || 0, normalized.length - 1));
        renderActiveImageGallerySlide();
    };

    window.moveImageModalSlide = function (direction = 1) {
        if (!imageGalleryData.length) return;
        imageGalleryIndex = (imageGalleryIndex + (Number(direction) || 0) + imageGalleryData.length) % imageGalleryData.length;
        renderActiveImageGallerySlide();
    };

    function updateCommentsUrl(selectedId) {
        if (!selectedId || !window.idType) return;
        try {
            const url = new URL(window.location.href);
            url.searchParams.set(window.idType, String(selectedId));
            url.hash = "comments";
            window.history.replaceState(null, "", url.toString());
        } catch (err) {
            console.error(err);
        }
    }

    function clearCommentsUrl() {
        try {
            const url = new URL(window.location.href);
            url.searchParams.delete(window.idType || "vlog_id");
            url.searchParams.delete("gallery_id");
            url.hash = "";
            window.history.replaceState(null, "", url.toString());
        } catch (err) {
            console.error(err);
        }
    }

    // Function to open the modal and show the image
    function openModal(fileSrc, title = '', description = '', type = ModalType.IMAGE, enableComments = false, selectedId = null, options = {}) {
        currentSelectedId = selectedId;
        const keepImageGallery = Boolean(options && options.keepImageGallery);
        var boxModalContainer = document.querySelector(".box-modal-container");
        var modalImage = document.getElementById("modalImage");
        var modalVideo = document.getElementById("modalVideo");
        var caption = document.getElementById("caption");
        var imageModal = document.getElementById("imageModal");
        if (!imageModal) return;
        imageModal.style.display = "flex";
        const adminFloadtBtn = document.querySelector(".admin-float-btn");
        let isImageView = false;

        if (!keepImageGallery) {
            clearImageGalleryNav();
        }

        if (type == ModalType.BOX) {
            if (boxModalContainer) boxModalContainer.style.display = "block";
            if (modalImage) modalImage.style.display = "none";
            if (modalVideo) modalVideo.style.display = "none";
            if (caption) caption.style.display = "none";
            isImageView = false;
        } else {
            if (boxModalContainer) boxModalContainer.style.display = "none";
            if (isVideoFile(fileSrc)) {
                pauseAllVideos();
                if (modalImage) modalImage.style.display = "none";
                if (modalVideo) modalVideo.style.display = "block";
                if (modalImage) modalImage.src = "";
                if (modalVideo) modalVideo.src = fileSrc;

                // Force autoplay
                if (modalVideo) {
                    modalVideo.muted = true;      // required for autoplay
                    modalVideo.autoplay = true;
                    modalVideo.play().catch(err => {
                        console.warn("Autoplay failed:", err);
                    });
                }
                isImageView = false;
            } else {
                if (modalVideo) modalVideo.style.display = "none";
                if (modalImage) modalImage.style.display = "block";
                if (modalVideo) modalVideo.src = "";
                if (modalImage) modalImage.src = fileSrc;
                isImageView = true;
            }

            if (caption) {
                caption.style.display = "block";
                caption.innerHTML = "";
                if (title && title.trim() !== "") {
                    caption.innerHTML += "<h3>" + title + "</h3>";
                }

                if (description && description.trim() !== "") {
                    caption.innerHTML += "<p>" + description + "</p>";
                }
            }
        }

        // Show or hide comment section
        const isMobile = window.innerWidth <= 768;
        const commentSection = document.querySelector(".comment-section");
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (enableComments) {
            if (commentSection) commentSection.style.display = "flex";
            if (modalContentContainer) modalContentContainer.style.width = isMobile ? "100%" : "50%";
            resetCommentPanelState(true);
            currentCommentPage = 1;
            updateCommentsUrl(selectedId);
            loadComments(selectedId, currentCommentPage, false, true);
        } else {
            if (commentSection) commentSection.style.display = "none";
            if (modalContentContainer) {
                modalContentContainer.style.width = "100%";
                modalContentContainer.style.height = "";
                modalContentContainer.style.minHeight = "";
                modalContentContainer.style.maxHeight = "";
                modalContentContainer.style.paddingBottom = "";
            }
            resetCommentPanelState(false);
        }

        adminFloadtBtn && (adminFloadtBtn.style.display = "none");
        closeCommentEmojiPicker();
        syncImageGalleryNav(isImageView);
    }

    // Function to close the modal
    function closeModal() {
        const adminFloadtBtn = document.querySelector(".admin-float-btn");
        const imageModal = document.getElementById("imageModal");
        if (imageModal) imageModal.style.display = "none";
        const boxModalContainer = document.querySelector(".box-modal-container");
        if (boxModalContainer) boxModalContainer.style.display = "none";
        adminFloadtBtn && (adminFloadtBtn.style.display = "flex");
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (modalContentContainer) {
            modalContentContainer.style.height = "";
            modalContentContainer.style.minHeight = "";
            modalContentContainer.style.maxHeight = "";
            modalContentContainer.style.paddingBottom = "";
        }
        pauseAllVideos();
        closeCommentEmojiPicker();
        clearImageGalleryNav();
        clearCommentsUrl();
        resetCommentPanelState(false);
    }

    // ---------------- Comments ----------------
    function getSkeletonMarkup(count = 4) {
        let html = `<div class="comment-skeleton-list">`;
        for (let i = 0; i < count; i++) {
            html += `
            <div class="comment-skeleton-item">
                <div class="comment-skeleton-avatar"></div>
                <div class="comment-skeleton-body">
                    <div class="comment-skeleton-line comment-skeleton-line--short"></div>
                    <div class="comment-skeleton-line comment-skeleton-line--long"></div>
                    <div class="comment-skeleton-meta">
                        <div class="comment-skeleton-line"></div>
                        <div class="comment-skeleton-line"></div>
                    </div>
                </div>
            </div>`;
        }
        html += `</div>`;
        return html;
    }

    function showCommentSkeletons(commentList) {
        const existing = commentList.querySelector(".comment-skeleton-list");
        if (existing) return;
        commentList.insertAdjacentHTML("beforeend", getSkeletonMarkup(4));
    }

    function removeCommentSkeletons(commentList) {
        const skeletons = commentList.querySelectorAll(".comment-skeleton-list");
        skeletons.forEach(s => s.remove());
    }

    async function loadComments(selectedId, page = 1, prependOlder = false, initial = false) {
        const commentList = document.querySelector(".comment-list");
        const commentSection = document.querySelector(".comment-section");

        if (initial) {
            commentList.innerHTML = '';
            showCommentSkeletons(commentList);
        }

        // Save current scroll position if prepending older comments
        let previousScrollHeight = 0;
        let previousScrollTop = 0;
        if (prependOlder) {
            previousScrollHeight = commentList.scrollHeight;
            previousScrollTop = commentList.scrollTop;
        }

        // "Load Previous" button logic
        let prevBtn = document.getElementById("prevCommentsBtn");
        if (!prevBtn) {
            prevBtn = document.createElement("button");
            prevBtn.id = "prevCommentsBtn";
            prevBtn.textContent = tm("loadPrevious", "Previous");
            prevBtn.classList.add("prev-comments-btn");
            commentSection.insertBefore(prevBtn, commentList);
        }

        try {
            prevBtn.disabled = true;
            prevBtn.textContent = tm("loading", "Loading...");

            const res = await fetch(`/api/${baseUrl}?${idType}=${selectedId}&page=${page}&limit=${COMMENTS_PER_PAGE}`);
            const data = await res.json();

            if (typeof data.display_name === "string" && data.display_name.trim() !== "") {
                currentDisplayName = data.display_name;
            }
            if (typeof data.remaining_changes === "number") {
                remainingNameChanges = data.remaining_changes;
            }
            if (typeof data.avatar_url === "string" && data.avatar_url.trim() !== "") {
                currentAvatarUrl = data.avatar_url;
            }
            const commenterAvatar = document.getElementById("commenterAvatar");
            if (commenterAvatar) commenterAvatar.src = currentAvatarUrl || DEFAULT_AVATAR;

            // Remove skeletons once data arrives
            removeCommentSkeletons(commentList);

            const comments = data.comments || [];
            const totalComments = data.total || 0;
            const totalPages = Math.ceil(totalComments / COMMENTS_PER_PAGE);

            if (!prependOlder && comments.length === 0) {
                const emptyDiv = document.createElement("div");
                emptyDiv.classList.add("no-comments");
                emptyDiv.textContent = tm("noCommentsYet", "No comments yet.");
                commentList.appendChild(emptyDiv);
                document.getElementById("commentCount").textContent = 0;
                prevBtn.style.display = "none";
                return;
            }

            // app sends newest first, so reverse for UI (oldest ?' newest)
            const sortedComments = !prependOlder ? [...comments].reverse() : comments;
            sortedComments.forEach(comment => {
                const div = renderComment(comment);
                if (prependOlder) {
                    commentList.prepend(div); // older page gets prepended to top
                } else {
                    commentList.appendChild(div); // normal order: bottom = latest
                }
            });

            document.getElementById("commentCount").textContent = totalComments;

            prevBtn.style.display = page < totalPages ? "block" : "none";
            prevBtn.onclick = () => {
                currentCommentPage++;
                loadComments(selectedId, currentCommentPage, true);
            };

            if (prependOlder) {
                const newScrollHeight = commentList.scrollHeight;
                commentList.scrollTop = newScrollHeight - previousScrollHeight + previousScrollTop;
            } else {
                commentList.scrollTop = commentList.scrollHeight;
            }
        } catch (err) {
            console.error(err);
            removeCommentSkeletons(commentList);
            const emptyDiv = document.createElement("div");
            emptyDiv.classList.add("no-comments");
            emptyDiv.textContent = tm(
                "failedToLoadComments",
                "Failed to load comments."
            );
            commentList.appendChild(emptyDiv);
        } finally {
            // spinner.style.display = "none";
            prevBtn.disabled = false;
            prevBtn.textContent = tm("loadPrevious", "Previous");
        }
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function renderComment(comment) {
        const div = document.createElement("div");
        div.classList.add("comment-item");
        div.dataset.commentId = comment._id;
        div.dataset.isOwn = comment.is_own ? "true" : "false";
        const likedClass = comment.is_liked ? "liked" : "";
        const deleteBtnMarkup = comment.is_own
            ? `<u class="comment-remove-btn" title="${escapeHTML(tm("deleteCommentTitle", "Delete comment"))}">${tm("removeCommentLabel", "remove")}</u>`
            : "";

        const avatarUrl = comment.avatar_url || DEFAULT_AVATAR;
        div.innerHTML = `
            <img src="${escapeHTML(avatarUrl)}" class="comment-avatar" alt="Avatar" title="${escapeHTML(tm("viewAvatar", "View avatar"))}" />
            <div class="comment-content">
                <div class="comment-author-line">
                    <p class="comment-author">${escapeHTML(comment.author_name)}</p>
                </div>
                <p class="comment-text">${escapeHTML(comment.text)}</p>
                <div class="comment-meta">
                    <u>${new Date(comment.created_at).toLocaleString()}</u>
                    <u class="like-btn ${likedClass}">${tm("commentLike", "Like")}</u>
                    <span class="like-count">${comment.liked_ips ? comment.liked_ips.length : 0}</span>
                    ${deleteBtnMarkup}
                </div>
            </div>
        `;

        const likeBtn = div.querySelector('.like-btn');
        likeBtn.addEventListener('click', () => toggleCommentLike(likeBtn, comment._id));

        const avatarImg = div.querySelector(".comment-avatar");
        avatarImg?.addEventListener("click", () => {
            if (typeof window.openAdminImagePreview === "function") {
                window.openAdminImagePreview(avatarUrl, comment.author_name);
            } else {
                openModal(avatarUrl, comment.author_name, "", ModalType.IMAGE, true, currentSelectedId);
            }
        });

        const deleteBtn = div.querySelector(".comment-remove-btn");
        deleteBtn?.addEventListener("click", (e) => {
            e.preventDefault();
            deleteCommentById(comment._id);
        });

        return div;
    }

    async function submitComment() {
        const commentList = document.querySelector(".comment-list");
        const commentBox = document.getElementById("commentBox");
        const text = commentBox.value.trim();

        if (!text || !currentSelectedId) return;
        if (text.length > MAX_COMMENT_LENGTH) {
            window.notify(
                tm(
                    "commentTooLong",
                    "Comment cannot exceed {max} characters.",
                    { max: MAX_COMMENT_LENGTH }
                ),
                "warning"
            );
            return;
        }

        commentBox.disabled = true;

        try {
            const bodyPayload = {
                author_name: tm("commentAuthorYou", "You"),
                text
            };
            bodyPayload[window.idType] = currentSelectedId;

            const res = await fetch(`/api/${baseUrl}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(bodyPayload),
            });

            const data = await res.json();
            const noCommentsDiv = document.querySelector(".no-comments");
            if (noCommentsDiv) noCommentsDiv.remove();

            // Create and append the new comment directly at the bottom
            const newComment = {
                _id: data.comment_id,
                author_name: currentDisplayName || tm("commentAuthorYou", "You"),
                text,
                liked_ips: [],
                created_at: new Date(),
                is_own: true,
                avatar_url: currentAvatarUrl || DEFAULT_AVATAR,
            };
            const div = renderComment(newComment);
            document.querySelector(".comment-list").appendChild(div);

            // Update count
            document.getElementById("commentCount").textContent =
                Number(document.getElementById("commentCount").textContent) + 1;

            commentBox.value = "";

            // ?? Auto-scroll to bottom smoothly
            commentList.scrollTo({
                top: commentList.scrollHeight,
                behavior: "smooth",
            });
        } catch (err) {
            console.error(err);
        } finally {
            commentBox.disabled = false;
            commentBox.focus();
        }
    }

    // ---------------- Display name / avatar editing ----------------
    function updateAvatarLimitUI() {
        const hint = document.getElementById("avatarEditHint");
        if (!hint) return;

        const limited = remainingAvatarChanges <= 0;
        if (limited) {
            hint.textContent = tm("avatarLimit", "You have reached the daily limit of 20 avatar changes. Try again tomorrow.");
        } else {
            hint.textContent =
                remainingAvatarChanges === 1
                    ? tm("avatarHintOne", "You can change your avatar 1 more time today.")
                    : tm("avatarHintMany", "You can change your avatar {remaining} more times today.", { remaining: remainingAvatarChanges });
        }

        const uploadInput = document.getElementById("avatarUploadInput");
        const removeBtn = document.getElementById("avatarRemoveBtn");
        const noAvatarToRemove = !currentAvatarUrl || currentAvatarUrl === DEFAULT_AVATAR;
        if (uploadInput) uploadInput.disabled = limited;
        if (removeBtn) removeBtn.disabled = limited || noAvatarToRemove;
        document.querySelectorAll(".avatar-presets__item").forEach((btn) => {
            btn.disabled = limited;
        });
    }

    async function refreshAvatarStatus() {
        try {
            const res = await fetch("/api/comment-avatar", { method: "GET" });
            const data = await res.json();
            if (!res.ok) return;
            if (typeof data.avatar_url === "string" && data.avatar_url.trim() !== "") {
                currentAvatarUrl = data.avatar_url;
            }
            if (typeof data.remaining_avatar_changes === "number") {
                remainingAvatarChanges = data.remaining_avatar_changes;
            }
            syncAvatarEditor();
        } catch (err) {
            console.error(err);
        }
    }

    async function refreshNameStatus() {
        try {
            const res = await fetch("/api/comment-username", { method: "GET" });
            const data = await res.json();
            if (!res.ok) return;
            if (typeof data.display_name === "string" && data.display_name.trim() !== "") {
                currentDisplayName = data.display_name;
            }
            if (typeof data.remaining_changes === "number") {
                remainingNameChanges = data.remaining_changes;
            }
            updateNameEditHint();
        } catch (err) {
            console.error(err);
        }
    }

    function syncAvatarEditor() {
        const preview = document.getElementById("avatarPreview");
        const avatarError = document.getElementById("avatarError");
        if (avatarError) avatarError.hidden = true;
        if (preview) preview.src = currentAvatarUrl || DEFAULT_AVATAR;
        document.querySelectorAll(".avatar-presets__item").forEach((btn) => {
            btn.classList.toggle("is-selected", (currentAvatarUrl || "") === btn.dataset.avatarUrl);
        });
        updateAvatarLimitUI();
    }

    function applyAvatarToComments(avatarUrl) {
        document.querySelectorAll(".comment-item").forEach((item) => {
            if (item.dataset.isOwn === "true") {
                const img = item.querySelector(".comment-avatar");
                if (img) img.src = avatarUrl;
            }
        });
        const commenterAvatar = document.getElementById("commenterAvatar");
        if (commenterAvatar) commenterAvatar.src = avatarUrl;
        const preview = document.getElementById("avatarPreview");
        if (preview) preview.src = avatarUrl;
        document.querySelectorAll(".avatar-presets__item").forEach((btn) => {
            btn.classList.toggle("is-selected", avatarUrl === btn.dataset.avatarUrl);
        });
    }

    function openEditNameModal() {
        const modal = document.getElementById("nameEditModal");
        const input = document.getElementById("nameEditInput");
        const error = document.getElementById("nameEditError");
        if (!modal || !input) return;

        input.value = currentDisplayName || "";
        if (error) error.hidden = true;
        updateNameEditHint();
        syncAvatarEditor();
        refreshAvatarStatus();
        refreshNameStatus();
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
    }

    function closeEditNameModal() {
        const modal = document.getElementById("nameEditModal");
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    }

    function updateNameEditHint() {
        const hint = document.getElementById("nameEditHint");
        const saveBtn = document.getElementById("nameEditSaveBtn");
        if (!hint || !saveBtn) return;

        if (remainingNameChanges <= 0) {
            hint.textContent = tm(
                "editNameLimit",
                "You have reached the daily limit of 20 name changes. Try again tomorrow."
            );
            saveBtn.disabled = true;
            return;
        }

        hint.textContent =
            remainingNameChanges === 1
                ? tm("editNameHintOne", "You can change your name 1 more time today.")
                : tm(
                    "editNameHintMany",
                    "You can change your name {remaining} more times today.",
                    { remaining: remainingNameChanges }
                );
        saveBtn.disabled = false;
    }

    function setButtonLoading(btn, loading) {
        if (!btn) return;
        if (loading) {
            btn.classList.add("is-loading");
            btn.setAttribute("aria-busy", "true");
            btn.disabled = true;
            const labelEl = btn.querySelector(".btn-label") || btn;
            if (!labelEl.dataset.originalText) {
                labelEl.dataset.originalText = labelEl.textContent || "";
            }
            if (btn.dataset.loadingText !== undefined) {
                labelEl.textContent = btn.dataset.loadingText;
            }
        } else {
            btn.classList.remove("is-loading");
            btn.removeAttribute("aria-busy");
            btn.disabled = false;
            const labelEl = btn.querySelector(".btn-label") || btn;
            if (labelEl.dataset.originalText) {
                labelEl.textContent = labelEl.dataset.originalText;
                delete labelEl.dataset.originalText;
            }
        }
    }

    async function saveDisplayName() {
        const input = document.getElementById("nameEditInput");
        const error = document.getElementById("nameEditError");
        const saveBtn = document.getElementById("nameEditSaveBtn");
        if (!input || !error || !saveBtn) return;

        const name = input.value.trim();
        if (!name) {
            error.textContent = tm("editNameRequired", "Please enter a display name.");
            error.hidden = false;
            return;
        }

        error.hidden = true;
        setButtonLoading(saveBtn, true);

        try {
            const res = await fetch("/api/comment-username", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ display_name: name }),
            });
            const data = await res.json();

            if (typeof data.remaining_changes === "number") {
                remainingNameChanges = data.remaining_changes;
            }

            if (!res.ok) {
                error.textContent =
                    (data.errors && data.errors._global) ||
                    tm("editNameError", "Failed to save your name. Please try again.");
                error.hidden = false;
                updateNameEditHint();
                return;
            }

            currentDisplayName = data.display_name || name;

            document.querySelectorAll(".comment-item").forEach((item) => {
                if (item.dataset.isOwn === "true") {
                    const author = item.querySelector(".comment-author");
                    if (author) author.textContent = currentDisplayName;
                }
            });

            closeEditNameModal();
            if (window.notify) {
                window.notify(tm("editNameSaved", "Name updated successfully."), "success");
            }
        } catch (err) {
            console.error(err);
            error.textContent = tm("editNameError", "Failed to save your name. Please try again.");
            error.hidden = false;
        } finally {
            setButtonLoading(saveBtn, false);
            updateNameEditHint();
        }
    }

    function getAvatarEditorButtons() {
        const uploadInput = document.getElementById("avatarUploadInput");
        const uploadLabel = uploadInput ? uploadInput.closest("label") : null;
        const removeBtn = document.getElementById("avatarRemoveBtn");
        const presets = document.querySelectorAll(".avatar-presets__item");
        return { uploadLabel, removeBtn, presets };
    }

    async function uploadAvatar(file) {
        const avatarError = document.getElementById("avatarError");
        const { uploadLabel, presets } = getAvatarEditorButtons();
        if (file && file.size > MAX_AVATAR_BYTES) {
            if (avatarError) {
                avatarError.textContent = tm("avatarTooLarge", "Image must be 2MB or smaller.");
                avatarError.hidden = false;
            }
            return;
        }
        setButtonLoading(uploadLabel, true);
        presets.forEach((btn) => (btn.disabled = true));
        try {
            const formData = new FormData();
            formData.append("avatar", file);

            const res = await fetch("/api/comment-avatar/upload", { method: "POST", body: formData });
            const data = await res.json();
            if (typeof data.remaining_avatar_changes === "number") {
                remainingAvatarChanges = data.remaining_avatar_changes;
            }
            if (!res.ok) {
                if (avatarError) {
                    avatarError.textContent =
                        data.code === "avatar_too_large"
                            ? tm("avatarTooLarge", "Image is still larger than 2MB after compression.")
                            : data.code === "avatar_limit_reached"                            ? tm("avatarLimit", "You have reached the daily limit of 20 avatar changes. Try again tomorrow.")
                            : tm("avatarUploadError", "Failed to upload avatar. Please try again.");
                    avatarError.hidden = false;
                }
                updateAvatarLimitUI();
                return;
            }

            currentAvatarUrl = data.avatar_url;
            applyAvatarToComments(currentAvatarUrl);
            updateAvatarLimitUI();
            if (window.notify) window.notify(tm("avatarSaved", "Avatar updated successfully."), "success");
        } catch (err) {
            console.error(err);
            if (avatarError) {
                avatarError.textContent = tm("avatarUploadError", "Failed to upload avatar. Please try again.");
                avatarError.hidden = false;
            }
        } finally {
            setButtonLoading(uploadLabel, false);
            updateAvatarLimitUI();
        }
    }

    async function selectPresetAvatar(avatarUrl) {
        const avatarError = document.getElementById("avatarError");
        const { presets } = getAvatarEditorButtons();
        presets.forEach((btn) => (btn.disabled = true));
        try {
            const res = await fetch("/api/comment-avatar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ avatar_url: avatarUrl }),
            });
            const data = await res.json();
            if (typeof data.remaining_avatar_changes === "number") {
                remainingAvatarChanges = data.remaining_avatar_changes;
            }
            if (!res.ok) {
                if (avatarError) {
                    avatarError.textContent =
                        data.code === "avatar_limit_reached"
                            ? tm("avatarLimit", "You have reached the daily limit of 20 avatar changes. Try again tomorrow.")
                            : tm("avatarUploadError", "Failed to update avatar. Please try again.");
                    avatarError.hidden = false;
                }
                updateAvatarLimitUI();
                return;
            }
            currentAvatarUrl = data.avatar_url;
            applyAvatarToComments(currentAvatarUrl);
            updateAvatarLimitUI();
            if (window.notify) window.notify(tm("avatarSaved", "Avatar updated successfully."), "success");
        } catch (err) {
            console.error(err);
        } finally {
            updateAvatarLimitUI();
        }
    }

    async function removeAvatar() {
        const avatarError = document.getElementById("avatarError");
        const { removeBtn, presets } = getAvatarEditorButtons();
        setButtonLoading(removeBtn, true);
        presets.forEach((btn) => (btn.disabled = true));
        try {
            const res = await fetch("/api/comment-avatar", { method: "DELETE" });
            const data = await res.json();
            if (typeof data.remaining_avatar_changes === "number") {
                remainingAvatarChanges = data.remaining_avatar_changes;
            }
            if (!res.ok) {
                if (avatarError) {
                    avatarError.textContent =
                        data.code === "avatar_limit_reached"
                            ? tm("avatarLimit", "You have reached the daily limit of 20 avatar changes. Try again tomorrow.")
                            : tm("avatarUploadError", "Failed to update avatar. Please try again.");
                    avatarError.hidden = false;
                }
                updateAvatarLimitUI();
                return;
            }
            currentAvatarUrl = data.avatar_url || DEFAULT_AVATAR;
            applyAvatarToComments(currentAvatarUrl);
            updateAvatarLimitUI();
            if (window.notify) window.notify(tm("avatarRemoved", "Avatar removed."), "success");
        } catch (err) {
            console.error(err);
        } finally {
            setButtonLoading(removeBtn, false);
            updateAvatarLimitUI();
        }
    }

    function deleteCommentById(commentId) {
        if (!commentId) return;
        if (typeof window.openConfirmModal !== "function") return;

        window.openConfirmModal({
            title: tm("deleteCommentTitle", "Delete comment"),
            message: tm("deleteCommentMsg", "Delete this comment? This cannot be undone."),
            confirmText: tm("confirmAction", "Delete"),
            onConfirm: async () => {
                try {
                    const res = await fetch(`/api/${baseUrl}/${commentId}`, { method: "DELETE" });
                    const data = await res.json();
                    if (!res.ok) {
                        if (window.notify) window.notify(data.message || tm("deleteError", "Failed to delete. Please try again."), "error");
                        return;
                    }
                    const commentEl = document.querySelector(`.comment-item[data-comment-id="${commentId}"]`);
                    if (commentEl) commentEl.remove();
                    const countEl = document.getElementById("commentCount");
                    if (countEl) countEl.textContent = Math.max(0, Number(countEl.textContent) - 1);
                    if (window.notify) window.notify(tm("commentDeleted", "Comment deleted."), "success");
                } catch (err) {
                    console.error(err);
                }
            },
        });
    }

    function deleteAllMyComments() {
        if (!currentSelectedId) return;
        if (typeof window.openConfirmModal !== "function") return;

        window.openConfirmModal({
            title: tm("deleteAllTitle", "Delete all my comments"),
            message: tm("deleteAllMsg", "Delete all your comments on this content? This cannot be undone."),
            confirmText: tm("confirmAction", "Delete"),
            onConfirm: async () => {
                const deleteAllBtn = document.getElementById("deleteAllCommentsBtn");
                if (deleteAllBtn) {
                    deleteAllBtn.disabled = true;
                    deleteAllBtn.setAttribute("aria-busy", "true");
                }
                try {
                    const body = {};
                    body[window.idType] = currentSelectedId;
                    const res = await fetch(`/api/${baseUrl}/delete-all`, {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        if (window.notify) window.notify(data.message || tm("deleteError", "Failed to delete. Please try again."), "error");
                        return;
                    }
                    closeEditNameModal();
                    loadComments(currentSelectedId, 1, false, true);
                    if (window.notify) window.notify(tm("commentsDeleted", "All your comments were deleted."), "success");
                } catch (err) {
                    console.error(err);
                } finally {
                    if (deleteAllBtn) {
                        deleteAllBtn.disabled = false;
                        deleteAllBtn.removeAttribute("aria-busy");
                    }
                }
            },
        });
    }

    function initNameEditModal() {
        const modal = document.getElementById("nameEditModal");
        if (!modal || modal.dataset.initialized === "true") return;
        modal.dataset.initialized = "true";

        modal.querySelectorAll("[data-name-edit-close]").forEach((el) => {
            el.addEventListener("click", closeEditNameModal);
        });

        const saveBtn = document.getElementById("nameEditSaveBtn");
        saveBtn?.addEventListener("click", saveDisplayName);

        const input = document.getElementById("nameEditInput");
        input?.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                saveDisplayName();
            }
        });

        document.getElementById("commentHeaderEditBtn")?.addEventListener("click", () => {
            openEditNameModal();
        });

        document.getElementById("commenterEditBtn")?.addEventListener("click", () => {
            openEditNameModal();
        });

        const uploadInput = document.getElementById("avatarUploadInput");
        uploadInput?.addEventListener("change", (e) => {
            const file = e.target.files && e.target.files[0];
            if (file) uploadAvatar(file);
            e.target.value = "";
        });

        document.getElementById("avatarRemoveBtn")?.addEventListener("click", removeAvatar);
        document.getElementById("deleteAllCommentsBtn")?.addEventListener("click", deleteAllMyComments);

        modal.querySelectorAll(".avatar-presets__item").forEach((btn) => {
            btn.addEventListener("click", () => selectPresetAvatar(btn.dataset.avatarUrl));
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && modal.classList.contains("is-open")) {
                closeEditNameModal();
            }
        });
    }

    // Toggle IP-based like
    async function toggleCommentLike(button, commentId) {
        const countSpan = button.nextElementSibling;
        try {
            const res = await fetch(`/api/${baseUrl}/like`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ comment_id: commentId })
            });
            const data = await res.json();
            if (data.liked !== undefined && data.like_count !== undefined) {
                button.classList.toggle("liked", data.liked);
                countSpan.textContent = data.like_count;
            }
        } catch (err) { console.error(err); }
    }

    function initCommentBox() {
        const commentBox = document.getElementById("commentBox");
        if (!commentBox) return;
        if (commentBox.dataset.initialized === "true") return;
        commentBox.dataset.initialized = "true";

        const emojiToggle = document.getElementById("commentEmojiToggle");
        const emojiPicker = document.getElementById("commentEmojiPicker");

        commentBox.addEventListener("input", () => {
            if (commentBox.value.length > MAX_COMMENT_LENGTH) {
                commentBox.value = commentBox.value.slice(0, MAX_COMMENT_LENGTH);
            }
        });

        commentBox.addEventListener("keypress", async (e) => {
            if (e.key === "Enter" && commentBox.value.trim() !== "") {
                await submitComment();
            }
        });

        emojiToggle?.addEventListener("click", toggleCommentEmojiPicker);
        emojiPicker?.addEventListener("click", (event) => {
            event.stopPropagation();
        });

        const commenterAvatar = document.getElementById("commenterAvatar");
        commenterAvatar?.addEventListener("click", () => {
            const avatarUrl = commenterAvatar.src || currentAvatarUrl || DEFAULT_AVATAR;
            if (typeof window.openAdminImagePreview === "function") {
                window.openAdminImagePreview(avatarUrl, currentDisplayName || tm("commentAuthorYou", "You"));
            } else {
                openModal(avatarUrl, currentDisplayName || tm("commentAuthorYou", "You"), "", ModalType.IMAGE, true, currentSelectedId);
            }
        });

        document.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            if (target.closest(".comment-input-field")) return;
            closeCommentEmojiPicker();
        });

        window.addEventListener("resize", () => {
            const { commentSection } = getCommentPanelElements();
            const commentsVisible = Boolean(commentSection) && commentSection.style.display !== "none";
            const modalContentContainer = document.querySelector(".modal-content-container");
            if (modalContentContainer && commentsVisible) {
                const { commentPanelToggle } = getCommentPanelElements();
                const expanded = commentPanelToggle?.getAttribute("aria-expanded") === "true";
                setMobileModalContentHeight(expanded);
            }
            syncCommentPanelToggleVisibility(commentsVisible);
            if (!isMobileViewport()) {
                setCommentPanelExpanded(false);
            } else if (commentsVisible) {
                const { commentPanelToggle } = getCommentPanelElements();
                const expanded = commentPanelToggle?.getAttribute("aria-expanded") === "true";
                setCommentPanelExpanded(expanded);
            }
        });
    }

    // Call after DOM is ready (or immediately if already ready)
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            initCommentBox();
            initNameEditModal();
        });
    } else {
        initCommentBox();
        initNameEditModal();
    }

    document.addEventListener("keydown", (event) => {
        if (!imageGalleryData.length) return;
        const imageModal = document.getElementById("imageModal");
        const boxContainer = document.querySelector(".box-modal-container");
        if (!imageModal || imageModal.style.display !== "flex") return;
        if (boxContainer && boxContainer.style.display === "block") return;

        if (event.key === "ArrowLeft") {
            event.preventDefault();
            window.moveImageModalSlide(-1);
        } else if (event.key === "ArrowRight") {
            event.preventDefault();
            window.moveImageModalSlide(1);
        }
    });


    // expose needed functions globally
    window.submitComment = submitComment;
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.toggleCommentLike = toggleCommentLike;
    window.moveSlide = moveSlide;
    window.moveImageModalSlide = window.moveImageModalSlide;
    window.loadComments = loadComments;
    window.toggleCommentEmojiPicker = toggleCommentEmojiPicker;
    window.insertCommentEmoji = insertCommentEmoji;
    window.toggleCommentPanel = toggleCommentPanel;
}

