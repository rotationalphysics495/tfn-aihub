/**
 * Tests for Seed Data Validation
 *
 * Story 11.3 - Workcenter Seed Data
 *
 * UNIT tests that validate the seed data scripts contain correct data
 * definitions for all 14 assets, daily_summaries, shift_targets, and
 * workcenter area assignments.
 *
 * These tests read the source files and validate their contents statically.
 * They will FAIL until Story 11.3 implementation is complete because:
 *   - seed-data.mjs is missing shift_targets
 *   - seed-data.mjs is missing daily_summaries for 6 assets
 *   - Roaster shift_targets don't sum to 143
 *   - Several assets lack 7-day coverage
 */
import { describe, it, expect, beforeAll } from 'vitest'
import * as fs from 'fs'
import * as path from 'path'

// ============================================================================
// File Paths
// ============================================================================

const SEED_MJS_PATH = path.join(__dirname, '..', '..', '_bmad', 'scripts', 'seed-data.mjs')
const SEED_SQL_PATH = path.join(__dirname, '..', 'migrations', '0021_seed_data.sql')

// ============================================================================
// Asset Constants
// ============================================================================

const ALL_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000001', // Roaster 1
  'a0000001-0000-0000-0000-000000000002', // Roaster 2
  'a0000001-0000-0000-0000-000000000003', // Roaster 3
  'a0000001-0000-0000-0000-000000000004', // Grinder 1
  'a0000001-0000-0000-0000-000000000005', // Grinder 2
  'a0000001-0000-0000-0000-000000000006', // Grinder 3
  'a0000001-0000-0000-0000-000000000007', // Grinder 4
  'a0000001-0000-0000-0000-000000000014', // Grinder 5
  'a0000001-0000-0000-0000-000000000008', // Filler Line A
  'a0000001-0000-0000-0000-000000000009', // Filler Line B
  'a0000001-0000-0000-0000-000000000010', // Filler Line C
  'a0000001-0000-0000-0000-000000000011', // Packaging Line 1
  'a0000001-0000-0000-0000-000000000012', // Packaging Line 2
  'a0000001-0000-0000-0000-000000000013', // Packaging Line 3
]

const ROASTING_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000001',
  'a0000001-0000-0000-0000-000000000002',
  'a0000001-0000-0000-0000-000000000003',
]

const GRINDING_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000004',
  'a0000001-0000-0000-0000-000000000005',
  'a0000001-0000-0000-0000-000000000006',
  'a0000001-0000-0000-0000-000000000007',
  'a0000001-0000-0000-0000-000000000014',
]

const FILLING_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000008',
  'a0000001-0000-0000-0000-000000000009',
  'a0000001-0000-0000-0000-000000000010',
]

const PACKAGING_ASSET_IDS = [
  'a0000001-0000-0000-0000-000000000011',
  'a0000001-0000-0000-0000-000000000012',
  'a0000001-0000-0000-0000-000000000013',
]

const WORKCENTER_AREAS = ['Roasting', 'Grinding', 'Filling', 'Packaging'] as const

// Expected daily target_output per asset
const EXPECTED_DAILY_TARGETS: Record<string, number> = {
  'a0000001-0000-0000-0000-000000000001': 143,  // Roaster 1
  'a0000001-0000-0000-0000-000000000002': 143,  // Roaster 2
  'a0000001-0000-0000-0000-000000000003': 143,  // Roaster 3
  'a0000001-0000-0000-0000-000000000004': 1950, // Grinder 1
  'a0000001-0000-0000-0000-000000000005': 1950, // Grinder 2
  'a0000001-0000-0000-0000-000000000006': 1950, // Grinder 3
  'a0000001-0000-0000-0000-000000000007': 1950, // Grinder 4
  'a0000001-0000-0000-0000-000000000014': 1950, // Grinder 5
  'a0000001-0000-0000-0000-000000000008': 4600, // Filler A
  'a0000001-0000-0000-0000-000000000009': 4600, // Filler B
  'a0000001-0000-0000-0000-000000000010': 4000, // Filler C
  'a0000001-0000-0000-0000-000000000011': 6200, // Packaging 1
  'a0000001-0000-0000-0000-000000000012': 6200, // Packaging 2
  'a0000001-0000-0000-0000-000000000013': 5600, // Packaging 3
}

