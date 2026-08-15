import { GalleryLikeService } from "../services/GalleryLikeService.js";

const galleryLikeService = new GalleryLikeService();

// Format large numbers (1k+, 1.2M+, etc.)
const galleryPageI18n = window.galleryPageI18n || {};
const tg = (key, fallback) => galleryPageI18n[key] || fallback;

function formatNumber(num) {
    if (num >= 1_000_000) {
        return (num / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M+";
    }
    if (num >= 1000) {
        return Math.floor(num / 1000) + "k+";
    }
    return num.toString();
}

function normalizeShareUrl(rawUrl) {
    if (!rawUrl) return window.location.href;

    try {
        return new URL(rawUrl, window.location.origin).href;
    } catch {
        return window.location.href;
    }
}

function setShareButtonState(button, labelText) {
    const label = button?.querySelector(".action-state-label");
    if (label) {
        label.textContent = labelText;
    }
}

async function shareGalleryItem(button) {
    if (!button) return;

    const title =
        button.getAttribute("data-share-title") ||
        tg("shareDefaultTitle", "Gallery");
    const text =
        button.getAttribute("data-share-text") ||
        tg("shareDefaultText", "Check out this gallery item.");
    const url = normalizeShareUrl(button.getAttribute("data-share-url"));

    try {
        if (navigator.share) {
            await navigator.share({ title, text, url });
            setShareButtonState(button, tg("shareStateShared", "Shared"));
            setTimeout(
                () => setShareButtonState(button, tg("shareStateShare", "Share")),
                1200
            );
            return;
        }

        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(url);
            setShareButtonState(button, tg("shareStateCopied", "Copied"));
            setTimeout(
                () => setShareButtonState(button, tg("shareStateShare", "Share")),
                1200
            );
            return;
        }

        window.prompt(tg("sharePromptCopyLink", "Copy this link:"), url);
    } catch (error) {
        if (error?.name === "AbortError") return;
        console.error("Share failed:", error);
        setShareButtonState(button, tg("shareStateError", "Error"));
        setTimeout(
            () => setShareButtonState(button, tg("shareStateShare", "Share")),
            1200
        );
    }
}

function updateCountUI(buttonElement, data) {
    if (!buttonElement || !data) return;

    const cardRoot = buttonElement.closest(".gallery-item");
    const likeCountEl = cardRoot?.querySelector(".gallery-count-badge .like-count");
    const icon = buttonElement.querySelector("ion-icon");
    const commentCountEl = cardRoot?.querySelector(".gallery-count-badge .comment-count");
    const likeBadge = cardRoot?.querySelector(".gallery-count-badge--like");

    if (likeCountEl) {
        likeCountEl.setAttribute("data-raw", data.like_counts ?? 0);
        likeCountEl.textContent = formatNumber(data.like_counts ?? 0);
    }

    if (commentCountEl) {
        commentCountEl.setAttribute("data-raw", data.comment_counts ?? 0);
        commentCountEl.textContent = formatNumber(data.comment_counts ?? 0);
    }

    buttonElement.classList.toggle("liked", Boolean(data.is_liked));
    if (likeBadge) {
        likeBadge.classList.toggle("is-active", Boolean(data.is_liked));
    }
    if (icon) {
        icon.setAttribute("name", data.is_liked ? "heart" : "heart-outline");
    }
}

function spawnHeartEffect(cardRoot, button) {
    const rect = button.getBoundingClientRect();
    const cardRect = cardRoot.getBoundingClientRect();
    const heartX = rect.left + rect.width / 2 - cardRect.left;
    const heartY = rect.top + rect.height / 2 - cardRect.top;

    for (let i = 0; i < 6; i++) {
        const heart = document.createElement("div");
        heart.className = "heart-particle";
        heart.innerHTML = `<ion-icon name="heart"></ion-icon>`;
        heart.style.cssText = `
            position: absolute;
            left: ${heartX}px;
            top: ${heartY}px;
            color: #fb7299;
            font-size: ${10 + Math.random() * 10}px;
            pointer-events: none;
            z-index: 100;
            animation: heartBurst 0.7s ease-out forwards;
            --tx: ${(Math.random() - 0.5) * 120}px;
            --ty: ${-30 - Math.random() * 80}px;
        `;
        cardRoot.appendChild(heart);
        setTimeout(() => heart.remove(), 700);
    }
}

async function toggleLike(button, galleryId) {
    const icon = button.querySelector("ion-icon");
    const cardRoot = button.closest(".gallery-item");
    const countElement = cardRoot?.querySelector(".gallery-count-badge .like-count");
    let count = parseInt(countElement?.getAttribute("data-raw") || "0", 10);
    const likeBadge = cardRoot?.querySelector(".gallery-count-badge--like");

    const wasLiked = button.classList.contains("liked");
    const isLiked = !wasLiked;

    if (isLiked) {
        button.classList.add("liked");
        spawnHeartEffect(cardRoot, button);
    } else {
        button.classList.remove("liked");
    }

    if (likeBadge) {
        likeBadge.classList.toggle("is-active", isLiked);
    }

    const newCount = isLiked ? count + 1 : Math.max(0, count - 1);
    if (countElement) {
        countElement.setAttribute("data-raw", newCount);
        countElement.textContent = formatNumber(newCount);
    }

    if (icon) {
        icon.setAttribute("name", isLiked ? "heart" : "heart-outline");
    }

    try {
        const data = await galleryLikeService.toggleLike(galleryId);
        const liked = data.data.like === true;

        const finalCount = liked ? count + 1 : Math.max(0, count - 1);
        button.classList.toggle("liked", liked);
        if (likeBadge) {
            likeBadge.classList.toggle("is-active", liked);
        }
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
        if (likeBadge) {
            likeBadge.classList.toggle("is-active", wasLiked);
        }
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

    const data = await galleryLikeService.fetchCountsBatch(ids);
    const items = data.items || {};

    likeButtons.forEach(btn => {
        const galleryId = btn.getAttribute("data-gallery-id");
        if (!galleryId || !items[galleryId]) return;
        updateCountUI(btn, items[galleryId]);
    });
}

async function fetchLikeCount(galleryId, btnElement) {
    try {
        const data = await galleryLikeService.fetchCounts(galleryId);

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

function hideMediaSkeleton(skeleton) {
    if (!skeleton || skeleton.classList.contains("is-hidden")) return;
    skeleton.classList.add("is-hidden");
    setTimeout(() => skeleton.remove(), 400);
}

function setupMediaSkeletons() {
    document.querySelectorAll(".gallery-frame").forEach(frame => {
        const skeleton = frame.querySelector(".media-skeleton");
        const img = frame.querySelector(".gallery-image");
        if (!skeleton || !img) return;

        if (img.complete && img.naturalWidth > 0) {
            hideMediaSkeleton(skeleton);
            return;
        }

        const hide = () => hideMediaSkeleton(skeleton);
        img.addEventListener("load", hide);
        img.addEventListener("error", hide);
    });
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
    setupMediaSkeletons();
    optimizeGalleryRendering();
    bootstrapGalleryCounts();
});

window.toggleLike = toggleLike;
window.shareGalleryItem = shareGalleryItem;
