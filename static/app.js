/**
 * ParkRun Dashboard — client-side rendering
 *
 * Fetches JSON data, populates the athlete selector, and renders
 * the results chart and location map using Plotly.js.
 */

const DATA = {
    athletes:  "data/athletes.json",
    results:   "data/results.json",
    locations: "data/locations.json",
};

const COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
];

const MAP_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
    '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', '#ffbb78',
    '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7',
    '#dbdb8d', '#9edae5', '#393b79', '#637939', '#8c6d31', '#843c39'
];

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function getAthleteIdFromUrl() {
    return new URLSearchParams(window.location.search).get("athlete_id");
}

/** Convert total seconds to "MM:SS" string. */
function formatSeconds(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
}

/** Hash an event name to a consistent color. */
function hashColor(str, palette) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = Math.imul(hash, 31) + str.charCodeAt(i) | 0;
    }
    return palette[Math.abs(hash) % palette.length];
}

/** Return date string shifted by N months (ISO format). */
function shiftMonth(isoDate, n) {
    const d = new Date(isoDate);
    d.setMonth(d.getMonth() + n);
    return d.toISOString().split("T")[0];
}

/** Generate monthly tick dates between two ISO date strings (inclusive). */
function monthlyDates(startIso, endIso) {
    const dates = [];
    const end = new Date(endIso);
    const d = new Date(startIso);
    d.setDate(1);
    while (d <= end) {
        dates.push(d.toISOString().split("T")[0]);
        d.setMonth(d.getMonth() + 1);
    }
    return dates;
}

/** Mark PBs chronologically — a result is a PB if it beats all prior times. */
function markPBs(results) {
    const sorted = [...results].sort((a, b) => a.run_date.localeCompare(b.run_date));
    let minTime = Infinity;
    const pbSet = new Set();
    sorted.forEach(r => {
        if (r.time_seconds < minTime) {
            minTime = r.time_seconds;
            pbSet.add(`${r.run_date}_${r.event}_${r.time_seconds}`);
        }
    });
    return results.map(r => ({
        ...r,
        is_pb: pbSet.has(`${r.run_date}_${r.event}_${r.time_seconds}`)
    }));
}

// ---------------------------------------------------------------------------
// Athlete selector
// ---------------------------------------------------------------------------

function populateAthleteSelector(athletes, selectedId) {
    const select = document.getElementById("athlete-select");
    select.innerHTML = "";
    athletes.forEach(athlete => {
        const opt = document.createElement("option");
        opt.value = athlete.parkrun_id;
        opt.textContent = athlete.name;
        if (String(athlete.parkrun_id) === String(selectedId)) opt.selected = true;
        select.appendChild(opt);
    });
    select.addEventListener("change", () => {
        window.location.href = "?athlete_id=" + select.value;
    });
    return athletes.find(a => String(a.parkrun_id) === String(selectedId)) || athletes[0];
}

function updateHeading(athlete) {
    document.getElementById("athlete-heading").textContent =
        `${athlete.name} — Athlete ID: ${athlete.parkrun_id}`;
    document.title = `ParkRun Dashboard — ${athlete.name}`;
}

// ---------------------------------------------------------------------------
// Results chart
// ---------------------------------------------------------------------------

