from datetime import datetime, timezone, timedelta

from app.core.time_buckets import iter_bucket_starts, resolve_bucket, zero_fill_series


def test_resolve_bucket_hour_for_24h():
    end = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    start = end - timedelta(hours=24)
    assert resolve_bucket(start, end) == "hour"


def test_zero_fill_empty_series():
    end = datetime(2026, 1, 3, 0, 0, tzinfo=timezone.utc)
    start = end - timedelta(days=2)
    filled = zero_fill_series({}, start, end, "day")
    assert len(filled) == 3
    assert all(v == 0.0 for _, v in filled)


def test_iter_bucket_starts_hourly():
    end = datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)
    start = datetime(2026, 1, 1, 1, 30, tzinfo=timezone.utc)
    buckets = iter_bucket_starts(start, end, "hour")
    assert buckets[0] == datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc)
    assert len(buckets) == 3
