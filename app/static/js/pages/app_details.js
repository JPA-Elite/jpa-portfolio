import { BuiltAppLikeService } from "../services/BuiltAppLikeService.js";

const builtAppLikeService = new BuiltAppLikeService();

(function () {
    function prefersReducedMotion() {
        return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function setupSlideshow(root) {
        var track = root.querySelector("[data-app-slideshow-track]");
        if (!track) return;
        var slides = Array.prototype.slice.call(track.querySelectorAll("[data-app-slide]"));
        if (slides.length < 1) return;
        var section = root.closest("section") || document;
        var prevBtn = root.querySelector("[data-app-slideshow-prev]");
        var nextBtn = root.querySelector("[data-app-slideshow-next]");
        var dotsWrap = section.querySelector("[data-app-slideshow-dots]");
        var countEl = section.querySelector("[data-app-slideshow-count]");
        var activeIndex = 0;
        var activePage = 0;
        var ticking = false;
        var dots = [];

        function getGap() {
            var styles = window.getComputedStyle(track);
            var gap = parseFloat(styles.columnGap || styles.gap || "16");
            return isNaN(gap) ? 16 : gap;
        }

        function getPerView() {
            if (slides.length < 1) return 1;
            var slideWidth = slides[0].getBoundingClientRect().width;
            if (!slideWidth) return 1;
            var per = Math.round((track.clientWidth + getGap()) / (slideWidth + getGap()));
            return Math.max(1, Math.min(slides.length, per));
        }

        function getPageCount() {
            return Math.max(1, Math.ceil(slides.length / getPerView()));
        }

        function slideLeft(index) {
            var slide = slides[index];
            if (!slide) return 0;
            return Math.max(0, slide.offsetLeft - track.offsetLeft);
        }

        function closestIndex() {
            var left = track.scrollLeft;
            var best = 0;
            var bestDist = Number.POSITIVE_INFINITY;
            slides.forEach(function (slide, index) {
                var dist = Math.abs(left - (slide.offsetLeft - track.offsetLeft));
                if (dist < bestDist) {
                    bestDist = dist;
                    best = index;
                }
            });
            return best;
        }

        function buildDots(pageCount) {
            if (!dotsWrap) return;
            dotsWrap.textContent = "";
            dots = [];
            for (var i = 0; i < pageCount; i++) {
                (function (page) {
                    var dot = document.createElement("button");
                    dot.type = "button";
                    dot.className = "app-details__dot";
                    dot.setAttribute("role", "tab");
                    dot.setAttribute("aria-label", String(page + 1) + " / " + String(pageCount));
                    dot.addEventListener("click", function () {
                        scrollToPage(page);
                    });
                    dotsWrap.appendChild(dot);
                    dots.push(dot);
                })(i);
            }
            dotsWrap.hidden = pageCount < 2;
        }

        function render() {
            var perView = getPerView();
            var pageCount = getPageCount();
            activeIndex = Math.max(0, Math.min(slides.length - 1, closestIndex()));
            activePage = Math.max(0, Math.min(pageCount - 1, Math.floor(activeIndex / perView)));
            if (dots.length !== pageCount) buildDots(pageCount);
            slides.forEach(function (slide, index) {
                var inPage = Math.floor(index / perView) === activePage;
                slide.classList.toggle("is-active", inPage);
            });
            dots.forEach(function (dot, index) {
                var isActive = index === activePage;
                dot.classList.toggle("is-active", isActive);
                dot.setAttribute("aria-selected", isActive ? "true" : "false");
                dot.tabIndex = isActive ? 0 : -1;
            });
            if (countEl) countEl.textContent = String(activePage + 1) + " / " + String(pageCount);
            var singlePage = pageCount < 2;
            if (prevBtn) {
                prevBtn.hidden = singlePage;
                prevBtn.disabled = activePage === 0;
            }
            if (nextBtn) {
                nextBtn.hidden = singlePage;
                nextBtn.disabled = activePage >= pageCount - 1;
            }
            if (dotsWrap && pageCount < 2) dotsWrap.hidden = true;
        }

        function scrollToPage(page, behavior) {
            var pageCount = getPageCount();
            var perView = getPerView();
            var targetPage = Math.max(0, Math.min(pageCount - 1, page));
            var targetIndex = Math.max(0, Math.min(slides.length - 1, targetPage * perView));
            var mode = behavior || (prefersReducedMotion() ? "auto" : "smooth");
            track.scrollTo({ left: slideLeft(targetIndex), behavior: mode });
            activeIndex = targetIndex;
            activePage = targetPage;
            window.requestAnimationFrame(render);
        }

        function scrollToIndex(index, behavior) {
            var perView = getPerView();
            scrollToPage(Math.floor(Math.max(0, index) / perView), behavior);
        }

        if (slides.length < 2) {
            if (prevBtn) prevBtn.hidden = true;
            if (nextBtn) nextBtn.hidden = true;
            if (dotsWrap) dotsWrap.hidden = true;
            slides[0].classList.add("is-active");
            if (countEl) countEl.textContent = "1 / 1";
            return;
        }

        buildDots(getPageCount());

        if (prevBtn) prevBtn.addEventListener("click", function () {
            scrollToPage(activePage - 1);
        });
        if (nextBtn) nextBtn.addEventListener("click", function () {
            scrollToPage(activePage + 1);
        });

        track.addEventListener("scroll", function () {
            if (ticking) return;
            ticking = true;
            window.requestAnimationFrame(function () {
                render();
                ticking = false;
            });
        }, { passive: true });

        track.addEventListener("keydown", function (event) {
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                scrollToPage(activePage - 1);
            } else if (event.key === "ArrowRight") {
                event.preventDefault();
                scrollToPage(activePage + 1);
            } else if (event.key === "Home") {
                event.preventDefault();
                scrollToPage(0);
            } else if (event.key === "End") {
                event.preventDefault();
                scrollToPage(getPageCount() - 1);
            }
        });

        window.addEventListener("resize", function () {
            track.scrollTo({ left: slideLeft(activePage * getPerView()), behavior: "auto" });
            render();
        }, { passive: true });

        render();
    }

    function setupAppActions(root) {
        var appId = root.getAttribute("data-app-id") || "";
        if (!appId) return;
        var likeBtn = root.querySelector('[data-app-vote="1"]');
        var dislikeBtn = root.querySelector('[data-app-vote="0"]');
        var likeCount = root.querySelector("[data-app-like-count]");
        var dislikeCount = root.querySelector("[data-app-dislike-count]");
        var shareBtn = root.querySelector("[data-app-share]");
        var ratioFill = root.querySelector("[data-app-ratio-fill]");
        var appDetailsI18n = window.appDetailsI18n || {};
        var busy = false;

        function renderVotes(data) {
            var likes = Number(data.like_counts || 0);
            var dislikes = Number(data.dislike_counts || 0);
            var total = likes + dislikes;
            if (likeCount) likeCount.textContent = String(likes);
            if (dislikeCount) dislikeCount.textContent = String(dislikes);
            if (ratioFill) {
                ratioFill.hidden = total < 1;
                ratioFill.style.height = total < 1 ? "0%" : String(Math.round((likes / total) * 100)) + "%";
            }
            if (likeBtn) {
                likeBtn.classList.toggle("is-voted", data.user_vote === true);
                likeBtn.querySelector("ion-icon")?.setAttribute("name", data.user_vote === true ? "thumbs-up" : "thumbs-up-outline");
            }
            if (dislikeBtn) {
                dislikeBtn.classList.toggle("is-voted", data.user_vote === false);
                dislikeBtn.querySelector("ion-icon")?.setAttribute("name", data.user_vote === false ? "thumbs-down" : "thumbs-down-outline");
            }
        }

        function loadVotes() {
            builtAppLikeService.fetchCounts(appId)
                .then(renderVotes)
                .catch(function () {});
        }

        function sendVote(isLike, button) {
            if (busy) return;
            busy = true;
            button.disabled = true;
            builtAppLikeService.vote(appId, isLike)
                .then(function () {
                    return builtAppLikeService.fetchCounts(appId);
                })
                .then(renderVotes)
                .catch(function () {})
                .finally(function () {
                    busy = false;
                    button.disabled = false;
                });
        }

        if (likeBtn) likeBtn.addEventListener("click", function () { sendVote(true, likeBtn); });
        if (dislikeBtn) dislikeBtn.addEventListener("click", function () { sendVote(false, dislikeBtn); });

        function shareText(key, fallback) {
            return appDetailsI18n[key] || fallback;
        }

        function normalizeShareUrl(rawUrl) {
            if (!rawUrl) return window.location.href;
            try {
                return new URL(rawUrl, window.location.origin).href;
            } catch (error) {
                return window.location.href;
            }
        }

        function setShareButtonState(button, labelText) {
            var label = button ? button.querySelector(".action-state-label") : null;
            if (label) {
                label.textContent = labelText;
            }
        }

        function revertShareButton(button) {
            setShareButtonState(button, shareText("shareStateShare", "Share"));
            button.classList.remove("is-shared");
        }

        async function shareApp() {
            if (!shareBtn) return;
            var title = shareBtn.getAttribute("data-share-title") || shareText("shareDefaultTitle", document.title);
            var text = shareBtn.getAttribute("data-share-text") || shareText("shareDefaultText", "");
            var url = normalizeShareUrl(shareBtn.getAttribute("data-share-url"));
            try {
                if (navigator.share) {
                    await navigator.share({ title: title, text: text, url: url });
                    setShareButtonState(shareBtn, shareText("shareStateShared", "Shared"));
                    shareBtn.classList.add("is-shared");
                    setTimeout(function () { revertShareButton(shareBtn); }, 1200);
                    return;
                }
                var copied = false;
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    try {
                        await navigator.clipboard.writeText(url);
                        copied = true;
                    } catch (clipboardError) {
                        copied = copyTextFallback(url);
                    }
                } else {
                    copied = copyTextFallback(url);
                }
                if (copied) {
                    setShareButtonState(shareBtn, shareText("shareStateCopied", "Copied"));
                    shareBtn.classList.add("is-shared");
                    setTimeout(function () { revertShareButton(shareBtn); }, 1200);
                    return;
                }
                window.prompt(shareText("sharePromptCopyLink", "Copy this link:"), url);
            } catch (error) {
                if (error && error.name === "AbortError") return;
                setShareButtonState(shareBtn, shareText("shareStateError", "Error"));
                setTimeout(function () { revertShareButton(shareBtn); }, 1200);
            }
        }

        function copyTextFallback(text) {
            try {
                var area = document.createElement("textarea");
                area.value = text;
                area.setAttribute("readonly", "");
                area.style.position = "fixed";
                area.style.opacity = "0";
                document.body.appendChild(area);
                area.select();
                area.setSelectionRange(0, area.value.length);
                var copied = document.execCommand("copy");
                document.body.removeChild(area);
                return copied;
            } catch (fallbackError) {
                return false;
            }
        }

        if (shareBtn) shareBtn.addEventListener("click", shareApp);
        loadVotes();
    }

    function setupTechReveal(list) {
        var rows = Array.prototype.slice.call(list.querySelectorAll("[data-tech-row]"));
        if (!rows.length) return;

        if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
            list.classList.add("is-visible");
            return;
        }

        rows.forEach(function (row, index) {
            row.style.transitionDelay = Math.min(index * 40, 320) + "ms";
        });
        list.classList.add("is-reveal-pending");

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                list.classList.add("is-visible");
                list.classList.remove("is-reveal-pending");
                observer.disconnect();
            });
        }, { threshold: 0.15 });

        observer.observe(list);
    }

    function init() {
        document.querySelectorAll("[data-app-slideshow]").forEach(setupSlideshow);
        document.querySelectorAll("[data-app-actions]").forEach(setupAppActions);
        document.querySelectorAll("[data-tech-reveal]").forEach(setupTechReveal);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
