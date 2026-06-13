"""OpenTelemetry self-instrumentation for Traceplane backend."""

from __future__ import annotations

import logging

from app.core.config import settings  # noqa: F401 — used in setup_otel

logger = logging.getLogger(__name__)

_tracer = None
_instrumented = False


def setup_otel(service_name: str = "traceplane-api") -> None:
    """Best-effort OTel setup — no-op when opentelemetry is not installed."""
    global _tracer, _instrumented
    if _instrumented:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        logger.info("OpenTelemetry packages not installed — using request tracing middleware only")
        return

    resource = Resource.create(
        {"service.name": service_name, "deployment.environment": settings.ENV}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)

    try:
        from sqlalchemy import create_engine

        sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
        SQLAlchemyInstrumentor().instrument(engine=sync_engine)
    except Exception as exc:
        logger.debug("SQLAlchemy OTel instrumentation skipped: %s", exc)

    _instrumented = True
    logger.info("OpenTelemetry tracing enabled for %s", service_name)


def instrument_fastapi(app) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        return
    FastAPIInstrumentor.instrument_app(app)


def get_tracer():
    return _tracer
