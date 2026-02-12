-- Story 15.2: Add failed_at column to followup_messages for tracking email send failures (AC#3)
ALTER TABLE followup_messages
ADD COLUMN failed_at TIMESTAMPTZ DEFAULT NULL;
