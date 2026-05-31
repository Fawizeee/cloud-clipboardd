"""
Cloud Clipboard — FastAPI Application Entry Point
=================================================
Wires up the application, middleware, lifespan handler, and health check.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import router
from core.config import settings
from db.session import engine
from db.models import base  # noqa: F401 — ensure Base is imported
# Import all models so SQLAlchemy registers their metadata before create_all
from db.models import user, clipboard, device, folder, shared_item, sync_event  # noqa: F401
from db.models.base import Base
from middleware.logging import LoggingMiddleware
from middleware.rate_limit import RateLimitMiddleware

# ── Logging configuration ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cloud_clipboard")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup (no-op if they already exist)."""
    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified / created.")
    yield
    logger.info("Shutting down.")


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="REST + WebSocket API for the Cloud Clipboard app.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware (order matters — first added is outermost wrapper) ─────────────

# 1. CORS — must be first so pre-flight OPTIONS requests are handled
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate limiting on auth endpoints
app.add_middleware(RateLimitMiddleware)

# 3. Request / response logging
app.add_middleware(LoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(router)


# ── Utility endpoints ─────────────────────────────────────────────────────────

@app.get("/", tags=["utility"])
def read_root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health", tags=["utility"])
async def health():
    """
    Detailed health check.
    Attempts a lightweight DB query to verify connectivity.
    """
    from sqlalchemy import text
    from db.session import SessionLocal

    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    overall = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall,
        "services": {
            "database": db_status,
        },
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


# ── Dev server entry-point ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)