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
    raise NotImplementedError


def append_athlete(name: str, parkrun_id, csv_path: str) -> None:
    """
    Append an athlete to the CSV file.
    Strips whitespace from name. Does nothing if athlete already exists.
    Creates the file if it doesn't exist.
    """
    raise NotImplementedError


def cmd_add(parkrun_id: int) -> None:
    """Look up an athlete by ID, confirm with the user, add to athletes.csv."""
    raise NotImplementedError


def cmd_update() -> None:
    """Scrape latest results for all athletes, update CSVs, rebuild JSON."""
    raise NotImplementedError


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
