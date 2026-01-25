-- Migration: Add financial_loss_dollars to live_snapshots
-- Story: 2.8 - Cost of Loss Widget
-- Date: 2026-01-24
--
-- This migration adds the financial_loss_dollars column to the live_snapshots
-- table to support the Cost of Loss widget's live mode data retrieval.
--
-- The column stores the calculated financial loss at each 15-minute snapshot,
-- populated by Pipeline B ("Live Pulse") using the Financial Impact Calculator.

-- ============================================================================
-- ALTER TABLE: live_snapshots
-- ============================================================================

-- Add financial_loss_dollars column to live_snapshots
ALTER TABLE live_snapshots
ADD COLUMN IF NOT EXISTS financial_loss_dollars DECIMAL(12, 2) DEFAULT 0.00;

-- Add comment for documentation
COMMENT ON COLUMN live_snapshots.financial_loss_dollars IS 'Calculated financial loss in USD at snapshot time, populated by Live Pulse pipeline';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- Check the column was added:
--   SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'live_snapshots' AND column_name = 'financial_loss_dollars';
