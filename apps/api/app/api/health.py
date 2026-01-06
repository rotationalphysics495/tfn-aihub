from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_mssql_db

router = APIRouter()


class DatabaseHealth(BaseModel):
    """Health check response for database connection."""
    status: str
    message: str
    connected: bool
    pool: Optional[dict] = None


class HealthResponse(BaseModel):
    """Overall health check response."""
    status: str
    service: str
    database: DatabaseHealth


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint that includes MSSQL connection status.

    Returns:
        HealthResponse: Health status including database connectivity.

    Returns 200 if all systems are healthy, 503 if database is unhealthy.
    """
    mssql_db = get_mssql_db()
    db_health = mssql_db.check_health()

    # Determine overall status based on database health
    # If DB is not configured, we still consider the service healthy
    # (it may run in degraded mode without MSSQL)
    overall_status = "healthy"
    http_status = status.HTTP_200_OK

    if db_health["status"] == "unhealthy" or db_health["status"] == "error":
        overall_status = "degraded"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    response_data = {
        "status": overall_status,
        "service": "manufacturing-api",
        "database": {
            "status": db_health["status"],
            "message": db_health["message"],
            "connected": db_health["connected"],
            "pool": db_health.get("pool"),
        },
    }

    return JSONResponse(content=response_data, status_code=http_status)


@router.get("/api/health", response_model=HealthResponse)
async def api_health_check():
    """
    Alternative health check endpoint at /api/health.

    Returns:
        HealthResponse: Health status including database connectivity.
    """
    return await health_check()
