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
    throw new Error("Not implemented");
}

/**
 * Calculate y-axis bounds from an array of time values (in seconds).
 * yMin is floored at 0. Both bounds are multiples of the chosen tick.
 *
 * @param {number[]} timesInSeconds
 * @returns {{ yMin: number, yMax: number, tick: number }}
 */
export function calcYAxisBounds(timesInSeconds) {
    throw new Error("Not implemented");
}

/**
 * Calculate x-axis bounds from an array of ISO date strings.
 * Returns dates padded by one month either side.
 *
 * @param {string[]} isoDates  e.g. ["2024-01-10", "2025-03-22"]
 * @returns {{ xMin: string, xMax: string }}
 */
export function calcXAxisBounds(isoDates) {
    throw new Error("Not implemented");
}