function renderResultsChart(results) {
    const container = document.getElementById("chart-container");

    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">No results available for this athlete.</div>';
        return;
    }

    const sorted = markPBs(
        [...results].sort((a, b) => a.run_date.localeCompare(b.run_date))
    );

    // Events ordered by race count desc, then alphabetically
    const countMap = {};
    sorted.forEach(r => { countMap[r.event] = (countMap[r.event] || 0) + 1; });
    const events = Object.keys(countMap).sort((a, b) =>
        countMap[b] - countMap[a] || a.localeCompare(b)
    );

    const eventColor = {};
    events.forEach((e, i) => { eventColor[e] = COLORS[i % COLORS.length]; });

    const traces = [];

    // Pass 1: circles per event
    events.forEach(event => {
        const evRows = sorted.filter(r => r.event === event);
        traces.push({
            type: "scatter",
            mode: "markers",
            name: `${event} (${evRows.length})`,
            x: evRows.map(r => r.run_date),
            y: evRows.map(r => r.time_seconds),
            customdata: evRows.map(r => [r.time, r.position, r.age_grade]),
            hovertemplate:
                "<b>%{fullData.name}</b><br>" +
                "Date: %{x|%d/%m/%Y}<br>" +
                "Time: %{customdata[0]}<br>" +
                "Position: %{customdata[1]}<br>" +
                "Age Grade: %{customdata[2]}<br>" +
                "<extra></extra>",
            marker: { size: 8, color: eventColor[event], symbol: "circle",
                      line: { width: 1, color: "white" } },
            legendgroup: event,
            showlegend: true,
        });
    });

    // Pass 2: PB stars (hidden by default)
    events.forEach(event => {
        const pbRows = sorted.filter(r => r.event === event && r.is_pb);
        if (pbRows.length === 0) return;
        traces.push({
            type: "scatter",
            mode: "markers",
            name: `${event} PB`,
            x: pbRows.map(r => r.run_date),
            y: pbRows.map(r => r.time_seconds),
            marker: { size: 14, color: eventColor[event], symbol: "star",
                      line: { width: 2, color: "gold" } },
            legendgroup: event,
            showlegend: false,
            visible: false,
            hoverinfo: "skip",
        });
    });

    // Axis ranges
    const allTimes = sorted.map(r => r.time_seconds);
    const allDates = sorted.map(r => r.run_date);
    const xMin = shiftMonth(allDates[0], -1);
    const xMax = shiftMonth(allDates[allDates.length - 1], 1);

    const TICK = 60;
    const yDataMin = Math.min(...allTimes);
    const yDataMax = Math.max(...allTimes);
    let yMin = Math.floor(yDataMin / TICK) * TICK - TICK;
    let yMax = (Math.floor(yDataMax / TICK) + 1) * TICK + TICK;
    yMin = Math.min(yMin, 20 * 60);
    yMax = Math.max(yMax, 30 * 60);

    const yTicks = [];
    for (let t = yMin; t <= yMax; t += TICK) yTicks.push(t);

    // Monthly grid lines
    const goldenEnd = "2026-06-30";
    const lineEnd = xMax > goldenEnd ? xMax : goldenEnd;
    const shapes = monthlyDates(xMin, lineEnd).map(d => ({
        type: "line", x0: d, x1: d, y0: 0, y1: 1, yref: "paper",
        line: { color: "lightgray", width: 1, dash: "dot" }
    }));

    const numEvents = events.length;
    const total = traces.length;
    const pbShowVisible = Array(total).fill(true);
    const pbHideVisible = [...Array(numEvents).fill(true), ...Array(total - numEvents).fill(false)];

    const layout = {
        title: { text: "ParkRun Results Over Time", x: 0.5, xanchor: "center" },
        xaxis: {
            title: "Date", showgrid: true, gridcolor: "lightgray",
            showline: true, linewidth: 2, linecolor: "black", mirror: true,
            range: [xMin, xMax], fixedrange: true, tickangle: -45,
            tickfont: { size: 10 }, title_standoff: 25,
        },
        yaxis: {
            title: "Time", showgrid: true, gridcolor: "lightgray",
            tickmode: "array", tickvals: yTicks,
            ticktext: yTicks.map(formatSeconds),
            showline: true, linewidth: 2, linecolor: "black", mirror: true,
            range: [yMin, yMax], fixedrange: true,
            tickfont: { size: 10 }, title_standoff: 15,
        },
        hovermode: "closest",
        plot_bgcolor: "white",
        height: 600,
        margin: { l: 80, b: 100, r: 250, t: 60 },
        legend: {
            yanchor: "top", y: 0.95, xanchor: "left", x: 1.02,
            bordercolor: "black", borderwidth: 2, bgcolor: "white",
            font: { size: 11 }, itemsizing: "constant", tracegroupgap: 8,
        },
        updatemenus: [
            {
                type: "buttons", direction: "right", active: 0,
                x: 0.12, y: -0.15, xanchor: "left", yanchor: "top",
                bgcolor: "lightgray", bordercolor: "black", borderwidth: 1,
                buttons: [
                    { label: "All Results", method: "relayout",
                      args: [{ "xaxis.range": [xMin, xMax], "yaxis.range": [yMin, yMax] }] },
                    { label: "Golden Zone", method: "relayout",
                      args: [{ "xaxis.range": ["2022-01-01", "2026-06-30"],
                               "yaxis.range": [20 * 60, 30 * 60] }] },
                ],
            },
            {
                type: "buttons", direction: "right", active: 0,
                x: 0.72, y: -0.15, xanchor: "left", yanchor: "top",
                bgcolor: "lightgray", bordercolor: "black", borderwidth: 1,
                buttons: [
                    { label: "Hide PBs", method: "update",
                      args: [{ visible: pbHideVisible }] },
                    { label: "Show PBs", method: "update",
                      args: [{ visible: pbShowVisible }] },
                ],
            },
        ],
        annotations: [
            {
                text: "<b>Race Location (Count)</b>",
                x: 1.02, y: 1.0, xref: "paper", yref: "paper",
                xanchor: "left", showarrow: false, font: { size: 12 },
            },
        ],
        shapes,
    };

    container.innerHTML = "";
    const div = document.createElement("div");
    container.appendChild(div);
    Plotly.newPlot(div, traces, layout, { responsive: true, displaylogo: false });
}

