// static/js/utils.js

/**
 * Calculate age based on a given birth date.
 * @param {Date} birthDate - The birth date to calculate the age from.
 * @returns {number} - The calculated age.
 */
function calculateAge() {
    const today = new Date();
    const birthDate = new Date('2001-09-16');
    
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    // Adjust age if the birthday hasn't occurred yet this year
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

function startTypingAnimation(elementId, text, typingSpeed = 200, deletingSpeed = 100, pauseDuration = 1000) {
    let index = 0;                // Current index in the text
    let direction = 1;            // 1 for typing, -1 for deleting
    const headingElement = document.getElementById(elementId);

    function animateText() {
        if (direction === 1) { // Typing mode
            if (index < text.length) {
                headingElement.textContent = text.substring(0, index + 1);
                index++;
                setTimeout(animateText, typingSpeed);
            } else {
                direction = -1;  // Switch to deleting mode
                setTimeout(animateText, pauseDuration); // Pause before deleting
            }
        } else { // Deleting mode
            if (index > 0) {
                headingElement.textContent = text.substring(0, index - 1);
                index--;
                setTimeout(animateText, deletingSpeed);
            } else {
                direction = 1;  // Switch back to typing mode
                setTimeout(animateText, pauseDuration); // Pause before typing
            }
        }
    }

    // Start the animation
    animateText();
}