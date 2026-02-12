/**
 * Tests for Downtime Events Schema Migration & Seed Data Validation
 *
 * Story 14.1 - Downtime Events Data Model & Seed Data
 *
 * UNIT tests that validate:
 *   - Migration file structure and SQL syntax for 0029_downtime_events.sql
 *   - Seed script (seed-data.mjs) contains downtime_events generation logic
 *
 * These tests read source files and validate their contents statically.
 * They will FAIL until Story 14.1 implementation is complete because:
 *   - Migration file 0029_downtime_events.sql does not yet exist
 *   - seed-data.mjs does not yet contain downtime_events insertion logic
 */
import { describe, it, expect, beforeAll } from 'vitest'
import * as fs from 'fs'
import * as path from 'path'

// ============================================================================
// File Paths
// ============================================================================

const MIGRATION_PATH = path.join(
  __dirname,
  '..',
  'migrations',
  '0029_downtime_events.sql'
)

const SEED_MJS_PATH = path.join(__dirname, '..', '..', '_bmad', 'scripts', 'seed-data.mjs')

// ============================================================================
// Constants
// ============================================================================

const STANDARD_REASON_CODES = [
  'Mechanical',
  'Changeover',
  'Material Shortage',
  'Quality Hold',
  'Operator Unavailable',
  'Planned Maintenance',
] as const