// ---------------------------------------------------------------------------
// Location map
// ---------------------------------------------------------------------------

function renderLocationMap(results, locations) {
    const container = document.getElementById("map-container");

    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">No results available for this athlete.</div>';
        return;
    }

    // Aggregate stats per event
    const stats = {};
    results.forEach(r => {
        if (!stats[r.event]) {
            stats[r.event] = { count: 0, minTime: Infinity, totalTime: 0, latestDate: "" };
        }
        const s = stats[r.event];
        s.count++;
        if (r.time_seconds < s.minTime) s.minTime = r.time_seconds;
        s.totalTime += r.time_seconds;
        if (r.run_date > s.latestDate) s.latestDate = r.run_date;
    });

    // Join with location coordinates
    const locMap = {};
    locations.forEach(l => { locMap[l.event] = l; });

    const rows = Object.entries(stats)
        .map(([event, s]) => ({ event, ...s, loc: locMap[event] }))
        .filter(r => r.loc && r.loc.latitude != null);

    if (rows.length === 0) {
        container.innerHTML = '<div class="no-results">No location data available for mapping.</div>';
        return;
    }

    const maxCount = Math.max(...rows.map(r => r.count));

    const lats       = rows.map(r => r.loc.latitude);
    const lons       = rows.map(r => r.loc.longitude);
    const texts      = rows.map(r => r.event);
    const sizes      = rows.map(r => 10 + (r.count / maxCount) * 20);
    const markerColors = rows.map(r => hashColor(r.event, MAP_COLORS));
    const customdata = rows.map(r => [
        r.count,
        formatSeconds(r.minTime),
        formatSeconds(Math.round(r.totalTime / r.count)),
        r.latestDate,
    ]);

    const trace = {
        type: "scattermapbox",
        lat: lats,
        lon: lons,
        mode: "markers",
        marker: { size: sizes, color: markerColors, opacity: 0.8 },
        text: texts,
        customdata,
        hovertemplate:
            "<b>%{text}</b><br><br>" +
            "Races: %{customdata[0]}<br>" +
            "Best Time: %{customdata[1]}<br>" +
            "Avg Time: %{customdata[2]}<br>" +
            "Last Race: %{customdata[3]}<br>" +
            "<extra></extra>",
    };

    const layout = {
        title: { text: "ParkRun Race Locations", x: 0.5, xanchor: "center" },
        mapbox: {
            style: "open-street-map",
            center: { lat: lats.reduce((a, b) => a + b) / lats.length,
                      lon: lons.reduce((a, b) => a + b) / lons.length },
            zoom: 5,
        },
        height: 600,
        margin: { l: 0, r: 0, t: 40, b: 0 },
        hovermode: "closest",
    };

    container.innerHTML = "";
    const div = document.createElement("div");
    container.appendChild(div);
    Plotly.newPlot(div, [trace], layout, {
        scrollZoom: true, displayModeBar: true, displaylogo: false, responsive: true
    });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function init() {
    const [athletes, results, locations] = await Promise.all([
        fetch(DATA.athletes).then(r => r.json()),
        fetch(DATA.results).then(r => r.json()),
        fetch(DATA.locations).then(r => r.json()),
    ]);

    const urlId = getAthleteIdFromUrl();
    const selectedId = urlId ?? String(athletes[0].parkrun_id);

    const athlete = populateAthleteSelector(athletes, selectedId);
    updateHeading(athlete);

    const athleteResults = results.filter(
        r => String(r.athlete_id) === String(athlete.parkrun_id)
    );

    renderResultsChart(athleteResults);
    renderLocationMap(athleteResults, locations);
}

init();
