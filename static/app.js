/**
 * ParkRun Dashboard — client-side data loading (Step 3)
 *
 * Fetches data/athletes.json and data/results.json, populates the athlete
 * selector, and updates the heading for the selected athlete.
 * Charts are added in Step 4.
 */

const DATA = {
    athletes: "data/athletes.json",
    results:  "data/results.json",
};

/**
 * Read the athlete_id URL parameter.
 * Returns null if not present.
 */
function getAthleteIdFromUrl() {
    return new URLSearchParams(window.location.search).get("athlete_id");
}

/**
 * Populate the athlete <select> and return the selected athlete object.
 */
function populateAthleteSelector(athletes, selectedId) {
    const select = document.getElementById("athlete-select");
    select.innerHTML = "";

    athletes.forEach(athlete => {
        const option = document.createElement("option");
        option.value = athlete.parkrun_id;
        option.textContent = athlete.name;
        if (String(athlete.parkrun_id) === String(selectedId)) {
            option.selected = true;
        }
        select.appendChild(option);
    });

    select.addEventListener("change", () => {
        window.location.href = "?athlete_id=" + select.value;
    });

    return athletes.find(a => String(a.parkrun_id) === String(selectedId))
        || athletes[0];
}

/**
 * Filter results for a single athlete by parkrun_id.
 */
function filterResults(results, athleteId) {
    return results.filter(r => String(r.athlete_id) === String(athleteId));
}

/**
 * Update the athlete heading.
 */
function updateHeading(athlete) {
    document.getElementById("athlete-heading").textContent =
        `${athlete.name} — Athlete ID: ${athlete.parkrun_id}`;
    document.title = `ParkRun Dashboard — ${athlete.name}`;
}

/**
 * Main entry point.
 */
async function init() {
    // Fetch both files in parallel
    const [athletes, results] = await Promise.all([
        fetch(DATA.athletes).then(r => r.json()),
        fetch(DATA.results).then(r => r.json()),
    ]);

    // Determine selected athlete
    const urlId = getAthleteIdFromUrl();
    const selectedId = urlId ?? String(athletes[0].parkrun_id);

    // Populate selector and resolve the athlete object
    const athlete = populateAthleteSelector(athletes, selectedId);

    // Filter results for this athlete
    const athleteResults = filterResults(results, athlete.parkrun_id);

    // Update heading
    updateHeading(athlete);

    // Placeholder messages until charts are added in Step 4
    if (athleteResults.length === 0) {
        document.getElementById("chart-container").innerHTML =
            '<div class="no-results">No results available for this athlete.</div>';
        document.getElementById("map-container").innerHTML =
            '<div class="no-results">No results available for this athlete.</div>';
    } else {
        document.getElementById("chart-container").innerHTML =
            '<div class="no-results">Chart coming in Step 4.</div>';
        document.getElementById("map-container").innerHTML =
            '<div class="no-results">Map coming in Step 4.</div>';
    }
}

init();
