function toggleContent() {
    const content = document.getElementById("collapsibleContent");
    const icon = document.querySelector(".mobile-toggle ion-icon");

    if (!content || !icon) return;

    content.classList.toggle("show");
    icon.style.transform = content.classList.contains("show")
        ? "rotate(180deg)"
        : "rotate(0deg)";
}

function setupCarousel() {
    const carouselWrapper = document.querySelector(".carousel-track-wrapper");
    const carouselCards = document.querySelectorAll(".carousel-card");
    const nextButton = document.getElementById("carousel-next");
    const prevButton = document.getElementById("carousel-prev");

    if (!carouselWrapper || !carouselCards.length || !nextButton || !prevButton) {
        return;
    }

    let scrollPosition = 0;

    const getCardWidth = () => carouselCards[0].offsetWidth + 10;

    const clampScrollPosition = () => {
        const maxScroll = Math.max(
            0,
            carouselWrapper.scrollWidth - carouselWrapper.clientWidth
        );
        scrollPosition = Math.min(Math.max(scrollPosition, 0), maxScroll);
    };

    const updateCarouselButtons = () => {
        const maxScroll = Math.max(
            0,
            carouselWrapper.scrollWidth - carouselWrapper.clientWidth
        );

        prevButton.disabled = carouselWrapper.scrollLeft <= 1;
        nextButton.disabled = carouselWrapper.scrollLeft >= maxScroll - 1;
    };

    nextButton.addEventListener("click", () => {
        scrollPosition = carouselWrapper.scrollLeft + getCardWidth();
        clampScrollPosition();

        carouselWrapper.scrollTo({
            left: scrollPosition,
            behavior: "smooth",
        });
    });

    prevButton.addEventListener("click", () => {
        scrollPosition = carouselWrapper.scrollLeft - getCardWidth();
        clampScrollPosition();

        carouselWrapper.scrollTo({
            left: scrollPosition,
            behavior: "smooth",
        });
    });

    carouselWrapper.addEventListener("scroll", updateCarouselButtons, { passive: true });
    window.addEventListener("resize", () => {
        scrollPosition = carouselWrapper.scrollLeft;
        clampScrollPosition();
        updateCarouselButtons();
    }, { passive: true });

    updateCarouselButtons();
}

function setupProfileGifHover() {
    const image = document.querySelector(".project-image img");
    if (!image) return;

    const originalSrc = image.getAttribute("data-original");
    const gifSrc = image.getAttribute("data-gif");

    if (!originalSrc || !gifSrc) return;

    // Skip on touch-first devices where hover is not a common interaction.
    if (!window.matchMedia("(hover: hover)").matches) {
        return;
    }

    let hasPreloadedGif = false;

    const preloadGif = () => {
        if (hasPreloadedGif) return;

        const gifImage = new Image();
        gifImage.src = gifSrc;
        hasPreloadedGif = true;
    };

    image.addEventListener("mouseenter", () => {
        preloadGif();
        if (image.src !== gifSrc) {
            image.src = gifSrc;
        }
    });

    image.addEventListener("mouseleave", () => {
        if (image.src !== originalSrc) {
            image.src = originalSrc;
        }
    });
}

