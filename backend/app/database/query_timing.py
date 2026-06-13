"""Log slow SQL statements."""

from __future__ import annotations

import logging
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("app.db")

SLOW_QUERY_MS = 200


def install_query_timing(engine: Engine) -> None:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):
        context._query_start = time.perf_counter()

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):
        start = getattr(context, "_query_start", None)
        if start is None:
            return
        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms < SLOW_QUERY_MS:
            return
        snippet = " ".join(statement.split())[:180]
        logger.warning("SLOW SQL duration_ms=%.1f sql=%s", duration_ms, snippet)
