"""
Pipeline API Endpoints

Provides endpoints for manual pipeline triggering, status checking,
and execution log viewing.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #8 - Pipeline Execution Logging
AC: #10 - API Endpoints
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.pipeline import (
    PipelineExecutionLog,
    PipelineResult,
    PipelineStatus,
    PipelineStatusResponse,
    PipelineTriggerRequest,
    PipelineTriggerResponse,
)
from app.models.user import CurrentUser
from app.services.pipelines.morning_report import get_pipeline, run_morning_report

logger = logging.getLogger(__name__)

router = APIRouter()

# Track if pipeline is currently running using a dict for thread-safety reference semantics
# Note: For true multi-worker deployments, use Redis or database locking
_pipeline_state = {"is_running": False}


async def _execute_pipeline(target_date: date, force: bool = False) -> None:
    """Background task to execute the pipeline."""
    _pipeline_state["is_running"] = True
    try:
        await run_morning_report(target_date, force)
    finally:
        _pipeline_state["is_running"] = False


@router.post(
    "/morning-report/trigger",
    response_model=PipelineTriggerResponse,
    summary="Trigger Morning Report Pipeline",
    description="Manually trigger the morning report batch pipeline for a specific date."
)
async def trigger_morning_report(
    request: PipelineTriggerRequest = None,
    background_tasks: BackgroundTasks = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> PipelineTriggerResponse:
    """
    Manually trigger the morning report pipeline.

    - Requires authentication
    - Defaults to processing yesterday's data (T-1)
    - Can specify a target date to reprocess historical data
    - Use force=True to replace existing data for that date
    """
    if _pipeline_state["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline is already running. Please wait for completion."
        )

    # Default request if not provided
    if request is None:
        request = PipelineTriggerRequest()

    # Default to yesterday (T-1)
    target_date = request.target_date or (date.today() - timedelta(days=1))

    logger.info(
        f"Pipeline trigger requested by {current_user.email} for {target_date}"
    )

    # Execute pipeline in background
    _pipeline_state["is_running"] = True
    background_tasks.add_task(_execute_pipeline, target_date, request.force)

    return PipelineTriggerResponse(
        message=f"Morning Report pipeline triggered for {target_date}",
        status=PipelineStatus.RUNNING,
        target_date=target_date,
    )


@router.get(
    "/morning-report/status",
    response_model=PipelineStatusResponse,
    summary="Get Pipeline Status",
    description="Get the current status of the morning report pipeline."
)
async def get_pipeline_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> PipelineStatusResponse:
    """
    Get the current status of the morning report pipeline.

    Returns:
        - Last run details if available
        - Whether pipeline is currently running
        - Next scheduled run time (if scheduled)
    """
    pipeline = get_pipeline()
    last_run = pipeline.get_last_execution()

    # Calculate next scheduled run (06:00 AM tomorrow)
    now = datetime.utcnow()
    next_run = datetime(now.year, now.month, now.day, 6, 0, 0) + timedelta(days=1)

    return PipelineStatusResponse(
        last_run=last_run,
        is_running=_pipeline_state["is_running"],
        next_scheduled_run=next_run,
    )


@router.get(
    "/morning-report/logs",
    response_model=List[PipelineExecutionLog],
    summary="Get Pipeline Execution Logs",
    description="Get the execution history of the morning report pipeline."
)
async def get_pipeline_logs(
    limit: int = 10,
    current_user: CurrentUser = Depends(get_current_user),
) -> List[PipelineExecutionLog]:
    """
    Get recent execution logs for the morning report pipeline.

    Args:
        limit: Maximum number of logs to return (default: 10, max: 100)

    Returns:
        List of execution logs, most recent first
    """
    # Cap limit at 100
    limit = min(limit, 100)

    pipeline = get_pipeline()
    logs = pipeline.get_execution_logs(limit)

    # Return in reverse order (most recent first)
    return list(reversed(logs))


@router.post(
    "/morning-report/run-sync",
    response_model=PipelineResult,
    summary="Run Pipeline Synchronously",
    description="Run the morning report pipeline synchronously (blocking). For testing only."
)
async def run_pipeline_sync(
    request: PipelineTriggerRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> PipelineResult:
    """
    Run the morning report pipeline synchronously.

    WARNING: This is a blocking operation that may take several minutes.
    Use /trigger for production use cases.

    - Requires authentication
    - Waits for pipeline completion before returning
    - Returns full pipeline result with all details
    """
    if _pipeline_state["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline is already running. Please wait for completion."
        )

    # Default request if not provided
    if request is None:
        request = PipelineTriggerRequest()

    # Default to yesterday (T-1)
    target_date = request.target_date or (date.today() - timedelta(days=1))

    logger.info(
        f"Synchronous pipeline run requested by {current_user.email} for {target_date}"
    )

    _pipeline_state["is_running"] = True
    try:
        result = await run_morning_report(target_date, request.force)
        return result
    finally:
        _pipeline_state["is_running"] = False
