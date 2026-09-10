"""
LLM Cost Optimization Gateway
==============================
FastAPI entry point. Initializes providers, database, and mounts all routers.
"""
from __future__ import annotations
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from models.database import init_db
from models.config import settings
from models.schemas import HealthResponse
from gateway.router import get_router
from gateway.cache import get_cache
from api.chat import router as chat_router
from api.analytics import router as analytics_router
from api.admin import router as admin_router

logging.basicConfig(
    level=getattr(logging, settings.GATEWAY_LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

START_TIME = time.time()

# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 LLM Cost Optimization Gateway starting up...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Auto-seed sample analytics if database is empty
    try:
        from seed import seed_database
        await seed_database(auto_only_if_empty=True)
    except Exception as e:
        logger.warning(f"Auto-seed warning: {e}")

    # Initialize router (load providers)
    router = get_router()
    router.setup(
        openai_key=settings.OPENAI_API_KEY,
        anthropic_key=settings.ANTHROPIC_API_KEY,
        google_key=settings.GOOGLE_API_KEY,
        mock=settings.MOCK_PROVIDERS,
    )

    # Warm up cache (loads embedding model)
    get_cache()

    logger.info("✅ Gateway ready!")
    yield

    logger.info("🛑 Gateway shutting down...")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="LLM Cost Optimization Gateway",
    description=(
        "A smart API gateway that routes LLM requests to the cheapest capable provider, "
        "caches semantically similar prompts, tracks costs, and enforces per-key budgets."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(admin_router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check — returns provider status and cache info."""
    smart_router = get_router()
    cache = get_cache()
    provider_health = await smart_router.health()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        providers=provider_health,
        cache_entries=cache.stats["size"],
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse, tags=["System"], include_in_schema=False)
async def dashboard():
    """Serve the cost analytics dashboard."""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "index.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return {
        "name": "LLM Cost Optimization Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/health",
    }


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=settings.GATEWAY_DEBUG,
        log_level=settings.GATEWAY_LOG_LEVEL,
    )