function animateSkillBars(container, forceReplay) {
    const bars = container.querySelectorAll('.bar');
    const percents = container.querySelectorAll('.percent');

    bars.forEach((bar, i) => {
        if (!forceReplay && bar.classList.contains('animated')) return;

        bar.classList.remove('animated');
        const rawWidth = bar.style.width;
        const target = parseFloat(rawWidth);
        // Force reflow so browser picks up width: 0 immediately
        bar.style.width = '0';
        bar.style.opacity = '1';
        void bar.offsetWidth;

        const delay = i * 100;
        const duration = 1200;
        const startTime = Date.now() + delay;

        function tick() {
            const elapsed = Date.now() - startTime;
            if (elapsed < 0) {
                setTimeout(tick, 20);
                return;
            }
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            bar.style.width = (eased * target) + '%';
            if (progress < 1) {
                setTimeout(tick, 16);
            } else {
                bar.style.width = rawWidth;
                bar.classList.add('animated');
            }
        }

        setTimeout(tick, 20);
    });

    // Count-up for percent spans
    percents.forEach((el, i) => {
        if (forceReplay) el.classList.remove('counting');
        const target = parseInt(el.textContent, 10);
        const delay = i * 100;
        el.classList.add('counting');
        let current = 0;
        const duration = 1200;
        const startTime = Date.now() + delay;

        function tick() {
            const elapsed = Date.now() - startTime;
            if (elapsed < 0) {
                setTimeout(tick, 20);
                return;
            }
            const progress = Math.min(elapsed / duration, 1);
            current = Math.round((1 - Math.pow(1 - progress, 3)) * target);
            el.textContent = current + '%';
            if (progress < 1) {
                setTimeout(tick, 16);
            } else {
                el.classList.remove('counting');
            }
        }

        setTimeout(tick, 20);
    });
}

function setupSkillsTabs() {
    const tabs = document.querySelectorAll(".tab");
    const sections = document.querySelectorAll(".skills-container");

    if (!tabs.length || !sections.length) return;

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = tab.getAttribute("data-target");
            if (!targetId) return;

            const targetSection = document.getElementById(targetId);
            if (!targetSection || targetSection.classList.contains("active")) return;

            tabs.forEach(t => t.classList.remove("active"));

            const currentSection = document.querySelector(".skills-container.active");
            if (currentSection) {
                currentSection.classList.remove("active");
                currentSection.classList.add("hidden");
            }

            tab.classList.add("active");
            targetSection.classList.remove("hidden");
            void targetSection.offsetWidth;
            targetSection.classList.add("active");
            animateSkillBars(targetSection, true); // force replay on tab switch
        });
    });

    // Animate bars on page load for the active tab
    const activeSection = document.querySelector(".skills-container.active");
    if (activeSection) {
        setTimeout(() => animateSkillBars(activeSection), 400);
    }
}

function setupSkillsScrollAnimation() {
    const skillsSection = document.getElementById("skills");
    if (!skillsSection) return;

    const triggerAnimation = () => {
        const activeTab = document.querySelector(".skills-container.active");
        if (activeTab) animateSkillBars(activeTab, true);
    };

    if (!("IntersectionObserver" in window)) {
        triggerAnimation();
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    triggerAnimation();
                }
            });
        },
        { threshold: 0.15 }
    );

    observer.observe(skillsSection);
}

function setupMarqueeVisibility() {
    const marqueeSection = document.getElementById("profile-marquee-section");
    if (!marqueeSection) return;

    const enableAnimation = () => marqueeSection.classList.add("is-animating");
    const disableAnimation = () => marqueeSection.classList.remove("is-animating");

    if (!("IntersectionObserver" in window)) {
        enableAnimation();
        return;
    }

    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    enableAnimation();
                } else {
                    disableAnimation();
                }
            });
        },
        { threshold: 0.1 }
    );

    observer.observe(marqueeSection);
}

