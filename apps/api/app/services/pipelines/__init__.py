"""
Pipeline Services Module

Contains data pipeline implementations:
- Pipeline A: "Morning Report" (Batch) - Daily at 06:00 AM
- Pipeline B: "Live Pulse" (Polling) - Every 15 Minutes (Story 2.2)
"""

from app.services.pipelines.morning_report import MorningReportPipeline, run_morning_report
from app.services.pipelines.live_pulse import (
    LivePulsePipeline,
    run_live_pulse_poll,
    get_live_pulse_pipeline,
)

__all__ = [
    "MorningReportPipeline",
    "run_morning_report",
    "LivePulsePipeline",
    "run_live_pulse_poll",
    "get_live_pulse_pipeline",
]
