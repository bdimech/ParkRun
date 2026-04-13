"""
ParkRun data update script.

Usage:
    python update.py --add <parkrun_id>   # look up athlete, confirm, add to athletes.csv
    python update.py --update             # scrape all athletes, update CSVs, rebuild JSON
"""
import argparse
import os
import pandas as pd


def athlete_already_exists(parkrun_id, athletes_df: pd.DataFrame) -> bool:
    """Return True if parkrun_id is already in the athletes DataFrame."""
    if athletes_df.empty:
        return False
    return bool(athletes_df["parkrun_id"].astype(str).str.strip().isin([str(parkrun_id).strip()]).any())


def append_athlete(name: str, parkrun_id, csv_path: str) -> None:
    """
    Append an athlete to the CSV file.
    Strips whitespace from name. Does nothing if athlete already exists.
    Creates the file if it doesn't exist.
    """
    name = name.strip()

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["name", "parkrun_id"])

    if athlete_already_exists(parkrun_id, df):
        return

    new_row = pd.DataFrame([{"name": name, "parkrun_id": parkrun_id}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(csv_path, index=False)


def cmd_add(parkrun_id: int) -> None:
    """Look up an athlete by ID, confirm with the user, add to athletes.csv."""
    from dashboard.data_fetcher import fetch_parkrun_results, ParkRunScraperError

    athletes_csv = os.path.join("data", "athletes.csv")

    # Check for duplicate before hitting the web
    if os.path.exists(athletes_csv):
        existing = pd.read_csv(athletes_csv)
        if athlete_already_exists(parkrun_id, existing):
            print(f"Athlete {parkrun_id} is already in athletes.csv — nothing to do.")
            return

    print(f"Looking up athlete {parkrun_id} on parkrun.com.au...")
    try:
        name, _ = fetch_parkrun_results(parkrun_id)
    except ParkRunScraperError as e:
        print(f"Error: {e}")
        return

    print(f"\nFound: {name} (ID: {parkrun_id})")
    confirm = input("Add this athlete? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    append_athlete(name, parkrun_id, athletes_csv)
    print(f"Added {name} to {athletes_csv}.")


def cmd_update() -> None:
    """Scrape latest results for all athletes, update CSVs, rebuild JSON."""
    from dashboard.data_loader import update_results_from_web
    from scripts.export_json import export_all

    results_csv  = os.path.join("data", "results.csv")
    athletes_csv = os.path.join("data", "athletes.csv")

    print("Fetching latest results from parkrun.com.au...")
    success = update_results_from_web(results_csv, athletes_csv)

    if not success:
        print("Update failed or no athletes configured.")
        return

    print("Rebuilding JSON files...")
    export_all(data_dir="data")
    print("Done. Commit and push data/*.json to deploy.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ParkRun data updater")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", type=int, metavar="PARKRUN_ID",
                       help="Look up athlete by ID and add to athletes.csv")
    group.add_argument("--update", action="store_true",
                       help="Scrape latest results for all athletes and rebuild JSON")
    args = parser.parse_args()

    if args.add:
        cmd_add(args.add)
    elif args.update:
        cmd_update()
