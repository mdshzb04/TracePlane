from datetime import datetime, timezone

from app.services.session_replay import _parse_ts, _preview


def test_preview_edge_cases():
    assert _preview("abc", limit=10) == "abc"


def test_parse_ts_invalid():
    assert _parse_ts("not-a-date") is None


def test_replay_step_ordering_logic():
    """Offset-based sort mirrors session replay waterfall ordering."""
    steps = [
        {"offset_ms": 200, "step_index": 1},
        {"offset_ms": 50, "step_index": 0},
        {"offset_ms": 200, "step_index": 2},
    ]
    ordered = sorted(steps, key=lambda s: (s["offset_ms"], s["step_index"]))
    assert ordered[0]["offset_ms"] == 50
    assert ordered[-1]["step_index"] == 2


def test_session_replay_route_exists():
    from app.main import app

    paths = [getattr(r, "path", "") for r in app.routes]
    assert any("session-replay" in p for p in paths)
