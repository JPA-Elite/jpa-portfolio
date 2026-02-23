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

document.addEventListener("DOMContentLoaded", () => {
    setupCarousel();
    setupProfileGifHover();
    setupSkillsTabs();
    setupMarqueeVisibility();
});
