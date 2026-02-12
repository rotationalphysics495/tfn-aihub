/**
 * Transformer Trend Data Tests (Story 14.4: Trend Indicators on Action Cards)
 *
 * TDD tests — these MUST FAIL until transformAPIActionItem is updated to handle trend_data.
 * Tests cover snake_case to camelCase mapping, null handling, and field preservation.
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #6 - TypeScript types and transformer mapping for trend_data
 */

import { describe, it, expect } from 'vitest'

// ---------------------------------------------------------------------------
// Imports
// ---------------------------------------------------------------------------

import { transformAPIActionItem } from '../transformers'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/**
 * Creates a mock API action item (snake_case format matching backend response).
 * Mimics the shape from useDailyActions.ts ActionItem interface.
 */
const createMockAPIActionItem = (overrides: Record<string, unknown> = {}) => ({
  id: 'action-api-1',
  asset_id: 'asset-001',
  asset_name: 'Grinder 5',
  priority_level: 'high' as const,
  category: 'oee' as const,
  primary_metric_value: 'OEE: 72.5%',
  recommendation_text: 'Investigate downtime on Grinder 5',
  evidence_summary: 'OEE dropped below threshold',
  evidence_refs: [
    {
      table: 'daily_summaries',
      column: 'oee',
      value: '72.5',
      record_id: 'rec-001',
      source_table: 'daily_summaries',
    },
  ],
  created_at: '2026-02-11T08:00:00Z',
  financial_impact_usd: 2000,
  priority_rank: 2,
  title: 'Grinder 5 OEE Below Threshold',
  description: 'OEE fell to 72.5%, below the 85% target',
  acknowledgment: null,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Trend Data Transformer (Story 14.4)', () => {
  // =========================================================================
  // AC6: Transformer mapping for trend_data
  // =========================================================================
  describe('AC6: Transformer Maps API trend_data to Component trendData', () => {
    it('UNIT-039: Transformer maps API trend_data snake_case to component trendData camelCase', () => {
      // Given: An API response ActionItem has trend_data with snake_case fields
      const apiItem = createMockAPIActionItem({
        trend_data: {
          metric_values: [72.5, 74.1, 68.3],
          days_on_report: 4,
          consecutive_days: 3,
          week_over_week_change: -3.1,
        },
      })

      // When: transformAPIActionItem() processes the item
      const result = transformAPIActionItem(apiItem as never)

      // Then: The result has trendData with camelCase fields
      expect(result.trendData).toBeDefined()
      expect(result.trendData!.metricHistory).toEqual([72.5, 74.1, 68.3])
      expect(result.trendData!.daysOnReport).toBe(4)
      expect(result.trendData!.consecutiveDays).toBe(3)
      expect(result.trendData!.weekOverWeekChange).toBe(-3.1)
    })

    it('UNIT-040: Transformer handles null trend_data from API', () => {
      // Given: An API response ActionItem has trend_data = null
      const apiItem = createMockAPIActionItem({
        trend_data: null,
      })

      // When: transformAPIActionItem() processes the item
      const result = transformAPIActionItem(apiItem as never)

      // Then: The result has trendData = undefined (not null)
      expect(result.trendData).toBeUndefined()
    })

    it('UNIT-041: Transformer handles absent trend_data from API', () => {
      // Given: An API response ActionItem has no trend_data field at all
      const apiItem = createMockAPIActionItem()
      // Ensure no trend_data key exists
      delete (apiItem as Record<string, unknown>).trend_data

      // When: transformAPIActionItem() processes the item
      const result = transformAPIActionItem(apiItem as never)

      // Then: The result has trendData = undefined
      expect(result.trendData).toBeUndefined()
    })

    it('UNIT-042: Transformer preserves null values in metric_values array', () => {
      // Given: An API response has trend_data.metric_values with null entries
      const apiItem = createMockAPIActionItem({
        trend_data: {
          metric_values: [72.5, null, 68.3, null, 69.2, 73.8, 72.5],
          days_on_report: 5,
          consecutive_days: 2,
          week_over_week_change: -1.5,
        },
      })

      // When: transformAPIActionItem() processes the item
      const result = transformAPIActionItem(apiItem as never)

      // Then: The result trendData.metricHistory preserves null values
      expect(result.trendData).toBeDefined()
      expect(result.trendData!.metricHistory).toEqual([72.5, null, 68.3, null, 69.2, 73.8, 72.5])
      expect(result.trendData!.metricHistory[1]).toBeNull()
      expect(result.trendData!.metricHistory[3]).toBeNull()
    })

    it('UNIT-043: Transformer handles null week_over_week_change', () => {
      // Given: An API response has trend_data with week_over_week_change = null
      const apiItem = createMockAPIActionItem({
        trend_data: {
          metric_values: [72.5],
          days_on_report: 1,
          consecutive_days: 1,
          week_over_week_change: null,
        },
      })

      // When: transformAPIActionItem() processes the item
      const result = transformAPIActionItem(apiItem as never)

      // Then: The result trendData.weekOverWeekChange = null
      expect(result.trendData).toBeDefined()
      expect(result.trendData!.weekOverWeekChange).toBeNull()
    })
  })

  // =========================================================================
  // Error Scenarios
  // =========================================================================
  describe('Error Scenarios: Malformed trend_data', () => {
    it('ERROR-001: Transformer handles malformed trend_data without crashing', () => {
      // Given: API returns trend_data where metric_values is not an array
      const apiItem = createMockAPIActionItem({
        trend_data: {
          metric_values: 'not-an-array',
          days_on_report: 4,
          consecutive_days: 3,
          week_over_week_change: -3.1,
        },
      })

      // When: transformAPIActionItem() processes the item
      // Then: It should not throw (graceful handling)
      expect(() => {
        transformAPIActionItem(apiItem as never)
      }).not.toThrow()
    })

    it('ERROR-002: Transformer handles trend_data with unexpected field names', () => {
      // Given: API returns trend_data with unexpected field names
      const apiItem = createMockAPIActionItem({
        trend_data: {
          unknown_field: 'value',
          days_on_report: 2,
        },
      })

      // When: transformAPIActionItem() processes the item
      // Then: It should not throw and missing fields become undefined
      expect(() => {
        transformAPIActionItem(apiItem as never)
      }).not.toThrow()
    })
  })
})
