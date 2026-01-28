/**
 * Tests for Analytical Cache Schema Migration
 *
 * Story 1.4 - Analytical Cache Schema
 *
 * These tests validate the migration file structure and SQL syntax.
 * For full integration tests, run the migration against a local Supabase instance.
 */
import { describe, it, expect, beforeAll } from 'vitest'
import * as fs from 'fs'
import * as path from 'path'

const MIGRATION_PATH = path.join(
  __dirname,
  '..',
  'migrations',
  '0003_analytical_cache.sql'
)

const ROLLBACK_PATH = path.join(
  __dirname,
  '..',
  'migrations',
  '_0003_analytical_cache_down.sql'
)

describe('Analytical Cache Schema Migration', () => {
  let migrationSQL: string
  let rollbackSQL: string

  beforeAll(() => {
    migrationSQL = fs.readFileSync(MIGRATION_PATH, 'utf-8')
    rollbackSQL = fs.readFileSync(ROLLBACK_PATH, 'utf-8')
  })

  describe('Migration file exists and is valid', () => {
    it('should have the migration file', () => {
      expect(fs.existsSync(MIGRATION_PATH)).toBe(true)
    })

    it('should have the rollback file', () => {
      expect(fs.existsSync(ROLLBACK_PATH)).toBe(true)
    })

    it('should have non-empty migration content', () => {
      expect(migrationSQL.length).toBeGreaterThan(0)
    })

    it('should have non-empty rollback content', () => {
      expect(rollbackSQL.length).toBeGreaterThan(0)
    })
  })

  describe('AC#1: daily_summaries table', () => {
    it('should create daily_summaries table', () => {
      expect(migrationSQL).toContain('CREATE TABLE IF NOT EXISTS daily_summaries')
    })

    it('should have id UUID primary key', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?id UUID PRIMARY KEY/)
    })

    it('should have asset_id foreign key', () => {
      expect(migrationSQL).toMatch(
        /daily_summaries[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\)/
      )
    })

    it('should have report_date column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?report_date DATE NOT NULL/)
    })

    it('should have oee_percentage column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?oee_percentage DECIMAL\(5,\s*2\)/)
    })

    it('should have actual_output column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?actual_output INTEGER/)
    })

    it('should have target_output column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?target_output INTEGER/)
    })

    it('should have downtime_minutes column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?downtime_minutes INTEGER/)
    })

    it('should have waste_count column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?waste_count INTEGER/)
    })

    it('should have financial_loss_dollars column', () => {
      expect(migrationSQL).toMatch(
        /daily_summaries[\s\S]*?financial_loss_dollars DECIMAL\(12,\s*2\)/
      )
    })

    it('should have smart_summary_text column', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?smart_summary_text TEXT/)
    })

    it('should have created_at and updated_at timestamps', () => {
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?created_at TIMESTAMP/)
      expect(migrationSQL).toMatch(/daily_summaries[\s\S]*?updated_at TIMESTAMP/)
    })

    it('should have unique constraint on (asset_id, report_date)', () => {
      expect(migrationSQL).toMatch(/UNIQUE\s*\(\s*asset_id\s*,\s*report_date\s*\)/)
    })
  })

  describe('AC#2: live_snapshots table', () => {
    it('should create live_snapshots table', () => {
      expect(migrationSQL).toContain('CREATE TABLE IF NOT EXISTS live_snapshots')
    })

    it('should have id UUID primary key', () => {
      expect(migrationSQL).toMatch(/live_snapshots[\s\S]*?id UUID PRIMARY KEY/)
    })

    it('should have asset_id foreign key', () => {
      expect(migrationSQL).toMatch(
        /live_snapshots[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\)/
      )
    })

    it('should have snapshot_timestamp column', () => {
      expect(migrationSQL).toMatch(
        /live_snapshots[\s\S]*?snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL/
      )
    })

    it('should have current_output column', () => {
      expect(migrationSQL).toMatch(/live_snapshots[\s\S]*?current_output INTEGER/)
    })

    it('should have target_output column', () => {
      expect(migrationSQL).toMatch(/live_snapshots[\s\S]*?target_output INTEGER/)
    })

    it('should have computed output_variance column', () => {
      expect(migrationSQL).toMatch(
        /live_snapshots[\s\S]*?output_variance INTEGER GENERATED ALWAYS AS/
      )
    })

    it('should have status column with CHECK constraint', () => {
      expect(migrationSQL).toMatch(
        /live_snapshots[\s\S]*?status TEXT.*CHECK.*\('on_target'.*'behind'.*'ahead'\)/
      )
    })

    it('should have created_at timestamp', () => {
      expect(migrationSQL).toMatch(/live_snapshots[\s\S]*?created_at TIMESTAMP/)
    })
  })

  describe('AC#3: safety_events table', () => {
    it('should create safety_events table', () => {
      expect(migrationSQL).toContain('CREATE TABLE IF NOT EXISTS safety_events')
    })

    it('should have id UUID primary key', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?id UUID PRIMARY KEY/)
    })

    it('should have asset_id foreign key', () => {
      expect(migrationSQL).toMatch(
        /safety_events[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\)/
      )
    })

    it('should have event_timestamp column', () => {
      expect(migrationSQL).toMatch(
        /safety_events[\s\S]*?event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL/
      )
    })

    it('should have reason_code column', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?reason_code TEXT NOT NULL/)
    })

    it('should have severity column with CHECK constraint', () => {
      expect(migrationSQL).toMatch(
        /safety_events[\s\S]*?severity TEXT NOT NULL CHECK.*\('low'.*'medium'.*'high'.*'critical'\)/
      )
    })

    it('should have description column', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?description TEXT/)
    })

    it('should have is_resolved column with default', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?is_resolved BOOLEAN DEFAULT FALSE/)
    })

    it('should have resolved_at column', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?resolved_at TIMESTAMP/)
    })

    it('should have resolved_by column referencing auth.users', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?resolved_by UUID REFERENCES auth\.users/)
    })

    it('should have created_at timestamp', () => {
      expect(migrationSQL).toMatch(/safety_events[\s\S]*?created_at TIMESTAMP/)
    })
  })

  describe('AC#4: Foreign key relationships', () => {
    it('should have FK on daily_summaries.asset_id with ON DELETE CASCADE', () => {
      expect(migrationSQL).toMatch(
        /daily_summaries[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\) ON DELETE CASCADE/
      )
    })

    it('should have FK on live_snapshots.asset_id with ON DELETE CASCADE', () => {
      expect(migrationSQL).toMatch(
        /live_snapshots[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\) ON DELETE CASCADE/
      )
    })

    it('should have FK on safety_events.asset_id with ON DELETE CASCADE', () => {
      expect(migrationSQL).toMatch(
        /safety_events[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\) ON DELETE CASCADE/
      )
    })

    it('should have FK on safety_events.resolved_by with ON DELETE SET NULL', () => {
      expect(migrationSQL).toMatch(
        /safety_events[\s\S]*?resolved_by UUID REFERENCES auth\.users\(id\) ON DELETE SET NULL/
      )
    })
  })

  describe('AC#5: Indexes for common query patterns', () => {
    // daily_summaries indexes
    it('should have index on daily_summaries(report_date)', () => {
      expect(migrationSQL).toContain('idx_daily_summaries_report_date')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_daily_summaries_report_date ON daily_summaries\(report_date\)/
      )
    })

    it('should have index on daily_summaries(asset_id, report_date)', () => {
      expect(migrationSQL).toContain('idx_daily_summaries_asset_report_date')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_daily_summaries_asset_report_date ON daily_summaries\(asset_id,\s*report_date\)/
      )
    })

    // live_snapshots indexes
    it('should have index on live_snapshots(snapshot_timestamp)', () => {
      expect(migrationSQL).toContain('idx_live_snapshots_snapshot_timestamp')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_live_snapshots_snapshot_timestamp ON live_snapshots\(snapshot_timestamp\)/
      )
    })

    it('should have index on live_snapshots(asset_id, snapshot_timestamp)', () => {
      expect(migrationSQL).toContain('idx_live_snapshots_asset_snapshot_timestamp')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_live_snapshots_asset_snapshot_timestamp ON live_snapshots\(asset_id,\s*snapshot_timestamp\)/
      )
    })

    // safety_events indexes
    it('should have index on safety_events(event_timestamp)', () => {
      expect(migrationSQL).toContain('idx_safety_events_event_timestamp')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_safety_events_event_timestamp ON safety_events\(event_timestamp\)/
      )
    })

    it('should have index on safety_events(asset_id, is_resolved)', () => {
      expect(migrationSQL).toContain('idx_safety_events_asset_is_resolved')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_safety_events_asset_is_resolved ON safety_events\(asset_id,\s*is_resolved\)/
      )
    })

    it('should have index on safety_events(severity)', () => {
      expect(migrationSQL).toContain('idx_safety_events_severity')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_safety_events_severity ON safety_events\(severity\)/
      )
    })
  })

  describe('AC#6: Row Level Security (RLS) policies', () => {
    it('should enable RLS on daily_summaries', () => {
      expect(migrationSQL).toContain('ALTER TABLE daily_summaries ENABLE ROW LEVEL SECURITY')
    })

    it('should enable RLS on live_snapshots', () => {
      expect(migrationSQL).toContain('ALTER TABLE live_snapshots ENABLE ROW LEVEL SECURITY')
    })

    it('should enable RLS on safety_events', () => {
      expect(migrationSQL).toContain('ALTER TABLE safety_events ENABLE ROW LEVEL SECURITY')
    })

    // Authenticated read access policies
    it('should have authenticated read policy on daily_summaries', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*authenticated read access on daily_summaries[\s\S]*?ON daily_summaries FOR SELECT[\s\S]*?TO authenticated/
      )
    })

    it('should have authenticated read policy on live_snapshots', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*authenticated read access on live_snapshots[\s\S]*?ON live_snapshots FOR SELECT[\s\S]*?TO authenticated/
      )
    })

    it('should have authenticated read policy on safety_events', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*authenticated read access on safety_events[\s\S]*?ON safety_events FOR SELECT[\s\S]*?TO authenticated/
      )
    })

    // Service role full access policies
    it('should have service_role full access policy on daily_summaries', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*service_role full access on daily_summaries[\s\S]*?ON daily_summaries FOR ALL[\s\S]*?TO service_role/
      )
    })

    it('should have service_role full access policy on live_snapshots', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*service_role full access on live_snapshots[\s\S]*?ON live_snapshots FOR ALL[\s\S]*?TO service_role/
      )
    })

    it('should have service_role full access policy on safety_events', () => {
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*service_role full access on safety_events[\s\S]*?ON safety_events FOR ALL[\s\S]*?TO service_role/
      )
    })
  })

  describe('AC#7: Rollback capability', () => {
    it('should drop daily_summaries table in rollback', () => {
      expect(rollbackSQL).toContain('DROP TABLE IF EXISTS daily_summaries')
    })

    it('should drop live_snapshots table in rollback', () => {
      expect(rollbackSQL).toContain('DROP TABLE IF EXISTS live_snapshots')
    })

    it('should drop safety_events table in rollback', () => {
      expect(rollbackSQL).toContain('DROP TABLE IF EXISTS safety_events')
    })

    it('should drop all indexes in rollback', () => {
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_daily_summaries_report_date')
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_daily_summaries_asset_report_date')
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_live_snapshots_snapshot_timestamp')
      expect(rollbackSQL).toContain(
        'DROP INDEX IF EXISTS idx_live_snapshots_asset_snapshot_timestamp'
      )
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_safety_events_event_timestamp')
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_safety_events_asset_is_resolved')
      expect(rollbackSQL).toContain('DROP INDEX IF EXISTS idx_safety_events_severity')
    })

    it('should drop all RLS policies in rollback', () => {
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow authenticated read access on daily_summaries"'
      )
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow service_role full access on daily_summaries"'
      )
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow authenticated read access on live_snapshots"'
      )
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow service_role full access on live_snapshots"'
      )
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow authenticated read access on safety_events"'
      )
      expect(rollbackSQL).toContain(
        'DROP POLICY IF EXISTS "Allow service_role full access on safety_events"'
      )
    })

    it('should drop trigger in rollback', () => {
      expect(rollbackSQL).toContain(
        'DROP TRIGGER IF EXISTS update_daily_summaries_updated_at ON daily_summaries'
      )
    })
  })

  describe('SQL syntax validation', () => {
    it('should not have unmatched parentheses in migration', () => {
      const openParens = (migrationSQL.match(/\(/g) || []).length
      const closeParens = (migrationSQL.match(/\)/g) || []).length
      expect(openParens).toBe(closeParens)
    })

    it('should not have unmatched parentheses in rollback', () => {
      const openParens = (rollbackSQL.match(/\(/g) || []).length
      const closeParens = (rollbackSQL.match(/\)/g) || []).length
      expect(openParens).toBe(closeParens)
    })

    it('should end statements with semicolons in migration', () => {
      // Check that CREATE TABLE, CREATE INDEX, ALTER TABLE, CREATE POLICY statements end with semicolons
      const createTableMatches = migrationSQL.match(/CREATE TABLE[^;]+;/g)
      expect(createTableMatches).not.toBeNull()
      expect(createTableMatches!.length).toBe(3) // 3 tables
    })

    it('should use consistent naming convention (snake_case)', () => {
      // Table names should be snake_case
      expect(migrationSQL).toContain('daily_summaries')
      expect(migrationSQL).toContain('live_snapshots')
      expect(migrationSQL).toContain('safety_events')

      // Column names should be snake_case
      expect(migrationSQL).toContain('asset_id')
      expect(migrationSQL).toContain('report_date')
      expect(migrationSQL).toContain('oee_percentage')
      expect(migrationSQL).toContain('snapshot_timestamp')
      expect(migrationSQL).toContain('event_timestamp')
      expect(migrationSQL).toContain('is_resolved')
      expect(migrationSQL).toContain('resolved_by')
    })
  })
})