const PLANNED_REASON_CODES = ['Planned Maintenance', 'Changeover'] as const
const UNPLANNED_REASON_CODES = [
  'Mechanical',
  'Material Shortage',
  'Quality Hold',
  'Operator Unavailable',
] as const

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Downtime Events Data Model & Seed Data (Story 14.1)', () => {
  let migrationSQL: string = ''
  let seedContent: string = ''
  let migrationExists: boolean = false

  beforeAll(() => {
    // Migration file may not exist yet (pre-TDD)
    migrationExists = fs.existsSync(MIGRATION_PATH)
    if (migrationExists) {
      migrationSQL = fs.readFileSync(MIGRATION_PATH, 'utf-8')
    }
    // Seed file should always exist
    seedContent = fs.readFileSync(SEED_MJS_PATH, 'utf-8')
  })

  // Helper: assert migration file exists (used as first assertion in migration tests)
  function requireMigration() {
    expect(
      migrationExists,
      `Migration file must exist at ${MIGRATION_PATH}`
    ).toBe(true)
  }

  // ==========================================================================
  // AC1: Database Migration Creates Table
  // ==========================================================================

  describe('AC1: Database Migration Creates Table', () => {
    it('14-1-downtime-events-data-model-seed-data-UNIT-001: Migration file exists and is non-empty', () => {
      // Given: The migration file 0029_downtime_events.sql has been created
      // When: The file system is checked for the migration file
      // Then: The file exists at the expected path and has non-empty content

      requireMigration()
      expect(migrationSQL.length).toBeGreaterThan(0)
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-002: Migration creates downtime_events table with CREATE TABLE IF NOT EXISTS', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for CREATE TABLE statement
      // Then: The migration contains CREATE TABLE IF NOT EXISTS downtime_events

      requireMigration()
      expect(migrationSQL).toContain('CREATE TABLE IF NOT EXISTS downtime_events')
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-003: Table has id column as UUID PK with gen_random_uuid()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the id column definition
      // Then: The column is defined as UUID PRIMARY KEY DEFAULT gen_random_uuid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?id UUID PRIMARY KEY DEFAULT gen_random_uuid\(\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-004: Table has asset_id column as UUID FK to assets(id) ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the asset_id column definition
      // Then: The column is defined as UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?asset_id UUID NOT NULL REFERENCES assets\(id\) ON DELETE CASCADE/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-005: Table has event_date column as DATE NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the event_date column definition
      // Then: The column is defined as DATE NOT NULL

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?event_date DATE NOT NULL/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-006: Table has shift column with CHECK constraint', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the shift column definition
      // Then: The column is defined as TEXT with CHECK constraint allowing only 'morning', 'afternoon', 'night'

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?shift TEXT[\s\S]*?CHECK[\s\S]*?'morning'[\s\S]*?'afternoon'[\s\S]*?'night'/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-007: Table has reason_code column as TEXT NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the reason_code column definition
      // Then: The column is defined as TEXT NOT NULL

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?reason_code TEXT NOT NULL/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-008: Table has reason_detail column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the reason_detail column definition
      // Then: The column is defined as TEXT (without NOT NULL constraint)

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?reason_detail TEXT/
      )
      // Verify it does NOT have NOT NULL
      const reasonDetailLine = migrationSQL.match(/reason_detail TEXT[^\n,)]*/)
      expect(reasonDetailLine).not.toBeNull()
      expect(reasonDetailLine![0]).not.toMatch(/NOT NULL/)
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-009: Table has duration_minutes column as INTEGER NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the duration_minutes column definition
      // Then: The column is defined as INTEGER NOT NULL

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?duration_minutes INTEGER NOT NULL/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-010: Table has is_planned column as BOOLEAN DEFAULT false', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the is_planned column definition
      // Then: The column is defined as BOOLEAN DEFAULT false

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?is_planned BOOLEAN DEFAULT (false|FALSE)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-011: Table has source_system column as TEXT DEFAULT \'manual\'', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the source_system column definition
      // Then: The column is defined as TEXT DEFAULT 'manual'

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?source_system TEXT DEFAULT 'manual'/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-012: Table has source_event_id column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the source_event_id column definition
      // Then: The column is defined as TEXT (nullable, no NOT NULL)

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?source_event_id TEXT/
      )
      // Verify it does NOT have NOT NULL
      const sourceEventIdLine = migrationSQL.match(/source_event_id TEXT[^\n,)]*/)
      expect(sourceEventIdLine).not.toBeNull()
      expect(sourceEventIdLine![0]).not.toMatch(/NOT NULL/)
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-013: Table has created_at and updated_at TIMESTAMPTZ columns with DEFAULT NOW()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for timestamp columns
      // Then: Both created_at and updated_at are defined as TIMESTAMP WITH TIME ZONE DEFAULT NOW()

      requireMigration()
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW\(\)/
      )
      expect(migrationSQL).toMatch(
        /downtime_events[\s\S]*?updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW\(\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-014: Migration uses updated_at trigger referencing existing function', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for trigger definition
      // Then: A trigger named update_downtime_events_updated_at exists with EXECUTE FUNCTION update_updated_at_column()
      // And: The migration does NOT contain CREATE OR REPLACE FUNCTION update_updated_at_column (must not recreate)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TRIGGER update_downtime_events_updated_at/
      )
      expect(migrationSQL).toMatch(
        /EXECUTE FUNCTION update_updated_at_column\(\)/
      )
      // Must NOT recreate the existing function
      expect(migrationSQL).not.toMatch(
        /CREATE\s+(OR\s+REPLACE\s+)?FUNCTION\s+update_updated_at_column/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-015: Migration has table and column COMMENTs', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for COMMENT statements
      // Then: COMMENT ON TABLE downtime_events exists
      // And: COMMENT ON COLUMN downtime_events. exists for key columns

      requireMigration()
      expect(migrationSQL).toContain('COMMENT ON TABLE downtime_events')
      expect(migrationSQL).toContain('COMMENT ON COLUMN downtime_events.asset_id')
      expect(migrationSQL).toContain('COMMENT ON COLUMN downtime_events.event_date')
      expect(migrationSQL).toContain('COMMENT ON COLUMN downtime_events.reason_code')
      expect(migrationSQL).toContain('COMMENT ON COLUMN downtime_events.duration_minutes')
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-016: Migration SQL has balanced parentheses', () => {
      // Given: The migration SQL file content is loaded
      // When: Open and close parentheses are counted
      // Then: The count of ( equals the count of )

      requireMigration()
      const openParens = (migrationSQL.match(/\(/g) || []).length
      const closeParens = (migrationSQL.match(/\)/g) || []).length
      expect(openParens).toBe(closeParens)
    })
  })

  // ==========================================================================
  // AC2: Indexes Exist for Query Performance
  // ==========================================================================

  describe('AC2: Indexes Exist for Query Performance', () => {
    it('14-1-downtime-events-data-model-seed-data-UNIT-017: Migration creates index on asset_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_downtime_events_asset_id is created on downtime_events(asset_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_downtime_events_asset_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_downtime_events_asset_id ON downtime_events\(asset_id\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-018: Migration creates index on event_date', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_downtime_events_event_date is created on downtime_events(event_date)

      requireMigration()
      expect(migrationSQL).toContain('idx_downtime_events_event_date')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_downtime_events_event_date ON downtime_events\(event_date\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-019: Migration creates index on reason_code', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_downtime_events_reason_code is created on downtime_events(reason_code)

      requireMigration()
      expect(migrationSQL).toContain('idx_downtime_events_reason_code')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_downtime_events_reason_code ON downtime_events\(reason_code\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-020: Migration creates composite index on (asset_id, event_date)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for composite index creation
      // Then: A composite index named idx_downtime_events_asset_event_date is created

      requireMigration()
      expect(migrationSQL).toContain('idx_downtime_events_asset_event_date')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_downtime_events_asset_event_date ON downtime_events\(asset_id,\s*event_date\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-021: All indexes use IF NOT EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: All CREATE INDEX statements are parsed
      // Then: Every CREATE INDEX statement includes IF NOT EXISTS

      requireMigration()
      const createIndexLines = migrationSQL.match(/CREATE INDEX.*downtime_events/g)
      expect(createIndexLines).not.toBeNull()
      expect(createIndexLines!.length).toBeGreaterThanOrEqual(4)

      for (const line of createIndexLines!) {
        expect(
          line,
          `CREATE INDEX should include IF NOT EXISTS: ${line}`
        ).toMatch(/IF NOT EXISTS/)
      }
    })
  })

  // ==========================================================================
  // AC3: RLS Follows Existing Patterns
  // ==========================================================================

  describe('AC3: RLS Follows Existing Patterns', () => {
    it('14-1-downtime-events-data-model-seed-data-UNIT-022: Migration enables RLS on downtime_events', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS enablement
      // Then: The statement ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY exists

      requireMigration()
      expect(migrationSQL).toContain('ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY')
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-023: Migration creates authenticated read access policy', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS policies
      // Then: A policy named "Allow authenticated read access on downtime_events" exists
      // And: It is FOR SELECT with TO authenticated and USING (true)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*"Allow authenticated read access on downtime_events"[\s\S]*?ON downtime_events FOR SELECT[\s\S]*?TO authenticated[\s\S]*?USING \(true\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-024: Migration creates service_role full access policy', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS policies
      // Then: A policy named "Allow service_role full access on downtime_events" exists
      // And: It is FOR ALL with TO service_role, USING (true), and WITH CHECK (true)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY.*"Allow service_role full access on downtime_events"[\s\S]*?ON downtime_events FOR ALL[\s\S]*?TO service_role[\s\S]*?USING \(true\)[\s\S]*?WITH CHECK \(true\)/
      )
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-025: Migration drops existing policies before creating (idempotency)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for DROP POLICY statements
      // Then: DROP POLICY IF EXISTS appears before CREATE POLICY for both policies

      requireMigration()

      const dropAuthIdx = migrationSQL.indexOf(
        'DROP POLICY IF EXISTS "Allow authenticated read access on downtime_events"'
      )
      const createAuthIdx = migrationSQL.indexOf(
        'CREATE POLICY "Allow authenticated read access on downtime_events"'
      )
      const dropServiceIdx = migrationSQL.indexOf(
        'DROP POLICY IF EXISTS "Allow service_role full access on downtime_events"'
      )
      const createServiceIdx = migrationSQL.indexOf(
        'CREATE POLICY "Allow service_role full access on downtime_events"'
      )

      expect(dropAuthIdx, 'DROP POLICY for authenticated should exist').toBeGreaterThanOrEqual(0)
      expect(createAuthIdx, 'CREATE POLICY for authenticated should exist').toBeGreaterThanOrEqual(0)
      expect(dropAuthIdx, 'DROP POLICY should come before CREATE POLICY (authenticated)').toBeLessThan(createAuthIdx)

      expect(dropServiceIdx, 'DROP POLICY for service_role should exist').toBeGreaterThanOrEqual(0)
      expect(createServiceIdx, 'CREATE POLICY for service_role should exist').toBeGreaterThanOrEqual(0)
      expect(dropServiceIdx, 'DROP POLICY should come before CREATE POLICY (service_role)').toBeLessThan(createServiceIdx)
    })
  })

  // ==========================================================================
  // AC4: Seed Data Aligns with Existing daily_summaries
  // ==========================================================================

  describe('AC4: Seed Data Aligns with Existing daily_summaries', () => {
    it('14-1-downtime-events-data-model-seed-data-UNIT-026: Seed script contains downtime_events generation logic', () => {
      // Given: The seed-data.mjs file content is loaded
      // When: The file is parsed for downtime_events references
      // Then: The file contains insertion logic for downtime_events table

      expect(
        seedContent,
        'seed-data.mjs should reference downtime_events table'
      ).toMatch(/downtime_events/)

      expect(
        seedContent,
        "seed-data.mjs should use supabase.from('downtime_events') for insertion"
      ).toMatch(/from\(['"]downtime_events['"]\)/)
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-027: Seed script clears downtime_events before inserting', () => {
      // Given: The seed-data.mjs file content is loaded
      // When: The file is parsed for the clear/delete step
      // Then: A delete statement for downtime_events exists
      // And: The clear step appears before the insert step

      const deletePattern = /from\(['"]downtime_events['"]\)\.delete/
      const insertPattern = /from\(['"]downtime_events['"]\)\.insert/

      expect(seedContent, 'seed-data.mjs should have a delete step for downtime_events').toMatch(deletePattern)
      expect(seedContent, 'seed-data.mjs should have an insert step for downtime_events').toMatch(insertPattern)

      // Verify delete comes before insert
      const deleteMatch = seedContent.match(deletePattern)
      const insertMatch = seedContent.match(insertPattern)
      expect(deleteMatch).not.toBeNull()
      expect(insertMatch).not.toBeNull()

      const deleteIdx = seedContent.indexOf(deleteMatch![0])
      const insertIdx = seedContent.indexOf(insertMatch![0])
      expect(
        deleteIdx,
        'Delete should come before insert for downtime_events'
      ).toBeLessThan(insertIdx)
    })
  })

  // ==========================================================================
  // AC5: Standard Reason Codes Used
  // ==========================================================================

  describe('AC5: Standard Reason Codes Used', () => {
    it('14-1-downtime-events-data-model-seed-data-UNIT-028: Seed script defines reason code mapping', () => {
      // Given: The seed-data.mjs file content is loaded
      // When: The file is parsed for reason code definitions
      // Then: All 6 standard reason codes are referenced

      for (const code of STANDARD_REASON_CODES) {
        expect(
          seedContent,
          `seed-data.mjs should contain reason code "${code}"`
        ).toContain(code)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-UNIT-029: Seed script maps is_planned correctly in code', () => {
      // Given: The seed-data.mjs file content is loaded
      // When: The file is parsed for is_planned assignments
      // Then: "Planned Maintenance" and "Changeover" are associated with is_planned: true
      // And: "Mechanical", "Material Shortage", "Quality Hold", "Operator Unavailable" are associated with is_planned: false

      // Find entries with planned reason codes that have is_planned: true
      for (const code of PLANNED_REASON_CODES) {
        const plannedPattern = new RegExp(
          `reason_code:\\s*'${code}'[^}]*is_planned:\\s*true|is_planned:\\s*true[^}]*reason_code:\\s*'${code}'`,
          's'
        )
        expect(
          seedContent,
          `"${code}" should have is_planned: true in seed data`
        ).toMatch(plannedPattern)
      }

      // Find entries with unplanned reason codes that have is_planned: false
      for (const code of UNPLANNED_REASON_CODES) {
        const unplannedPattern = new RegExp(
          `reason_code:\\s*'${code}'[^}]*is_planned:\\s*false|is_planned:\\s*false[^}]*reason_code:\\s*'${code}'`,
          's'
        )
        expect(
          seedContent,
          `"${code}" should have is_planned: false in seed data`
        ).toMatch(unplannedPattern)
      }
    })
  })
})
