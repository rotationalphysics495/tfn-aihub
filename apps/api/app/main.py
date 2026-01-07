import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, assets, summaries, actions, auth, pipelines, production, oee, downtime, safety, financial, live_pulse, memory
from app.core.database import initialize_database, shutdown_database
from app.services.scheduler import get_scheduler
from app.services.pipelines.live_pulse import run_live_pulse_poll

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Initialize database connections
    initialize_database()

    # Startup: Initialize and start the polling scheduler
    scheduler = get_scheduler()
    scheduler.set_poll_job(run_live_pulse_poll)
    try:
        await scheduler.start()
        logger.info("Live Pulse polling scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start polling scheduler: {e}")

    yield

    # Shutdown: Stop the polling scheduler
    try:
        await scheduler.shutdown(wait=True)
        logger.info("Live Pulse polling scheduler stopped")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")

    # Shutdown: Clean up database connections
    shutdown_database()


app = FastAPI(
    title="Manufacturing Performance Assistant API",
    description="Backend API for plant performance monitoring and insights",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["Summaries"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
# Story 3.2: Add /api/v1/actions alias for versioned API endpoint (AC#1)
app.include_router(actions.router, prefix="/api/v1/actions", tags=["Actions V1"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["Pipelines"])
app.include_router(production.router, prefix="/api/production", tags=["Production"])
app.include_router(oee.router, prefix="/api/oee", tags=["OEE"])
app.include_router(downtime.router, prefix="/api/v1/downtime", tags=["Downtime"])
app.include_router(safety.router, prefix="/api/safety", tags=["Safety"])
app.include_router(financial.router, prefix="/api/financial", tags=["Financial"])
app.include_router(live_pulse.router, prefix="/api/live-pulse", tags=["Live Pulse"])
# Story 4.1: Memory API for Mem0 vector memory integration
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])


@app.get("/")
async def root():
    return {"message": "Manufacturing Performance Assistant API"}
