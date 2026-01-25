-- Migration: Enhance safety_events table for Story 2.6
-- Story: 2.6 - Safety Alert System
-- Date: 2026-01-06
--
-- This migration adds additional fields to the safety_events table:
--   - source_record_id: Reference to MSSQL record for deduplication
--   - duration_minutes: Duration of the safety event
--   - financial_impact: Calculated financial impact from cost_centers
--   - acknowledged: Boolean for acknowledgement status (alias for is_resolved)
--   - acknowledged_at: When acknowledged (alias for resolved_at)
--   - acknowledged_by: Who acknowledged (alias for resolved_by)
--
-- Note: The existing is_resolved/resolved_at/resolved_by fields serve the same
-- purpose, so we add aliases for consistency with Story 2.6 API spec.

-- ============================================================================
-- ADD NEW COLUMNS TO safety_events
-- ============================================================================

-- Add source_record_id for deduplication against MSSQL records
ALTER TABLE safety_events
ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(255);

COMMENT ON COLUMN safety_events.source_record_id IS 'Reference to MSSQL record ID for deduplication';

-- Add duration_minutes for tracking event duration
ALTER TABLE safety_events
ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;

COMMENT ON COLUMN safety_events.duration_minutes IS 'Duration of the safety event in minutes';

-- Add financial_impact for FR5 integration
ALTER TABLE safety_events
ADD COLUMN IF NOT EXISTS financial_impact DECIMAL(12, 2);

COMMENT ON COLUMN safety_events.financial_impact IS 'Calculated financial impact from cost_centers.standard_hourly_rate';

-- Add occurred_at as an alias for event_timestamp (if not exists)
-- This matches the LivePulsePipeline SafetyEventData.to_dict() output
ALTER TABLE safety_events
ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMP WITH TIME ZONE;

-- Update occurred_at from event_timestamp where null
UPDATE safety_events
SET occurred_at = event_timestamp
WHERE occurred_at IS NULL;

-- ============================================================================
-- ADD INDEX FOR DEDUPLICATION
-- ============================================================================

-- Index on source_record_id for efficient deduplication lookups
CREATE INDEX IF NOT EXISTS idx_safety_events_source_record_id
ON safety_events(source_record_id)
WHERE source_record_id IS NOT NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- To verify the migration:
--
-- Check new columns exist:
--   SELECT column_name, data_type
--   FROM information_schema.columns
--   WHERE table_name = 'safety_events'
--   AND column_name IN ('source_record_id', 'duration_minutes', 'financial_impact', 'occurred_at');
--
-- Check index exists:
--   SELECT indexname FROM pg_indexes
--   WHERE tablename = 'safety_events' AND indexname = 'idx_safety_events_source_record_id';
