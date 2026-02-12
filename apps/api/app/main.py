import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, assets, summaries, actions, auth, pipelines, production, oee, downtime, safety, financial, live_pulse, memory, chat, asset_history, citations, agent, cache, voice, briefing, preferences, handoff, admin, team, schedule, followups, action_plans, notifications
from app.core.database import initialize_database, shutdown_database
from app.services.scheduler import get_scheduler
from app.services.pipelines.live_pulse import run_live_pulse_poll
from app.services.notifications.escalation import run_escalation_check

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Clear endpoint caches
    from app.api.downtime import _pareto_cache
    _pareto_cache.clear()

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

    # Story 18.5: Register escalation check job on the underlying scheduler
    # Option A per dev notes — add directly to scheduler._scheduler to avoid modifying PipelineScheduler
    try:
        if scheduler._scheduler is not None and scheduler._scheduler.running:
            from apscheduler.triggers.interval import IntervalTrigger
            from app.core.config import get_settings
            _settings = get_settings()
            scheduler._scheduler.add_job(
                run_escalation_check,
                IntervalTrigger(minutes=_settings.escalation_check_interval_minutes),
                id="escalation_check",
                name="Escalation Nudge Check",
                replace_existing=True,
                misfire_grace_time=120,
            )
            logger.info("Escalation nudge check job registered")
    except Exception as e:
        logger.warning(f"Failed to register escalation check job: {e}")

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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
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
# Story 11.1: Add /api/v1/production alias for versioned API endpoint (AC#1)
app.include_router(production.router, prefix="/api/v1/production", tags=["Production V1"])
app.include_router(oee.router, prefix="/api/oee", tags=["OEE"])
app.include_router(downtime.router, prefix="/api/v1/downtime", tags=["Downtime"])
app.include_router(safety.router, prefix="/api/safety", tags=["Safety"])
app.include_router(financial.router, prefix="/api/financial", tags=["Financial"])
app.include_router(live_pulse.router, prefix="/api/live-pulse", tags=["Live Pulse"])
# Story 4.1: Memory API for Mem0 vector memory integration
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
# Story 4.2: Chat API for Text-to-SQL natural language queries
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
# Story 4.4: Asset History Memory API for historical context
app.include_router(asset_history.router, prefix="/api/assets", tags=["Asset History"])
# Story 4.5: Citations API for cited response generation
app.include_router(citations.router, prefix="/api/citations", tags=["Citations"])
# Story 5.1: Agent API for LangChain agent-based queries
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
# Story 5.8: Cache API for tool response cache management
app.include_router(cache.router, prefix="/api/cache", tags=["Cache"])
# Story 8.1/8.2: Voice API for TTS and STT features
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
# Story 8.4: Briefing API for morning briefings
app.include_router(briefing.router, prefix="/api/v1/briefing", tags=["Briefing"])
# Story 8.8: User Preferences API for onboarding and settings
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["Preferences"])
# Story 9.1: Shift Handoff API for handoff creation and management
app.include_router(handoff.router, prefix="/api/v1/handoff", tags=["Handoff"])
# Story 9.13: Admin API for asset assignment management
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
# Team API for listing team members (any authenticated user)
app.include_router(team.router, prefix="/api/v1/team", tags=["Team"])
# Story 12.3: Schedule Upload API for CSV/Excel schedule file upload and confirmation
app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["Schedule"])
# Story 15.2: Follow-Ups API for creating follow-ups with email notifications
app.include_router(followups.router, prefix="/api/v1/followups", tags=["Follow-Ups"])
# Story 16.2: Action Plans CRUD API
app.include_router(action_plans.router, prefix="/api/v1/action-plans", tags=["Action Plans"])
# Story 18.2: Notifications API for Teams webhook integration
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])


@app.get("/")
async def root():
    return {"message": "Manufacturing Performance Assistant API"}
