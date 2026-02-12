/**
 * Tests for Action Plans Schema Migration
 *
 * Story 16.1 - Action Plans Data Model
 *
 * UNIT tests that validate:
 *   - Migration file structure and SQL syntax for 0034_action_plans.sql
 *   - action_plans table schema (columns, types, constraints, defaults)
 *   - action_plan_updates table schema (columns, types, constraints, defaults)
 *   - Performance indexes
 *   - RLS policies for access control
 *   - Foreign key cascade behavior declarations
 *   - Trigger attachment for updated_at
 *   - Migration naming convention and idempotency
 *
 * These tests read the migration SQL file and validate its contents statically.
 * They will FAIL until Story 16.1 implementation is complete because:
 *   - Migration file 0034_action_plans.sql does not yet exist
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
  '0034_action_plans.sql'
)

const MIGRATIONS_DIR = path.join(__dirname, '..', 'migrations')

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Action Plans Data Model (Story 16.1)', () => {
  let migrationSQL: string = ''
  let migrationExists: boolean = false

  beforeAll(() => {
    migrationExists = fs.existsSync(MIGRATION_PATH)
    if (migrationExists) {
      migrationSQL = fs.readFileSync(MIGRATION_PATH, 'utf-8')
    }
  })

  // Helper: assert migration file exists (used as first assertion in migration tests)
  function requireMigration() {
    expect(
      migrationExists,
      `Migration file must exist at ${MIGRATION_PATH}`
    ).toBe(true)
  }

  /**
   * Helper: extract the CREATE TABLE action_plans block from migration SQL.
   * Returns the text from CREATE TABLE through the closing );
   */
  function getActionPlansCreateTableBlock(): string {
    const match = migrationSQL.match(
      /CREATE TABLE(?:\s+IF NOT EXISTS)?\s+action_plans\s*\([\s\S]*?\);/
    )
    return match ? match[0] : ''
  }

  /**
   * Helper: extract the CREATE TABLE action_plan_updates block from migration SQL.
   * Returns the text from CREATE TABLE through the closing );
   */
  function getActionPlanUpdatesCreateTableBlock(): string {
    const match = migrationSQL.match(
      /CREATE TABLE(?:\s+IF NOT EXISTS)?\s+action_plan_updates\s*\([\s\S]*?\);/
    )
    return match ? match[0] : ''
  }

  // ==========================================================================
  // AC1: action_plans Table Created
  // ==========================================================================

  describe('AC1: action_plans Table Created', () => {
    it('16-1-action-plans-data-model-UNIT-001: Migration file exists and is non-empty', () => {
      // Given: The migration file 0034_action_plans.sql has been created
      // When: The file system is checked for the migration file
      // Then: The file exists at the expected path and has non-empty content

      requireMigration()
      expect(migrationSQL.length).toBeGreaterThan(0)
    })

    it('16-1-action-plans-data-model-UNIT-002: Migration creates action_plans table with CREATE TABLE IF NOT EXISTS', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for CREATE TABLE statement
      // Then: The migration contains CREATE TABLE IF NOT EXISTS action_plans (idempotent per AC5)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plans/
      )
    })

    it('16-1-action-plans-data-model-UNIT-003: Table has id column as UUID PK with gen_random_uuid() default', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the id column definition within the action_plans CREATE TABLE block
      // Then: The column is defined as id UUID PRIMARY KEY DEFAULT gen_random_uuid()

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /id\s+UUID\s+PRIMARY KEY\s+DEFAULT\s+gen_random_uuid\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-004: Table has title column as TEXT NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the title column definition
      // Then: The column is defined as title TEXT NOT NULL

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(/title\s+TEXT\s+NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-005: Table has description column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the description column definition in the action_plans CREATE TABLE block
      // Then: The column is defined as description TEXT without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toContain('description TEXT')
      // Verify it does NOT have NOT NULL
      const descLine = block.match(/description\s+TEXT[^\n,)]*/)
      expect(descLine).not.toBeNull()
      expect(descLine![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-006: Table has asset_id column as nullable UUID FK to assets(id) ON DELETE SET NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the asset_id column definition
      // Then: The column is defined as asset_id UUID REFERENCES assets(id) ON DELETE SET NULL without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /asset_id\s+UUID\s+REFERENCES\s+assets\(id\)\s+ON DELETE SET NULL/
      )
      // Verify it does NOT have NOT NULL
      const assetIdLine = block.match(/asset_id\s+UUID[^\n,)]*/)
      expect(assetIdLine).not.toBeNull()
      expect(assetIdLine![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-007: Table has category column with CHECK constraint for corrective/preventive/improvement', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the category column definition
      // Then: The column is defined as category TEXT CHECK (category IN ('corrective', 'preventive', 'improvement'))

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /category\s+TEXT\s+CHECK\s*\(category\s+IN\s*\('corrective',\s*'preventive',\s*'improvement'\)\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-008: Table has root_cause column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the root_cause column definition in the action_plans CREATE TABLE block
      // Then: The column is defined as root_cause TEXT without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toContain('root_cause TEXT')
      const rootCauseLine = block.match(/root_cause\s+TEXT[^\n,)]*/)
      expect(rootCauseLine).not.toBeNull()
      expect(rootCauseLine![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-009: Table has corrective_action column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the corrective_action column definition
      // Then: The column is defined as corrective_action TEXT without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toContain('corrective_action TEXT')
      const line = block.match(/corrective_action\s+TEXT[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-010: Table has preventive_action column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the preventive_action column definition
      // Then: The column is defined as preventive_action TEXT without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toContain('preventive_action TEXT')
      const line = block.match(/preventive_action\s+TEXT[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-011: Table has source_followup_id column as nullable UUID FK to action_followups(id) ON DELETE SET NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the source_followup_id column definition
      // Then: The column is defined as source_followup_id UUID REFERENCES action_followups(id) ON DELETE SET NULL without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /source_followup_id\s+UUID\s+REFERENCES\s+action_followups\(id\)\s+ON DELETE SET NULL/
      )
      // Verify it does NOT have NOT NULL
      const line = block.match(/source_followup_id\s+UUID[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-012: source_followup_id FK does NOT use ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for CASCADE behavior on source_followup_id
      // Then: No ON DELETE CASCADE appears in conjunction with action_followups(id) in the action_plans table

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).not.toMatch(
        /action_followups\(id\)\s+ON DELETE CASCADE/
      )
    })

    it('16-1-action-plans-data-model-UNIT-013: Table has owner_id column as UUID NOT NULL FK to auth.users(id) ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the owner_id column definition
      // Then: The column is defined as owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /owner_id\s+UUID\s+NOT NULL\s+REFERENCES\s+auth\.users\(id\)\s+ON DELETE CASCADE/
      )
    })

    it('16-1-action-plans-data-model-UNIT-014: Table has status column with DEFAULT draft and CHECK constraint', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the status column definition in the action_plans CREATE TABLE block
      // Then: The column is defined as status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'in_progress', 'completed', 'verified'))

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /status\s+TEXT\s+DEFAULT\s+'draft'\s+CHECK\s*\(status\s+IN\s*\('draft',\s*'open',\s*'in_progress',\s*'completed',\s*'verified'\)\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-015: Table has priority column with DEFAULT medium and CHECK constraint', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the priority column definition
      // Then: The column is defined as priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical'))

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /priority\s+TEXT\s+DEFAULT\s+'medium'\s+CHECK\s*\(priority\s+IN\s*\('low',\s*'medium',\s*'high',\s*'critical'\)\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-016: Table has due_date column as DATE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the due_date column definition
      // Then: The column is defined as due_date DATE (simple date without timezone)

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(/due_date\s+DATE/)
    })

    it('16-1-action-plans-data-model-UNIT-017: Table has completed_at column as nullable TIMESTAMPTZ', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the completed_at column definition
      // Then: The column is defined as completed_at TIMESTAMPTZ (or TIMESTAMP WITH TIME ZONE) without NOT NULL and without DEFAULT

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(/completed_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)/)
      const line = block.match(/completed_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
      expect(line![0]).not.toMatch(/DEFAULT/)
    })

    it('16-1-action-plans-data-model-UNIT-018: Table has verified_by column as nullable UUID FK to auth.users(id) ON DELETE SET NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the verified_by column definition
      // Then: The column is defined as verified_by UUID REFERENCES auth.users(id) ON DELETE SET NULL without NOT NULL constraint

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /verified_by\s+UUID\s+REFERENCES\s+auth\.users\(id\)\s+ON DELETE SET NULL/
      )
      const line = block.match(/verified_by\s+UUID[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-019: Table has verified_at column as nullable TIMESTAMPTZ', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the verified_at column definition
      // Then: The column is defined as verified_at TIMESTAMPTZ (or TIMESTAMP WITH TIME ZONE) without NOT NULL and without DEFAULT

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(/verified_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)/)
      const line = block.match(/verified_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
      expect(line![0]).not.toMatch(/DEFAULT/)
    })

    it('16-1-action-plans-data-model-UNIT-020: Table has created_at column as TIMESTAMPTZ with DEFAULT NOW()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the created_at column definition in the action_plans CREATE TABLE block
      // Then: The column is defined as created_at TIMESTAMPTZ DEFAULT NOW() (or TIMESTAMP WITH TIME ZONE DEFAULT NOW())

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /created_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)\s+(NOT NULL\s+)?DEFAULT\s+NOW\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-021: Table has updated_at column as TIMESTAMPTZ with DEFAULT NOW()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the updated_at column definition in the action_plans CREATE TABLE block
      // Then: The column is defined as updated_at TIMESTAMPTZ DEFAULT NOW() (or TIMESTAMP WITH TIME ZONE DEFAULT NOW())

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).toMatch(
        /updated_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)\s+(NOT NULL\s+)?DEFAULT\s+NOW\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-022: update_updated_at_column() trigger is attached to action_plans', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for trigger creation on action_plans
      // Then: A CREATE TRIGGER statement exists that attaches update_updated_at_column() to action_plans with BEFORE UPDATE FOR EACH ROW

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TRIGGER[\s\S]*?BEFORE UPDATE ON action_plans[\s\S]*?FOR EACH ROW[\s\S]*?EXECUTE\s+(FUNCTION|PROCEDURE)\s+update_updated_at_column\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-023: Trigger uses DROP TRIGGER IF EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for trigger idempotency pattern
      // Then: A DROP TRIGGER IF EXISTS statement appears before the CREATE TRIGGER for action_plans

      requireMigration()
      expect(migrationSQL).toMatch(
        /DROP TRIGGER IF EXISTS[\s\S]*?ON action_plans/
      )
    })

    it('16-1-action-plans-data-model-UNIT-024: Migration does NOT recreate update_updated_at_column() function', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for function creation statements
      // Then: No CREATE FUNCTION or CREATE OR REPLACE FUNCTION update_updated_at_column exists (function already exists from migration 0002)

      requireMigration()
      expect(migrationSQL).not.toMatch(
        /CREATE\s+(OR REPLACE\s+)?FUNCTION\s+update_updated_at_column/
      )
    })

    it('16-1-action-plans-data-model-UNIT-025: Table has exactly 18 columns', () => {
      // Given: The migration SQL file content is loaded
      // When: The action_plans CREATE TABLE statement is parsed for column definitions
      // Then: Exactly 18 columns are defined

      requireMigration()
      const block = getActionPlansCreateTableBlock()

      const expectedColumns = [
        'id',
        'title',
        'description',
        'asset_id',
        'category',
        'root_cause',
        'corrective_action',
        'preventive_action',
        'source_followup_id',
        'owner_id',
        'status',
        'priority',
        'due_date',
        'completed_at',
        'verified_by',
        'verified_at',
        'created_at',
        'updated_at',
      ]

      // Verify each expected column exists
      for (const col of expectedColumns) {
        expect(
          block,
          `Column "${col}" should exist in CREATE TABLE action_plans`
        ).toMatch(new RegExp(`\\b${col}\\b`))
      }

      // Count column definitions by matching lines that start with a column name followed by a type keyword
      const columnPattern =
        /^\s+(id|title|description|asset_id|category|root_cause|corrective_action|preventive_action|source_followup_id|owner_id|status|priority|due_date|completed_at|verified_by|verified_at|created_at|updated_at)\s+(UUID|TEXT|DATE|TIMESTAMPTZ|TIMESTAMP)/gm
      const matches = block.match(columnPattern)
      expect(
        matches,
        'Should find column definitions in CREATE TABLE block'
      ).not.toBeNull()
      expect(
        matches!.length,
        `Expected exactly 18 columns, found ${matches?.length}`
      ).toBe(18)
    })

    it('16-1-action-plans-data-model-UNIT-026: asset_id FK does NOT use ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for CASCADE behavior on asset_id FK
      // Then: No ON DELETE CASCADE appears in conjunction with assets(id) in the action_plans table

      requireMigration()
      const block = getActionPlansCreateTableBlock()
      expect(block).not.toMatch(
        /assets\(id\)\s+ON DELETE CASCADE/
      )
    })
  })

  // ==========================================================================
  // AC2: action_plan_updates Table Created
  // ==========================================================================

  describe('AC2: action_plan_updates Table Created', () => {
    it('16-1-action-plans-data-model-UNIT-027: Migration creates action_plan_updates table', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the action_plan_updates CREATE TABLE statement
      // Then: The migration contains CREATE TABLE IF NOT EXISTS action_plan_updates (idempotent per AC5)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plan_updates/
      )
    })

    it('16-1-action-plans-data-model-UNIT-028: action_plan_updates has id column as UUID PK with gen_random_uuid() default', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the id column within the action_plan_updates CREATE TABLE block
      // Then: The column is defined as id UUID PRIMARY KEY DEFAULT gen_random_uuid()

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toMatch(
        /id\s+UUID\s+PRIMARY KEY\s+DEFAULT\s+gen_random_uuid\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-029: action_plan_updates has action_plan_id column as UUID NOT NULL FK to action_plans(id) ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the action_plan_id column definition
      // Then: The column is defined as action_plan_id UUID NOT NULL REFERENCES action_plans(id) ON DELETE CASCADE

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toMatch(
        /action_plan_id\s+UUID\s+NOT NULL\s+REFERENCES\s+action_plans\(id\)\s+ON DELETE CASCADE/
      )
    })

    it('16-1-action-plans-data-model-UNIT-030: action_plan_updates has author_id column as UUID NOT NULL FK to auth.users(id) ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the author_id column definition in action_plan_updates
      // Then: The column is defined as author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toMatch(
        /author_id\s+UUID\s+NOT NULL\s+REFERENCES\s+auth\.users\(id\)\s+ON DELETE CASCADE/
      )
    })

    it('16-1-action-plans-data-model-UNIT-031: action_plan_updates has update_text column as TEXT NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the update_text column definition
      // Then: The column is defined as update_text TEXT NOT NULL

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toMatch(/update_text\s+TEXT\s+NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-032: action_plan_updates has status_change column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the status_change column definition
      // Then: The column is defined as status_change TEXT without NOT NULL constraint

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toContain('status_change TEXT')
      const line = block.match(/status_change\s+TEXT[^\n,)]*/)
      expect(line).not.toBeNull()
      expect(line![0]).not.toMatch(/NOT NULL/)
    })

    it('16-1-action-plans-data-model-UNIT-033: action_plan_updates has created_at column as TIMESTAMPTZ with DEFAULT NOW()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the created_at column in the action_plan_updates CREATE TABLE block
      // Then: The column is defined as created_at TIMESTAMPTZ DEFAULT NOW() (or TIMESTAMP WITH TIME ZONE DEFAULT NOW())

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).toMatch(
        /created_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)\s+(NOT NULL\s+)?DEFAULT\s+NOW\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-034: action_plan_updates does NOT have updated_at column (append-only)', () => {
      // Given: The migration SQL file content is loaded
      // When: The action_plan_updates CREATE TABLE block is searched for an updated_at column
      // Then: No updated_at column definition exists in the action_plan_updates CREATE TABLE statement

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()
      expect(block).not.toMatch(/updated_at/)
    })

    it('16-1-action-plans-data-model-UNIT-035: action_plan_updates does NOT have an updated_at trigger (append-only)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for triggers on action_plan_updates
      // Then: No CREATE TRIGGER statement references the action_plan_updates table

      requireMigration()
      expect(migrationSQL).not.toMatch(
        /CREATE TRIGGER[\s\S]*?ON action_plan_updates/
      )
    })

    it('16-1-action-plans-data-model-UNIT-036: action_plan_updates has exactly 6 columns', () => {
      // Given: The migration SQL file content is loaded
      // When: The action_plan_updates CREATE TABLE statement is parsed for column definitions
      // Then: Exactly 6 columns are defined: id, action_plan_id, author_id, update_text, status_change, created_at

      requireMigration()
      const block = getActionPlanUpdatesCreateTableBlock()

      const expectedColumns = [
        'id',
        'action_plan_id',
        'author_id',
        'update_text',
        'status_change',
        'created_at',
      ]

      // Verify each expected column exists
      for (const col of expectedColumns) {
        expect(
          block,
          `Column "${col}" should exist in CREATE TABLE action_plan_updates`
        ).toMatch(new RegExp(`\\b${col}\\b`))
      }

      // Count column definitions
      const columnPattern =
        /^\s+(id|action_plan_id|author_id|update_text|status_change|created_at)\s+(UUID|TEXT|TIMESTAMPTZ|TIMESTAMP)/gm
      const matches = block.match(columnPattern)
      expect(
        matches,
        'Should find column definitions in CREATE TABLE block'
      ).not.toBeNull()
      expect(
        matches!.length,
        `Expected exactly 6 columns, found ${matches?.length}`
      ).toBe(6)
    })
  })

  // ==========================================================================
  // AC3: Row Level Security Enabled
  // ==========================================================================

  describe('AC3: Row Level Security Enabled', () => {
    it('16-1-action-plans-data-model-UNIT-037: Migration enables RLS on action_plans', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS enablement on action_plans
      // Then: The statement ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY exists

      requireMigration()
      expect(migrationSQL).toContain(
        'ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY'
      )
    })

    it('16-1-action-plans-data-model-UNIT-038: Migration enables RLS on action_plan_updates', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS enablement on action_plan_updates
      // Then: The statement ALTER TABLE action_plan_updates ENABLE ROW LEVEL SECURITY exists

      requireMigration()
      expect(migrationSQL).toContain(
        'ALTER TABLE action_plan_updates ENABLE ROW LEVEL SECURITY'
      )
    })

    it('16-1-action-plans-data-model-UNIT-039: action_plans has SELECT policy for all authenticated users (USING true)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the SELECT RLS policy on action_plans
      // Then: A policy exists FOR SELECT TO authenticated on action_plans with USING (true) for shared visibility

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plans\s+FOR SELECT[\s\S]*?TO authenticated[\s\S]*?USING\s*\(true\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-040: action_plans has INSERT policy restricting owner_id = auth.uid()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the INSERT RLS policy on action_plans
      // Then: A policy exists FOR INSERT TO authenticated on action_plans with WITH CHECK containing owner_id = auth.uid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plans\s+FOR INSERT[\s\S]*?TO authenticated[\s\S]*?WITH CHECK\s*\([\s\S]*?owner_id\s*=\s*auth\.uid\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-041: action_plans has UPDATE policy restricting owner_id = auth.uid()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the UPDATE RLS policy on action_plans
      // Then: A policy exists FOR UPDATE TO authenticated on action_plans with USING and/or WITH CHECK containing owner_id = auth.uid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plans\s+FOR UPDATE[\s\S]*?TO authenticated/
      )
      // The UPDATE policy should contain owner_id = auth.uid() check
      expect(migrationSQL).toMatch(
        /FOR UPDATE[\s\S]*?TO authenticated[\s\S]*?owner_id\s*=\s*auth\.uid\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-042: action_plans has service_role full access policy', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the service_role policy on action_plans
      // Then: A policy exists FOR ALL TO service_role on action_plans with USING (true) and WITH CHECK (true)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plans\s+FOR ALL[\s\S]*?TO service_role[\s\S]*?USING\s*\(true\)[\s\S]*?WITH CHECK\s*\(true\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-043: action_plan_updates has SELECT policy for all authenticated users (USING true)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the SELECT RLS policy on action_plan_updates
      // Then: A policy exists FOR SELECT TO authenticated on action_plan_updates with USING (true) for timeline visibility

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plan_updates\s+FOR SELECT[\s\S]*?TO authenticated[\s\S]*?USING\s*\(true\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-044: action_plan_updates has INSERT policy restricting author_id = auth.uid()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the INSERT RLS policy on action_plan_updates
      // Then: A policy exists FOR INSERT TO authenticated on action_plan_updates with WITH CHECK containing author_id = auth.uid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plan_updates\s+FOR INSERT[\s\S]*?TO authenticated[\s\S]*?WITH CHECK\s*\([\s\S]*?author_id\s*=\s*auth\.uid\(\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-045: action_plan_updates has service_role full access policy', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the service_role policy on action_plan_updates
      // Then: A policy exists FOR ALL TO service_role on action_plan_updates with USING (true) and WITH CHECK (true)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON action_plan_updates\s+FOR ALL[\s\S]*?TO service_role[\s\S]*?USING\s*\(true\)[\s\S]*?WITH CHECK\s*\(true\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-046: action_plans RLS policies use DROP POLICY IF EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for DROP POLICY IF EXISTS statements for action_plans
      // Then: Each CREATE POLICY on action_plans is preceded by a corresponding DROP POLICY IF EXISTS statement

      requireMigration()
      // Count CREATE POLICY statements on action_plans
      const createPolicies = migrationSQL.match(
        /CREATE POLICY[\s\S]*?ON action_plans\s/g
      )
      expect(createPolicies).not.toBeNull()

      // Count DROP POLICY IF EXISTS statements on action_plans
      const dropPolicies = migrationSQL.match(
        /DROP POLICY IF EXISTS[\s\S]*?ON action_plans/g
      )
      expect(dropPolicies).not.toBeNull()
      expect(dropPolicies!.length).toBeGreaterThanOrEqual(createPolicies!.length)
    })

    it('16-1-action-plans-data-model-UNIT-047: action_plan_updates RLS policies use DROP POLICY IF EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for DROP POLICY IF EXISTS statements for action_plan_updates
      // Then: Each CREATE POLICY on action_plan_updates is preceded by a corresponding DROP POLICY IF EXISTS statement

      requireMigration()
      // Count CREATE POLICY statements on action_plan_updates
      const createPolicies = migrationSQL.match(
        /CREATE POLICY[\s\S]*?ON action_plan_updates\s/g
      )
      expect(createPolicies).not.toBeNull()

      // Count DROP POLICY IF EXISTS statements on action_plan_updates
      const dropPolicies = migrationSQL.match(
        /DROP POLICY IF EXISTS[\s\S]*?ON action_plan_updates/g
      )
      expect(dropPolicies).not.toBeNull()
      expect(dropPolicies!.length).toBeGreaterThanOrEqual(createPolicies!.length)
    })
  })

  // ==========================================================================
  // AC4: Performance Indexes Created
  // ==========================================================================

  describe('AC4: Performance Indexes Created', () => {
    it('16-1-action-plans-data-model-UNIT-048: Migration creates index idx_action_plans_asset_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_action_plans_asset_id is created on action_plans(asset_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_action_plans_asset_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_action_plans_asset_id\s+ON\s+action_plans\s*\(asset_id\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-049: Migration creates index idx_action_plans_status', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_action_plans_status is created on action_plans(status)

      requireMigration()
      expect(migrationSQL).toContain('idx_action_plans_status')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_action_plans_status\s+ON\s+action_plans\s*\(status\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-050: Migration creates index idx_action_plans_owner_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_action_plans_owner_id is created on action_plans(owner_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_action_plans_owner_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_action_plans_owner_id\s+ON\s+action_plans\s*\(owner_id\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-051: Migration creates index idx_action_plans_source_followup_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_action_plans_source_followup_id is created on action_plans(source_followup_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_action_plans_source_followup_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_action_plans_source_followup_id\s+ON\s+action_plans\s*\(source_followup_id\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-052: Migration creates index idx_action_plan_updates_action_plan_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_action_plan_updates_action_plan_id is created on action_plan_updates(action_plan_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_action_plan_updates_action_plan_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_action_plan_updates_action_plan_id\s+ON\s+action_plan_updates\s*\(action_plan_id\)/
      )
    })

    it('16-1-action-plans-data-model-UNIT-053: All five required indexes are present', () => {
      // Given: The migration SQL file content is loaded
      // When: All CREATE INDEX statements targeting action_plans and action_plan_updates are counted
      // Then: At least 5 CREATE INDEX statements exist across both tables

      requireMigration()
      const createIndexLines = migrationSQL.match(
        /CREATE INDEX.*action_plan/g
      )
      expect(createIndexLines).not.toBeNull()
      expect(createIndexLines!.length).toBeGreaterThanOrEqual(5)
    })

    it('16-1-action-plans-data-model-UNIT-054: Indexes use CREATE INDEX IF NOT EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for CREATE INDEX statements
      // Then: All index creation statements use CREATE INDEX IF NOT EXISTS for idempotency

      requireMigration()
      const allCreateIndex = migrationSQL.match(
        /CREATE INDEX.*action_plan/g
      )
      expect(allCreateIndex).not.toBeNull()

      for (const stmt of allCreateIndex!) {
        expect(stmt).toMatch(/CREATE INDEX IF NOT EXISTS/)
      }
    })
  })

  // ==========================================================================
  // AC5: Migration File Created
  // ==========================================================================

  describe('AC5: Migration File Created', () => {
    it('16-1-action-plans-data-model-UNIT-055: Migration file exists at correct path', () => {
      // Given: The migration is needed for story 16.1
      // When: The migrations folder is checked
      // Then: supabase/migrations/0034_action_plans.sql exists

      requireMigration()
      expect(fs.existsSync(MIGRATION_PATH)).toBe(true)
    })

    it('16-1-action-plans-data-model-UNIT-056: Migration file follows naming convention with correct sequence number', () => {
      // Given: The migration directory contains existing migrations up to 0033
      // When: The file name is validated against the sequence
      // Then: The migration file is named 0034_action_plans.sql and its number follows after the existing highest migration

      requireMigration()

      // Verify 0033 exists (the previous highest migration)
      const prevMigration = path.join(MIGRATIONS_DIR, '0033_followup_last_viewed.sql')
      expect(
        fs.existsSync(prevMigration),
        'Previous migration 0033_followup_last_viewed.sql should exist'
      ).toBe(true)

      // Verify 0034 follows 0033
      const migrationFilename = path.basename(MIGRATION_PATH)
      expect(migrationFilename).toBe('0034_action_plans.sql')
      expect(migrationFilename).toMatch(/^0034_/)
    })

    it('16-1-action-plans-data-model-UNIT-057: Migration uses CREATE TABLE IF NOT EXISTS for idempotency', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for CREATE TABLE statements
      // Then: Both CREATE TABLE IF NOT EXISTS action_plans and CREATE TABLE IF NOT EXISTS action_plan_updates are used

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plans/
      )
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plan_updates/
      )
    })

    it('16-1-action-plans-data-model-UNIT-058: Migration has header comment with story reference', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for header comments
      // Then: A comment referencing Story 16.1 or action plans exists at the top of the file

      requireMigration()
      // Look for a comment near the top of the file referencing 16.1 or action plans
      const firstLines = migrationSQL.substring(0, 500)
      expect(firstLines).toMatch(/--.*16\.1|--.*[Aa]ction [Pp]lan/)
    })

    it('16-1-action-plans-data-model-UNIT-059: Both tables are created in a single migration file', () => {
      // Given: The migration SQL file content is loaded
      // When: The file is checked for both CREATE TABLE statements
      // Then: Both CREATE TABLE IF NOT EXISTS action_plans and CREATE TABLE IF NOT EXISTS action_plan_updates exist in the same file

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plans/
      )
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plan_updates/
      )
    })

    it('16-1-action-plans-data-model-UNIT-060: No other files are created by this story (pure SQL migration)', () => {
      // Given: The story specifies this is a pure migration story
      // When: The migration file is the only artifact
      // Then: Only supabase/migrations/0034_action_plans.sql is created; no API code, frontend code, or Pydantic models

      requireMigration()
      // Validate the migration file is a SQL file
      expect(MIGRATION_PATH).toMatch(/\.sql$/)
      expect(path.basename(MIGRATION_PATH)).toBe('0034_action_plans.sql')
    })

    it('16-1-action-plans-data-model-UNIT-061: Migration does NOT use VARCHAR (uses TEXT consistently)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for VARCHAR usage
      // Then: No VARCHAR type appears in the migration; all string columns use TEXT

      requireMigration()
      expect(migrationSQL).not.toMatch(/VARCHAR/i)
    })

    it('16-1-action-plans-data-model-UNIT-062: Migration does NOT use uuid_generate_v4() (uses gen_random_uuid())', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for uuid_generate_v4()
      // Then: No uuid_generate_v4() appears; only gen_random_uuid() is used

      requireMigration()
      expect(migrationSQL).not.toMatch(/uuid_generate_v4\(\)/)
    })
  })

  // ==========================================================================
  // SQL Syntax Validation (cross-cutting)
  // ==========================================================================

  describe('SQL Syntax Validation', () => {
    it('16-1-action-plans-data-model-UNIT-063: Migration SQL has balanced parentheses', () => {
      // Given: The migration SQL file content is loaded
      // When: Open and close parentheses are counted
      // Then: The count of ( equals the count of )

      requireMigration()
      const openParens = (migrationSQL.match(/\(/g) || []).length
      const closeParens = (migrationSQL.match(/\)/g) || []).length
      expect(openParens).toBe(closeParens)
    })

    it('16-1-action-plans-data-model-UNIT-064: All SQL statements end with semicolons', () => {
      // Given: The migration SQL file content is loaded
      // When: CREATE TABLE, CREATE INDEX, ALTER TABLE, CREATE POLICY, and CREATE TRIGGER statements are parsed
      // Then: Each statement is properly terminated with a semicolon

      requireMigration()

      // Check that CREATE TABLE blocks end with ;
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plans\s*\([\s\S]*?\);/
      )
      expect(migrationSQL).toMatch(
        /CREATE TABLE IF NOT EXISTS action_plan_updates\s*\([\s\S]*?\);/
      )

      // Check that each CREATE INDEX ends with ;
      const createIndexStatements = migrationSQL.match(/CREATE INDEX[^;]*;/g)
      expect(createIndexStatements).not.toBeNull()
      expect(createIndexStatements!.length).toBeGreaterThanOrEqual(5)

      // Check that ALTER TABLE statements end with ;
      expect(migrationSQL).toMatch(
        /ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY\s*;/
      )
      expect(migrationSQL).toMatch(
        /ALTER TABLE action_plan_updates ENABLE ROW LEVEL SECURITY\s*;/
      )

      // Check that each CREATE POLICY ends with ;
      const createPolicyStatements = migrationSQL.match(/CREATE POLICY[^;]*;/g)
      expect(createPolicyStatements).not.toBeNull()
      expect(createPolicyStatements!.length).toBeGreaterThanOrEqual(7)

      // Check that CREATE TRIGGER ends with ;
      expect(migrationSQL).toMatch(/CREATE TRIGGER[^;]*;/)
    })
  })
})
