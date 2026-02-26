if (!window.__modal_js_loaded__) {
    window.__modal_js_loaded__ = true;
    const ModalType = {
        IMAGE: 'imageModal',
        BOX: 'boxModal'
    };
    let currentSlide = 0;
    const currentLocale = window.pageLocale || "en";
    const modalI18n = window.modalI18n || {};
    const tm = (key, fallback, vars = {}) => {
        let text = modalI18n[key] || fallback;
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
    let imageGalleryData = [];
    let imageGalleryIndex = 0;

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
        carouselIndicators && (carouselIndicators.innerHTML = '');
        carouselInner && (carouselInner.innerHTML = '');

        if (!slideData.length) {
            const boxContainer = document.querySelector(".box-modal-container");
            boxContainer && (boxContainer.style.display = "none");
            return;
        }

        slideData.forEach((slide, index) => {
            // Create indicator
            const indicator = document.createElement('span');
            indicator.classList.add('indicator');
            indicator.dataset.slideTo = index;
            if (index === 0) indicator.classList.add('active');
            carouselIndicators && carouselIndicators.appendChild(indicator);

            // Create carousel item
            const carouselItem = document.createElement('div');
            carouselItem.classList.add('carousel-item');
            if (index === 0) carouselItem.classList.add('active');

            const img = document.createElement('img');
            img.classList.add('d-block', 'w-100');
            img.src = slide.src;
            carouselItem.appendChild(img);

            carouselInner && carouselInner.appendChild(carouselItem);
        });

        // Call updateCarousel function to set the first slide
        const indicators = document.querySelectorAll('.indicator');
        const slides = document.querySelectorAll('.carousel-item');

        function setActiveSlide() {
            // Update the active class on slides
            slides.forEach((slide, index) => {
                slide.classList.toggle("active", index === currentSlide);
            });

            // Update the active class on indicators
            indicators.forEach((indicator, index) => {
                indicator.classList.toggle("active", index === currentSlide);
            });

            // Move carousel
            const offset = -currentSlide * 100;
            document.querySelector(".carousel-inner").style.transform = `translateX(${offset}%)`;

            // Update title and description with multilingual support
            const currentSlideTitle = slideData[currentSlide].titles;
            const currentSlideDescription = slideData[currentSlide].descriptions;

            const titleText = currentSlideTitle[currentLocale] || currentSlideTitle["en"];
            const descriptionText = currentSlideDescription[currentLocale] || currentSlideDescription["en"];

            document.getElementById("descriptionTitle").textContent = titleText;
            document.getElementById("descriptionText").textContent = descriptionText;

            // Display the modal container
            document.querySelector(".box-modal-container").style.display = "block";
        }

        // Set up click event for indicators
        indicators.forEach((indicator, index) => {
            indicator.addEventListener("click", () => {
                currentSlide = index;
                setActiveSlide();
            });
        });

        // Initial update when the data is ready
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

    // Function to open the modal and show the image
    function openModal(fileSrc, title = '', description = '', type = ModalType.IMAGE, enableComments = false, selectedId = null, options = {}) {
        currentSelectedId = selectedId;
        const keepImageGallery = Boolean(options && options.keepImageGallery);
        var boxModalContainer = document.querySelector(".box-modal-container");
        var modalImage = document.getElementById("modalImage");
        var modalVideo = document.getElementById("modalVideo");
        var caption = document.getElementById("caption");
        var imageModal = document.getElementById("imageModal");
        imageModal.style.display = "flex";
        const adminFloadtBtn = document.querySelector(".admin-float-btn");
        let isImageView = false;

        if (!keepImageGallery) {
            clearImageGalleryNav();
        }

        if (type == ModalType.BOX) {
            boxModalContainer.style.display = "block";
            modalImage.style.display = "none";
            modalVideo.style.display = "none";
            caption.style.display = "none";
            isImageView = false;
        } else {
            boxModalContainer.style.display = "none";
            if (isVideoFile(fileSrc)) {
                pauseAllVideos();
                modalImage.style.display = "none";
                modalVideo.style.display = "block";
                modalImage.src = "";
                modalVideo.src = fileSrc;

                // Force autoplay
                modalVideo.muted = true;      // required for autoplay
                modalVideo.autoplay = true;
                modalVideo.play().catch(err => {
                    console.warn("Autoplay failed:", err);
                });
                isImageView = false;
            } else {
                modalVideo.style.display = "none";
                modalImage.style.display = "block";
                modalVideo.src = "";
                modalImage.src = fileSrc;
                isImageView = true;
            }

            caption.style.display = "block";

            caption.innerHTML = "";
            if (title && title.trim() !== "") {
                caption.innerHTML += "<h3>" + title + "</h3>";
            }

            if (description && description.trim() !== "") {
                caption.innerHTML += "<p>" + description + "</p>";
            }
        }

        // Show or hide comment section
        const isMobile = window.innerWidth <= 768;
        const commentSection = document.querySelector(".comment-section");
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (enableComments) {
            commentSection.style.display = isMobile ? "block" : "flex";
            modalContentContainer.style.width = isMobile ? "100%" : "50%";
            currentCommentPage = 1;
            loadComments(selectedId, currentCommentPage, false, true);
        } else {
            commentSection.style.display = "none";
            modalContentContainer.style.width = "100%";
        }

        adminFloadtBtn && (adminFloadtBtn.style.display = "none");
        closeCommentEmojiPicker();
        syncImageGalleryNav(isImageView);
    }

    // Function to close the modal
    function closeModal() {
        const adminFloadtBtn = document.querySelector(".admin-float-btn");
        document.getElementById("imageModal").style.display = "none";
        document.querySelector(".box-modal-container").style.display = "none";
        adminFloadtBtn && (adminFloadtBtn.style.display = "flex");
        pauseAllVideos();
        closeCommentEmojiPicker();
        clearImageGalleryNav();
    }

    // ---------------- Comments ----------------
    async function loadComments(selectedId, page = 1, prependOlder = false, initial = false) {
        const commentList = document.querySelector(".comment-list");
        const commentSection = document.querySelector(".comment-section");

        if (initial) commentList.innerHTML = '';

        // Save current scroll position if prepending older comments
        let previousScrollHeight = 0;
        let previousScrollTop = 0;
        if (prependOlder) {
            previousScrollHeight = commentList.scrollHeight;
            previousScrollTop = commentList.scrollTop;
        }

        // “Load Previous” button logic
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

            // Backend sends newest first, so reverse for UI (oldest → newest)
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
        const likedClass = comment.is_liked ? "liked" : "";

        div.innerHTML = `
            <img src="/static/images/user.webp" />
            <div class="comment-content">
                <p class="comment-author">${escapeHTML(comment.author_name)}</p>
                <p class="comment-text">${escapeHTML(comment.text)}</p>
                <div class="comment-meta">
                    <u>${new Date(comment.created_at).toLocaleString()}</u>
                    <u class="like-btn ${likedClass}">${tm("commentLike", "Like")}</u>
                    <span class="like-count">${comment.liked_ips ? comment.liked_ips.length : 0}</span>
                </div>
            </div>
        `;

        const likeBtn = div.querySelector('.like-btn');
        likeBtn.addEventListener('click', () => toggleCommentLike(likeBtn, comment._id));

        return div;
    }

    async function submitComment() {
        const commentList = document.querySelector(".comment-list");
        const commentBox = document.getElementById("commentBox");
        const text = commentBox.value.trim();

        if (!text || !currentSelectedId) return;
        if (text.length > MAX_COMMENT_LENGTH) {
            alert(
                tm(
                    "commentTooLong",
                    "Comment cannot exceed {max} characters.",
                    { max: MAX_COMMENT_LENGTH }
                )
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
                author_name: tm("commentAuthorYou", "You"),
                text,
                liked_ips: [],
                created_at: new Date(),
            };
            const div = renderComment(newComment);
            document.querySelector(".comment-list").appendChild(div);

            // Update count
            document.getElementById("commentCount").textContent =
                Number(document.getElementById("commentCount").textContent) + 1;

            commentBox.value = "";

            // 🧷 Auto-scroll to bottom smoothly
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

        document.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            if (target.closest(".comment-input-field")) return;
            closeCommentEmojiPicker();
        });
    }

    // Call after DOM is ready (or immediately if already ready)
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCommentBox);
    } else {
        initCommentBox();
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
}

