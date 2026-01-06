from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, assets, summaries, actions, auth, pipelines
from app.core.database import initialize_database, shutdown_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Initialize database connections
    initialize_database()
    yield
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
