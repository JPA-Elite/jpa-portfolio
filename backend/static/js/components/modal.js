if (!window.__modal_js_loaded__) {
    window.__modal_js_loaded__ = true;
    const ModalType = {
        IMAGE: 'imageModal',
        BOX: 'boxModal'
    };
    let currentSlide = 0;
    const currentLocale = "{{ get_locale() }}";
    const baseUrl = window.baseUrl;
    let slideData = [];
    let currentGalleryId = null;
    let currentCommentPage = 1;
    const COMMENTS_PER_PAGE = 100;
    const MAX_COMMENT_LENGTH = 1000;

    fetch("/static/json/project.json")
        .then(response => response.json())
        .then(data => {
            slideData = data;
            updateCarousel();
        })
        .catch(error => {
            console.error('Error fetching slide data:', error);
        });


    function updateCarousel() {
        const carouselInner = document.getElementById('carouselInner');
        const carouselIndicators = document.getElementById('carouselIndicators');
        carouselIndicators && (carouselIndicators.innerHTML = '');
        carouselInner && (carouselInner.innerHTML = '');

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
        currentSlide = (currentSlide + direction + slideData.length) % slideData.length;
        updateCarousel();
    }

    // Function to open the modal and show the image
    function openModal(imageSrc, title = '', description = '', type = ModalType.IMAGE, enableComments = false, galleryId = null) {
        currentGalleryId = galleryId;
        var boxModalContainer = document.querySelector(".box-modal-container");
        var modalImage = document.getElementById("modalImage");
        var caption = document.getElementById("caption");
        var imageModal = document.getElementById("imageModal");
        imageModal.style.display = "flex";
        const adminFloadtBtn = document.querySelector(".admin-float-btn");

        if (type == ModalType.BOX) {
            boxModalContainer.style.display = "block";
            modalImage.style.display = "none";
            caption.style.display = "none";
        } else {
            boxModalContainer.style.display = "none";
            modalImage.style.display = "flex";
            caption.style.display = "block";
            document.getElementById("modalImage").src = imageSrc;

            // Create a caption element
            const captionElement = document.getElementById("caption");

            // Set title if available
            captionElement.innerHTML = ""; // Clear previous content
            if (title && title.trim() !== "") {
                captionElement.innerHTML += "<h3>" + title + "</h3>";
            }

            // Set description if available
            if (description && description.trim() !== "") {
                captionElement.innerHTML += "<p>" + description + "</p>";
            }
        }

        // Show or hide comment section
        const isMobile = window.innerWidth <= 900;
        const commentSection = document.querySelector(".comment-section");
        const modalContentContainer = document.querySelector(".modal-content-container");
        if (enableComments) {
            commentSection.style.display = isMobile ? "block" : "flex";
            modalContentContainer.style.width = isMobile ? "100%" : "50%";
            currentCommentPage = 1;
            loadComments(galleryId, currentCommentPage, false, true);
        } else {
            commentSection.style.display = "none";
            modalContentContainer.style.width = "100%";
        }

        adminFloadtBtn && (adminFloadtBtn.style.display = "none");
    }

    // Function to close the modal
    function closeModal() {
        const adminFloadtBtn = document.querySelector(".admin-float-btn");
        document.getElementById("imageModal").style.display = "none";
        document.querySelector(".box-modal-container").style.display = "none";
        adminFloadtBtn && (adminFloadtBtn.style.display = "flex");
    }

    // ---------------- Comments ----------------
    async function loadComments(galleryId, page = 1, prependOlder = false, initial = false) {
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
            prevBtn.textContent = "Previous";
            prevBtn.classList.add("prev-comments-btn");
            commentSection.insertBefore(prevBtn, commentList);
        }

        try {
            prevBtn.disabled = true;
            prevBtn.textContent = "Loading...";

            const res = await fetch(`/api/${baseUrl}?gallery_id=${galleryId}&page=${page}&limit=${COMMENTS_PER_PAGE}`);
            const data = await res.json();

            const comments = data.comments || [];
            const totalComments = data.total || 0;
            const totalPages = Math.ceil(totalComments / COMMENTS_PER_PAGE);

            if (!prependOlder && comments.length === 0) {
                const emptyDiv = document.createElement("div");
                emptyDiv.classList.add("no-comments");
                emptyDiv.textContent = "No comments yet.";
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
                loadComments(galleryId, currentCommentPage, true);
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
            emptyDiv.textContent = "Failed to load comments.";
            commentList.appendChild(emptyDiv);
        } finally {
            // spinner.style.display = "none";
            prevBtn.disabled = false;
            prevBtn.textContent = "Previous";
        }
    }


    function renderComment(comment) {
        const div = document.createElement("div");
        div.classList.add("comment-item");
        div.dataset.commentId = comment._id;
        const likedClass = comment.is_liked ? "liked" : "";

        div.innerHTML = `
            <img src="/static/images/user.webp" />
            <div class="comment-content">
                <p class="comment-author">${comment.author_name}</p>
                <p class="comment-text">${comment.text}</p>
                <div class="comment-meta">
                    <u>${new Date(comment.created_at).toLocaleString()}</u>
                    <u class="like-btn ${likedClass}">Like</u>
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

        if (!text || !currentGalleryId) return;
        if (text.length > MAX_COMMENT_LENGTH) {
            alert(`Comment cannot exceed ${MAX_COMMENT_LENGTH} characters.`);
            return;
        }

        commentBox.disabled = true;

        try {
            const res = await fetch(`/api/${baseUrl}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ gallery_id: currentGalleryId, author_name: "You", text }),
            });

            const data = await res.json();
            const noCommentsDiv = document.querySelector(".no-comments");
            if (noCommentsDiv) noCommentsDiv.remove();

            // Create and append the new comment directly at the bottom
            const newComment = {
                _id: data.comment_id,
                author_name: "You",
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
    }

    // Call after DOM is ready
    document.addEventListener("DOMContentLoaded", initCommentBox);


    // expose needed functions globally
    window.submitComment = submitComment;
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.toggleCommentLike = toggleCommentLike;
    window.moveSlide = moveSlide;
    window.loadComments = loadComments;
}

