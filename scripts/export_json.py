"""
Export ParkRun CSV data to JSON files for the static Cloudflare Pages site.

Usage:
    python scripts/export_json.py

Reads:
    data/results.csv
    data/athletes.csv
    data/parkrun_locations.csv

Writes:
    data/results.json
    data/athletes.json
    data/locations.json
"""
import json
import os
import pandas as pd


def _time_to_seconds(time_str) -> int | None:
    """Convert 'MM:SS' string to total seconds. Returns None for invalid input."""
    if pd.isna(time_str):
        return None
    time_str = str(time_str).strip()
    if time_str.endswith(":00") and time_str.count(":") == 2:
        time_str = time_str[:-3]
    parts = time_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return None


def results_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a results DataFrame to a list of JSON-serializable dicts."""
    records = []
    for _, row in df.iterrows():
        pb_raw = row.get("PB", "")
        is_pb = isinstance(pb_raw, str) and pb_raw.strip() != "" or (
            not isinstance(pb_raw, str) and not pd.isna(pb_raw)
        )

        age_grade_raw = str(row["Age Grade"]).strip().rstrip("%")

        records.append({
            "event":        str(row["Event"]),
            "run_date":     pd.to_datetime(row["Run Date"], format="%d/%m/%Y").strftime("%Y-%m-%d"),
            "run_number":   int(row["Run Number"]),
            "position":     int(row["Pos"]),
            "time":         str(row["Time"]).strip(),
            "time_seconds": _time_to_seconds(row["Time"]),
            "age_grade":    float(age_grade_raw),
            "is_pb":        is_pb,
            "athlete_name": str(row["Athlete Name"]).strip(),
            "athlete_id":   int(str(row["Athlete ID"]).strip()),
        })
    return records


def athletes_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert an athletes DataFrame to a list of JSON-serializable dicts."""
    records = []
    for _, row in df.iterrows():
        records.append({
            "name":       str(row["name"]).strip(),
            "parkrun_id": int(str(row["parkrun_id"]).strip()),
        })
    return records


def locations_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a locations DataFrame to a list of JSON-serializable dicts."""
    records = []
    for _, row in df.iterrows():
        state_raw = row.get("State", None)
        if pd.isna(state_raw) or str(state_raw).strip() == "":
            state = None
        else:
            state = str(state_raw).strip()

        records.append({
            "event":     str(row["Event"]).strip(),
            "latitude":  float(row["Latitude"]),
            "longitude": float(row["Longitude"]),
            "state":     state,
        })
    return records


def export_all(data_dir: str = "data", output_dir: str = None) -> None:
    """
    Read all three CSVs and write their JSON equivalents.

    Args:
        data_dir:   Directory containing the CSV files.
        output_dir: Directory to write JSON files (defaults to data_dir).
    """
    if output_dir is None:
        output_dir = data_dir

    results_df = pd.read_csv(os.path.join(data_dir, "results.csv"), encoding="latin-1")
    athletes_df = pd.read_csv(os.path.join(data_dir, "athletes.csv"))
    locations_df = pd.read_csv(os.path.join(data_dir, "parkrun_locations.csv"))

    files = {
        "results.json": results_to_records(results_df),
        "athletes.json": athletes_to_records(athletes_df),
        "locations.json": locations_to_records(locations_df),
    }

    for filename, records in files.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, separators=(",", ":"))
        print(f"Wrote {len(records)} records to {path}")


if __name__ == "__main__":
    export_all()
