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


def results_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a results DataFrame to a list of JSON-serializable dicts."""
    raise NotImplementedError


def athletes_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert an athletes DataFrame to a list of JSON-serializable dicts."""
    raise NotImplementedError


def locations_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a locations DataFrame to a list of JSON-serializable dicts."""
    raise NotImplementedError


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
            json.dump(records, f, indent=2)
        print(f"Wrote {len(records)} records to {path}")


if __name__ == "__main__":
    export_all()
