const ModalType = {
    IMAGE: 'imageModal',
    BOX: 'boxModal'
};
let currentSlide = 0;
const currentLocale = "{{ get_locale() }}";
let slideData = [];
let currentGalleryId = null;

fetch("/static/json/project.json")
    .then(response => response.json())
    .then(data => {
        slideData = data;
        updateCarousel();
    })
    .catch(error => {
        console.error('Error fetching slide data:', error);
    });

const carouselIndicators = document.getElementById('carouselIndicators');
const carouselInner = document.getElementById('carouselInner');
const adminFloadtBtn = document.querySelector(".admin-float-btn");

function updateCarousel() {
    carouselIndicators.innerHTML = '';
    carouselInner.innerHTML = '';

    slideData.forEach((slide, index) => {
        // Create indicator
        const indicator = document.createElement('span');
        indicator.classList.add('indicator');
        indicator.dataset.slideTo = index;
        if (index === 0) indicator.classList.add('active');
        carouselIndicators.appendChild(indicator);

        // Create carousel item
        const carouselItem = document.createElement('div');
        carouselItem.classList.add('carousel-item');
        if (index === 0) carouselItem.classList.add('active');

        const img = document.createElement('img');
        img.classList.add('d-block', 'w-100');
        img.src = slide.src;
        carouselItem.appendChild(img);

        carouselInner.appendChild(carouselItem);
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
function openModal(imageSrc, title = '', description = '', type = ModalType.IMAGE, enableComments = false, galleryId=null) {
    currentGalleryId = galleryId;
    var boxModalContainer = document.querySelector(".box-modal-container");
    var modalImage = document.getElementById("modalImage");
    var caption = document.getElementById("caption");
    var imageModal = document.getElementById("imageModal");
    imageModal.style.display = "flex";

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
        loadComments(galleryId);
    } else {
        commentSection.style.display = "none";
        modalContentContainer.style.width = "100%";
    }

    adminFloadtBtn.style.display = "none";
}

// Function to close the modal
function closeModal() {
    document.getElementById("imageModal").style.display = "none";
    document.querySelector(".box-modal-container").style.display = "none";
    adminFloadtBtn.style.display = "flex";
}

const commentBox = document.getElementById("commentBox");
const commentList = document.querySelector(".comment-list");
const commentCount = document.getElementById("commentCount");
const MAX_COMMENT_LENGTH = 1000;

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

// ---------------- Comments ----------------
async function loadComments(galleryId) {
    const commentList = document.querySelector(".comment-list");
    commentList.innerHTML = "";
    try {
        const res = await fetch(`/api/gallery-comments?gallery_id=${galleryId}`);
        const comments = await res.json();

        if (!comments || comments.length === 0) {
            // Display a "No comments" message
            const emptyDiv = document.createElement("div");
            emptyDiv.classList.add("no-comments");
            emptyDiv.textContent = "No comments yet.";
            commentList.appendChild(emptyDiv);

            document.getElementById("commentCount").textContent = 0;
            return;
        }

        comments.forEach(renderComment);
        document.getElementById("commentCount").textContent = comments.length;
    } catch(err) {
        console.error(err);
        // Optional: show error message
        const emptyDiv = document.createElement("div");
        emptyDiv.classList.add("no-comments");
        emptyDiv.textContent = "Failed to load comments.";
        commentList.appendChild(emptyDiv);
    }
}

function renderComment(comment) {
    const commentList = document.querySelector(".comment-list");
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
                <u class="like-btn ${likedClass}" onclick="toggleCommentLike(this, '${comment._id}')">Like</u>
                <span class="like-count">${comment.liked_ips ? comment.liked_ips.length : 0}</span>
            </div>
        </div>
    `;
    commentList.appendChild(div);
}

async function submitComment() {
    const box = document.getElementById("commentBox");
    const text = box.value.trim();

    if(!text || !currentGalleryId) return;
    if (text.length > MAX_COMMENT_LENGTH) {
        alert(`Comment cannot exceed ${MAX_COMMENT_LENGTH} characters.`);
        return;
    }

    box.disabled = true;

    try {
        const res = await fetch("/api/gallery-comments", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ gallery_id: currentGalleryId, author_name:"You", text })
        });
        const data = await res.json();

        const noCommentsDiv = document.querySelector(".no-comments");
        if (noCommentsDiv) noCommentsDiv.remove();

        renderComment({ _id: data.comment_id, author_name:"You", text, liked_ips:[], like_count:0, created_at:new Date() });
        box.value = "";
        document.getElementById("commentCount").textContent = Number(document.getElementById("commentCount").textContent)+1;
    } catch(err) {
        console.error(err);
    } finally {
        box.disabled = false;
        box.focus();
    }
}

// Toggle IP-based like
async function toggleCommentLike(button, commentId) {
    const countSpan = button.nextElementSibling;
    try {
        const res = await fetch("/api/gallery-comments/like", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ comment_id: commentId })
        });
        const data = await res.json();
        if (data.liked !== undefined && data.like_count !== undefined) {
            button.classList.toggle("liked", data.liked);
            countSpan.textContent = data.like_count;
        }
    } catch(err) { console.error(err); }
}