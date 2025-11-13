async function toggleLike(button, galleryId) {
    const icon = button.querySelector("ion-icon");
    const countElement = button.querySelector(".like-count");
    let count = parseInt(countElement.textContent);

    // Optimistic toggle (instant feedback)
    button.classList.toggle("liked");
    const isLiked = button.classList.contains("liked");
    icon.setAttribute("name", isLiked ? "heart" : "heart-outline");
    countElement.textContent = isLiked ? count + 1 : Math.max(0, count - 1);

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
        console.log("✅ Like toggled:", data);

        // Sync UI with backend result
        const liked = data.data.like === true;
        button.classList.toggle("liked", liked);
        icon.setAttribute("name", liked ? "heart" : "heart-outline");
        countElement.textContent = liked ? count + 1 : Math.max(0, count - 1);

    } catch (error) {
        console.error("❌ Toggle failed:", error);

        // Rollback UI on failure
        button.classList.toggle("liked");
        const revertedLiked = button.classList.contains("liked");
        icon.setAttribute("name", revertedLiked ? "heart" : "heart-outline");
        countElement.textContent = revertedLiked ? count + 1 : Math.max(0, count - 1);
    }
}

async function fetchLikeCount(galleryId, btnElement) {
    try {
        const response = await fetch(`/api/gallery-like/counts?gallery_id=${galleryId}`);
        const data = await response.json();

        // Update like count
        const likeCountEl = btnElement.querySelector(".like-count");
        likeCountEl.textContent = data.like_counts;

        // Toggle liked state visually
        if (data.is_liked) {
            btnElement.classList.add("liked");
        } else {
            btnElement.classList.remove("liked");
        }
    } catch (err) {
        console.error("Error fetching like count:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const likeButtons = document.querySelectorAll(".like-btn");
    likeButtons.forEach(btn => {
        const galleryId = btn.getAttribute("onclick").match(/'([^']+)'/)[1];
        fetchLikeCount(galleryId, btn);
    });
});