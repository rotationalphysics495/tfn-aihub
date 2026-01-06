"""
Background Scheduler Service

Manages APScheduler for polling data pipelines.
Implements the "Live Pulse" (Pipeline B) 15-minute polling cycle.

Story: 2.2 - Polling Data Pipeline (T-15m)
AC: #1 - Background Scheduler Configuration
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Callable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

logger = logging.getLogger(__name__)


class PipelineSchedulerStatus:
    """Tracks the status of the polling pipeline for health checks."""

    def __init__(self):
        self.is_running: bool = False
        self.last_poll_timestamp: Optional[datetime] = None
        self.last_poll_success: bool = True
        self.last_poll_duration_seconds: Optional[float] = None
        self.last_error_message: Optional[str] = None
        self.polls_executed: int = 0
        self.polls_failed: int = 0

    def record_poll_start(self) -> None:
        """Record that a poll has started."""
        pass  # Currently we track end events only

    def record_poll_success(self, duration_seconds: float) -> None:
        """Record a successful poll completion."""
        self.last_poll_timestamp = datetime.utcnow()
        self.last_poll_success = True
        self.last_poll_duration_seconds = duration_seconds
        self.last_error_message = None
        self.polls_executed += 1

    def record_poll_failure(self, error_message: str, duration_seconds: float) -> None:
        """Record a poll failure."""
        self.last_poll_timestamp = datetime.utcnow()
        self.last_poll_success = False
        self.last_poll_duration_seconds = duration_seconds
        self.last_error_message = error_message
        self.polls_executed += 1
        self.polls_failed += 1

    def to_dict(self, scheduler: Optional["PipelineScheduler"] = None) -> dict:
        """Convert status to dictionary for API responses."""
        result = {
            "status": "running" if self.is_running else "stopped",
            "last_poll_timestamp": (
                self.last_poll_timestamp.isoformat()
                if self.last_poll_timestamp else None
            ),
            "last_poll_success": self.last_poll_success,
            "last_poll_duration_seconds": self.last_poll_duration_seconds,
            "last_error_message": self.last_error_message,
            "polls_executed": self.polls_executed,
            "polls_failed": self.polls_failed,
            "next_poll_scheduled": None,
        }

        # Add next scheduled run if scheduler is provided
        if scheduler and scheduler._scheduler:
            job = scheduler._scheduler.get_job("live_pulse_poll")
            if job and job.next_run_time:
                result["next_poll_scheduled"] = job.next_run_time.isoformat()

        return result


class PipelineScheduler:
    """
    Manages the APScheduler for polling pipelines.

    Features:
    - AsyncIOScheduler for non-blocking operation
    - Configurable poll interval via environment variable
    - Job execution tracking for health monitoring
    - Graceful startup and shutdown
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._status = PipelineSchedulerStatus()
        self._poll_job: Optional[Callable] = None
        self._poll_interval_minutes: int = int(
            os.getenv("POLL_INTERVAL_MINUTES", "15")
        )
        self._run_on_startup: bool = os.getenv(
            "POLL_RUN_ON_STARTUP", "true"
        ).lower() == "true"

    @property
    def status(self) -> PipelineSchedulerStatus:
        """Get the current pipeline status."""
        return self._status

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._scheduler is not None and self._scheduler.running

    def _on_job_executed(self, event: JobExecutionEvent) -> None:
        """Handle successful job execution."""
        if event.job_id == "live_pulse_poll":
            # Duration from APScheduler event
            duration = 0.0
            if hasattr(event, 'scheduled_run_time') and event.scheduled_run_time:
                duration = (datetime.now(event.scheduled_run_time.tzinfo) -
                           event.scheduled_run_time).total_seconds()
            logger.info(
                f"Live Pulse poll completed successfully "
                f"(duration: {duration:.2f}s)"
            )

    def _on_job_error(self, event: JobExecutionEvent) -> None:
        """Handle job execution error."""
        if event.job_id == "live_pulse_poll":
            error_msg = str(event.exception) if event.exception else "Unknown error"
            logger.error(f"Live Pulse poll failed: {error_msg}")

    def set_poll_job(self, job_func: Callable) -> None:
        """
        Set the polling job function to be scheduled.

        Args:
            job_func: Async function to execute on each poll cycle
        """
        self._poll_job = job_func

    async def start(self) -> None:
        """
        Start the scheduler and begin polling.

        The scheduler will:
        1. Initialize APScheduler with asyncio support
        2. Add the live pulse job with configured interval
        3. Execute the first poll immediately if configured
        4. Register event listeners for monitoring
        """
        if self._scheduler is not None:
            logger.warning("Scheduler already initialized")
            return

        if self._poll_job is None:
            logger.error("No poll job configured. Call set_poll_job() first.")
            return

        logger.info(
            f"Starting pipeline scheduler "
            f"(interval: {self._poll_interval_minutes} minutes)"
        )

        self._scheduler = AsyncIOScheduler()

        # Add event listeners
        self._scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self._scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )

        # Add the live pulse job
        self._scheduler.add_job(
            self._poll_job,
            IntervalTrigger(minutes=self._poll_interval_minutes),
            id="live_pulse_poll",
            name="Live Pulse Data Pipeline",
            replace_existing=True,
            misfire_grace_time=60,  # Allow 60 second grace for misfired jobs
        )

        # Start the scheduler
        self._scheduler.start()
        self._status.is_running = True

        logger.info("Pipeline scheduler started")

        # Execute first poll immediately if configured
        if self._run_on_startup:
            logger.info("Executing initial poll on startup")
            try:
                await self._poll_job()
            except Exception as e:
                logger.error(f"Initial poll failed: {e}")
                # Don't fail startup - scheduler will retry on next interval

    async def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler gracefully.

        Args:
            wait: If True, wait for running jobs to complete
        """
        if self._scheduler is None:
            return

        logger.info("Shutting down pipeline scheduler")

        self._scheduler.shutdown(wait=wait)
        self._scheduler = None
        self._status.is_running = False

        logger.info("Pipeline scheduler stopped")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled poll time."""
        if self._scheduler is None:
            return None

        job = self._scheduler.get_job("live_pulse_poll")
        if job:
            return job.next_run_time
        return None

    def trigger_poll_now(self) -> bool:
        """
        Trigger an immediate poll execution.

        Returns:
            True if job was triggered, False if scheduler not running
        """
        if self._scheduler is None or not self._scheduler.running:
            return False

        job = self._scheduler.get_job("live_pulse_poll")
        if job:
            job.modify(next_run_time=datetime.now())
            return True
        return False


# Global scheduler instance
_scheduler_instance: Optional[PipelineScheduler] = None


def get_scheduler() -> PipelineScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PipelineScheduler()
    return _scheduler_instance


def get_pipeline_status() -> dict:
    """
    Get the current pipeline status for health checks.

    Returns:
        Dictionary with pipeline health information
    """
    scheduler = get_scheduler()
    return scheduler.status.to_dict(scheduler)
