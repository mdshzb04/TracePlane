from datetime import datetime, timezone

from app.services.session_replay import _parse_ts, _preview


def test_preview_truncates():
    assert _preview("short") == "short"
    long = "x" * 500
    assert _preview(long, limit=10) == "x" * 10 + "…"


def test_preview_none():
    assert _preview(None) is None
    assert _preview("") is None


def test_parse_ts_datetime():
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert _parse_ts(dt) == dt


def test_parse_ts_iso_string():
    parsed = _parse_ts("2026-01-01T12:00:00Z")
    assert parsed is not None
    assert parsed.year == 2026
