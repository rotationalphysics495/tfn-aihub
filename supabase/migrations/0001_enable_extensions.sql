-- Migration: Enable required PostgreSQL extensions
-- This must run before any other migrations that use UUID functions
-- Date: 2026-01-05

-- Enable UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;

-- Also enable pgcrypto as a fallback (provides gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA extensions;
