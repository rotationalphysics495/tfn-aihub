"""
Data Ingestion Service

Handles:
- Pipeline A: "Morning Report" (Batch) - Daily at 06:00 AM
- Pipeline B: "Live Pulse" (Polling) - Every 15 Minutes
"""


class IngestionService:
    """Service for data ingestion from MSSQL to Supabase."""

    async def run_daily_batch(self):
        """
        Pipeline A: Morning Report (T-1)
        1. Fetch T-1 Data (24h) from MSSQL
        2. Cleanse Data (Handle NaN, 0)
        3. Calculate OEE & Financial Loss using cost_centers
        4. Generate "Smart Summary" text via LLM
        5. Store in daily_summaries
        """
        pass

    async def run_live_poll(self):
        """
        Pipeline B: Live Pulse (T-15m)
        1. Fetch last 30 mins data (rolling window) from MSSQL
        2. Check for reason_code = 'Safety Issue'
           - If Found: Trigger Alert entry in safety_events
        3. Calculate current Output vs Target
        4. Update live_snapshots
        """
        pass
