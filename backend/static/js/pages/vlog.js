// Format large numbers (1k+, 1.2M+, etc.)
function formatNumber(num) {
    if (num >= 1_000_000) {
        return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M+';
    }
    if (num >= 1000) {
        return Math.floor(num / 1000) + 'k+';
    }
    return num.toString();
}

async function toggleLike(button, vlogId) {
    const icon = button.querySelector("ion-icon");
    const countElement = button.querySelector(".like-count");
    let count = parseInt(countElement.getAttribute("data-raw") || "0");

    // Optimistic UI update
    const wasLiked = button.classList.contains("liked");
    button.classList.toggle("liked");
    const isLiked = !wasLiked;

    const newCount = isLiked ? count + 1 : Math.max(0, count - 1);
    countElement.setAttribute("data-raw", newCount);
    countElement.textContent = formatNumber(newCount);

    icon.setAttribute("name", isLiked ? "heart" : "heart-outline");

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

        // Sync with backend
        const finalCount = liked ? count + 1 : Math.max(0, count - 1);
        button.classList.toggle("liked", liked);
        countElement.setAttribute("data-raw", finalCount);
        countElement.textContent = formatNumber(finalCount);

        icon.setAttribute("name", liked ? "heart" : "heart-outline");

    } catch (error) {
        console.error("❌ Toggle failed:", error);

        // Rollback UI on failure
        button.classList.toggle("liked", wasLiked);
        countElement.setAttribute("data-raw", count);
        countElement.textContent = formatNumber(count);

        icon.setAttribute("name", wasLiked ? "heart" : "heart-outline");
    }
}

async function fetchLikeCount(vlogId, btnElement) {
    try {
        const response = await fetch(`/api/vlog-like/counts?vlog_id=${vlogId}`);
        const data = await response.json();

        const rawCount = data.like_counts;

        const likeCountEl = btnElement.querySelector(".like-count");
        likeCountEl.setAttribute("data-raw", rawCount);
        likeCountEl.textContent = formatNumber(rawCount);

        // --- COMMENT COUNT ---
        const rawCommentCount = data.comment_counts;
        const commentBtn = btnElement.parentElement.querySelector(".comment-btn");
        const commentCountEl = commentBtn.querySelector(".comment-count");

        commentCountEl.setAttribute("data-raw", rawCommentCount);
        commentCountEl.textContent = formatNumber(rawCommentCount);

        // Visual liked state
        btnElement.classList.toggle("liked", data.is_liked);

    } catch (err) {
        console.error("Error fetching like count:", err);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const players = Array.from(document.querySelectorAll('.player')).map((player) => new Plyr(player));

    players.forEach((player, index, playerList) => {
        player.on('play', () => {
            playerList.forEach((otherPlayer, otherIndex) => {
                if (otherIndex !== index && !otherPlayer.paused) {
                    otherPlayer.pause();
                }
            });
        });
    });

    const likeButtons = document.querySelectorAll(".like-btn");
    likeButtons.forEach(btn => {
        const vlogId = btn.getAttribute("onclick").match(/'([^']+)'/)[1];
        fetchLikeCount(vlogId, btn);
    });
});