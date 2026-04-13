"""
Tests for the refactored geocoding logic in dashboard/data_loader.py

Tests cover three pure/injectable functions:
  - build_url_slug(event_name)
  - extract_coordinates(html)
  - geocode_single_event(event, fetch_fn, prompt_fn, confirm_fn)

No network requests or terminal prompts are made — all I/O is injected.

Run with: python -m pytest tests/test_geocoding.py -v
"""
import pytest
from dashboard.data_loader import build_url_slug, extract_coordinates, geocode_single_event


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_geo_html(lat, lon):
    """Return minimal HTML with a geo.position meta tag."""
    return f'<html><head><meta name="geo.position" content="{lat};{lon}"/></head></html>'


def make_fetch_fn(responses):
    """
    Return a fake fetch function that maps URLs to (status_code, html) tuples.
    Raises ValueError if an unexpected URL is called.
    """
    def fetch(url):
        if url in responses:
            return responses[url]
        raise ValueError(f"Unexpected URL: {url}")
    return fetch


# ---------------------------------------------------------------------------
# build_url_slug
# ---------------------------------------------------------------------------

class TestBuildUrlSlug:

    def test_lowercases(self):
        assert build_url_slug("Largs Bay") == "largsbay"

    def test_removes_spaces(self):
        assert build_url_slug("Albert Melbourne") == "albertmelbourne"

    def test_removes_commas(self):
        assert build_url_slug("Kate Reed, Reserve") == "katereedreserve"

    def test_single_word(self):
        assert build_url_slug("Bushy") == "bushy"

    def test_already_lowercase(self):
        assert build_url_slug("anstey hill") == "ansteyhill"


# ---------------------------------------------------------------------------
# extract_coordinates
# ---------------------------------------------------------------------------

class TestExtractCoordinates:

    def test_returns_lat_lon_tuple(self):
        html = make_geo_html(-34.8726, 138.4958)
        result = extract_coordinates(html)
        assert result == pytest.approx((-34.8726, 138.4958))

    def test_returns_none_when_no_geo_tag(self):
        html = "<html><head></head></html>"
        assert extract_coordinates(html) is None

    def test_returns_none_when_content_malformed(self):
        html = '<html><head><meta name="geo.position" content="not_valid"/></head></html>'
        assert extract_coordinates(html) is None

    def test_returns_none_when_content_missing(self):
        html = '<html><head><meta name="geo.position"/></head></html>'
        assert extract_coordinates(html) is None

    def test_handles_uk_coordinates(self):
        html = make_geo_html(51.4074, -0.3015)
        lat, lon = extract_coordinates(html)
        assert lat == pytest.approx(51.4074)
        assert lon == pytest.approx(-0.3015)


# ---------------------------------------------------------------------------
# geocode_single_event
# ---------------------------------------------------------------------------

class TestGeocodeSingleEvent:

    def test_returns_coords_on_au_success(self):
        """Happy path — .com.au returns 200 with valid coordinates."""
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/largsbay/": (200, make_geo_html(-34.87, 138.49))
        })
        result = geocode_single_event(
            "Largs Bay", fetch,
            prompt_fn=lambda msg: "",
            confirm_fn=lambda msg: False,
        )
        assert result == pytest.approx((-34.87, 138.49))

    def test_calls_prompt_fn_on_404(self):
        """On 404, prompt_fn should be called with the event name."""
        called_with = []
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/largsbay/": (404, ""),
        })
        def prompt(msg):
            called_with.append(msg)
            return ""
        geocode_single_event("Largs Bay", fetch, prompt_fn=prompt, confirm_fn=lambda m: False)
        assert len(called_with) == 1
        assert "Largs Bay" in called_with[0]

    def test_uses_manual_url_when_provided(self):
        """If user provides a URL, fetch from that URL."""
        manual_url = "https://www.parkrun.com.au/largs/"
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/largsbay/": (404, ""),
            manual_url: (200, make_geo_html(-34.87, 138.49)),
        })
        result = geocode_single_event(
            "Largs Bay", fetch,
            prompt_fn=lambda msg: manual_url,
            confirm_fn=lambda msg: False,
        )
        assert result == pytest.approx((-34.87, 138.49))

    def test_calls_confirm_fn_when_user_skips_prompt(self):
        """If user skips manual URL, confirm_fn should be called."""
        called_with = []
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/bushy/": (404, ""),
        })
        def confirm(msg):
            called_with.append(msg)
            return False
        geocode_single_event("Bushy", fetch, prompt_fn=lambda m: "", confirm_fn=confirm)
        assert len(called_with) == 1

    def test_tries_uk_when_confirm_fn_returns_true(self):
        """If user confirms UK, try parkrun.org.uk."""
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/bushy/": (404, ""),
            "https://www.parkrun.org.uk/bushy/": (200, make_geo_html(51.41, -0.30)),
        })
        result = geocode_single_event(
            "Bushy", fetch,
            prompt_fn=lambda m: "",
            confirm_fn=lambda m: True,
        )
        assert result == pytest.approx((51.41, -0.30))

    def test_returns_none_when_all_fail(self):
        """If .com.au fails, user skips, and UK also fails, return None."""
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/bushy/": (404, ""),
            "https://www.parkrun.org.uk/bushy/": (404, ""),
        })
        result = geocode_single_event(
            "Bushy", fetch,
            prompt_fn=lambda m: "",
            confirm_fn=lambda m: True,
        )
        assert result is None

    def test_returns_none_when_user_declines_uk(self):
        """If user skips prompt and declines UK, return None."""
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/bushy/": (404, ""),
        })
        result = geocode_single_event(
            "Bushy", fetch,
            prompt_fn=lambda m: "",
            confirm_fn=lambda m: False,
        )
        assert result is None

    def test_returns_none_when_manual_url_also_404(self):
        """If user provides a URL but it also 404s, return None without asking about UK."""
        manual_url = "https://www.parkrun.com.au/wrong-slug/"
        fetch = make_fetch_fn({
            "https://www.parkrun.com.au/bushy/": (404, ""),
            manual_url: (404, ""),
        })
        result = geocode_single_event(
            "Bushy", fetch,
            prompt_fn=lambda m: manual_url,
            confirm_fn=lambda m: False,
        )
        assert result is None
