import { MusicLikeService } from "../services/MusicLikeService.js";

const musicLikeService = new MusicLikeService();

(function() {
    var list = document.getElementById("musicList") || document.querySelector(".music-list-items");

    var initInFlight = false;
    var initQueued = false;
    var lastInitKey = "";
    var initDebounceTimer = null;

    function getCurrentVoteButtonsKey() {
        // Used to avoid re-syncing counts for the same rendered set.
        var btns = document.querySelectorAll(".vote-btn, .dislike-btn");
        if (!btns || !btns.length) return "";
        var ids = [];
        btns.forEach(function(b) {
            var mid = b.dataset && b.dataset.musicId;
            if (mid) ids.push(String(mid));
        });
        ids.sort();
        // Deduplicate
        var out = [];
        for (var i = 0; i < ids.length; i++) {
            if (ids[i] !== ids[i - 1]) out.push(ids[i]);
        }
        return out.join(",");
    }

    function initVotes() {
        if (initInFlight) {
            initQueued = true;
            return;
        }

        if (!list || !list.isConnected) return;

        var currentKey = getCurrentVoteButtonsKey();
        if (!currentKey) return;
        if (currentKey === lastInitKey) return;

        initInFlight = true;
        initQueued = false;
        lastInitKey = currentKey;

        var btns = document.querySelectorAll(".vote-btn");
        if (!btns.length) {
            initInFlight = false;
            return;
        }

        var ids = [];
        btns.forEach(function(b) {
            var mid = b.dataset.musicId;
            if (mid && ids.indexOf(mid) === -1) ids.push(mid);
        });
        if (!ids.length) {
            initInFlight = false;
            return;
        }

        musicLikeService.fetchCountsBatch(ids)
            .then(function(d) {
                var items = d.items || {};

                // Update counts & voted state, but do it only once per sync.
                // Also store in voteStateCache for when music.js re-renders the list.
                var voteStateCache = window.voteStateCache || {};
                var cacheChanged = false;
                Object.entries(items).forEach(function(entry) {
                    var id = entry[0], data = entry[1];

                    // Store in cache for music.js to use on re-render
                    if (voteStateCache) {
                        voteStateCache[id] = data;
                        cacheChanged = true;
                    }

                    document.querySelectorAll('.like-btn[data-music-id="' + id + '"]')
                        .forEach(function(b) {
                            var c = b.querySelector(".vote-count");
                            if (c) c.textContent = data.like_counts || 0;
                            b.classList.toggle("voted", data.user_vote === true);
                        });

                    document.querySelectorAll('.dislike-btn[data-music-id="' + id + '"]')
                        .forEach(function(b) {
                            var c = b.querySelector(".vote-count");
                            if (c) c.textContent = data.dislike_counts || 0;
                            b.classList.toggle("voted", data.user_vote === false);
                        });
                });
                if (cacheChanged && window.voteStateCache) {
                    window.voteStateCache = voteStateCache;
                }
            })
            .catch(function() {
                // Keep UI stable on failures.
            })
            .finally(function() {
                initInFlight = false;
                if (initQueued) {
                    // If DOM changed during request, sync again once.
                    initVotes();
                }
            });
    }

    function scheduleInitVotes(reason) {
        if (initDebounceTimer) clearTimeout(initDebounceTimer);
        initDebounceTimer = setTimeout(function() {
            initDebounceTimer = null;
            initVotes();
        }, 300);
    }

    function setLoading(btn, loading) {
        var icon = btn.querySelector("ion-icon");
        if (!icon) return;

        if (loading) {
            btn._origIcon = icon.getAttribute("name");
            icon.setAttribute("name", "reload-outline");
            icon.classList.add("vote-btn-spin");
            btn.disabled = true;
        } else {
            if (btn._origIcon) icon.setAttribute("name", btn._origIcon);
            icon.classList.remove("vote-btn-spin");
            btn.disabled = false;
        }
    }

    function handleVote(e) {
        e.stopPropagation();

        var btn = e.currentTarget;
        var musicId = btn.dataset.musicId;
        var isLike = btn.dataset.vote === "1";

        var parent = btn.parentElement;
        var likeBtn = parent.querySelector(".like-btn");
        var dislikeBtn = parent.querySelector(".dislike-btn");

        setLoading(btn, true);

        // Keep immediate UI update path, then refresh counts for this item set.
        musicLikeService.toggleVote(musicId, isLike)
        .then(function() {
            return musicLikeService.fetchCounts(musicId);
        })
        .then(function(data) {
            var lc = likeBtn && likeBtn.querySelector(".vote-count");
            var dc = dislikeBtn && dislikeBtn.querySelector(".vote-count");
            if (lc) lc.textContent = data.like_counts || 0;
            if (dc) dc.textContent = data.dislike_counts || 0;

            if (likeBtn) likeBtn.classList.toggle("voted", data.user_vote === true);
            if (dislikeBtn) dislikeBtn.classList.toggle("voted", data.user_vote === false);

            // Store in voteStateCache so music.js uses cached values on re-render
            var voteStateCache = window.voteStateCache;
            if (voteStateCache && musicId) {
                voteStateCache[musicId] = data;
            }

            // Counts are now correct for the updated item; refresh batch after a short debounce.
            scheduleInitVotes("vote-completed");

            setLoading(btn, false);
        })
        .catch(function() {
            setLoading(btn, false);
        });
    }

    // Attach click handlers once when buttons are present.
    function ensureHandlers() {
        var btns = document.querySelectorAll(".vote-btn");
        if (!btns.length) return;
        btns.forEach(function(b) {
            b.removeEventListener("click", handleVote);
            b.addEventListener("click", handleVote);
        });
    }

    function maybeStartObserver() {
        if (!list) return;

        var obs = new MutationObserver(function() {
            // DOM changes happen on selection/pagination; debounce to avoid flicker.
            ensureHandlers();
            scheduleInitVotes("dom-change");
        });

        obs.observe(list, { childList: true, subtree: true });
    }

    if (list) {
        ensureHandlers();
        maybeStartObserver();
    }

    document.addEventListener("DOMContentLoaded", function() {
        ensureHandlers();
        initVotes();
    });

    // Fallback if script runs after list already rendered.
    setTimeout(function() {
        ensureHandlers();
        scheduleInitVotes("fallback");
    }, 800);
})();
