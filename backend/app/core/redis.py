"""Backward-compatible Redis accessor — delegates to infrastructure module."""

from app.core.infrastructure import get_redis

__all__ = ["get_redis"]
