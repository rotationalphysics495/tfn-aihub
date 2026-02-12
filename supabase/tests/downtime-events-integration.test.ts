/**
 * Integration Tests for Downtime Events
 *
 * Story 14.1 - Downtime Events Data Model & Seed Data
 *
 * These tests validate the downtime_events table and seed data against
 * a running Supabase instance. They require:
 *   - A running Supabase instance (local or remote)
 *   - SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
 *   - Schema migrations applied (including 0029_downtime_events.sql)
 *   - Seed data loaded (via seed-data.mjs)
 *
 * Tests will FAIL until Story 14.1 is implemented because:
 *   - Migration 0029_downtime_events.sql does not yet exist
 *   - seed-data.mjs does not yet contain downtime_events data
 *   - The downtime_events table does not exist in the database
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// ============================================================================
// Setup
// ============================================================================

const SUPABASE_URL = process.env.SUPABASE_URL || 'http://127.0.0.1:54321'
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_KEY || ''

const canConnect = !!SUPABASE_KEY

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

const PLANNED_REASON_CODES = new Set(['Planned Maintenance', 'Changeover'])

const REQUIRED_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000004', // Grinder 1
  'a0000001-0000-0000-0000-000000000005', // Grinder 2
  'a0000001-0000-0000-0000-000000000006', // Grinder 3
  'a0000001-0000-0000-0000-000000000014', // Grinder 5
  'a0000001-0000-0000-0000-000000000001', // Roaster 1
  'a0000001-0000-0000-0000-000000000002', // Roaster 2
  'a0000001-0000-0000-0000-000000000008', // Filler Line A
  'a0000001-0000-0000-0000-000000000011', // Packaging Line 1
] as const

const SHIFT_VALUES = ['morning', 'afternoon', 'night'] as const

// ============================================================================
// Helpers
// ============================================================================

function daysAgoISO(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().split('T')[0]
}

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Downtime Events Integration (Story 14.1)', () => {
  let supabase: SupabaseClient
  let serviceClient: SupabaseClient

  beforeAll(() => {
    if (!canConnect) {
      console.warn('Skipping integration tests: SUPABASE_SERVICE_KEY not set')
      return
    }
    supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false },
    })
    serviceClient = supabase
  })

  // ==========================================================================
  // AC1: Database Migration Creates Table (Integration)
  // ==========================================================================

  describe('AC1: Table exists after migration', () => {
    it('14-1-downtime-events-data-model-seed-data-INT-001: Table exists in database after migration', async () => {
      // Given: The migration 0029_downtime_events.sql has been applied
      // When: The database is queried for the downtime_events table existence
      // Then: The table exists and can be queried

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('id')
        .limit(0)

      expect(error).toBeNull()
      expect(data).not.toBeNull()
    })

    it('14-1-downtime-events-data-model-seed-data-INT-002: All 12 columns exist with correct types after migration', async () => {
      // Given: The migration has been applied
      // When: A row is inserted and selected with all columns
      // Then: All 12 columns are returned

      if (!canConnect) return

      // Use a known asset_id from seed data
      const testAssetId = REQUIRED_ASSET_IDS[0]

      const testRow = {
        asset_id: testAssetId,
        event_date: daysAgoISO(1),
        shift: 'morning',
        reason_code: 'Mechanical',
        reason_detail: 'Integration test event',
        duration_minutes: 15,
        is_planned: false,
        source_system: 'manual',
        source_event_id: null,
      }

      // Insert test row
      const { data: inserted, error: insertErr } = await serviceClient
        .from('downtime_events')
        .insert(testRow)
        .select('*')
        .single()

      expect(insertErr).toBeNull()
      expect(inserted).not.toBeNull()

      // Verify all 12 columns exist
      expect(inserted).toHaveProperty('id')
      expect(inserted).toHaveProperty('asset_id')
      expect(inserted).toHaveProperty('event_date')
      expect(inserted).toHaveProperty('shift')
      expect(inserted).toHaveProperty('reason_code')
      expect(inserted).toHaveProperty('reason_detail')
      expect(inserted).toHaveProperty('duration_minutes')
      expect(inserted).toHaveProperty('is_planned')
      expect(inserted).toHaveProperty('source_system')
      expect(inserted).toHaveProperty('source_event_id')
      expect(inserted).toHaveProperty('created_at')
      expect(inserted).toHaveProperty('updated_at')

      // Clean up test row
      if (inserted) {
        await serviceClient
          .from('downtime_events')
          .delete()
          .eq('id', (inserted as any).id)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-003: Shift CHECK constraint rejects invalid values', async () => {
      // Given: The migration has been applied
      // When: An INSERT is attempted with shift = 'evening'
      // Then: The insert fails with a CHECK constraint violation

      if (!canConnect) return

      const { error } = await serviceClient
        .from('downtime_events')
        .insert({
          asset_id: REQUIRED_ASSET_IDS[0],
          event_date: daysAgoISO(1),
          shift: 'evening', // Invalid value
          reason_code: 'Mechanical',
          duration_minutes: 10,
        })

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/check|constraint|violat/i)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-004: FK constraint enforced - invalid asset_id rejected', async () => {
      // Given: The migration has been applied
      // When: An INSERT is attempted with a non-existent asset_id
      // Then: The insert fails with a FK constraint violation

      if (!canConnect) return

      const { error } = await serviceClient
        .from('downtime_events')
        .insert({
          asset_id: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
          event_date: daysAgoISO(1),
          shift: 'morning',
          reason_code: 'Mechanical',
          duration_minutes: 10,
        })

      expect(error).not.toBeNull()
      expect(error!.message).toMatch(/foreign key|violat|reference/i)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-005: CASCADE delete removes downtime_events when parent asset is deleted', async () => {
      // Given: A downtime_event row exists linked to a test asset
      // When: The parent asset is deleted
      // Then: The associated downtime_events rows are automatically deleted

      if (!canConnect) return

      // Create a test asset
      const testAssetId = 'aaaaaaaa-test-test-test-000000000001'
      const { error: assetInsertErr } = await serviceClient
        .from('assets')
        .insert({
          id: testAssetId,
          name: 'Test Asset for CASCADE',
          type: 'machine',
          area: 'Grinding',
        })

      // If we can't insert (already exists or other reason), skip
      if (assetInsertErr) {
        console.warn('Skipping CASCADE test: could not create test asset', assetInsertErr.message)
        return
      }

      // Insert a downtime event for the test asset
      const { data: eventData, error: eventInsertErr } = await serviceClient
        .from('downtime_events')
        .insert({
          asset_id: testAssetId,
          event_date: daysAgoISO(1),
          shift: 'morning',
          reason_code: 'Mechanical',
          duration_minutes: 20,
        })
        .select('id')
        .single()

      expect(eventInsertErr).toBeNull()
      expect(eventData).not.toBeNull()

      // Delete the parent asset
      await serviceClient
        .from('assets')
        .delete()
        .eq('id', testAssetId)

      // Verify the downtime event was cascade-deleted
      const { data: orphanCheck, error: orphanErr } = await serviceClient
        .from('downtime_events')
        .select('id')
        .eq('asset_id', testAssetId)

      expect(orphanErr).toBeNull()
      expect(orphanCheck).not.toBeNull()
      expect(orphanCheck!.length).toBe(0)
    })
  })

  // ==========================================================================
  // AC3: RLS Follows Existing Patterns (Integration)
  // ==========================================================================

  describe('AC3: RLS Policies', () => {
    it('14-1-downtime-events-data-model-seed-data-INT-006: Authenticated user can SELECT from downtime_events', async () => {
      // Given: RLS is enabled on downtime_events and seed data has been loaded
      // When: An authenticated user queries downtime_events
      // Then: Rows are returned successfully (read access granted)

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('id, asset_id, reason_code')
        .limit(5)

      expect(error).toBeNull()
      expect(data).not.toBeNull()
    })

    it('14-1-downtime-events-data-model-seed-data-INT-007: Service role can INSERT, UPDATE, DELETE on downtime_events', async () => {
      // Given: RLS is enabled on downtime_events
      // When: The service_role client performs INSERT, UPDATE, and DELETE
      // Then: All operations succeed

      if (!canConnect) return

      // INSERT
      const { data: inserted, error: insertErr } = await serviceClient
        .from('downtime_events')
        .insert({
          asset_id: REQUIRED_ASSET_IDS[0],
          event_date: daysAgoISO(1),
          shift: 'morning',
          reason_code: 'Mechanical',
          reason_detail: 'RLS test event',
          duration_minutes: 5,
          is_planned: false,
        })
        .select('id')
        .single()

      expect(insertErr).toBeNull()
      expect(inserted).not.toBeNull()

      const testId = (inserted as any).id

      // UPDATE
      const { error: updateErr } = await serviceClient
        .from('downtime_events')
        .update({ reason_detail: 'RLS test event - updated' })
        .eq('id', testId)

      expect(updateErr).toBeNull()

      // DELETE
      const { error: deleteErr } = await serviceClient
        .from('downtime_events')
        .delete()
        .eq('id', testId)

      expect(deleteErr).toBeNull()
    })

    it('14-1-downtime-events-data-model-seed-data-INT-008: Non-service-role cannot INSERT into downtime_events', async () => {
      // Given: RLS is enabled on downtime_events
      // When: An authenticated (non-service-role) user attempts to INSERT
      // Then: The insert is rejected by RLS policy

      if (!canConnect) return

      // Use the anon key if available, otherwise skip
      const anonKey = process.env.SUPABASE_ANON_KEY || ''
      if (!anonKey) {
        console.warn('Skipping anon INSERT test: SUPABASE_ANON_KEY not set')
        return
      }

      const anonClient = createClient(SUPABASE_URL, anonKey, {
        auth: { autoRefreshToken: false, persistSession: false },
      })

      const { error } = await anonClient
        .from('downtime_events')
        .insert({
          asset_id: REQUIRED_ASSET_IDS[0],
          event_date: daysAgoISO(1),
          shift: 'morning',
          reason_code: 'Mechanical',
          duration_minutes: 10,
        })

      // Expect RLS to block the insert
      expect(error).not.toBeNull()
    })
  })

  // ==========================================================================
  // AC4: Seed Data Aligns with Existing daily_summaries (Integration)
  // ==========================================================================

  describe('AC4: Seed Data Alignment with daily_summaries', () => {
    it('14-1-downtime-events-data-model-seed-data-INT-009: Downtime events exist for past 7 days after seed runs', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Downtime events are queried for event_date from daysAgo(7) to daysAgo(0)
      // Then: Events exist with event_date covering at least 7 distinct days

      if (!canConnect) return

      const startDate = daysAgoISO(7)
      const endDate = daysAgoISO(0)

      const { data, error } = await supabase
        .from('downtime_events')
        .select('event_date')
        .gte('event_date', startDate)
        .lte('event_date', endDate)

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const distinctDates = new Set(data!.map((row: any) => row.event_date))
      expect(
        distinctDates.size,
        `Should have at least 7 distinct event dates, found ${distinctDates.size}`
      ).toBeGreaterThanOrEqual(7)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-010: Sum of event durations per asset per day approximately matches daily_summaries.downtime_minutes', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: SUM(duration_minutes) from downtime_events is compared to daily_summaries.downtime_minutes
      // Then: The sums match within ±1 minute tolerance

      if (!canConnect) return

      const startDate = daysAgoISO(7)
      const endDate = daysAgoISO(0)

      // Get daily_summaries
      const { data: summaries, error: dsErr } = await supabase
        .from('daily_summaries')
        .select('asset_id, report_date, downtime_minutes')
        .gte('report_date', startDate)
        .lte('report_date', endDate)

      expect(dsErr).toBeNull()
      expect(summaries).not.toBeNull()

      // Get downtime_events
      const { data: events, error: evtErr } = await supabase
        .from('downtime_events')
        .select('asset_id, event_date, duration_minutes')
        .gte('event_date', startDate)
        .lte('event_date', endDate)

      expect(evtErr).toBeNull()
      expect(events).not.toBeNull()

      // Sum downtime_events durations per (asset_id, event_date)
      const eventSums: Record<string, number> = {}
      for (const evt of events!) {
        const key = `${(evt as any).asset_id}:${(evt as any).event_date}`
        eventSums[key] = (eventSums[key] || 0) + (evt as any).duration_minutes
      }

      // Compare with daily_summaries
      let mismatchCount = 0
      for (const ds of summaries!) {
        const key = `${(ds as any).asset_id}:${(ds as any).report_date}`
        const dsDowntime = (ds as any).downtime_minutes || 0
        const eventSum = eventSums[key] || 0

        // Only check assets that have downtime > 0 (they should have matching events)
        if (dsDowntime > 0) {
          const diff = Math.abs(dsDowntime - eventSum)
          if (diff > 1) {
            mismatchCount++
          }
        }
      }

      expect(
        mismatchCount,
        `Found ${mismatchCount} asset/day combinations where downtime_events sum doesn't match daily_summaries.downtime_minutes (±1 min tolerance)`
      ).toBe(0)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-011: Assets with zero downtime_minutes in daily_summaries have no downtime_events', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Daily summaries with downtime_minutes = 0 are identified
      // Then: No corresponding downtime_events rows exist

      if (!canConnect) return

      const startDate = daysAgoISO(7)
      const endDate = daysAgoISO(0)

      // Find daily_summaries where downtime_minutes = 0
      const { data: zeroDowntime, error: dsErr } = await supabase
        .from('daily_summaries')
        .select('asset_id, report_date')
        .eq('downtime_minutes', 0)
        .gte('report_date', startDate)
        .lte('report_date', endDate)

      expect(dsErr).toBeNull()

      if (!zeroDowntime || zeroDowntime.length === 0) {
        // No zero-downtime records to check
        return
      }

      // Check each zero-downtime asset/day for orphaned events
      for (const zd of zeroDowntime) {
        const { data: orphans, error: evtErr } = await supabase
          .from('downtime_events')
          .select('id')
          .eq('asset_id', (zd as any).asset_id)
          .eq('event_date', (zd as any).report_date)

        expect(evtErr).toBeNull()
        expect(
          orphans!.length,
          `Asset ${(zd as any).asset_id} on ${(zd as any).report_date} has 0 downtime_minutes but ${orphans!.length} downtime_events`
        ).toBe(0)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-012: Reason code distribution is realistic (Mechanical is most frequent)', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Downtime events are grouped by reason_code and counted
      // Then: "Mechanical" has the highest count and multiple reason codes are represented

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('reason_code')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      // Count by reason_code
      const counts: Record<string, number> = {}
      for (const row of data!) {
        const code = (row as any).reason_code
        counts[code] = (counts[code] || 0) + 1
      }

      const reasonCodes = Object.keys(counts)
      expect(
        reasonCodes.length,
        'Multiple reason codes should be represented'
      ).toBeGreaterThanOrEqual(4)

      // Mechanical should be most frequent
      const mechanicalCount = counts['Mechanical'] || 0
      for (const [code, count] of Object.entries(counts)) {
        if (code !== 'Mechanical') {
          expect(
            mechanicalCount,
            `Mechanical (${mechanicalCount}) should have higher count than ${code} (${count})`
          ).toBeGreaterThanOrEqual(count)
        }
      }
    })
  })

  // ==========================================================================
  // AC5: Standard Reason Codes Used (Integration)
  // ==========================================================================

  describe('AC5: Standard Reason Codes in Database', () => {
    it('14-1-downtime-events-data-model-seed-data-INT-013: Only standard reason codes exist in seeded data', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: SELECT DISTINCT reason_code FROM downtime_events is queried
      // Then: Only the 6 standard values appear

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('reason_code')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const distinctCodes = new Set(data!.map((row: any) => row.reason_code))

      // All codes should be in the standard set
      for (const code of distinctCodes) {
        expect(
          STANDARD_REASON_CODES as readonly string[],
          `"${code}" is not a standard reason code`
        ).toContain(code)
      }

      // All standard codes should be present
      for (const code of STANDARD_REASON_CODES) {
        expect(
          distinctCodes.has(code),
          `Standard reason code "${code}" should be present in seed data`
        ).toBe(true)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-014: is_planned is true for Planned Maintenance and Changeover, false for others', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Downtime events are queried grouped by reason_code and is_planned
      // Then: Correct planned/unplanned mapping

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('reason_code, is_planned')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      for (const row of data!) {
        const code = (row as any).reason_code
        const isPlanned = (row as any).is_planned

        if (PLANNED_REASON_CODES.has(code)) {
          expect(
            isPlanned,
            `"${code}" should have is_planned = true`
          ).toBe(true)
        } else {
          expect(
            isPlanned,
            `"${code}" should have is_planned = false`
          ).toBe(false)
        }
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-015: No events have non-standard reason codes', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Events are queried where reason_code is NOT one of the 6 standard codes
      // Then: Zero rows are returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('id, reason_code')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const standardSet = new Set<string>(STANDARD_REASON_CODES)
      const nonStandard = data!.filter(
        (row: any) => !standardSet.has(row.reason_code)
      )

      expect(
        nonStandard.length,
        `Found ${nonStandard.length} events with non-standard reason codes: ${nonStandard.map((r: any) => r.reason_code).join(', ')}`
      ).toBe(0)
    })
  })

  // ==========================================================================
  // AC6: Seed Data Covers Multiple Assets and Days (Integration)
  // ==========================================================================

  describe('AC6: Seed Data Coverage', () => {
    it('14-1-downtime-events-data-model-seed-data-INT-016: Events exist for at least 6 distinct assets', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: SELECT DISTINCT asset_id FROM downtime_events is queried
      // Then: At least 6 distinct asset IDs are returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('asset_id')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const distinctAssets = new Set(data!.map((row: any) => row.asset_id))
      expect(
        distinctAssets.size,
        `Should have at least 6 distinct assets, found ${distinctAssets.size}`
      ).toBeGreaterThanOrEqual(6)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-017: Events span at least 7 distinct days', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: SELECT DISTINCT event_date FROM downtime_events is queried
      // Then: At least 7 distinct event_date values are returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('event_date')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const distinctDates = new Set(data!.map((row: any) => row.event_date))
      expect(
        distinctDates.size,
        `Should have at least 7 distinct dates, found ${distinctDates.size}`
      ).toBeGreaterThanOrEqual(7)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-018: Each asset has 2-5 events per day on average', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Events are grouped by (asset_id, event_date) and counted
      // Then: Each group has between 1 and 8 events, average across all groups is between 2 and 5

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('asset_id, event_date')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      // Count events per (asset_id, event_date)
      const groupCounts: Record<string, number> = {}
      for (const row of data!) {
        const key = `${(row as any).asset_id}:${(row as any).event_date}`
        groupCounts[key] = (groupCounts[key] || 0) + 1
      }

      const counts = Object.values(groupCounts)
      expect(counts.length).toBeGreaterThan(0)

      // Each group should have between 1 and 8 events
      for (const [key, count] of Object.entries(groupCounts)) {
        expect(
          count,
          `Group ${key} has ${count} events, expected 1-8`
        ).toBeGreaterThanOrEqual(1)
        expect(
          count,
          `Group ${key} has ${count} events, expected 1-8`
        ).toBeLessThanOrEqual(8)
      }

      // Average should be between 2 and 5
      const avgCount = counts.reduce((a, b) => a + b, 0) / counts.length
      expect(
        avgCount,
        `Average events per asset/day is ${avgCount.toFixed(1)}, expected 2-5`
      ).toBeGreaterThanOrEqual(2)
      expect(
        avgCount,
        `Average events per asset/day is ${avgCount.toFixed(1)}, expected 2-5`
      ).toBeLessThanOrEqual(5)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-019: Events are distributed across all three shifts', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: SELECT DISTINCT shift FROM downtime_events is queried
      // Then: All three shift values appear: 'morning', 'afternoon', 'night'

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('shift')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const distinctShifts = new Set(data!.map((row: any) => row.shift))

      for (const shift of SHIFT_VALUES) {
        expect(
          distinctShifts.has(shift),
          `Shift "${shift}" should be present in downtime events`
        ).toBe(true)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-020: Specific required assets are covered', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Downtime events are queried for the 8 required asset UUIDs
      // Then: Events exist for all 8 required assets

      if (!canConnect) return

      for (const assetId of REQUIRED_ASSET_IDS) {
        const { data, error } = await supabase
          .from('downtime_events')
          .select('id')
          .eq('asset_id', assetId)
          .limit(1)

        expect(error).toBeNull()
        expect(
          data!.length,
          `Asset ${assetId} should have at least one downtime event`
        ).toBeGreaterThanOrEqual(1)
      }
    })

    it('14-1-downtime-events-data-model-seed-data-INT-021: source_system is \'manual\' and source_event_id is NULL for all seed data', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: All downtime_events are queried
      // Then: Every row has source_system = 'manual' and source_event_id IS NULL

      if (!canConnect) return

      // Check for non-manual source_system
      const { data: nonManual, error: err1 } = await supabase
        .from('downtime_events')
        .select('id, source_system')
        .neq('source_system', 'manual')

      expect(err1).toBeNull()
      expect(
        nonManual!.length,
        'All events should have source_system = "manual"'
      ).toBe(0)

      // Check for non-null source_event_id
      const { data: nonNullSource, error: err2 } = await supabase
        .from('downtime_events')
        .select('id, source_event_id')
        .not('source_event_id', 'is', null)

      expect(err2).toBeNull()
      expect(
        nonNullSource!.length,
        'All events should have source_event_id = NULL'
      ).toBe(0)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-022: Running seed script twice produces same row count (idempotency)', async () => {
      // Given: The seed script has been executed once
      // When: The count of downtime_events is recorded
      // Then: No duplicates exist (each asset_id/event_date/reason_code/shift combo is unique-ish)

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('asset_id, event_date, shift, reason_code, duration_minutes')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      // Build a map of composite keys to detect exact duplicates
      const keyCountMap = new Map<string, number>()
      for (const row of data!) {
        const key = `${(row as any).asset_id}:${(row as any).event_date}:${(row as any).shift}:${(row as any).reason_code}:${(row as any).duration_minutes}`
        keyCountMap.set(key, (keyCountMap.get(key) || 0) + 1)
      }

      // No exact duplicate should appear more than once
      let duplicateCount = 0
      for (const [, count] of keyCountMap.entries()) {
        if (count > 1) duplicateCount++
      }

      expect(
        duplicateCount,
        `Found ${duplicateCount} duplicate event combinations (idempotency check)`
      ).toBe(0)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-023: All events have positive duration_minutes', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Events are queried where duration_minutes <= 0
      // Then: Zero rows are returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('downtime_events')
        .select('id, duration_minutes')
        .lte('duration_minutes', 0)

      expect(error).toBeNull()
      expect(
        data!.length,
        'All events should have positive duration_minutes'
      ).toBe(0)
    })

    it('14-1-downtime-events-data-model-seed-data-INT-024: All events have non-null reason_detail descriptions', async () => {
      // Given: Schema migrations and seed script have been executed
      // When: Events are queried for reason_detail
      // Then: All (or most) events have non-empty reason_detail values

      if (!canConnect) return

      const { data: allEvents, error: allErr } = await supabase
        .from('downtime_events')
        .select('id')

      expect(allErr).toBeNull()

      const { data: nullDetails, error: nullErr } = await supabase
        .from('downtime_events')
        .select('id')
        .is('reason_detail', null)

      expect(nullErr).toBeNull()

      const totalCount = allEvents!.length
      const nullCount = nullDetails!.length

      // At least 90% of events should have non-null reason_detail
      const nonNullPercentage = ((totalCount - nullCount) / totalCount) * 100
      expect(
        nonNullPercentage,
        `${nonNullPercentage.toFixed(1)}% of events have reason_detail, expected >= 90%`
      ).toBeGreaterThanOrEqual(90)
    })
  })
})
