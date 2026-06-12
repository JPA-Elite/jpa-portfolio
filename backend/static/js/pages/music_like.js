(function() {
    var list = document.getElementById("musicList") || document.querySelector(".music-list-items");
    function initVotes() {
        var btns = document.querySelectorAll(".vote-btn");
        if (!btns.length) return;
        var ids = [];
        btns.forEach(function(b) {
            b.removeEventListener("click", handleVote);
            b.addEventListener("click", handleVote);
            var mid = b.dataset.musicId;
            if (mid && ids.indexOf(mid) === -1) ids.push(mid);
        });
        if (!ids.length) return;
        fetch("/api/music-like/counts/batch?music_ids=" + encodeURIComponent(ids.join(",")))
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var items = d.items || {};
                Object.entries(items).forEach(function(entry) {
                    var id = entry[0], data = entry[1];
                    document.querySelectorAll('.like-btn[data-music-id="' + id + '"]').forEach(function(b) {
                        var c = b.querySelector(".vote-count");
                        if (c) c.textContent = data.like_counts || 0;
                        b.classList.toggle("voted", data.user_vote === true);
                    });
                    document.querySelectorAll('.dislike-btn[data-music-id="' + id + '"]').forEach(function(b) {
                        var c = b.querySelector(".vote-count");
                        if (c) c.textContent = data.dislike_counts || 0;
                        b.classList.toggle("voted", data.user_vote === false);
                    });
                });
            })
            .catch(function() {});
    }
    function handleVote(e) {
        var btn = e.currentTarget;
        var musicId = btn.dataset.musicId;
        var isLike = btn.dataset.vote === "1";
        var parent = btn.parentElement;
        var likeBtn = parent.querySelector(".like-btn");
        var dislikeBtn = parent.querySelector(".dislike-btn");
        fetch("/api/music-like/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ music_id: musicId, is_like: isLike })
        })
        .then(function(r) { return r.json(); })
        .then(function() {
            var params = new URLSearchParams();
            params.set("music_id", musicId);
            fetch("/api/music-like/counts?" + params)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    var lc = likeBtn.querySelector(".vote-count");
                    var dc = dislikeBtn.querySelector(".vote-count");
                    if (lc) lc.textContent = data.like_counts || 0;
                    if (dc) dc.textContent = data.dislike_counts || 0;
                    likeBtn.classList.toggle("voted", data.user_vote === true);
                    dislikeBtn.classList.toggle("voted", data.user_vote === false);
                })
                .catch(function() {});
        })
        .catch(function() {});
    }
    if (list) {
        new MutationObserver(function() { setTimeout(initVotes, 100); }).observe(list, { childList: true, subtree: true });
    }
    document.addEventListener("DOMContentLoaded", function() { setTimeout(initVotes, 600); });
    setTimeout(initVotes, 1000);
})();
