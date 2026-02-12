-- Migration: 0032_response_tokens.sql
-- Story: 15.3 - Response Capture via Token Link
-- Purpose: Add response token columns to followup_messages for token-based response capture.
-- Adds response_token, token_expires_at, token_used_at columns and a unique partial index.

ALTER TABLE followup_messages ADD COLUMN response_token TEXT;
ALTER TABLE followup_messages ADD COLUMN token_expires_at TIMESTAMPTZ;
ALTER TABLE followup_messages ADD COLUMN token_used_at TIMESTAMPTZ;

-- Unique partial index for fast token lookup (allows multiple NULLs)
CREATE UNIQUE INDEX idx_followup_messages_response_token
  ON followup_messages(response_token)
  WHERE response_token IS NOT NULL;
