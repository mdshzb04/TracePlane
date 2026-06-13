"""Time-range bucketing and zero-filled timeline generation for observability charts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

BucketUnit = Literal["hour", "day", "week"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_range(preset: str) -> tuple[datetime, datetime]:
    end = utc_now()
    if preset == "24h":
        return end - timedelta(hours=24), end
    if preset == "7d":
        return end - timedelta(days=7), end
    if preset == "30d":
        return end - timedelta(days=30), end
    if preset == "90d":
        return end - timedelta(days=90), end
    return end - timedelta(days=7), end


def resolve_bucket(start: datetime, end: datetime) -> BucketUnit:
    hours = (end - start).total_seconds() / 3600
    if hours <= 48:
        return "hour"
    if hours <= 60 * 24:
        return "day"
    return "week"


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _truncate(dt: datetime, bucket: BucketUnit) -> datetime:
    dt = _ensure_utc(dt)
    if bucket == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if bucket == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    # ISO week start (Monday)
    day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return day - timedelta(days=day.weekday())


def _step(bucket: BucketUnit) -> timedelta:
    if bucket == "hour":
        return timedelta(hours=1)
    if bucket == "day":
        return timedelta(days=1)
    return timedelta(weeks=1)


def iter_bucket_starts(start: datetime, end: datetime, bucket: BucketUnit) -> list[datetime]:
    start = _truncate(_ensure_utc(start), bucket)
    end = _ensure_utc(end)
    step = _step(bucket)
    buckets: list[datetime] = []
    current = start
    while current <= end:
        buckets.append(current)
        current += step
    return buckets


def bucket_label(dt: datetime, bucket: BucketUnit) -> str:
    dt = _ensure_utc(dt)
    if bucket == "hour":
        return dt.strftime("%Y-%m-%dT%H:00")
    if bucket == "day":
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def zero_fill_series(
    raw: dict[str, float],
    start: datetime,
    end: datetime,
    bucket: BucketUnit,
) -> list[tuple[str, float]]:
    return [
        (bucket_label(ts, bucket), float(raw.get(bucket_label(ts, bucket), 0.0)))
        for ts in iter_bucket_starts(start, end, bucket)
    ]
