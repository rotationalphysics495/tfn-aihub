-- Rollback Migration: Drop Analytical Cache tables
-- Story: 1.4 - Analytical Cache Schema
-- Date: 2026-01-06
--
-- This rollback migration removes the Analytical Cache layer tables in reverse order
-- to respect foreign key constraints.

-- ============================================================================
-- DROP POLICIES
-- ============================================================================

-- Drop RLS policies for daily_summaries
DROP POLICY IF EXISTS "Allow authenticated read access on daily_summaries" ON daily_summaries;
DROP POLICY IF EXISTS "Allow service_role full access on daily_summaries" ON daily_summaries;

-- Drop RLS policies for live_snapshots
DROP POLICY IF EXISTS "Allow authenticated read access on live_snapshots" ON live_snapshots;
DROP POLICY IF EXISTS "Allow service_role full access on live_snapshots" ON live_snapshots;

-- Drop RLS policies for safety_events
DROP POLICY IF EXISTS "Allow authenticated read access on safety_events" ON safety_events;
DROP POLICY IF EXISTS "Allow service_role full access on safety_events" ON safety_events;

-- ============================================================================
-- DROP TRIGGERS
-- ============================================================================

DROP TRIGGER IF EXISTS update_daily_summaries_updated_at ON daily_summaries;

-- ============================================================================
-- DROP INDEXES
-- ============================================================================

DROP INDEX IF EXISTS idx_daily_summaries_report_date;
DROP INDEX IF EXISTS idx_daily_summaries_asset_report_date;
DROP INDEX IF EXISTS idx_live_snapshots_snapshot_timestamp;
DROP INDEX IF EXISTS idx_live_snapshots_asset_snapshot_timestamp;
DROP INDEX IF EXISTS idx_safety_events_event_timestamp;
DROP INDEX IF EXISTS idx_safety_events_asset_is_resolved;
DROP INDEX IF EXISTS idx_safety_events_severity;

-- ============================================================================
-- DROP TABLES
-- ============================================================================

DROP TABLE IF EXISTS safety_events;
DROP TABLE IF EXISTS live_snapshots;
DROP TABLE IF EXISTS daily_summaries;
