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
    const visitorCount = document.getElementById("visitorCount");
    const botCount = document.getElementById("botCount");

    try {
        const count = await visitService.getVisitCount();
        animateCount(visitorCount, 0, count.visitor_total_count, 800);
        animateCount(botCount, 0, count.bot_total_count, 800);
    } catch (err) {
        console.error("Dashboard Error:", err);
    }
});
