"""Shared numeric formatting for API responses."""


def format_cost(value: float | None) -> float | None:
    """Normalize cost to 6 decimal places for consistent API output."""
    if value is None:
        return None
    return round(float(value), 6)
