"""
Tests for scripts/export_json.py

Tests are written against pure transformation functions (DataFrame in, list of
dicts out) so no file I/O is needed. Each function is tested in isolation with
minimal in-memory data.
"""
import pytest
import pandas as pd

from scripts.export_json import results_to_records, athletes_to_records, locations_to_records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_results_df(**overrides):
    """Return a single-row results DataFrame with sensible defaults."""
    row = {
        "Event": "Largs Bay",
        "Run Date": "10/01/2026",
        "Run Number": 369,
        "Pos": 50,
        "Time": "25:30",
        "Age Grade": "57.39%",
        "PB": "",
        "Athlete Name": "Brendan DIMECH",
        "Athlete ID": 7432768,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def make_athletes_df(**overrides):
    """Return a single-row athletes DataFrame with sensible defaults."""
    row = {"name": "Brendan DIMECH", "parkrun_id": 7432768}
    row.update(overrides)
    return pd.DataFrame([row])


def make_locations_df(**overrides):
    """Return a single-row locations DataFrame with sensible defaults."""
    row = {"Event": "Largs Bay", "Latitude": -34.8726, "Longitude": 138.4958, "State": "SA"}
    row.update(overrides)
    return pd.DataFrame([row])


# ---------------------------------------------------------------------------
# results_to_records
# ---------------------------------------------------------------------------

class TestResultsToRecords:

    def test_returns_list(self):
        records = results_to_records(make_results_df())
        assert isinstance(records, list)

    def test_row_count_matches(self):
        df = pd.concat([make_results_df(), make_results_df(Event="Jamestown Golf Course")])
        records = results_to_records(df)
        assert len(records) == 2

    def test_required_keys_present(self):
        record = results_to_records(make_results_df())[0]
        expected_keys = {
            "event", "run_date", "run_number", "position",
            "time", "time_seconds", "age_grade", "is_pb",
            "athlete_name", "athlete_id",
        }
        assert expected_keys == set(record.keys())

    def test_position_is_int(self):
        record = results_to_records(make_results_df(Pos="50"))[0]
        assert isinstance(record["position"], int)
        assert record["position"] == 50

    def test_run_number_is_int(self):
        record = results_to_records(make_results_df())[0]
        assert isinstance(record["run_number"], int)

    def test_athlete_id_is_int(self):
        record = results_to_records(make_results_df())[0]
        assert isinstance(record["athlete_id"], int)

    def test_age_grade_is_float(self):
        """Age Grade comes in as '57.39%' — should be stored as 57.39."""
        record = results_to_records(make_results_df())[0]
        assert isinstance(record["age_grade"], float)
        assert record["age_grade"] == pytest.approx(57.39)

    def test_time_seconds_is_int(self):
        """'25:30' should convert to 1530 seconds."""
        record = results_to_records(make_results_df(Time="25:30"))[0]
        assert record["time_seconds"] == 1530

    def test_time_string_preserved(self):
        record = results_to_records(make_results_df(Time="25:30"))[0]
        assert record["time"] == "25:30"

    def test_run_date_is_iso_format(self):
        """'10/01/2026' (DD/MM/YYYY) should become '2026-01-10'."""
        record = results_to_records(make_results_df())[0]
        assert record["run_date"] == "2026-01-10"

    def test_is_pb_false_when_empty(self):
        record = results_to_records(make_results_df(PB=""))[0]
        assert record["is_pb"] is False

    def test_is_pb_true_when_set(self):
        record = results_to_records(make_results_df(PB="PB"))[0]
        assert record["is_pb"] is True

    def test_is_pb_true_when_whitespace_value(self):
        """Some entries may have a non-empty whitespace PB — should be False."""
        record = results_to_records(make_results_df(PB="  "))[0]
        assert record["is_pb"] is False

    def test_known_row_values(self):
        """Regression: a specific known row round-trips correctly."""
        df = make_results_df(
            Event="Jamestown Golf Course",
            **{"Run Date": "04/04/2026", "Run Number": 212, "Pos": 3,
               "Time": "24:08", "Age Grade": "57.39%", "PB": "",
               "Athlete Name": "Brendan DIMECH", "Athlete ID": 7432768}
        )
        record = results_to_records(df)[0]
        assert record["event"] == "Jamestown Golf Course"
        assert record["run_date"] == "2026-04-04"
        assert record["run_number"] == 212
        assert record["position"] == 3
        assert record["time"] == "24:08"
        assert record["time_seconds"] == 1448
        assert record["age_grade"] == pytest.approx(57.39)
        assert record["is_pb"] is False
        assert record["athlete_name"] == "Brendan DIMECH"
        assert record["athlete_id"] == 7432768


# ---------------------------------------------------------------------------
# athletes_to_records
# ---------------------------------------------------------------------------

class TestAthletesToRecords:

    def test_returns_list(self):
        records = athletes_to_records(make_athletes_df())
        assert isinstance(records, list)

    def test_row_count_matches(self):
        df = pd.concat([make_athletes_df(), make_athletes_df(name="Charlie GORDON", parkrun_id=1930646)])
        records = athletes_to_records(df)
        assert len(records) == 2

    def test_required_keys_present(self):
        record = athletes_to_records(make_athletes_df())[0]
        assert set(record.keys()) == {"name", "parkrun_id"}

    def test_parkrun_id_is_int(self):
        record = athletes_to_records(make_athletes_df())[0]
        assert isinstance(record["parkrun_id"], int)

    def test_leading_space_stripped_from_parkrun_id(self):
        """athletes.csv has entries like 'name, 7830731' with a leading space."""
        df = make_athletes_df(parkrun_id=" 7830731")
        record = athletes_to_records(df)[0]
        assert record["parkrun_id"] == 7830731

    def test_leading_space_stripped_from_name(self):
        df = make_athletes_df(name="  Kylie EGAN")
        record = athletes_to_records(df)[0]
        assert record["name"] == "Kylie EGAN"

    def test_name_is_string(self):
        record = athletes_to_records(make_athletes_df())[0]
        assert isinstance(record["name"], str)


# ---------------------------------------------------------------------------
# locations_to_records
# ---------------------------------------------------------------------------

class TestLocationsToRecords:

    def test_returns_list(self):
        records = locations_to_records(make_locations_df())
        assert isinstance(records, list)

    def test_row_count_matches(self):
        df = pd.concat([make_locations_df(), make_locations_df(Event="Anstey Hill")])
        records = locations_to_records(df)
        assert len(records) == 2

    def test_required_keys_present(self):
        record = locations_to_records(make_locations_df())[0]
        assert set(record.keys()) == {"event", "latitude", "longitude", "state"}

    def test_latitude_is_float(self):
        record = locations_to_records(make_locations_df())[0]
        assert isinstance(record["latitude"], float)

    def test_longitude_is_float(self):
        record = locations_to_records(make_locations_df())[0]
        assert isinstance(record["longitude"], float)

    def test_state_is_string(self):
        record = locations_to_records(make_locations_df(State="SA"))[0]
        assert record["state"] == "SA"

    def test_missing_state_is_none(self):
        """Locations CSV has many rows with an empty State column."""
        record = locations_to_records(make_locations_df(State=""))[0]
        assert record["state"] is None

    def test_nan_state_is_none(self):
        """pd.read_csv converts empty cells to NaN — should become None."""
        df = make_locations_df()
        df["State"] = float("nan")
        record = locations_to_records(df)[0]
        assert record["state"] is None

    def test_coordinates_preserved(self):
        record = locations_to_records(make_locations_df(Latitude=-34.8726, Longitude=138.4958))[0]
        assert record["latitude"] == pytest.approx(-34.8726)
        assert record["longitude"] == pytest.approx(138.4958)
