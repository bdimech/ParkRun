/**
 * Pure scaling utilities for the results chart.
 * Used by app.js (browser) and tested via Node's built-in test runner.
 */

/**
 * Choose a y-axis tick interval (in seconds) based on the data range.
 *
 * Range        Tick
 * ≤ 15 min  →  1 min
 * ≤ 30 min  →  2 min
 * ≤ 60 min  →  5 min
 * > 60 min  →  10 min
 *
 * @param {number} rangeSeconds
 * @returns {number} tick interval in seconds
 */
export function chooseTickInterval(rangeSeconds) {
    const mins = rangeSeconds / 60;
    if (mins <= 15) return 1 * 60;
    if (mins <= 30) return 2 * 60;
    if (mins <= 60) return 5 * 60;
    return 10 * 60;
}

/**
 * Calculate y-axis bounds from an array of time values (in seconds).
 * yMin is floored at 0. Both bounds are multiples of the chosen tick.
 *
 * @param {number[]} timesInSeconds
 * @returns {{ yMin: number, yMax: number, tick: number }}
 */
export function calcYAxisBounds(timesInSeconds) {
    const minTime = Math.min(...timesInSeconds);
    const maxTime = Math.max(...timesInSeconds);
    const tick = chooseTickInterval(maxTime - minTime);

    const yMin = Math.max(0, Math.floor(minTime / tick) * tick - tick);
    const yMax = (Math.floor(maxTime / tick) + 1) * tick + tick;

    return { yMin, yMax, tick };
}

/**
 * Calculate x-axis bounds from an array of ISO date strings.
 * Returns dates padded by one month either side.
 *
 * @param {string[]} isoDates  e.g. ["2024-01-10", "2025-03-22"]
 * @returns {{ xMin: string, xMax: string }}
 */
export function calcXAxisBounds(isoDates) {
    const sorted = [...isoDates].sort();
    const pad = (iso, months) => {
        const d = new Date(iso);
        d.setMonth(d.getMonth() + months);
        return d.toISOString().split("T")[0];
    };
    return {
        xMin: pad(sorted[0], -1),
        xMax: pad(sorted[sorted.length - 1], 1),
    };
}