function setupCareerRoadmapReveal() {
    const roadmapSection = document.getElementById("company-roadmap");
    const timeline = document.getElementById("careerRoadmapTimeline");
    const items = Array.from(document.querySelectorAll(".js-roadmap-item"));

    if (!roadmapSection || !timeline || !items.length) return;

    items.forEach((item, index) => {
        item.style.setProperty("--roadmap-item-index", String(index));
    });

    const updateTimelineProgress = () => {
        const rect = roadmapSection.getBoundingClientRect();
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 1;
        const start = viewportHeight * 0.18;
        const end = viewportHeight * 0.82;
        const total = rect.height + (end - start);
        const progressed = end - rect.top;
        const ratio = Math.max(0, Math.min(1, total > 0 ? progressed / total : 0));
        timeline.style.setProperty("--roadmap-progress", ratio.toFixed(4));
    };

    if (!("IntersectionObserver" in window)) {
        items.forEach((item) => item.classList.add("is-visible"));
        updateTimelineProgress();
        window.addEventListener("scroll", updateTimelineProgress, { passive: true });
        window.addEventListener("resize", updateTimelineProgress, { passive: true });
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                }
            });
            updateTimelineProgress();
        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -8% 0px",
        }
    );

    items.forEach((item) => observer.observe(item));
    updateTimelineProgress();
    window.addEventListener("scroll", updateTimelineProgress, { passive: true });
    window.addEventListener("resize", updateTimelineProgress, { passive: true });
}

