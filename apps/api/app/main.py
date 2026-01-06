import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, assets, summaries, actions, auth, pipelines
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
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["Pipelines"])


@app.get("/")
async def root():
    return {"message": "Manufacturing Performance Assistant API"}
