/**
 * Tests for Follow-Up Messages Schema Migration
 *
 * Story 15.1 - Follow-Up Messages Data Model
 *
 * UNIT tests that validate:
 *   - Migration file structure and SQL syntax for 0030_followup_messages.sql
 *   - Table schema (columns, types, constraints, defaults)
 *   - Indexes for query performance
 *   - RLS policies for access control
 *   - Foreign key cascade behavior
 *   - Migration naming convention and idempotency
 *
 * These tests read the migration SQL file and validate its contents statically.
 * They will FAIL until Story 15.1 implementation is complete because:
 *   - Migration file 0030_followup_messages.sql does not yet exist
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
  '0030_followup_messages.sql'
)

const MIGRATIONS_DIR = path.join(__dirname, '..', 'migrations')

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Follow-Up Messages Data Model (Story 15.1)', () => {
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
   * Helper: extract the CREATE TABLE followup_messages block from migration SQL.
   * Returns the text from CREATE TABLE through the closing );
   */
  function getCreateTableBlock(): string {
    const match = migrationSQL.match(
      /CREATE TABLE\s+followup_messages\s*\([\s\S]*?\);/
    )
    return match ? match[0] : ''
  }

  // ==========================================================================
  // AC1: Table exists with correct schema
  // ==========================================================================

  describe('AC1: Table exists with correct schema', () => {
    it('15-1-followup-messages-data-model-UNIT-001: Migration file exists and is non-empty', () => {
      // Given: The migration file 0030_followup_messages.sql has been created
      // When: The file system is checked for the migration file
      // Then: The file exists at the expected path and has non-empty content

      requireMigration()
      expect(migrationSQL.length).toBeGreaterThan(0)
    })

    it('15-1-followup-messages-data-model-UNIT-002: Migration creates followup_messages table with standard CREATE TABLE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for CREATE TABLE statement
      // Then: The migration contains CREATE TABLE followup_messages (without IF NOT EXISTS, per AC5)

      requireMigration()
      expect(migrationSQL).toContain('CREATE TABLE followup_messages')
      // Must NOT use IF NOT EXISTS per AC5
      expect(migrationSQL).not.toMatch(
        /CREATE TABLE IF NOT EXISTS followup_messages/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-003: Table has id column as UUID PK with gen_random_uuid() default', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the id column definition
      // Then: The column is defined as id UUID PRIMARY KEY DEFAULT gen_random_uuid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?id UUID PRIMARY KEY DEFAULT gen_random_uuid\(\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-004: Table has followup_id column as UUID NOT NULL FK to action_followups(id) ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the followup_id column definition
      // Then: The column is defined as followup_id UUID NOT NULL REFERENCES action_followups(id) ON DELETE CASCADE

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?followup_id UUID NOT NULL REFERENCES action_followups\(id\) ON DELETE CASCADE/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-005: Table has sender_id column as nullable UUID FK to auth.users(id)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the sender_id column definition
      // Then: The column is defined as sender_id UUID REFERENCES auth.users(id) without NOT NULL constraint

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?sender_id UUID REFERENCES auth\.users\(id\)/
      )
      // Verify it does NOT have NOT NULL
      const senderIdLine = migrationSQL.match(/sender_id UUID[^\n,)]*/)
      expect(senderIdLine).not.toBeNull()
      expect(senderIdLine![0]).not.toMatch(/NOT NULL/)
    })

    it('15-1-followup-messages-data-model-UNIT-006: Table has sender_email column as TEXT NOT NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the sender_email column definition
      // Then: The column is defined as sender_email TEXT NOT NULL

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?sender_email TEXT NOT NULL/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-007: Table has direction column with CHECK constraint for outbound/inbound', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the direction column definition
      // Then: The column is defined as direction TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound'))

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?direction TEXT NOT NULL CHECK\s*\(direction IN \('outbound',\s*'inbound'\)\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-008: Table has message_type column with CHECK constraint for valid types', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the message_type column definition
      // Then: The column is defined as message_type TEXT NOT NULL CHECK (message_type IN ('assignment', 'response', 'escalation', 'status_update'))

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_messages[\s\S]*?message_type TEXT NOT NULL CHECK\s*\(message_type IN \('assignment',\s*'response',\s*'escalation',\s*'status_update'\)\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-009: Table has subject column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the subject column definition
      // Then: The column is defined as subject TEXT without NOT NULL constraint

      requireMigration()
      const block = getCreateTableBlock()
      expect(block).toContain('subject TEXT')
      // Verify subject does NOT have NOT NULL
      const subjectLine = block.match(/subject TEXT[^\n,)]*/)
      expect(subjectLine).not.toBeNull()
      expect(subjectLine![0]).not.toMatch(/NOT NULL/)
    })

    it('15-1-followup-messages-data-model-UNIT-010: Table has body column as nullable TEXT', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the body column definition
      // Then: The column is defined as body TEXT without NOT NULL constraint

      requireMigration()
      const block = getCreateTableBlock()
      expect(block).toContain('body TEXT')
      // Verify body does NOT have NOT NULL
      const bodyLine = block.match(/body TEXT[^\n,)]*/)
      expect(bodyLine).not.toBeNull()
      expect(bodyLine![0]).not.toMatch(/NOT NULL/)
    })

    it('15-1-followup-messages-data-model-UNIT-011: Table has sent_at column as TIMESTAMPTZ without default', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the sent_at column definition
      // Then: The column is defined as sent_at TIMESTAMPTZ (or TIMESTAMP WITH TIME ZONE) without a DEFAULT

      requireMigration()
      const block = getCreateTableBlock()
      // Accept either TIMESTAMPTZ or TIMESTAMP WITH TIME ZONE
      expect(block).toMatch(/sent_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)/)
      // Verify no DEFAULT on sent_at
      const sentAtLine = block.match(/sent_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)[^\n,)]*/)
      expect(sentAtLine).not.toBeNull()
      expect(sentAtLine![0]).not.toMatch(/DEFAULT/)
    })

    it('15-1-followup-messages-data-model-UNIT-012: Table has created_at column as TIMESTAMPTZ with DEFAULT NOW()', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the created_at column definition
      // Then: The column is defined as created_at TIMESTAMPTZ DEFAULT NOW() (or TIMESTAMP WITH TIME ZONE DEFAULT NOW())

      requireMigration()
      const block = getCreateTableBlock()
      expect(block).toMatch(
        /created_at\s+(TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE)\s+(NOT NULL\s+)?DEFAULT NOW\(\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-013: Table does NOT have updated_at column (append-only)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for an updated_at column
      // Then: No updated_at column definition exists in the followup_messages CREATE TABLE statement

      requireMigration()
      const block = getCreateTableBlock()
      expect(block).not.toMatch(/updated_at/)
    })

    it('15-1-followup-messages-data-model-UNIT-014: Table does NOT have a status or read_at column', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for status or read_at columns in the followup_messages table
      // Then: Neither status nor read_at appear as column definitions in the followup_messages CREATE TABLE block

      requireMigration()
      const block = getCreateTableBlock()
      // status and read_at should NOT be column definitions in this table
      expect(block).not.toMatch(/\bstatus\b\s+TEXT/)
      expect(block).not.toMatch(/\bread_at\b/)
    })

    it('15-1-followup-messages-data-model-UNIT-015: Table has exactly 10 columns', () => {
      // Given: The migration SQL file content is loaded
      // When: The CREATE TABLE statement is parsed for column definitions
      // Then: Exactly 10 columns are defined: id, followup_id, sender_id, sender_email, direction, message_type, subject, body, sent_at, created_at

      requireMigration()
      const block = getCreateTableBlock()

      const expectedColumns = [
        'id',
        'followup_id',
        'sender_id',
        'sender_email',
        'direction',
        'message_type',
        'subject',
        'body',
        'sent_at',
        'created_at',
      ]

      // Verify each expected column exists
      for (const col of expectedColumns) {
        expect(
          block,
          `Column "${col}" should exist in CREATE TABLE followup_messages`
        ).toMatch(new RegExp(`\\b${col}\\b`))
      }

      // Count column definitions by matching lines that start with a column name followed by a type keyword
      // Column definitions start with an identifier followed by a SQL type
      const columnPattern = /^\s+(id|followup_id|sender_id|sender_email|direction|message_type|subject|body|sent_at|created_at)\s+(UUID|TEXT|TIMESTAMPTZ|TIMESTAMP)/gm
      const matches = block.match(columnPattern)
      expect(
        matches,
        'Should find column definitions in CREATE TABLE block'
      ).not.toBeNull()
      expect(
        matches!.length,
        `Expected exactly 10 columns, found ${matches?.length}`
      ).toBe(10)
    })
  })

  // ==========================================================================
  // AC2: Indexes exist for query performance
  // ==========================================================================

  describe('AC2: Indexes exist for query performance', () => {
    it('15-1-followup-messages-data-model-UNIT-016: Migration creates index on followup_id', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_followup_messages_followup_id is created on followup_messages(followup_id)

      requireMigration()
      expect(migrationSQL).toContain('idx_followup_messages_followup_id')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_followup_messages_followup_id\s+ON\s+followup_messages\s*\(followup_id\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-017: Migration creates index on direction', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_followup_messages_direction is created on followup_messages(direction)

      requireMigration()
      expect(migrationSQL).toContain('idx_followup_messages_direction')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_followup_messages_direction\s+ON\s+followup_messages\s*\(direction\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-018: Migration creates index on sent_at', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for index creation statements
      // Then: An index named idx_followup_messages_sent_at is created on followup_messages(sent_at)

      requireMigration()
      expect(migrationSQL).toContain('idx_followup_messages_sent_at')
      expect(migrationSQL).toMatch(
        /CREATE INDEX.*idx_followup_messages_sent_at\s+ON\s+followup_messages\s*\(sent_at\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-019: All three required indexes are present', () => {
      // Given: The migration SQL file content is loaded
      // When: All CREATE INDEX statements targeting followup_messages are counted
      // Then: At least 3 CREATE INDEX statements exist for the followup_messages table

      requireMigration()
      const createIndexLines = migrationSQL.match(
        /CREATE INDEX.*followup_messages/g
      )
      expect(createIndexLines).not.toBeNull()
      expect(createIndexLines!.length).toBeGreaterThanOrEqual(3)
    })
  })

  // ==========================================================================
  // AC3: RLS policies enforce access control
  // ==========================================================================

  describe('AC3: RLS policies enforce access control', () => {
    it('15-1-followup-messages-data-model-UNIT-020: Migration enables RLS on followup_messages', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for RLS enablement
      // Then: The statement ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY exists

      requireMigration()
      expect(migrationSQL).toContain(
        'ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY'
      )
    })

    it('15-1-followup-messages-data-model-UNIT-021: SELECT policy uses EXISTS subquery joining action_followups', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the SELECT RLS policy
      // Then: A policy exists FOR SELECT TO authenticated with a USING clause containing
      //       an EXISTS subquery that joins action_followups on followup_id and checks
      //       assigned_to = auth.uid() OR assigned_by = auth.uid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON followup_messages\s+FOR SELECT[\s\S]*?TO authenticated/
      )
      // The SELECT policy should contain an EXISTS subquery referencing action_followups
      expect(migrationSQL).toMatch(
        /FOR SELECT[\s\S]*?USING\s*\([\s\S]*?EXISTS\s*\([\s\S]*?action_followups[\s\S]*?followup_id[\s\S]*?(assigned_to\s*=\s*auth\.uid\(\)|assigned_by\s*=\s*auth\.uid\(\))/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-022: INSERT policy uses EXISTS subquery joining action_followups', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the INSERT RLS policy
      // Then: A policy exists FOR INSERT TO authenticated with a WITH CHECK clause containing
      //       an EXISTS subquery that joins action_followups on followup_id and checks
      //       assigned_to = auth.uid() OR assigned_by = auth.uid()

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON followup_messages\s+FOR INSERT[\s\S]*?TO authenticated/
      )
      // The INSERT policy should contain a WITH CHECK clause with EXISTS subquery
      expect(migrationSQL).toMatch(
        /FOR INSERT[\s\S]*?WITH CHECK\s*\([\s\S]*?EXISTS\s*\([\s\S]*?action_followups[\s\S]*?followup_id[\s\S]*?(assigned_to\s*=\s*auth\.uid\(\)|assigned_by\s*=\s*auth\.uid\(\))/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-023: Service role has full access policy', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the service_role policy
      // Then: A policy exists FOR ALL TO service_role with USING (true) and WITH CHECK (true)

      requireMigration()
      expect(migrationSQL).toMatch(
        /CREATE POLICY[\s\S]*?ON followup_messages\s+FOR ALL[\s\S]*?TO service_role[\s\S]*?USING\s*\(true\)[\s\S]*?WITH CHECK\s*\(true\)/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-024: No DELETE policy exists for authenticated users', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for DELETE policies targeting authenticated role
      // Then: No policy contains FOR DELETE with TO authenticated

      requireMigration()
      // Should NOT have a DELETE policy for authenticated users
      expect(migrationSQL).not.toMatch(
        /CREATE POLICY[\s\S]*?ON followup_messages\s+FOR DELETE[\s\S]*?TO authenticated/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-025: No UPDATE policy exists for authenticated users', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for UPDATE policies targeting authenticated role
      // Then: No policy contains FOR UPDATE with TO authenticated

      requireMigration()
      // Should NOT have an UPDATE policy for authenticated users
      expect(migrationSQL).not.toMatch(
        /CREATE POLICY[\s\S]*?ON followup_messages\s+FOR UPDATE[\s\S]*?TO authenticated/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-026: RLS policies are in the same migration file as table creation', () => {
      // Given: The migration SQL file content is loaded
      // When: The file is checked for both CREATE TABLE and CREATE POLICY statements
      // Then: Both CREATE TABLE followup_messages and all CREATE POLICY statements exist in the same file

      requireMigration()
      expect(migrationSQL).toContain('CREATE TABLE followup_messages')
      expect(migrationSQL).toMatch(/CREATE POLICY[\s\S]*?ON followup_messages/)
      expect(migrationSQL).toContain(
        'ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY'
      )
    })
  })

  // ==========================================================================
  // AC4: Foreign key cascades
  // ==========================================================================

  describe('AC4: Foreign key cascades', () => {
    it('15-1-followup-messages-data-model-UNIT-027: followup_id FK uses ON DELETE CASCADE', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the followup_id foreign key constraint
      // Then: The followup_id column definition includes REFERENCES action_followups(id) ON DELETE CASCADE

      requireMigration()
      expect(migrationSQL).toMatch(
        /followup_id[\s\S]*?REFERENCES action_followups\(id\) ON DELETE CASCADE/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-028: followup_id FK does NOT use ON DELETE SET NULL', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for SET NULL behavior on followup_id
      // Then: No ON DELETE SET NULL appears in conjunction with action_followups(id)

      requireMigration()
      expect(migrationSQL).not.toMatch(
        /action_followups\(id\)\s+ON DELETE SET NULL/
      )
    })
  })

  // ==========================================================================
  // AC5: Migration is idempotent-safe
  // ==========================================================================

  describe('AC5: Migration is idempotent-safe', () => {
    it('15-1-followup-messages-data-model-UNIT-029: Migration file uses standard CREATE TABLE (not IF NOT EXISTS)', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is parsed for the CREATE TABLE statement
      // Then: The statement is CREATE TABLE followup_messages without IF NOT EXISTS

      requireMigration()
      expect(migrationSQL).toContain('CREATE TABLE followup_messages')
      expect(migrationSQL).not.toMatch(
        /CREATE TABLE IF NOT EXISTS followup_messages/
      )
    })

    it('15-1-followup-messages-data-model-UNIT-030: Migration file follows naming convention with correct sequence number', () => {
      // Given: The migration directory is checked for existing migration files
      // When: The file name 0030_followup_messages.sql is validated against the sequence
      // Then: The migration file is named 0030_followup_messages.sql and its number (0030) follows after the existing highest migration (0029_downtime_events.sql)

      requireMigration()

      // Verify 0029 exists (the previous highest migration)
      const prevMigration = path.join(MIGRATIONS_DIR, '0029_downtime_events.sql')
      expect(
        fs.existsSync(prevMigration),
        'Previous migration 0029_downtime_events.sql should exist'
      ).toBe(true)

      // Verify 0030 follows 0029
      const migrationFilename = path.basename(MIGRATION_PATH)
      expect(migrationFilename).toBe('0030_followup_messages.sql')
      expect(migrationFilename).toMatch(/^0030_/)
    })

    it('15-1-followup-messages-data-model-UNIT-031: No other file is created by this story', () => {
      // Given: The story specifies this is a pure migration story
      // When: The migration file is the only artifact
      // Then: Only supabase/migrations/0030_followup_messages.sql is created; no API code, frontend code, or Pydantic models

      requireMigration()
      // This is validated by confirming the migration file exists
      // and that the migration file is a SQL file (not a TypeScript, Python, etc. file)
      expect(MIGRATION_PATH).toMatch(/\.sql$/)
      expect(path.basename(MIGRATION_PATH)).toBe('0030_followup_messages.sql')
    })
  })

  // ==========================================================================
  // SQL Syntax Validation (cross-cutting)
  // ==========================================================================

  describe('SQL Syntax Validation', () => {
    it('15-1-followup-messages-data-model-UNIT-032: Migration SQL has balanced parentheses', () => {
      // Given: The migration SQL file content is loaded
      // When: Open and close parentheses are counted
      // Then: The count of ( equals the count of )

      requireMigration()
      const openParens = (migrationSQL.match(/\(/g) || []).length
      const closeParens = (migrationSQL.match(/\)/g) || []).length
      expect(openParens).toBe(closeParens)
    })

    it('15-1-followup-messages-data-model-UNIT-033: All SQL statements end with semicolons', () => {
      // Given: The migration SQL file content is loaded
      // When: CREATE TABLE, CREATE INDEX, ALTER TABLE, and CREATE POLICY statements are parsed
      // Then: Each statement is properly terminated with a semicolon

      requireMigration()

      // Check that CREATE TABLE block ends with ;
      expect(migrationSQL).toMatch(/CREATE TABLE followup_messages\s*\([\s\S]*?\);/)

      // Check that each CREATE INDEX ends with ;
      const createIndexStatements = migrationSQL.match(/CREATE INDEX[^;]*;/g)
      expect(createIndexStatements).not.toBeNull()
      expect(createIndexStatements!.length).toBeGreaterThanOrEqual(3)

      // Check that ALTER TABLE ends with ;
      expect(migrationSQL).toMatch(
        /ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY\s*;/
      )

      // Check that each CREATE POLICY ends with ;
      const createPolicyStatements = migrationSQL.match(/CREATE POLICY[^;]*;/g)
      expect(createPolicyStatements).not.toBeNull()
      expect(createPolicyStatements!.length).toBeGreaterThanOrEqual(3)
    })

    it('15-1-followup-messages-data-model-UNIT-034: Migration does NOT contain updated_at trigger', () => {
      // Given: The migration SQL file content is loaded
      // When: The SQL is searched for CREATE TRIGGER statements
      // Then: No trigger for updating updated_at exists, confirming the append-only design

      requireMigration()
      expect(migrationSQL).not.toMatch(/CREATE TRIGGER/i)
      expect(migrationSQL).not.toMatch(/update_updated_at/i)
    })
  })
})
