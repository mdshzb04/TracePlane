"""Lightweight timing helpers for performance diagnostics."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger("app.timing")


@asynccontextmanager
async def timed(label: str, *, slow_ms: float = 200) -> AsyncIterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms >= slow_ms:
            logger.warning("SLOW %s duration_ms=%.1f", label, duration_ms)
        else:
            logger.debug("%s duration_ms=%.1f", label, duration_ms)
