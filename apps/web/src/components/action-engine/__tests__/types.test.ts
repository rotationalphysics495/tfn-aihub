/**
 * Type Verification Tests (Story 14.4: Trend Indicators on Action Cards)
 *
 * TDD tests — these MUST FAIL until TrendData type and ActionItem.trendData field are implemented.
 * Tests verify TypeScript types at compile time and runtime shape compliance.
 *
 * Since TypeScript type imports are erased at runtime, these tests verify
 * the types exist by checking runtime behavior that depends on the type additions:
 * - ActionItem objects with trendData should be accepted by transformAPIActionItem
 * - The barrel export should expose TrendData-related type documentation
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 * @see AC #6 - TypeScript types and transformer mapping for trend_data
 */

import { describe, it, expect } from 'vitest'

// ---------------------------------------------------------------------------
// Imports
// ---------------------------------------------------------------------------

import { transformAPIActionItem } from '../transformers'
import type { ActionItem } from '../types'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Trend Data Types (Story 14.4)', () => {
  // =========================================================================
  // AC6: TypeScript types for trend_data
  // =========================================================================
  describe('AC6: TrendData Type Definitions', () => {
    it('UNIT-037: TrendData interface has correct fields and transformer maps them', () => {
      // Given: The TrendData interface is defined in types.ts
      // When: An API action item with trend_data is transformed
      const apiItem = {
        id: 'action-api-1',
        asset_id: 'asset-001',
        asset_name: 'Grinder 5',
        priority_level: 'high' as const,
        category: 'oee' as const,
        primary_metric_value: 'OEE: 72.5%',
        recommendation_text: 'Investigate downtime',
        evidence_summary: 'OEE dropped below threshold',
        evidence_refs: [{ table: 'daily_summaries', column: 'oee', value: '72.5', record_id: 'rec-001', source_table: 'daily_summaries' }],
        created_at: '2026-02-11T08:00:00Z',
        financial_impact_usd: 2000,
        priority_rank: 2,
        title: 'OEE Below Threshold',
        description: 'OEE fell to 72.5%',
        acknowledgment: null,
        trend_data: {
          metric_values: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
          days_on_report: 4,
          consecutive_days: 3,
          week_over_week_change: -3.1,
        },
      }

      const result = transformAPIActionItem(apiItem as never)

      // Then: The transformed result has a trendData field with correct shape
      // This WILL FAIL because transformAPIActionItem doesn't yet map trend_data
      expect(result).toHaveProperty('trendData')
      expect(result.trendData).toBeDefined()
      expect(result.trendData).toEqual({
        metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
        daysOnReport: 4,
        consecutiveDays: 3,
        weekOverWeekChange: -3.1,
      })

      // And: metricHistory supports null values
      const apiItemWithNulls = {
        ...apiItem,
        trend_data: {
          metric_values: [72.5, null, 68.3, null, 69.2, 73.8, 72.5],
          days_on_report: 3,
          consecutive_days: 1,
          week_over_week_change: null,
        },
      }
      const resultWithNulls = transformAPIActionItem(apiItemWithNulls as never)
      expect(resultWithNulls.trendData).toBeDefined()
      expect(resultWithNulls.trendData!.weekOverWeekChange).toBeNull()
      expect(resultWithNulls.trendData!.metricHistory[1]).toBeNull()
    })

    it('UNIT-038: ActionItem type includes optional trendData field', () => {
      // Given: The ActionItem interface in types.ts
      // When: An API action item WITHOUT trend_data is transformed
      const apiItem = {
        id: 'action-api-2',
        asset_id: 'asset-002',
        asset_name: 'Conveyor 3',
        priority_level: 'medium' as const,
        category: 'financial' as const,
        primary_metric_value: '$3,000 loss',
        recommendation_text: 'Review conveyor maintenance',
        evidence_summary: 'Financial impact detected',
        evidence_refs: [{ table: 'daily_summaries', column: 'cost', value: '3000', record_id: 'rec-002', source_table: 'daily_summaries' }],
        created_at: '2026-02-11T09:00:00Z',
        financial_impact_usd: 3000,
        priority_rank: 3,
        title: 'Conveyor Financial Loss',
        description: 'High financial impact',
        acknowledgment: null,
      }

      // Then: The item can be created without trendData (field is optional)
      const result = transformAPIActionItem(apiItem as never)
      expect(result.trendData).toBeUndefined()

      // And: When trend_data IS provided, trendData is populated
      const apiItemWithTrend = {
        ...apiItem,
        trend_data: {
          metric_values: [70, 71, 72, 73, 74, 75, 76],
          days_on_report: 3,
          consecutive_days: 2,
          week_over_week_change: 3.5,
        },
      }
      const resultWithTrend = transformAPIActionItem(apiItemWithTrend as never)

      // This WILL FAIL because transformAPIActionItem doesn't yet map trend_data
      expect(resultWithTrend.trendData).toBeDefined()
      expect(resultWithTrend.trendData!.consecutiveDays).toBe(2)
      expect(resultWithTrend.trendData!.metricHistory).toHaveLength(7)
    })
  })
})