function setupMobileImageSliders() {
    const sliderTracks = document.querySelectorAll("[data-mobile-slider]");
    if (!sliderTracks.length) return;

    const mobileQuery = window.matchMedia("(max-width: 768px)");
    const sliderI18n = window.profileI18n || {};
    const t = (key, fallback, vars = {}) => {
        let text = sliderI18n[key] || fallback;
        Object.entries(vars).forEach(([name, value]) => {
            const safeValue = String(value);
            text = text
                .replaceAll(`{${name}}`, safeValue)
                .replaceAll(`%(${name})s`, safeValue);
        });
        return text;
    };

    sliderTracks.forEach((track) => {
        if (track.dataset.mobileSliderReady === "true") return;

        const slides = Array.from(track.children).filter(
            (node) => node.nodeType === Node.ELEMENT_NODE
        );
        const desktopPerView = Math.max(
            1,
            Number.parseInt(track.dataset.sliderDesktopPerView || "1", 10) || 1
        );
        const mobilePerView = Math.max(
            1,
            Number.parseInt(track.dataset.sliderMobilePerView || "1", 10) || 1
        );

        if (!slides.length || !track.parentNode) return;

        track.dataset.mobileSliderReady = "true";
        track.classList.add("mobile-image-slider__track");
        slides.forEach((slide) => slide.classList.add("mobile-image-slider__slide"));

        // Keep single-item tracks full-width on mobile, but skip controls/dots.
        if (slides.length < 2) {
            return;
        }

        const shell = document.createElement("div");
        shell.className = "mobile-image-slider";

        track.parentNode.insertBefore(shell, track);
        shell.appendChild(track);

        const controls = document.createElement("div");
        controls.className = "mobile-image-slider__controls";

        const prevButton = document.createElement("button");
        prevButton.type = "button";
        prevButton.className = "mobile-image-slider__btn";
        prevButton.setAttribute(
            "aria-label",
            t("sliderPreviousImageAria", "Previous image")
        );
        prevButton.textContent = t("sliderPrev", "Prev");

        const counter = document.createElement("div");
        counter.className = "mobile-image-slider__counter";
        counter.setAttribute("aria-live", "polite");

        const nextButton = document.createElement("button");
        nextButton.type = "button";
        nextButton.className = "mobile-image-slider__btn";
        nextButton.setAttribute(
            "aria-label",
            t("sliderNextImageAria", "Next image")
        );
        nextButton.textContent = t("sliderNext", "Next");

        controls.appendChild(prevButton);
        controls.appendChild(counter);
        controls.appendChild(nextButton);

        const dots = document.createElement("div");
        dots.className = "mobile-image-slider__dots";
        dots.setAttribute("role", "tablist");
        dots.setAttribute(
            "aria-label",
            t("sliderNavigationLabel", "{label} slider navigation", {
                label:
                    track.dataset.mobileSliderLabel ||
                    t("sliderDefaultLabel", "Image"),
            })
        );

        const dotButtons = slides.map((_, index) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = "mobile-image-slider__dot";
            dot.setAttribute("role", "tab");
            dot.setAttribute(
                "aria-label",
                t("sliderGoToImage", "Go to image {index}", {
                    index: index + 1,
                })
            );
            dots.appendChild(dot);
            return dot;
        });

        shell.appendChild(controls);
        shell.appendChild(dots);

        let activeIndex = 0;
        let scrollTicking = false;
        let activePage = 0;

        const clampIndex = (index) => Math.max(0, Math.min(index, slides.length - 1));
        const getPerView = () => (mobileQuery.matches ? mobilePerView : desktopPerView);
        const getPageCount = () => Math.max(1, Math.ceil(slides.length / getPerView()));

        const getSlideLeft = (index) => {
            const slide = slides[index];
            if (!slide) return 0;
            return Math.max(0, slide.offsetLeft - track.offsetLeft);
        };

        const applyTrackResponsiveVars = () => {
            track.style.setProperty(
                "--mobile-image-slider-slides-per-view",
                String(getPerView())
            );
        };

        const findClosestIndex = () => {
            const scrollLeft = track.scrollLeft;
            let closestIndex = 0;
            let closestDistance = Number.POSITIVE_INFINITY;

            slides.forEach((slide, index) => {
                const distance = Math.abs(scrollLeft - (slide.offsetLeft - track.offsetLeft));
                if (distance < closestDistance) {
                    closestDistance = distance;
                    closestIndex = index;
                }
            });

            return closestIndex;
        };

        const updateUi = () => {
            activeIndex = clampIndex(findClosestIndex());
            const perView = getPerView();
            const pageCount = getPageCount();
            activePage = Math.max(0, Math.min(pageCount - 1, Math.floor(activeIndex / perView)));

            counter.textContent = `${activePage + 1} / ${pageCount}`;
            prevButton.disabled = activePage === 0;
            nextButton.disabled = activePage >= pageCount - 1;

            const showNavigation = pageCount > 1;
            controls.hidden = !showNavigation;
            dots.hidden = !showNavigation;

            dotButtons.forEach((dot, index) => {
                const isVisible = index < pageCount;
                const isActive = isVisible && index === activePage;
                dot.hidden = !isVisible;
                dot.classList.toggle("is-active", isActive);
                dot.setAttribute("aria-selected", isActive ? "true" : "false");
                dot.setAttribute("tabindex", isActive && isVisible ? "0" : "-1");
            });
        };

        const scrollToPage = (page, behavior = "smooth") => {
            const pageCount = getPageCount();
            const nextPage = Math.max(0, Math.min(pageCount - 1, page));
            const nextIndex = clampIndex(nextPage * getPerView());
            track.scrollTo({
                left: getSlideLeft(nextIndex),
                behavior,
            });
            activeIndex = nextIndex;
            activePage = nextPage;
            updateUi();
        };

        prevButton.addEventListener("click", () => scrollToPage(activePage - 1));
        nextButton.addEventListener("click", () => scrollToPage(activePage + 1));

        dotButtons.forEach((dot, index) => {
            dot.addEventListener("click", () => scrollToPage(index));
        });

        track.addEventListener(
            "scroll",
            () => {
                if (scrollTicking) return;
                scrollTicking = true;
                requestAnimationFrame(() => {
                    updateUi();
                    scrollTicking = false;
                });
            },
            { passive: true }
        );

        const handleResize = () => {
            applyTrackResponsiveVars();
            if (mobileQuery.matches) {
                track.scrollTo({
                    left: getSlideLeft(clampIndex(activePage * getPerView())),
                    behavior: "auto",
                });
            } else {
                track.scrollTo({
                    left: getSlideLeft(clampIndex(activePage * getPerView())),
                    behavior: "auto",
                });
            }
            updateUi();
        };

        window.addEventListener("resize", handleResize, { passive: true });

        applyTrackResponsiveVars();
        updateUi();
    });
}

