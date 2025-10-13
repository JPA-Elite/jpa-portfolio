// pages/dashboard.js
import { VisitService } from "../../services/VisitService.js";

// Count animation utility
function animateCount(element, start, end, duration) {
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current.toLocaleString();
        if (current === end) clearInterval(timer);
    }, stepTime);
}

document.addEventListener("DOMContentLoaded", async () => {
    const visitService = new VisitService();
    const element = document.getElementById("visitorCount");

    try {
        const count = await visitService.getVisitCount();
        animateCount(element, 0, count, 800);
    } catch (err) {
        console.error("Dashboard Error:", err);
    }
});
