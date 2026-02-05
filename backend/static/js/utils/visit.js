// utils/visit.js

export const EMPTY_VISIT_COUNTS = Object.freeze({
    visitor_total_count: 0,
    bot_total_count: 0,
});

/**
 * Normalize API payload to a stable count shape.
 * @param {{visitor_total_count?: number, bot_total_count?: number} | null | undefined} count
 * @returns {{visitor_total_count: number, bot_total_count: number}}
 */
export function normalizeVisitCount(count) {
    return {
        visitor_total_count: Number(count?.visitor_total_count ?? 0),
        bot_total_count: Number(count?.bot_total_count ?? 0),
    };
}

/**
 * Animate integer text content from start to end.
 * @param {HTMLElement | null} element
 * @param {number} start
 * @param {number} end
 * @param {number} duration
 */
export function animateCount(element, start, end, duration) {
    if (!element) return;

    if (start === end) {
        element.textContent = end.toLocaleString();
        return;
    }

    const increment = end > start ? 1 : -1;
    const range = Math.abs(end - start);
    const stepTime = Math.max(16, Math.floor(duration / range));
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        element.textContent = current.toLocaleString();

        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}