function setupContactCopy() {
    const buttons = document.querySelectorAll("#contactCopyEmailBtn, #copyEmailBtn");
    buttons.forEach((btn) => {
        if (!btn || btn.dataset.copyBound === "true") return;
        btn.dataset.copyBound = "true";

        btn.addEventListener("click", async (event) => {
            event.preventDefault();
            const email = btn.dataset.email || "";
            if (!email) return;

            let copied = false;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(email);
                    copied = true;
                }
            } catch (err) {
                copied = false;
            }

            if (!copied) {
                try {
                    const tempInput = document.createElement("textarea");
                    tempInput.value = email;
                    tempInput.setAttribute("readonly", "");
                    tempInput.style.position = "absolute";
                    tempInput.style.left = "-9999px";
                    document.body.appendChild(tempInput);
                    tempInput.select();
                    copied = document.execCommand("copy");
                    document.body.removeChild(tempInput);
                } catch (err) {
                    copied = false;
                }
            }

            const defaultHTML = btn.innerHTML;
            if (copied) {
                if (typeof window.showToast === "function") {
                    window.showToast(
                        btn.dataset.copiedMessage || "Email copied to clipboard!",
                        { type: "success" }
                    );
                }
                btn.classList.add("is-copied");
                btn.innerHTML = '<ion-icon name="checkmark-outline" aria-hidden="true"></ion-icon>';
                setTimeout(() => {
                    btn.classList.remove("is-copied");
                    btn.innerHTML = defaultHTML;
                }, 2000);
            } else if (typeof window.showToast === "function") {
                window.showToast(email, { type: "info", title: "Email" });
            }
        });
    });
}

function setupStatReveal() {
    const container = document.querySelector(".summary-stats");
    if (!container) return;

    const stats = container.querySelectorAll(".summary-stat");
    if (!stats.length) return;

    stats.forEach((el, i) => el.style.setProperty("--stat-index", String(i)));

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            stats.forEach((el) => el.classList.add("is-revealed"));
                            animateStatCounters(stats);
                        }, 200);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );
        observer.observe(container);
    } else {
        stats.forEach((el) => el.classList.add("is-revealed"));
        animateStatCounters(stats);
    }
}

function animateStatCounters(stats) {
    stats.forEach((el, i) => {
        const numEl = el.querySelector(".summary-stat__num");
        if (!numEl) return;

        const originalText = numEl.textContent.trim();
        const match = originalText.match(/^(\d+)(.*)/);
        if (!match) return;

        const target = parseInt(match[1], 10);
        const suffix = match[2] || "";
        const delay = i * 150;
        const duration = 1200;
        const startTime = Date.now() + delay;

        function tick() {
            const elapsed = Date.now() - startTime;
            if (elapsed < 0) {
                setTimeout(tick, 20);
                return;
            }
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);
            numEl.textContent = current + suffix;
            if (progress < 1) {
                setTimeout(tick, 16);
            }
        }

        setTimeout(tick, 20);
    });
}

function parallaxScroll(refSel, targetsSel, opts) {
    if (window.innerWidth < 768) return;
    const ref = document.querySelector(refSel);
    if (!ref) return;
    var targets = null;

    function findTargets() {
        if (!targets || !targets.length) targets = document.querySelectorAll(targetsSel);
        return targets.length ? targets : null;
    }

    const sMin = opts.sMin || 0.85;
    const oMin = opts.oMin || 0.75;
    const yMax = opts.yMax || -30;
    const rMax = opts.rMax || 0;
    const ringEl = opts.ring ? document.querySelector(opts.ring) : null;

    const update = () => {
        var els = findTargets();
        if (!els) return;

        const rect = ref.getBoundingClientRect();
        let p = 0;
        if (rect.top < 0) p = Math.min(1, -rect.top / rect.height);

        const s = 1 - p * (1 - sMin);
        const y = p * yMax;
        const r = p * rMax;
        const o = 1 - p * (1 - oMin);
        const tf = "scale(" + s + ") translateY(" + y + "px) rotate(" + r + "deg)";

        for (var i = 0; i < els.length; i++) {
            els[i].style.transform = tf;
            els[i].style.opacity = o;
        }
        if (ringEl) ringEl.style.transform = "rotate(" + p * 90 + "deg)";
    };

    window.addEventListener("scroll", update, { passive: true });
    update();
}

