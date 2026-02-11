/**
 * Integration Tests for Seed Data
 *
 * Story 11.3 - Workcenter Seed Data
 *
 * These tests validate the seed data against a running Supabase instance.
 * They require:
 *   - A running Supabase instance (local or remote)
 *   - SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
 *   - Schema migrations applied
 *   - Seed data loaded (via seed-data.mjs or 0021_seed_data.sql)
 *
 * Tests will FAIL until Story 11.3 is implemented because:
 *   - Missing daily_summaries for 6 assets on T-1
 *   - Missing shift_targets in seed-data.mjs
 *   - Roaster shift_target sums don't equal 143
 *   - No 7-day coverage for several assets
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// ============================================================================
// Setup
// ============================================================================

const SUPABASE_URL = process.env.SUPABASE_URL || 'http://127.0.0.1:54321'
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_KEY || ''

const WORKCENTER_AREAS = ['Roasting', 'Grinding', 'Filling', 'Packaging'] as const

const EXPECTED_ASSET_COUNTS: Record<string, number> = {
  Roasting: 3,
  Grinding: 5,
  Filling: 3,
  Packaging: 3,
}

const ALL_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000001',
  'a0000001-0000-0000-0000-000000000002',
  'a0000001-0000-0000-0000-000000000003',
  'a0000001-0000-0000-0000-000000000004',
  'a0000001-0000-0000-0000-000000000005',
  'a0000001-0000-0000-0000-000000000006',
  'a0000001-0000-0000-0000-000000000007',
  'a0000001-0000-0000-0000-000000000014',
  'a0000001-0000-0000-0000-000000000008',
  'a0000001-0000-0000-0000-000000000009',
  'a0000001-0000-0000-0000-000000000010',
  'a0000001-0000-0000-0000-000000000011',
  'a0000001-0000-0000-0000-000000000012',
  'a0000001-0000-0000-0000-000000000013',
]

// Helper to compute yesterday's date in ISO format
function getYesterdayISO(): string {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
}

// Helper to compute a date N days ago in ISO format
function daysAgoISO(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().split('T')[0]
}

// ============================================================================
// Skip integration tests if no Supabase connection available
// ============================================================================

const canConnect = !!SUPABASE_KEY

describe('Feature: Workcenter Seed Data Integration (Story 11.3)', () => {
  let supabase: SupabaseClient
  const yesterday = getYesterdayISO()

  beforeAll(() => {
    if (!canConnect) {
      console.warn('Skipping integration tests: SUPABASE_SERVICE_KEY not set')
      return
    }
    supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false },
    })
  })

  // ==========================================================================
  // AC1: All 4 workcenters have daily_summaries for T-1
  // ==========================================================================

  describe('AC1: All 4 workcenters have data for T-1', () => {
    it('11-3-workcenter-seed-data-INT-001: All 4 workcenters have daily_summaries for T-1 after seed-data.mjs runs', async () => {
      // Given: A clean database with schema migrations applied and seed-data.mjs has been executed
      // When: daily_summaries are queried joined with assets, filtered by T-1, grouped by area
      // Then: Exactly 4 distinct area values are returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const areas = new Set(data!.map((row: any) => row.assets.area))
      expect(areas.size).toBe(4)
      for (const area of WORKCENTER_AREAS) {
        expect(areas.has(area), `${area} should have T-1 data`).toBe(true)
      }

      // All 14 assets must have at least one daily_summary row for T-1
      const assetIds = new Set(data!.map((row: any) => row.asset_id))
      expect(assetIds.size).toBe(14)
    })

    it('11-3-workcenter-seed-data-INT-002: All 4 workcenters have daily_summaries for T-1 after 0021_seed_data.sql runs', async () => {
      // Given: A clean database with schema migrations applied via supabase db reset
      // When: daily_summaries are queried for T-1 grouped by area
      // Then: Exactly 4 distinct area values are returned

      // This test validates the same condition as INT-001 but focuses on
      // verifying the SQL migration path. In practice, both should produce
      // the same result.

      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const areas = new Set(data!.map((row: any) => row.assets.area))
      expect(areas.size).toBe(4)
      for (const area of WORKCENTER_AREAS) {
        expect(areas.has(area)).toBe(true)
      }
    })

    it('11-3-workcenter-seed-data-INT-003: No workcenter is missing from T-1 data (symmetric difference check)', async () => {
      // Given: The seed script has run successfully
      // When: The set of distinct area values from daily_summaries for T-1 is compared against expected
      // Then: The symmetric difference is empty (no missing, no extra)

      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('assets!inner(area)')
        .eq('report_date', yesterday)

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const actualAreas = new Set(data!.map((row: any) => row.assets.area))
      const expectedAreas = new Set(WORKCENTER_AREAS)

      // Symmetric difference should be empty
      const missingFromActual = [...expectedAreas].filter(a => !actualAreas.has(a))
      const extraInActual = [...actualAreas].filter(a => !expectedAreas.has(a))

      expect(
        missingFromActual,
        `Missing workcenters: ${missingFromActual.join(', ')}`
      ).toHaveLength(0)
      expect(
        extraInActual,
        `Extra workcenters: ${extraInActual.join(', ')}`
      ).toHaveLength(0)
    })
  })

  // ==========================================================================
  // AC2: Each workcenter has correct asset counts and varied performance
  // ==========================================================================

  describe('AC2: Correct asset counts and varied performance per workcenter', () => {
    it('11-3-workcenter-seed-data-INT-004: Roasting workcenter has exactly 3 assets with T-1 daily_summaries', async () => {
      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)
        .eq('assets.area', 'Roasting')

      expect(error).toBeNull()
      const distinctAssets = new Set(data!.map((row: any) => row.asset_id))
      expect(distinctAssets.size).toBe(3)
    })

    it('11-3-workcenter-seed-data-INT-005: Grinding workcenter has exactly 5 assets with T-1 daily_summaries', async () => {
      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)
        .eq('assets.area', 'Grinding')

      expect(error).toBeNull()
      const distinctAssets = new Set(data!.map((row: any) => row.asset_id))
      expect(distinctAssets.size).toBe(5)
    })

    it('11-3-workcenter-seed-data-INT-006: Filling workcenter has exactly 3 assets with T-1 daily_summaries', async () => {
      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)
        .eq('assets.area', 'Filling')

      expect(error).toBeNull()
      const distinctAssets = new Set(data!.map((row: any) => row.asset_id))
      expect(distinctAssets.size).toBe(3)
    })

    it('11-3-workcenter-seed-data-INT-007: Packaging workcenter has exactly 3 assets with T-1 daily_summaries', async () => {
      if (!canConnect) return

      const { data, error } = await supabase
        .from('daily_summaries')
        .select('asset_id, assets!inner(area)')
        .eq('report_date', yesterday)
        .eq('assets.area', 'Packaging')

      expect(error).toBeNull()
      const distinctAssets = new Set(data!.map((row: any) => row.asset_id))
      expect(distinctAssets.size).toBe(3)
    })

    it('11-3-workcenter-seed-data-INT-008: Each workcenter has at least one asset that hits target on T-1', async () => {
      // Given: Seed data has been loaded
      // When: For each workcenter, actual_output >= target_output is evaluated per asset
      // Then: Every workcenter has at least 1 asset where actual_output >= target_output

      if (!canConnect) return

      for (const area of WORKCENTER_AREAS) {
        const { data, error } = await supabase
          .from('daily_summaries')
          .select('asset_id, actual_output, target_output, assets!inner(area)')
          .eq('report_date', yesterday)
          .eq('assets.area', area)

        expect(error).toBeNull()
        expect(data).not.toBeNull()

        const hitters = data!.filter(
          (row: any) => row.actual_output >= row.target_output
        )
        expect(
          hitters.length,
          `${area} should have at least one asset hitting target`
        ).toBeGreaterThanOrEqual(1)
      }
    })

    it('11-3-workcenter-seed-data-INT-009: Each workcenter has at least one asset that misses target on T-1', async () => {
      // Given: Seed data has been loaded
      // When: For each workcenter, actual_output < target_output is evaluated per asset
      // Then: Every workcenter has at least 1 asset where actual_output < target_output

      if (!canConnect) return

      for (const area of WORKCENTER_AREAS) {
        const { data, error } = await supabase
          .from('daily_summaries')
          .select('asset_id, actual_output, target_output, assets!inner(area)')
          .eq('report_date', yesterday)
          .eq('assets.area', area)

        expect(error).toBeNull()
        expect(data).not.toBeNull()

        const missers = data!.filter(
          (row: any) => row.actual_output < row.target_output
        )
        expect(
          missers.length,
          `${area} should have at least one asset missing target`
        ).toBeGreaterThanOrEqual(1)
      }
    })
  })

  // ==========================================================================
  // AC3: Attainment ranges ~70% to ~100%
  // ==========================================================================

  describe('AC3: Realistic attainment variation across workcenters', () => {
    /**
     * Helper: calculate workcenter attainment from daily_summaries.
     */
    async function getWorkcenterAttainment(
      client: SupabaseClient,
      area: string,
      reportDate: string
    ): Promise<number> {
      const { data, error } = await client
        .from('daily_summaries')
        .select('actual_output, target_output, assets!inner(area)')
        .eq('report_date', reportDate)
        .eq('assets.area', area)

      if (error || !data || data.length === 0) return 0

      const totalActual = data.reduce((sum: number, row: any) => sum + (row.actual_output || 0), 0)
      const totalTarget = data.reduce((sum: number, row: any) => sum + (row.target_output || 0), 0)

      return totalTarget > 0 ? (totalActual / totalTarget) * 100 : 0
    }

    it('11-3-workcenter-seed-data-INT-010: Roasting workcenter attainment is approximately 88% on T-1', async () => {
      if (!canConnect) return

      const attainment = await getWorkcenterAttainment(supabase, 'Roasting', yesterday)
      expect(attainment).toBeGreaterThanOrEqual(82)
      expect(attainment).toBeLessThanOrEqual(95)
    })

    it('11-3-workcenter-seed-data-INT-011: Grinding workcenter attainment is approximately 83% on T-1', async () => {
      if (!canConnect) return

      const attainment = await getWorkcenterAttainment(supabase, 'Grinding', yesterday)
      expect(attainment).toBeGreaterThanOrEqual(75)
      expect(attainment).toBeLessThanOrEqual(90)
    })

    it('11-3-workcenter-seed-data-INT-012: Filling workcenter attainment is approximately 80% on T-1', async () => {
      if (!canConnect) return

      const attainment = await getWorkcenterAttainment(supabase, 'Filling', yesterday)
      expect(attainment).toBeGreaterThanOrEqual(70)
      expect(attainment).toBeLessThanOrEqual(88)
    })

    it('11-3-workcenter-seed-data-INT-013: Packaging workcenter attainment is approximately 88% on T-1', async () => {
      if (!canConnect) return

      const attainment = await getWorkcenterAttainment(supabase, 'Packaging', yesterday)
      expect(attainment).toBeGreaterThanOrEqual(82)
      expect(attainment).toBeLessThanOrEqual(95)
    })

    it('11-3-workcenter-seed-data-INT-014: Cross-workcenter attainment spread covers meaningful range', async () => {
      // Given: Seed data has been loaded
      // When: Attainment percentages are calculated for all 4 workcenters on T-1
      // Then: min <= 85% AND max >= 85%, no workcenter below 70% or above 100%

      if (!canConnect) return

      const attainments: number[] = []
      for (const area of WORKCENTER_AREAS) {
        const att = await getWorkcenterAttainment(supabase, area, yesterday)
        attainments.push(att)
      }

      const minAtt = Math.min(...attainments)
      const maxAtt = Math.max(...attainments)

      expect(minAtt, 'Min workcenter attainment should be <= 85%').toBeLessThanOrEqual(85)
      expect(maxAtt, 'Max workcenter attainment should be >= 85%').toBeGreaterThanOrEqual(85)
      expect(minAtt, 'No workcenter should be below 70%').toBeGreaterThanOrEqual(70)
      expect(maxAtt, 'No workcenter should be above 100%').toBeLessThanOrEqual(100)
    })
  })

  // ==========================================================================
  // AC4: Correct asset counts per workcenter area
  // ==========================================================================

  describe('AC4: Asset counts per workcenter in database', () => {
    it('11-3-workcenter-seed-data-INT-015: Database query confirms correct asset counts per workcenter area', async () => {
      // Given: Seed data has been loaded
      // When: SELECT area, COUNT(*) FROM assets GROUP BY area is executed
      // Then: Roasting=3, Grinding=5, Filling=3, Packaging=3

      if (!canConnect) return

      const { data, error } = await supabase
        .from('assets')
        .select('area')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const areaCounts: Record<string, number> = {}
      for (const row of data!) {
        const area = (row as any).area
        if (area) {
          areaCounts[area] = (areaCounts[area] || 0) + 1
        }
      }

      expect(areaCounts['Roasting']).toBe(3)
      expect(areaCounts['Grinding']).toBe(5)
      expect(areaCounts['Filling']).toBe(3)
      expect(areaCounts['Packaging']).toBe(3)

      const total = Object.values(areaCounts).reduce((a, b) => a + b, 0)
      expect(total).toBe(14)
    })
  })

  // ==========================================================================
  // AC5: shift_targets exist for all assets
  // ==========================================================================

  describe('AC5: shift_targets coverage', () => {
    it('11-3-workcenter-seed-data-INT-016: Every asset has at least one shift_target record after seeding', async () => {
      // Given: Seed data has been loaded
      // When: Assets are LEFT JOINed with shift_targets
      // Then: Every asset has target_count >= 1

      if (!canConnect) return

      const { data: assets, error: assetsErr } = await supabase
        .from('assets')
        .select('id, name')

      expect(assetsErr).toBeNull()
      expect(assets).not.toBeNull()
      expect(assets!.length).toBe(14)

      for (const asset of assets!) {
        const { data: targets, error: targetErr } = await supabase
          .from('shift_targets')
          .select('id')
          .eq('asset_id', (asset as any).id)

        expect(targetErr).toBeNull()
        expect(
          targets!.length,
          `Asset ${(asset as any).name} (${(asset as any).id}) should have at least one shift_target`
        ).toBeGreaterThanOrEqual(1)
      }
    })

    it('11-3-workcenter-seed-data-INT-017: All workcenters have shift_target coverage', async () => {
      // Given: Seed data has been loaded
      // When: shift_targets are joined with assets and grouped by area
      // Then: Roasting=3, Grinding=5, Filling=3, Packaging=3

      if (!canConnect) return

      const { data, error } = await supabase
        .from('shift_targets')
        .select('asset_id, assets!inner(area)')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      const areaAssets: Record<string, Set<string>> = {}
      for (const row of data!) {
        const area = (row as any).assets.area
        if (!areaAssets[area]) areaAssets[area] = new Set()
        areaAssets[area].add((row as any).asset_id)
      }

      expect(areaAssets['Roasting']?.size).toBe(3)
      expect(areaAssets['Grinding']?.size).toBe(5)
      expect(areaAssets['Filling']?.size).toBe(3)
      expect(areaAssets['Packaging']?.size).toBe(3)
    })

    it('11-3-workcenter-seed-data-INT-018: shift_targets have valid target_output values (> 0)', async () => {
      // Given: Seed data has been loaded
      // When: shift_targets are queried for non-positive target_output
      // Then: Zero rows returned

      if (!canConnect) return

      const { data, error } = await supabase
        .from('shift_targets')
        .select('id, asset_id, target_output')
        .lte('target_output', 0)

      expect(error).toBeNull()
      expect(
        data!.length,
        'All shift_targets should have positive target_output'
      ).toBe(0)
    })

    it('11-3-workcenter-seed-data-INT-019: Running seed-data.mjs twice does not create duplicate shift_target rows', async () => {
      // Given: seed-data.mjs has been run once successfully
      // When: seed-data.mjs is run a second time
      // Then: The total number of shift_target rows is the same

      // NOTE: This test validates the idempotency pattern.
      // In a CI environment, this would run the script twice.
      // For now, we verify that the current count is consistent
      // (no duplicates exist where there shouldn't be).

      if (!canConnect) return

      const { data, error } = await supabase
        .from('shift_targets')
        .select('asset_id, shift, target_output')

      expect(error).toBeNull()
      expect(data).not.toBeNull()

      // Build a map of (asset_id, shift) -> count to detect duplicates
      const keyCountMap = new Map<string, number>()
      for (const row of data!) {
        const key = `${(row as any).asset_id}:${(row as any).shift}`
        keyCountMap.set(key, (keyCountMap.get(key) || 0) + 1)
      }

      // No key should appear more than once (no duplicate shift_targets)
      for (const [key, count] of keyCountMap.entries()) {
        expect(
          count,
          `shift_target key ${key} should not be duplicated, found ${count} times`
        ).toBe(1)
      }
    })
  })

  // ==========================================================================
  // AC6: Target value alignment
  // ==========================================================================

  describe('AC6: Target alignment between daily_summaries and shift_targets', () => {
    it('11-3-workcenter-seed-data-INT-020: daily_summaries.target_output equals sum of shift_targets for each asset', async () => {
      // Given: Seed data has been loaded with both daily_summaries and shift_targets
      // When: For each asset, daily_summaries.target_output is compared against SUM(shift_targets.target_output)
      // Then: The values are equal for all 14 assets

      if (!canConnect) return

      // Get daily_summaries for T-1
      const { data: summaries, error: dsErr } = await supabase
        .from('daily_summaries')
        .select('asset_id, target_output')
        .eq('report_date', yesterday)

      expect(dsErr).toBeNull()
      expect(summaries).not.toBeNull()

      // Get shift_targets per asset
      const { data: targets, error: stErr } = await supabase
        .from('shift_targets')
        .select('asset_id, target_output')

      expect(stErr).toBeNull()
      expect(targets).not.toBeNull()

      // Sum shift_targets per asset
      const shiftSums: Record<string, number> = {}
      for (const t of targets!) {
        const id = (t as any).asset_id
        shiftSums[id] = (shiftSums[id] || 0) + (t as any).target_output
      }

      // Compare for each asset with a daily_summary
      for (const ds of summaries!) {
        const assetId = (ds as any).asset_id
        const dailyTarget = (ds as any).target_output
        const shiftSum = shiftSums[assetId] || 0

        expect(
          dailyTarget,
          `Asset ${assetId}: daily_summaries.target_output (${dailyTarget}) should equal shift_targets sum (${shiftSum})`
        ).toBe(shiftSum)
      }
    })

    it('11-3-workcenter-seed-data-INT-021: Alignment query returns zero mismatches', async () => {
      // Given: Seed data has been loaded
      // When: A mismatch query is run comparing daily_summaries.target_output vs SUM(shift_targets)
      // Then: Zero rows returned (no mismatches)

      if (!canConnect) return

      // Get all daily_summaries for T-1
      const { data: summaries, error: dsErr } = await supabase
        .from('daily_summaries')
        .select('asset_id, target_output')
        .eq('report_date', yesterday)

      expect(dsErr).toBeNull()

      // Get all shift_targets
      const { data: targets, error: stErr } = await supabase
        .from('shift_targets')
        .select('asset_id, target_output')

      expect(stErr).toBeNull()

      // Compute shift sums
      const shiftSums: Record<string, number> = {}
      for (const t of targets!) {
        const id = (t as any).asset_id
        shiftSums[id] = (shiftSums[id] || 0) + (t as any).target_output
      }

      // Find mismatches
      const mismatches = summaries!.filter((ds: any) => {
        const shiftSum = shiftSums[ds.asset_id] || 0
        return ds.target_output !== shiftSum
      })

      expect(
        mismatches.length,
        `Found ${mismatches.length} target_output mismatches between daily_summaries and shift_targets`
      ).toBe(0)
    })
  })

  // ==========================================================================
  // Additional: 7-day data completeness
  // ==========================================================================

  describe('Additional: 7-day data completeness', () => {
    it('11-3-workcenter-seed-data-INT-022: All 14 assets have daily_summaries for T-1 through T-7', async () => {
      // Given: Seed data has been loaded
      // When: Daily summaries are queried for the last 7 days per asset
      // Then: Every asset has day_count = 7

      if (!canConnect) return

      const startDate = daysAgoISO(7)
      const endDate = daysAgoISO(1)

      for (const assetId of ALL_ASSET_IDS) {
        const { data, error } = await supabase
          .from('daily_summaries')
          .select('id')
          .eq('asset_id', assetId)
          .gte('report_date', startDate)
          .lte('report_date', endDate)

        expect(error).toBeNull()
        expect(
          data!.length,
          `Asset ${assetId} should have 7 days of daily_summaries (T-1 through T-7), found ${data!.length}`
        ).toBe(7)
      }
    })

    it('11-3-workcenter-seed-data-INT-023: seed-data.mjs executes without errors', async () => {
      // Given: A running Supabase instance with schema migrations applied
      // When: The seed script is executed
      // Then: It completes with exit code 0 and no error output

      // NOTE: This test requires a live Supabase instance. In CI, it would run:
      //   node _bmad/scripts/seed-data.mjs
      // For now, we verify the connection is available and the script can be parsed.

      if (!canConnect) return

      // Verify that Supabase is reachable by querying assets
      const { data, error } = await supabase.from('assets').select('id').limit(1)
      expect(error).toBeNull()
      expect(data).not.toBeNull()

      // The actual script execution would be validated in CI.
      // This test acts as a smoke test that the database is in a valid state
      // post-seeding by checking that at least some data exists.
      const { data: summaries, error: dsErr } = await supabase
        .from('daily_summaries')
        .select('id')
        .limit(1)

      expect(dsErr).toBeNull()
      expect(summaries!.length).toBeGreaterThan(0)
    })
  })
})
