/**
 * Tests for static/chart-utils.js
 *
 * Run with:  node --test tests/chart-utils.test.js
 *
 * Covers the three pure functions used to scale the results chart:
 *   - chooseTickInterval(rangeSeconds)
 *   - calcYAxisBounds(timesInSeconds)
 *   - calcXAxisBounds(isoDates)
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { chooseTickInterval, calcYAxisBounds, calcXAxisBounds } from "../static/chart-utils.js";

const MIN = 60; // seconds in a minute

// ---------------------------------------------------------------------------
// chooseTickInterval
// ---------------------------------------------------------------------------

describe("chooseTickInterval", () => {

    it("returns 1-min ticks for a small range (8 min)", () => {
        assert.equal(chooseTickInterval(8 * MIN), 1 * MIN);
    });

    it("returns 1-min ticks at the 15-min boundary", () => {
        assert.equal(chooseTickInterval(15 * MIN), 1 * MIN);
    });

    it("returns 2-min ticks just above 15 min", () => {
        assert.equal(chooseTickInterval(16 * MIN), 2 * MIN);
    });

    it("returns 2-min ticks at the 30-min boundary", () => {
        assert.equal(chooseTickInterval(30 * MIN), 2 * MIN);
    });

    it("returns 5-min ticks just above 30 min", () => {
        assert.equal(chooseTickInterval(31 * MIN), 5 * MIN);
    });

    it("returns 5-min ticks at the 60-min boundary", () => {
        assert.equal(chooseTickInterval(60 * MIN), 5 * MIN);
    });

    it("returns 10-min ticks above 60 min", () => {
        assert.equal(chooseTickInterval(61 * MIN), 10 * MIN);
    });

    it("returns 10-min ticks for a very wide range", () => {
        assert.equal(chooseTickInterval(120 * MIN), 10 * MIN);
    });
});

// ---------------------------------------------------------------------------
// calcYAxisBounds
// ---------------------------------------------------------------------------

describe("calcYAxisBounds", () => {

    it("yMin is never below zero", () => {
        // Times starting near 0 should not produce a negative yMin
        const { yMin } = calcYAxisBounds([30, 60, 90]);
        assert.ok(yMin >= 0, `yMin was ${yMin}`);
    });

    it("yMin is at or below the smallest time", () => {
        const times = [22 * MIN, 24 * MIN, 27 * MIN, 30 * MIN];
        const { yMin } = calcYAxisBounds(times);
        assert.ok(yMin <= Math.min(...times), `yMin ${yMin} > min time ${Math.min(...times)}`);
    });

    it("yMax is at or above the largest time", () => {
        const times = [22 * MIN, 24 * MIN, 27 * MIN, 30 * MIN];
        const { yMax } = calcYAxisBounds(times);
        assert.ok(yMax >= Math.max(...times), `yMax ${yMax} < max time ${Math.max(...times)}`);
    });

    it("uses 1-min ticks for a tight athlete range (22–30 min)", () => {
        const times = [22 * MIN, 24 * MIN, 27 * MIN, 30 * MIN];
        const { tick } = calcYAxisBounds(times);
        assert.equal(tick, 1 * MIN);
    });

    it("uses 5-min ticks for a wide range (15–50 min)", () => {
        const times = [15 * MIN, 25 * MIN, 40 * MIN, 50 * MIN];
        const { tick } = calcYAxisBounds(times);
        assert.equal(tick, 5 * MIN);
    });

    it("uses 10-min ticks for a very wide range (10–80 min)", () => {
        const times = [10 * MIN, 40 * MIN, 70 * MIN, 80 * MIN];
        const { tick } = calcYAxisBounds(times);
        assert.equal(tick, 10 * MIN);
    });

    it("does not extend to golden zone bounds (20–30 min) when data is outside them", () => {
        // Athlete with times all above 30 min — axis should not extend down to 20 min
        const times = [35 * MIN, 40 * MIN, 45 * MIN];
        const { yMin } = calcYAxisBounds(times);
        assert.ok(yMin > 20 * MIN, `yMin ${yMin / MIN} min should be above 20 min for this data`);
    });

    it("yMin and yMax are multiples of tick", () => {
        const times = [22 * MIN + 30, 25 * MIN + 15, 28 * MIN];
        const { yMin, yMax, tick } = calcYAxisBounds(times);
        assert.equal(yMin % tick, 0, `yMin ${yMin} is not a multiple of tick ${tick}`);
        assert.equal(yMax % tick, 0, `yMax ${yMax} is not a multiple of tick ${tick}`);
    });
});

// ---------------------------------------------------------------------------
// calcXAxisBounds
// ---------------------------------------------------------------------------

describe("calcXAxisBounds", () => {

    it("xMin is before the earliest date", () => {
        const dates = ["2023-03-15", "2024-06-01", "2025-01-10"];
        const { xMin } = calcXAxisBounds(dates);
        assert.ok(xMin < "2023-03-15", `xMin ${xMin} should be before earliest date`);
    });

    it("xMax is after the latest date", () => {
        const dates = ["2023-03-15", "2024-06-01", "2025-01-10"];
        const { xMax } = calcXAxisBounds(dates);
        assert.ok(xMax > "2025-01-10", `xMax ${xMax} should be after latest date`);
    });

    it("xMax is not hardcoded — it reflects the actual latest date", () => {
        const recentDates = ["2025-06-01", "2025-09-15", "2025-11-30"];
        const oldDates    = ["2020-01-01", "2020-06-15", "2020-12-31"];
        const { xMax: recentMax } = calcXAxisBounds(recentDates);
        const { xMax: oldMax }    = calcXAxisBounds(oldDates);
        assert.ok(recentMax > oldMax, "xMax should differ based on actual data");
    });

    it("works with a single date", () => {
        const { xMin, xMax } = calcXAxisBounds(["2024-04-13"]);
        assert.ok(xMin < "2024-04-13");
        assert.ok(xMax > "2024-04-13");
    });
});
