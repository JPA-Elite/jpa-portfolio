// Format large numbers (1k+, 1.2M+, etc.)
function formatNumber(num) {
    if (num >= 1_000_000) {
        return (num / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M+";
    }
    if (num >= 1000) {
        return Math.floor(num / 1000) + "k+";
    }
    return num.toString();
}

function updateCountUI(buttonElement, data) {
    if (!buttonElement || !data) return;

    const likeCountEl = buttonElement.querySelector(".like-count");
    const icon = buttonElement.querySelector("ion-icon");
    const commentBtn = buttonElement.parentElement?.querySelector(".comment-btn");
    const commentCountEl = commentBtn?.querySelector(".comment-count");

    if (likeCountEl) {
        likeCountEl.setAttribute("data-raw", data.like_counts ?? 0);
        likeCountEl.textContent = formatNumber(data.like_counts ?? 0);
    }

    if (commentCountEl) {
        commentCountEl.setAttribute("data-raw", data.comment_counts ?? 0);
        commentCountEl.textContent = formatNumber(data.comment_counts ?? 0);
    }

    buttonElement.classList.toggle("liked", Boolean(data.is_liked));
    if (icon) {
        icon.setAttribute("name", data.is_liked ? "heart" : "heart-outline");
    }
}

async function toggleLike(button, galleryId) {
    const icon = button.querySelector("ion-icon");
    const countElement = button.querySelector(".like-count");
    let count = parseInt(countElement?.getAttribute("data-raw") || "0", 10);

    const wasLiked = button.classList.contains("liked");
    button.classList.toggle("liked");
    const isLiked = !wasLiked;

    const newCount = isLiked ? count + 1 : Math.max(0, count - 1);
    if (countElement) {
        countElement.setAttribute("data-raw", newCount);
        countElement.textContent = formatNumber(newCount);
    }

    if (icon) {
        icon.setAttribute("name", isLiked ? "heart" : "heart-outline");
    }

    try {
        const formData = new FormData();
        formData.append("gallery_id", JSON.stringify(galleryId));

        const response = await fetch("/api/gallery-like", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Request failed");
        }

        const data = await response.json();
        const liked = data.data.like === true;

        const finalCount = liked ? count + 1 : Math.max(0, count - 1);
        button.classList.toggle("liked", liked);
        if (countElement) {
            countElement.setAttribute("data-raw", finalCount);
            countElement.textContent = formatNumber(finalCount);
        }

        if (icon) {
            icon.setAttribute("name", liked ? "heart" : "heart-outline");
        }
    } catch (error) {
        console.error("Toggle failed:", error);

        button.classList.toggle("liked", wasLiked);
        if (countElement) {
            countElement.setAttribute("data-raw", count);
            countElement.textContent = formatNumber(count);
        }

        if (icon) {
            icon.setAttribute("name", wasLiked ? "heart" : "heart-outline");
        }
    }
}

async function fetchGalleryCountsBatch(likeButtons) {
    const ids = likeButtons
        .map(btn => btn.getAttribute("data-gallery-id"))
        .filter(Boolean);

    if (!ids.length) return;

    const params = new URLSearchParams();
    params.set("gallery_ids", ids.join(","));

    const response = await fetch(`/api/gallery-like/counts/batch?${params.toString()}`);
    if (!response.ok) {
        throw new Error("Failed to load gallery counts");
    }

    const data = await response.json();
    const items = data.items || {};

    likeButtons.forEach(btn => {
        const galleryId = btn.getAttribute("data-gallery-id");
        if (!galleryId || !items[galleryId]) return;
        updateCountUI(btn, items[galleryId]);
    });
}

async function fetchLikeCount(galleryId, btnElement) {
    try {
        const response = await fetch(`/api/gallery-like/counts?gallery_id=${encodeURIComponent(galleryId)}`);
        const data = await response.json();

        updateCountUI(btnElement, {
            like_counts: data.like_counts,
            comment_counts: data.comment_counts,
            is_liked: data.is_liked,
        });
    } catch (err) {
        console.error("Error fetching like count:", err);
    }
}

async function bootstrapGalleryCounts() {
    const likeButtons = Array.from(document.querySelectorAll(".like-btn"));
    if (!likeButtons.length) return;

    try {
        await fetchGalleryCountsBatch(likeButtons);
    } catch (error) {
        console.warn("Batch count fetch failed, falling back to per-item requests.", error);

        // Fallback for older deployments if the batch route is not available yet
        likeButtons.forEach(btn => {
            const galleryId = btn.getAttribute("data-gallery-id");
            if (!galleryId) return;
            fetchLikeCount(galleryId, btn);
        });
    }
}

function optimizeGalleryRendering() {
    const cards = document.querySelectorAll(".gallery-item");
    if (!cards.length) return;

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    entry.target.classList.toggle("is-visible", entry.isIntersecting);
                });
            },
            { rootMargin: "120px 0px", threshold: 0.01 }
        );

        cards.forEach(card => observer.observe(card));
        return;
    }

    cards.forEach(card => card.classList.add("is-visible"));
}

document.addEventListener("DOMContentLoaded", () => {
    optimizeGalleryRendering();
    bootstrapGalleryCounts();
});
