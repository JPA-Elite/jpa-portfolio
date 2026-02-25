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

async function shareVlogItem(button) {
    if (!button) return;

    const title = button.getAttribute("data-share-title") || "Vlog";
    const text = button.getAttribute("data-share-text") || "Check out this vlog.";
    const url = normalizeShareUrl(button.getAttribute("data-share-url"));

    try {
        if (navigator.share) {
            await navigator.share({ title, text, url });
            setShareButtonState(button, "Shared");
            setTimeout(() => setShareButtonState(button, "Share"), 1200);
            return;
        }

        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(url);
            setShareButtonState(button, "Copied");
            setTimeout(() => setShareButtonState(button, "Share"), 1200);
            return;
        }

        window.prompt("Copy this link:", url);
    } catch (error) {
        if (error?.name === "AbortError") return;
        console.error("Share failed:", error);
        setShareButtonState(button, "Error");
        setTimeout(() => setShareButtonState(button, "Share"), 1200);
    }
}

function updateCountUI(buttonElement, data) {
    if (!buttonElement || !data) return;

    const cardRoot = buttonElement.closest(".video-item");
    const likeCountEl = cardRoot?.querySelector(".video-count-badge .like-count");
    const icon = buttonElement.querySelector("ion-icon");
    const commentCountEl = cardRoot?.querySelector(".video-count-badge .comment-count");
    const likeBadge = cardRoot?.querySelector(".video-count-badge--like");

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

async function toggleLike(button, vlogId) {
    const icon = button.querySelector("ion-icon");
    const cardRoot = button.closest(".video-item");
    const countElement = cardRoot?.querySelector(".video-count-badge .like-count");
    const count = parseInt(countElement?.getAttribute("data-raw") || "0", 10);

    const wasLiked = button.classList.contains("liked");
    const isLiked = !wasLiked;
    const optimisticCount = isLiked ? count + 1 : Math.max(0, count - 1);
    const likeBadge = cardRoot?.querySelector(".video-count-badge--like");

    button.classList.toggle("liked", isLiked);
    if (likeBadge) {
        likeBadge.classList.toggle("is-active", isLiked);
    }

    if (countElement) {
        countElement.setAttribute("data-raw", optimisticCount);
        countElement.textContent = formatNumber(optimisticCount);
    }

    if (icon) {
        icon.setAttribute("name", isLiked ? "heart" : "heart-outline");
    }

    try {
        const formData = new FormData();
        formData.append("vlog_id", JSON.stringify(vlogId));

        const response = await fetch("/api/vlog-like", {
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

async function fetchVlogCountsBatch(likeButtons) {
    const ids = likeButtons
        .map((btn) => btn.getAttribute("data-vlog-id"))
        .filter(Boolean);

    if (!ids.length) return;

    const params = new URLSearchParams();
    params.set("vlog_ids", ids.join(","));

    const response = await fetch(`/api/vlog-like/counts/batch?${params.toString()}`);
    if (!response.ok) {
        throw new Error("Failed to load vlog counts");
    }

    const data = await response.json();
    const items = data.items || {};

    likeButtons.forEach((btn) => {
        const vlogId = btn.getAttribute("data-vlog-id");
        if (!vlogId || !items[vlogId]) return;
        updateCountUI(btn, items[vlogId]);
    });
}

async function fetchLikeCount(vlogId, btnElement) {
    try {
        const response = await fetch(`/api/vlog-like/counts?vlog_id=${encodeURIComponent(vlogId)}`);
        const data = await response.json();

        updateCountUI(btnElement, {
            like_counts: data.like_counts,
            comment_counts: data.comment_counts,
            is_liked: data.is_liked,
        });
    } catch (err) {
        console.error("Error fetching vlog count:", err);
    }
}

async function bootstrapVlogCounts() {
    const likeButtons = Array.from(document.querySelectorAll(".like-btn"));
    if (!likeButtons.length) return;

    try {
        await fetchVlogCountsBatch(likeButtons);
    } catch (error) {
        console.warn("Batch count fetch failed, falling back to per-item requests.", error);

        likeButtons.forEach((btn) => {
            const vlogId = btn.getAttribute("data-vlog-id");
            if (!vlogId) return;
            fetchLikeCount(vlogId, btn);
        });
    }
}

function setupPlyrPlayers() {
    if (typeof Plyr === "undefined") return;

    const videoElements = Array.from(document.querySelectorAll(".player"));
    if (!videoElements.length) return;

    const playerMap = new Map();

    const pauseOthers = (activePlayer) => {
        playerMap.forEach((player) => {
            if (player !== activePlayer && player.playing) {
                player.pause();
            }
        });
    };

    const initPlayer = (videoElement) => {
        if (!videoElement || playerMap.has(videoElement)) {
            return playerMap.get(videoElement);
        }

        const player = new Plyr(videoElement);
        player.on("play", () => pauseOthers(player));
        playerMap.set(videoElement, player);
        return player;
    };

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    initPlayer(entry.target);
                    observer.unobserve(entry.target);
                });
            },
            { rootMargin: "200px 0px", threshold: 0.01 }
        );

        videoElements.forEach((videoElement) => observer.observe(videoElement));
        return;
    }

    videoElements.forEach((videoElement) => initPlayer(videoElement));
}

function scheduleCountsBootstrap() {
    if ("requestIdleCallback" in window) {
        requestIdleCallback(() => {
            bootstrapVlogCounts();
        }, { timeout: 1200 });
        return;
    }

    setTimeout(() => {
        bootstrapVlogCounts();
    }, 0);
}

document.addEventListener("DOMContentLoaded", () => {
    setupPlyrPlayers();
    scheduleCountsBootstrap();
});
