import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.auth.middleware import LoggingMiddleware
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.core.request_tracing import RequestTracingMiddleware
from app.core.security_headers import CSRFMiddleware
from app.database.session import async_session_factory, dispose_engine
from app.routers import (
    agents,
    alerts,
    analytics,
    api_keys,
    auth,
    evaluation_engine,
    executions,
    ingest,
    organizations,
    providers,
    quickstart,
    system,
    ws,
)
from app.services.email_service import validate_resend_at_startup
from app.services.langfuse_service import langfuse_service

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def _bootstrap_dev_roles() -> None:
    """In local development, upgrade viewer accounts so builder/investigator work out of the box."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("UPDATE users SET role = 'developer' WHERE role = 'viewer'")
        )
        await session.commit()
        if result.rowcount:
            logger.info("Development bootstrap: upgraded %s viewer(s) to developer", result.rowcount)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.encryption import encryption_self_test
    from app.core.otel import setup_otel

    setup_otel()
    encryption_self_test()
    if settings.ENV != "development" and not settings.ENCRYPTION_KEY.strip():
        logger.warning(
            "ENCRYPTION_KEY is not set — provider secrets use SECRET_KEY. "
            "Set a dedicated ENCRYPTION_KEY in production and keep it stable."
        )
    logger.info("Starting Traceplane API (env=%s)", settings.ENV)
    validate_resend_at_startup()
    if settings.ENV == "development":
        await _bootstrap_dev_roles()
    yield
    logger.info("Shutting down Traceplane API")
    if langfuse_service.is_enabled():
        langfuse_service.flush()
        langfuse_service.shutdown()
    await dispose_engine()


app = FastAPI(
    title="Traceplane",
    description="AI Agent Control Plane — monitor, evaluate, govern, and debug AI agents in production",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_kwargs: dict = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.ENV == "development":
    _cors_kwargs["allow_origin_regex"] = r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?"
    _cors_kwargs["allow_origins"] = settings.cors_origins_list
else:
    _cors_kwargs["allow_origins"] = settings.cors_origins_list

app.add_middleware(CORSMiddleware, **_cors_kwargs)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(evaluation_engine.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(providers.router, prefix="/api/v1")
app.include_router(quickstart.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")

from app.core.otel import instrument_fastapi  # noqa: E402

instrument_fastapi(app)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "Unhandled exception on %s %s [request_id=%s]",
        request.method,
        request.url.path,
        request_id,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


@app.get("/", tags=["meta"])
async def root():
    return {
        "name": "Traceplane API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
        "frontend": "http://localhost:3000",
        "message": "This is the API server. Open the frontend at http://localhost:3000",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    from app.core.infrastructure import check_celery_broker, check_redis, celery_worker_reachable

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            schema_check = await session.execute(
                text("SELECT to_regclass('public.users') IS NOT NULL AS ready")
            )
            if not schema_check.scalar():
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "not_ready",
                        "database": "connected",
                        "schema": "missing",
                        "detail": "Run alembic upgrade head",
                    },
                )
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "error"},
        )

    from app.core.rate_limit import get_rate_limit_status

    redis_status = check_redis()
    celery_broker = check_celery_broker()
    worker_up = celery_worker_reachable() if settings.CELERY_ENABLED else None

    # Redis/Celery are optional — API stays ready; ingest uses sync fallback when Redis is down
    return {
        "status": "ready",
        "database": "ok",
        "schema": "ok",
        "redis": redis_status,
        "celery_broker": celery_broker,
        "celery_worker": worker_up,
        "celery_enabled": settings.CELERY_ENABLED,
        "rate_limit": get_rate_limit_status(),
    }