function setupTagTooltips() {
    const tooltip = document.createElement("div");
    tooltip.className = "summary-tag-tooltip";
    document.body.appendChild(tooltip);

    document.querySelectorAll(".summary-tag").forEach((tag) => {
        const desc = tag.getAttribute("data-desc");
        if (!desc) return;

        let hideTimeout;

        tag.addEventListener("mouseenter", () => {
            clearTimeout(hideTimeout);
            tooltip.textContent = desc;
            const rect = tag.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 + "px";
            tooltip.style.top = rect.top - 10 + "px";
            tooltip.classList.add("is-visible");
        });

        tag.addEventListener("mouseleave", () => {
            hideTimeout = setTimeout(() => {
                tooltip.classList.remove("is-visible");
            }, 80);
        });
    });
}

function setupCertReveal() {
    const numEl = document.querySelector(".cert-headline__num");
    const section = document.getElementById("certifications");
    if (!numEl || !section) return;

    const trigger = () => animateCertCount(numEl);

    if (section.classList.contains("is-revealed")) {
        trigger();
        return;
    }

    const mo = new MutationObserver(() => {
        if (section.classList.contains("is-revealed")) {
            mo.disconnect();
            trigger();
        }
    });
    mo.observe(section, { attributes: true, attributeFilter: ["class"] });
}

function animateCertCount(el) {
    const target = parseInt(el.dataset.count || el.textContent.trim(), 10);
    if (isNaN(target)) return;
    const duration = 1000;
    const startTime = Date.now();

    function tick() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(eased * target);
        if (progress < 1) requestAnimationFrame(tick);
    }
    tick();
}

function setupBuiltAppsShowMore() {
    const showMoreBtn = document.getElementById("builtAppsShowMore");
    const extraGrid = document.getElementById("builtAppsExtra");
    if (!showMoreBtn || !extraGrid) return;

    showMoreBtn.addEventListener("click", () => {
        extraGrid.hidden = false;
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                extraGrid.classList.add("is-open");
            });
        });
        showMoreBtn.classList.add("is-hidden");
        setTimeout(() => {
            extraGrid.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 350);
    });
}

function setupBuiltAppsHashScroll() {
    if (window.location.hash !== "#built-apps") return;
    const target = document.getElementById("built-apps");
    if (!target) return;
    let node = target.parentElement;
    while (node) {
        if (node.classList && node.classList.contains("lazy-reveal")) {
            node.classList.add("is-revealed");
        }
        node = node.parentElement;
    }
    const scrollToApps = () => {
        requestAnimationFrame(() => {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    };
    const scheduleScroll = () => {
        setTimeout(scrollToApps, 150);
        setTimeout(scrollToApps, 600);
    };
    if (document.readyState === "complete") {
        scheduleScroll();
    } else {
        window.addEventListener("load", scheduleScroll);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    setupCarousel();
    setupProfileGifHover();
    setupSkillsTabs();
    setupSkillsScrollAnimation();
    setupMarqueeVisibility();
    setupCareerRoadmapReveal();
    setupMobileImageSliders();
    setupContactCopy();
    setupStatReveal();
    setupCertReveal();
    parallaxScroll("#portfolio", ".summary-hero__profile", { sMin: 0.85, oMin: 0.75, yMax: -30 });
    parallaxScroll("#portfolio", ".summary-hero__panel", { sMin: 0.85, oMin: 0.75, yMax: -30 });

    setupTagTooltips();
    setupBuiltAppsShowMore();
    setupBuiltAppsHashScroll();
    // setupLazyReveal() lives in base.js — shared across all pages
});
