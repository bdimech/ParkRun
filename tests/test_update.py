"""
Tests for update.py

Tests cover the pure helper functions only — no web requests are made.
The web-fetching parts (fetch_parkrun_results) are tested implicitly
through the existing scraper tests.

Run with: python -m pytest tests/test_update.py -v
"""
import pytest
import pandas as pd
import os

from update import athlete_already_exists, append_athlete


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_athletes_df(*rows):
    """Build a small athletes DataFrame from (name, parkrun_id) tuples."""
    return pd.DataFrame(rows, columns=["name", "parkrun_id"])


# ---------------------------------------------------------------------------
# athlete_already_exists
# ---------------------------------------------------------------------------

class TestAthleteAlreadyExists:

    def test_returns_false_when_empty(self):
        df = make_athletes_df()
        assert athlete_already_exists(7432768, df) is False

    def test_returns_true_when_id_present(self):
        df = make_athletes_df(("Brendan DIMECH", 7432768))
        assert athlete_already_exists(7432768, df) is True

    def test_returns_false_when_different_id(self):
        df = make_athletes_df(("Brendan DIMECH", 7432768))
        assert athlete_already_exists(9999999, df) is False

    def test_matches_id_as_string(self):
        """parkrun_id may be stored as string in CSV after read_csv."""
        df = make_athletes_df(("Brendan DIMECH", "7432768"))
        assert athlete_already_exists(7432768, df) is True

    def test_matches_id_as_int_against_string_input(self):
        df = make_athletes_df(("Brendan DIMECH", 7432768))
        assert athlete_already_exists("7432768", df) is True

    def test_multiple_athletes_correct_match(self):
        df = make_athletes_df(
            ("Brendan DIMECH", 7432768),
            ("Charlie GORDON", 1930646),
            ("Kylie EGAN", 7830731),
        )
        assert athlete_already_exists(1930646, df) is True
        assert athlete_already_exists(9999999, df) is False


# ---------------------------------------------------------------------------
# append_athlete
# ---------------------------------------------------------------------------

class TestAppendAthlete:

    def test_appends_to_existing_csv(self, tmp_path):
        csv = tmp_path / "athletes.csv"
        csv.write_text("name,parkrun_id\nBrendan DIMECH,7432768\n")
        append_athlete("Jane SMITH", 9999999, str(csv))
        df = pd.read_csv(csv)
        assert len(df) == 2
        assert df.iloc[1]["name"] == "Jane SMITH"
        assert int(df.iloc[1]["parkrun_id"]) == 9999999

    def test_creates_csv_if_missing(self, tmp_path):
        csv = tmp_path / "athletes.csv"
        append_athlete("Jane SMITH", 9999999, str(csv))
        df = pd.read_csv(csv)
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Jane SMITH"

    def test_strips_whitespace_from_name(self, tmp_path):
        csv = tmp_path / "athletes.csv"
        csv.write_text("name,parkrun_id\n")
        append_athlete("  Jane SMITH  ", 9999999, str(csv))
        df = pd.read_csv(csv)
        assert df.iloc[0]["name"] == "Jane SMITH"

    def test_does_not_duplicate_existing_athlete(self, tmp_path):
        csv = tmp_path / "athletes.csv"
        csv.write_text("name,parkrun_id\nBrendan DIMECH,7432768\n")
        append_athlete("Brendan DIMECH", 7432768, str(csv))
        df = pd.read_csv(csv)
        assert len(df) == 1

    def test_preserves_existing_rows(self, tmp_path):
        csv = tmp_path / "athletes.csv"
        csv.write_text("name,parkrun_id\nBrendan DIMECH,7432768\nCharlie GORDON,1930646\n")
        append_athlete("Jane SMITH", 9999999, str(csv))
        df = pd.read_csv(csv)
        assert len(df) == 3
        assert df.iloc[0]["name"] == "Brendan DIMECH"
        assert df.iloc[1]["name"] == "Charlie GORDON"
