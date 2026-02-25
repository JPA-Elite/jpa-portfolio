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
        });
    });
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

        const clampIndex = (index) => Math.max(0, Math.min(index, slides.length - 1));

        const getSlideLeft = (index) => {
            const slide = slides[index];
            if (!slide) return 0;
            return Math.max(0, slide.offsetLeft - track.offsetLeft);
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
            counter.textContent = `${activeIndex + 1} / ${slides.length}`;
            prevButton.disabled = activeIndex === 0;
            nextButton.disabled = activeIndex === slides.length - 1;

            dotButtons.forEach((dot, index) => {
                const isActive = index === activeIndex;
                dot.classList.toggle("is-active", isActive);
                dot.setAttribute("aria-selected", isActive ? "true" : "false");
                dot.setAttribute("tabindex", isActive ? "0" : "-1");
            });
        };

        const scrollToIndex = (index, behavior = "smooth") => {
            const nextIndex = clampIndex(index);
            track.scrollTo({
                left: getSlideLeft(nextIndex),
                behavior,
            });
            activeIndex = nextIndex;
            updateUi();
        };

        prevButton.addEventListener("click", () => scrollToIndex(activeIndex - 1));
        nextButton.addEventListener("click", () => scrollToIndex(activeIndex + 1));

        dotButtons.forEach((dot, index) => {
            dot.addEventListener("click", () => scrollToIndex(index));
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
            if (mobileQuery.matches) {
                track.scrollTo({
                    left: getSlideLeft(activeIndex),
                    behavior: "auto",
                });
            }
            updateUi();
        };

        window.addEventListener("resize", handleResize, { passive: true });

        updateUi();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupCarousel();
    setupProfileGifHover();
    setupSkillsTabs();
    setupMarqueeVisibility();
    setupMobileImageSliders();
});