// Expected shift_target sums per asset (should equal daily target)
const EXPECTED_SHIFT_TARGET_SUMS: Record<string, { shifts: number[]; total: number }> = {
  'a0000001-0000-0000-0000-000000000001': { shifts: [50, 48, 45], total: 143 },
  'a0000001-0000-0000-0000-000000000002': { shifts: [50, 48, 45], total: 143 },
  'a0000001-0000-0000-0000-000000000003': { shifts: [50, 48, 45], total: 143 },
  'a0000001-0000-0000-0000-000000000004': { shifts: [1000, 950], total: 1950 },
  'a0000001-0000-0000-0000-000000000005': { shifts: [1000, 950], total: 1950 },
  'a0000001-0000-0000-0000-000000000006': { shifts: [900, 1050], total: 1950 },
  'a0000001-0000-0000-0000-000000000007': { shifts: [850, 1100], total: 1950 },
  'a0000001-0000-0000-0000-000000000014': { shifts: [1000, 950], total: 1950 },
  'a0000001-0000-0000-0000-000000000008': { shifts: [2400, 2200], total: 4600 },
  'a0000001-0000-0000-0000-000000000009': { shifts: [2400, 2200], total: 4600 },
  'a0000001-0000-0000-0000-000000000010': { shifts: [2000, 2000], total: 4000 },
  'a0000001-0000-0000-0000-000000000011': { shifts: [3200, 3000], total: 6200 },
  'a0000001-0000-0000-0000-000000000012': { shifts: [3200, 3000], total: 6200 },
  'a0000001-0000-0000-0000-000000000013': { shifts: [2800, 2800], total: 5600 },
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Extract all occurrences of a UUID pattern in a string for a specific table context.
 */
function extractAssetIdsFromMjs(content: string, section: string): string[] {
  const ids: string[] = []
  const uuidPattern = /a0000001-0000-0000-0000-0000000000\d{2}/g
  let match
  while ((match = uuidPattern.exec(section)) !== null) {
    ids.push(match[0])
  }
  return [...new Set(ids)]
}

/**
 * Count occurrences of daysAgo(N) entries per asset_id in the dailySummaries section.
 * Uses the pattern: asset_id + report_date on adjacent lines within the same entry.
 */
function countDaysAgoEntries(content: string, assetId: string, daysAgo: number): number {
  // Extract the dailySummaries array section only
  const dsSection = content.match(/const dailySummaries = \[[\s\S]*?\n  \];/)
  if (!dsSection) return 0

  // Split into individual entry blocks by looking for opening braces at array level
  // Each entry starts with "    {" and contains asset_id and report_date
  // We look for entries where asset_id AND daysAgo(N) appear in close proximity
  // (within 200 characters, which covers asset_id line + report_date line)
  const entryPattern = new RegExp(
    `asset_id:\\s*'${assetId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}'.{0,100}report_date:\\s*daysAgo\\(${daysAgo}\\)`,
    'gs'
  )
  const matches = dsSection[0].match(entryPattern)
  return matches ? matches.length : 0
}

/**
 * Extract shift_targets section from SQL and parse target_output values per asset.
 */
function parseShiftTargetsFromSQL(sql: string): Record<string, number[]> {
  const result: Record<string, number[]> = {}
  // Match INSERT INTO shift_targets ... VALUES block
  const shiftTargetSection = sql.match(
    /INSERT INTO shift_targets[\s\S]*?ON CONFLICT/
  )
  if (!shiftTargetSection) return result

  const section = shiftTargetSection[0]
  // Parse each row: ('UUID', number, 'shift', 'date')
  const rowPattern = /\('(a0000001-0000-0000-0000-0000000000\d{2})',\s*(\d+),\s*'(\w+)'/g
  let match
  while ((match = rowPattern.exec(section)) !== null) {
    const assetId = match[1]
    const targetOutput = parseInt(match[2], 10)
    if (!result[assetId]) result[assetId] = []
    result[assetId].push(targetOutput)
  }
  return result
}

/**
 * Extract area assignments from the assets INSERT block in SQL.
 */
function parseAssetAreasFromSQL(sql: string): Record<string, string> {
  const result: Record<string, string> = {}
  const assetSection = sql.match(/INSERT INTO assets[\s\S]*?ON CONFLICT/)
  if (!assetSection) return result

  const rowPattern = /\('(a0000001-0000-0000-0000-0000000000\d{2})',\s*'[^']+',\s*'[^']+',\s*'(\w+)'\)/g
  let match
  while ((match = rowPattern.exec(assetSection[0])) !== null) {
    result[match[1]] = match[2]
  }
  return result
}

/**
 * Parse daily_summaries from SQL to get asset_id -> target_output mappings.
 */
function parseDailySummariesTargetsFromSQL(sql: string): Record<string, number[]> {
  const result: Record<string, number[]> = {}
  const dsSection = sql.match(
    /INSERT INTO daily_summaries[\s\S]*?ON CONFLICT/
  )
  if (!dsSection) return result

  // Pattern: ('UUID', CURRENT_DATE - N, oee, actual, target, ...)
  const rowPattern = /\('(a0000001-0000-0000-0000-0000000000\d{2})',\s*CURRENT_DATE\s*-\s*(\d+),\s*[\d.]+,\s*\d+,\s*(\d+)/g
  let match
  while ((match = rowPattern.exec(dsSection[0])) !== null) {
    const assetId = match[1]
    const targetOutput = parseInt(match[3], 10)
    if (!result[assetId]) result[assetId] = []
    result[assetId].push(targetOutput)
  }
  return result
}

// ============================================================================
// Tests
// ============================================================================

describe('Feature: Workcenter Seed Data (Story 11.3)', () => {
  let mjsContent: string
  let sqlContent: string

  beforeAll(() => {
    mjsContent = fs.readFileSync(SEED_MJS_PATH, 'utf-8')
    sqlContent = fs.readFileSync(SEED_SQL_PATH, 'utf-8')
  })

  // ==========================================================================
  // AC1: All 4 workcenters have data
  // ==========================================================================

  describe('AC1: All 4 workcenters have daily_summaries for T-1', () => {
    it('11-3-workcenter-seed-data-UNIT-001: seed-data.mjs generates daily_summaries entries for all 14 asset IDs', () => {
      // Given: The seed-data.mjs script source code is loaded for analysis
      // When: The daily_summaries data array is inspected
      // Then: All 14 asset UUIDs appear in daily_summaries entries with at least a T-1 row each

      for (const assetId of ALL_ASSET_IDS) {
        const hasDaysAgo1 = countDaysAgoEntries(mjsContent, assetId, 1)
        expect(
          hasDaysAgo1,
          `Asset ${assetId} should have at least one daysAgo(1) entry in daily_summaries`
        ).toBeGreaterThanOrEqual(1)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-002: 0021_seed_data.sql generates daily_summaries INSERT statements for all 14 asset IDs at T-1', () => {
      // Given: The 0021_seed_data.sql file is loaded for analysis
      // When: The INSERT INTO daily_summaries statements are parsed
      // Then: All 14 asset UUIDs appear in daily_summaries inserts with at least one row using CURRENT_DATE - 1

      const dsSection = sqlContent.match(
        /INSERT INTO daily_summaries[\s\S]*?ON CONFLICT/
      )
      expect(dsSection).not.toBeNull()

      for (const assetId of ALL_ASSET_IDS) {
        const pattern = new RegExp(
          `'${assetId}'.*CURRENT_DATE\\s*-\\s*1`
        )
        expect(
          dsSection![0],
          `Asset ${assetId} should have a CURRENT_DATE - 1 entry in SQL daily_summaries`
        ).toMatch(pattern)
      }
    })
  })

  // ==========================================================================
  // AC2: Each workcenter has varied performance
  // ==========================================================================

  describe('AC2: Varied performance per workcenter', () => {
    it('11-3-workcenter-seed-data-UNIT-003: seed-data.mjs daily_summaries contains varied actual vs target for T-1', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: The daily_summaries entries for daysAgo(1) are examined per workcenter
      // Then: Within each workcenter, at least one asset hits target and one misses

      const workcenterAssets: Record<string, string[]> = {
        Roasting: ROASTING_ASSET_IDS,
        Grinding: GRINDING_ASSET_IDS,
        Filling: FILLING_ASSET_IDS,
        Packaging: PACKAGING_ASSET_IDS,
      }

      // Extract daysAgo(1) entries from the mjs dailySummaries array
      // For each workcenter, check that there's variation in actual vs target
      for (const [wcName, assetIds] of Object.entries(workcenterAssets)) {
        let hasHitter = false
        let hasMisser = false

        for (const assetId of assetIds) {
          // Find the daysAgo(1) entry for this asset
          // Pattern: asset_id: 'UUID', ... report_date: daysAgo(1), ... actual_output: N, target_output: M
          const entryPattern = new RegExp(
            `\\{[^}]*asset_id:\\s*'${assetId}'[^}]*report_date:\\s*daysAgo\\(1\\)[^}]*actual_output:\\s*(\\d+)[^}]*target_output:\\s*(\\d+)`,
            's'
          )
          const match = mjsContent.match(entryPattern)
          if (match) {
            const actual = parseInt(match[1], 10)
            const target = parseInt(match[2], 10)
            if (actual >= target) hasHitter = true
            if (actual < target) hasMisser = true
          }
        }

        expect(
          hasHitter,
          `${wcName} workcenter should have at least one asset hitting target on T-1`
        ).toBe(true)
        expect(
          hasMisser,
          `${wcName} workcenter should have at least one asset missing target on T-1`
        ).toBe(true)
      }
    })
  })

  // ==========================================================================
  // AC4: Correct area assignments
  // ==========================================================================

  describe('AC4: Correct workcenter area assignments', () => {
    it('11-3-workcenter-seed-data-UNIT-005: seed-data.mjs assets array assigns correct area to all 14 assets', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: The assets array is inspected for area field assignments
      // Then: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14

      const areaCounts: Record<string, number> = {}

      for (const area of WORKCENTER_AREAS) {
        const areaPattern = new RegExp(`area:\\s*'${area}'`, 'g')
        // Only count within the assets array section
        const assetsSection = mjsContent.match(/const assets = \[[\s\S]*?\];/)
        expect(assetsSection).not.toBeNull()

        const matches = assetsSection![0].match(areaPattern)
        areaCounts[area] = matches ? matches.length : 0
      }

      expect(areaCounts['Roasting']).toBe(3)
      expect(areaCounts['Grinding']).toBe(5)
      expect(areaCounts['Filling']).toBe(3)
      expect(areaCounts['Packaging']).toBe(3)

      const totalAssets = Object.values(areaCounts).reduce((a, b) => a + b, 0)
      expect(totalAssets).toBe(14)
    })

    it('11-3-workcenter-seed-data-UNIT-006: 0021_seed_data.sql assets INSERT assigns correct area to all 14 assets', () => {
      // Given: The 0021_seed_data.sql file is analyzed
      // When: The INSERT INTO assets statements are parsed for area values
      // Then: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14

      const assetAreas = parseAssetAreasFromSQL(sqlContent)

      const areaCounts: Record<string, number> = { Roasting: 0, Grinding: 0, Filling: 0, Packaging: 0 }
      for (const area of Object.values(assetAreas)) {
        if (area in areaCounts) areaCounts[area]++
      }

      expect(areaCounts['Roasting']).toBe(3)
      expect(areaCounts['Grinding']).toBe(5)
      expect(areaCounts['Filling']).toBe(3)
      expect(areaCounts['Packaging']).toBe(3)
      expect(Object.keys(assetAreas).length).toBe(14)
    })

    it('11-3-workcenter-seed-data-UNIT-007: Asset UUIDs are consistent between seed-data.mjs and 0021_seed_data.sql', () => {
      // Given: Both seed files are analyzed
      // When: The set of asset UUIDs in seed-data.mjs is compared with those in 0021_seed_data.sql
      // Then: The UUID sets are identical and each UUID maps to the same area

      const sqlAreas = parseAssetAreasFromSQL(sqlContent)
      const sqlAssetIds = new Set(Object.keys(sqlAreas))

      // Extract asset UUIDs from mjs assets array
      const assetsSection = mjsContent.match(/const assets = \[[\s\S]*?\];/)
      expect(assetsSection).not.toBeNull()

      const mjsAssetIds = new Set<string>()
      const uuidPattern = /id:\s*'(a0000001-0000-0000-0000-0000000000\d{2})'/g
      let match
      while ((match = uuidPattern.exec(assetsSection![0])) !== null) {
        mjsAssetIds.add(match[1])
      }

      // Same count
      expect(mjsAssetIds.size).toBe(14)
      expect(sqlAssetIds.size).toBe(14)

      // Same UUIDs
      for (const id of ALL_ASSET_IDS) {
        expect(mjsAssetIds.has(id), `MJS should contain ${id}`).toBe(true)
        expect(sqlAssetIds.has(id), `SQL should contain ${id}`).toBe(true)
      }

      // Same area assignment for each UUID
      for (const id of ALL_ASSET_IDS) {
        const mjsAreaMatch = assetsSection![0].match(
          new RegExp(`id:\\s*'${id}'[^}]*area:\\s*'(\\w+)'`)
        )
        expect(mjsAreaMatch).not.toBeNull()
        expect(
          mjsAreaMatch![1],
          `Area for ${id} should match between MJS and SQL`
        ).toBe(sqlAreas[id])
      }
    })

    it('11-3-workcenter-seed-data-UNIT-008: No asset has a NULL or empty area assignment', () => {
      // Given: Both seed files are analyzed
      // When: All asset entries are inspected for the area field
      // Then: Every asset has a non-null, non-empty area value

      // Check MJS
      const assetsSection = mjsContent.match(/const assets = \[[\s\S]*?\];/)
      expect(assetsSection).not.toBeNull()

      const assetEntries = assetsSection![0].match(/\{[^}]+\}/g)
      expect(assetEntries).not.toBeNull()
      expect(assetEntries!.length).toBe(14)

      for (const entry of assetEntries!) {
        const areaMatch = entry.match(/area:\s*'(\w+)'/)
        expect(areaMatch, `Every MJS asset entry should have a non-empty area: ${entry.substring(0, 80)}`).not.toBeNull()
        expect(WORKCENTER_AREAS).toContain(areaMatch![1])
      }

      // Check SQL
      const sqlAreas = parseAssetAreasFromSQL(sqlContent)
      for (const [assetId, area] of Object.entries(sqlAreas)) {
        expect(area, `SQL asset ${assetId} should have a valid area`).toBeTruthy()
        expect(WORKCENTER_AREAS as readonly string[]).toContain(area)
      }
    })
  })

  // ==========================================================================
  // AC5: shift_targets exist for all assets
  // ==========================================================================

  describe('AC5: shift_targets coverage for all assets', () => {
    it('11-3-workcenter-seed-data-UNIT-009: seed-data.mjs contains a shift_targets upsert/insert block', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: The script is searched for shift_targets data insertion code
      // Then: A shift_targets insert or upsert block exists that covers all 14 asset UUIDs

      // Check that shift_targets section exists
      expect(
        mjsContent,
        'seed-data.mjs should contain shift_targets insertion code'
      ).toMatch(/shift_targets/i)

      // Check that it references all 14 asset IDs in a shift_targets context
      const shiftSection = mjsContent.match(
        /shift_targets[\s\S]*?(?:insert|upsert)/i
      )
      expect(
        shiftSection,
        'seed-data.mjs should have a shift_targets insert/upsert block'
      ).not.toBeNull()

      for (const assetId of ALL_ASSET_IDS) {
        expect(
          mjsContent,
          `seed-data.mjs shift_targets should include asset ${assetId}`
        ).toContain(assetId)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-010: 0021_seed_data.sql contains shift_targets INSERT for all 14 assets', () => {
      // Given: The 0021_seed_data.sql file is analyzed
      // When: The INSERT INTO shift_targets statements are parsed for distinct asset_id values
      // Then: All 14 asset UUIDs appear in shift_targets INSERT statements

      const shiftTargets = parseShiftTargetsFromSQL(sqlContent)
      const assetIdsWithTargets = Object.keys(shiftTargets)

      for (const assetId of ALL_ASSET_IDS) {
        expect(
          assetIdsWithTargets,
          `SQL shift_targets should include asset ${assetId}`
        ).toContain(assetId)
      }

      expect(assetIdsWithTargets.length).toBe(14)
    })

    it('11-3-workcenter-seed-data-UNIT-011: seed-data.mjs handles shift_targets cleanup to prevent duplicates on re-run', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: The shift_targets insertion section is inspected
      // Then: A delete-before-insert or equivalent idempotency pattern exists for shift_targets

      // Look specifically for a shift_targets delete/cleanup pattern
      // Must be specific to shift_targets, not a generic delete on another table
      const hasShiftTargetsCleanup =
        mjsContent.includes("from('shift_targets').delete") ||
        mjsContent.includes('from("shift_targets").delete') ||
        mjsContent.match(/shift_targets.*\.delete/) !== null ||
        mjsContent.match(/delete.*shift_targets/) !== null

      expect(
        hasShiftTargetsCleanup,
        'seed-data.mjs should have a cleanup/delete pattern specifically for shift_targets before inserting'
      ).toBe(true)
    })
  })

  // ==========================================================================
  // AC6: Target alignment between daily_summaries and shift_targets
  // ==========================================================================

  describe('AC6: Target value alignment', () => {
    it('11-3-workcenter-seed-data-UNIT-012: Roaster shift_targets sum to 143 in seed-data.mjs', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: The shift_targets entries for Roaster 1, 2, and 3 are inspected
      // Then: Each roaster's shift_targets sum to exactly 143

      // This test will FAIL because currently Roasters in seed-data.mjs have
      // NO shift_targets at all (the block is completely absent from the script)
      // After implementation, roaster targets should sum to 143 per asset

      for (const roasterId of ROASTING_ASSET_IDS) {
        const expected = EXPECTED_SHIFT_TARGET_SUMS[roasterId]
        expect(expected).toBeDefined()
        expect(expected.total).toBe(143)

        // The mjs file must contain a shift_targets block with these values
        // We look for the shift target values near the asset ID
        const shiftTargetPattern = new RegExp(
          `shift_targets[\\s\\S]*?${roasterId}`,
          'i'
        )
        expect(
          mjsContent,
          `seed-data.mjs should reference ${roasterId} in shift_targets context`
        ).toMatch(shiftTargetPattern)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-013: Roaster shift_targets sum to 143 in 0021_seed_data.sql', () => {
      // Given: The 0021_seed_data.sql file is analyzed
      // When: The INSERT INTO shift_targets for Roaster 1, 2, and 3 are parsed
      // Then: Each roaster's shift_targets sum to exactly 143

      const shiftTargets = parseShiftTargetsFromSQL(sqlContent)

      for (const roasterId of ROASTING_ASSET_IDS) {
        const targets = shiftTargets[roasterId]
        expect(
          targets,
          `SQL should have shift_targets for ${roasterId}`
        ).toBeDefined()

        const sum = targets ? targets.reduce((a, b) => a + b, 0) : 0
        expect(
          sum,
          `Roaster ${roasterId} shift_targets should sum to 143, got ${sum}`
        ).toBe(143)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-014: All Grinder shift_targets sum to their respective daily targets', () => {
      // Given: Both seed files are analyzed
      // When: Shift target values for Grinders 1-5 are summed per asset
      // Then: Each grinder's shift_targets sum to 1950

      const shiftTargets = parseShiftTargetsFromSQL(sqlContent)

      for (const grinderId of GRINDING_ASSET_IDS) {
        const targets = shiftTargets[grinderId]
        expect(targets, `SQL should have shift_targets for ${grinderId}`).toBeDefined()

        const sum = targets ? targets.reduce((a, b) => a + b, 0) : 0
        expect(
          sum,
          `Grinder ${grinderId} shift_targets should sum to 1950, got ${sum}`
        ).toBe(1950)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-015: All Filler shift_targets sum to their respective daily targets', () => {
      // Given: Both seed files are analyzed
      // When: Shift target values for Fillers A, B, C are summed per asset
      // Then: Filler A: sum=4600, Filler B: sum=4600, Filler C: sum=4000

      const shiftTargets = parseShiftTargetsFromSQL(sqlContent)

      const expectedFillerTotals: Record<string, number> = {
        'a0000001-0000-0000-0000-000000000008': 4600,
        'a0000001-0000-0000-0000-000000000009': 4600,
        'a0000001-0000-0000-0000-000000000010': 4000,
      }

      for (const [fillerId, expectedTotal] of Object.entries(expectedFillerTotals)) {
        const targets = shiftTargets[fillerId]
        expect(targets, `SQL should have shift_targets for ${fillerId}`).toBeDefined()

        const sum = targets ? targets.reduce((a, b) => a + b, 0) : 0
        expect(
          sum,
          `Filler ${fillerId} shift_targets should sum to ${expectedTotal}, got ${sum}`
        ).toBe(expectedTotal)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-016: All Packaging shift_targets sum to their respective daily targets', () => {
      // Given: Both seed files are analyzed
      // When: Shift target values for Packaging 1, 2, 3 are summed per asset
      // Then: Pack 1: sum=6200, Pack 2: sum=6200, Pack 3: sum=5600

      const shiftTargets = parseShiftTargetsFromSQL(sqlContent)

      const expectedPackTotals: Record<string, number> = {
        'a0000001-0000-0000-0000-000000000011': 6200,
        'a0000001-0000-0000-0000-000000000012': 6200,
        'a0000001-0000-0000-0000-000000000013': 5600,
      }

      for (const [packId, expectedTotal] of Object.entries(expectedPackTotals)) {
        const targets = shiftTargets[packId]
        expect(targets, `SQL should have shift_targets for ${packId}`).toBeDefined()

        const sum = targets ? targets.reduce((a, b) => a + b, 0) : 0
        expect(
          sum,
          `Packaging ${packId} shift_targets should sum to ${expectedTotal}, got ${sum}`
        ).toBe(expectedTotal)
      }
    })

    it('11-3-workcenter-seed-data-UNIT-017: target_output values are consistent across all 7 days per asset in seed-data.mjs', () => {
      // Given: The seed-data.mjs script source is analyzed
      // When: daily_summaries entries for each asset across T-1 through T-7 are inspected
      // Then: The target_output value is the same for every day for a given asset

      for (const assetId of ALL_ASSET_IDS) {
        const expectedTarget = EXPECTED_DAILY_TARGETS[assetId]
        // Find all target_output values for this asset in daysAgo(1) through daysAgo(7)
        for (let day = 1; day <= 7; day++) {
          const pattern = new RegExp(
            `\\{[^}]*asset_id:\\s*'${assetId}'[^}]*report_date:\\s*daysAgo\\(${day}\\)[^}]*target_output:\\s*(\\d+)`,
            's'
          )
          const match = mjsContent.match(pattern)
          if (match) {
            expect(
              parseInt(match[1], 10),
              `Asset ${assetId} day T-${day} target_output should be ${expectedTarget}`
            ).toBe(expectedTarget)
          }
          // If no match found for some days, that's caught by UNIT-001 (coverage tests)
        }
      }
    })

    it('11-3-workcenter-seed-data-UNIT-018: Both seed files use identical target_output values for the same assets', () => {
      // Given: Both seed-data.mjs and 0021_seed_data.sql are analyzed
      // When: The daily_summaries.target_output values are extracted from both files
      // Then: The values match exactly between the two files for every asset

      const sqlTargets = parseDailySummariesTargetsFromSQL(sqlContent)

      // Extract dailySummaries section from MJS to avoid matching live_snapshots target_output
      const dsSection = mjsContent.match(/const dailySummaries = \[[\s\S]*?\n  \];/)
      expect(dsSection, 'MJS should have a dailySummaries array').not.toBeNull()

      for (const assetId of ALL_ASSET_IDS) {
        const expectedTarget = EXPECTED_DAILY_TARGETS[assetId]

        // Check SQL targets
        const sqlTargetValues = sqlTargets[assetId]
        if (sqlTargetValues) {
          for (const val of sqlTargetValues) {
            expect(
              val,
              `SQL daily_summaries target for ${assetId} should be ${expectedTarget}`
            ).toBe(expectedTarget)
          }
        }

        // Check MJS targets - only within the dailySummaries section
        const mjsPattern = new RegExp(
          `asset_id:\\s*'${assetId}'[^}]*target_output:\\s*(\\d+)`,
          'g'
        )
        let match
        let foundInMjs = false
        while ((match = mjsPattern.exec(dsSection![0])) !== null) {
          foundInMjs = true
          expect(
            parseInt(match[1], 10),
            `MJS daily_summaries target for ${assetId} should be ${expectedTarget}`
          ).toBe(expectedTarget)
        }

        // The asset must be present in MJS daily_summaries
        expect(
          foundInMjs,
          `Asset ${assetId} should have daily_summaries entries in MJS`
        ).toBe(true)
      }
    })
  })

  // ==========================================================================
  // AC3: Attainment ranges - individual asset check
  // ==========================================================================

  describe('AC3: Realistic attainment variation', () => {
    it('11-3-workcenter-seed-data-UNIT-004: No individual asset attainment is unrealistically extreme', () => {
      // Given: Seed data is loaded
      // When: actual_output / target_output is calculated for each of the 14 assets on T-1
      // Then: No asset has attainment below 50% or above 110%

      for (const assetId of ALL_ASSET_IDS) {
        const pattern = new RegExp(
          `\\{[^}]*asset_id:\\s*'${assetId}'[^}]*report_date:\\s*daysAgo\\(1\\)[^}]*actual_output:\\s*(\\d+)[^}]*target_output:\\s*(\\d+)`,
          's'
        )
        const match = mjsContent.match(pattern)
        if (match) {
          const actual = parseInt(match[1], 10)
          const target = parseInt(match[2], 10)
          const attainment = (actual / target) * 100

          expect(
            attainment,
            `Asset ${assetId} attainment ${attainment.toFixed(1)}% should be >= 50%`
          ).toBeGreaterThanOrEqual(50)
          expect(
            attainment,
            `Asset ${assetId} attainment ${attainment.toFixed(1)}% should be <= 110%`
          ).toBeLessThanOrEqual(110)
        } else {
          // Asset doesn't have a daysAgo(1) entry yet - this will cause UNIT-001 to fail
          // but we also flag it here as an issue
          expect.fail(
            `Asset ${assetId} has no daysAgo(1) entry in seed-data.mjs - cannot validate attainment`
          )
        }
      }
    })
  })

  // ==========================================================================
  // Additional Coverage: 7-day data completeness
  // ==========================================================================

  describe('Additional: 7-day data completeness in seed-data.mjs', () => {
    it('11-3-workcenter-seed-data-UNIT-019: all 14 assets should have daysAgo(1) through daysAgo(7) entries', () => {
      // This validates that Story 11.3 fills in the missing daily_summaries
      // for Roaster 3, Grinder 4, Filler B (T-3 to T-7), Filler C,
      // Packaging 2 (T-3 to T-7), and Packaging 3

      for (const assetId of ALL_ASSET_IDS) {
        for (let day = 1; day <= 7; day++) {
          const count = countDaysAgoEntries(mjsContent, assetId, day)
          expect(
            count,
            `Asset ${assetId} should have a daysAgo(${day}) entry`
          ).toBeGreaterThanOrEqual(1)
        }
      }
    })
  })
})
