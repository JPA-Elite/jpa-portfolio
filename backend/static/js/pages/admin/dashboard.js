// pages/dashboard.js
import { VisitService } from "../../services/VisitService.js";
import { animateCount } from "../../utils/visit.js";

const ANIMATION_DURATION_MS = 800;

document.addEventListener("DOMContentLoaded", async () => {
    const visitService = new VisitService();
    const visitorCount = document.getElementById("visitorCount");
    const botCount = document.getElementById("botCount");
    const count = await visitService.getVisitCount();

    animateCount(visitorCount, 0, count.visitor_total_count, ANIMATION_DURATION_MS);
    animateCount(botCount, 0, count.bot_total_count, ANIMATION_DURATION_MS);
});
