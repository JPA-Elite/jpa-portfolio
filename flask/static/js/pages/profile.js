const carouselWrapper = document.querySelector('.carousel-track-wrapper');
const carouselCards = document.querySelectorAll('.carousel-card');
const nextButton = document.getElementById('carousel-next');
const prevButton = document.getElementById('carousel-prev');

const cardWidth = carouselCards[0].offsetWidth + 10;
let scrollPosition = 0;

function updateCarouselButtons() {
    // Check if at the beginning or end of the scrollable area
    prevButton.disabled = scrollPosition <= 0;
    nextButton.disabled = scrollPosition >= carouselWrapper.scrollWidth - carouselWrapper.clientWidth;
}

// Scroll to the next card
nextButton.addEventListener('click', () => {
    if (scrollPosition < carouselWrapper.scrollWidth - carouselWrapper.clientWidth) {
        scrollPosition += cardWidth;
        carouselWrapper.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });
        updateCarouselButtons();
    }
});

// Scroll to the previous card
prevButton.addEventListener('click', () => {
    if (scrollPosition > 0) {
        scrollPosition -= cardWidth;
        carouselWrapper.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });
        updateCarouselButtons();
    }
});

// Initial button state
updateCarouselButtons();

const image = document.querySelector(".project-image img");

image.addEventListener("mouseenter", function () {
    this.src = this.getAttribute("data-gif"); // Change to GIF on hover
});

image.addEventListener("mouseleave", function () {
    this.src = this.getAttribute("data-original"); // Revert back to the original image
});

function toggleContent() {
    const content = document.getElementById('collapsibleContent');
    const button = document.querySelector('.mobile-toggle ion-icon');
    content.classList.toggle('show');
    button.style.transform = content.classList.contains('show') ? 'rotate(180deg)' : 'rotate(0deg)';
}