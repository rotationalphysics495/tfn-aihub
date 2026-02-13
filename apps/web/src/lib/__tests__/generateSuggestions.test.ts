/**
 * Unit Tests for generateSuggestions utility (Story 19.3)
 *
 * Tests template-based question generation from action item categories and asset names.
 * These tests MUST FAIL until the feature is implemented (TDD).
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #1 - 2-3 contextual follow-up questions shown as clickable chips
 * @see AC #3 - Suggestions update to reflect new report content
 */

import { describe, it, expect } from 'vitest'
import { generateSuggestions, type SuggestionContext } from '../generateSuggestions'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const createMockActionItem = (overrides: Record<string, unknown> = {}) => ({
  id: 'action-default',
  asset_id: 'asset-default',
  asset_name: 'Default Asset',
  priority_level: 'medium' as const,
  category: 'oee' as const,
  primary_metric_value: '80%',
  recommendation_text: 'Check asset',
  evidence_summary: 'Evidence found',
  evidence_refs: [],
  created_at: '2026-02-13T08:00:00Z',
  financial_impact_usd: 0,
  priority_rank: 5,
  title: 'Action Title',
  description: 'Action description',
  ...overrides,
})

const safetyGrinder5 = createMockActionItem({
  id: 'action-safety-grinder5',
  asset_name: 'Grinder 5',
  category: 'safety',
  priority_level: 'critical',
  priority_rank: 1,
})

const oeeGrinder5 = createMockActionItem({
  id: 'action-oee-grinder5',
  asset_name: 'Grinder 5',
  category: 'oee',
  priority_level: 'high',
  primary_metric_value: '72%',
  priority_rank: 1,
})

const financialLine2 = createMockActionItem({
  id: 'action-financial-line2',
  asset_name: 'Line 2',
  category: 'financial',
  priority_level: 'high',
  financial_impact_usd: 12500,
  priority_rank: 2,
})

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: generateSuggestions utility (Story 19.3)', () => {
  // =========================================================================
  // AC1: 2-3 contextual follow-up questions shown as clickable chips
  // =========================================================================
  describe('AC1: Contextual question generation', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-001: generateSuggestions returns safety question when safety actions present', () => {
      // Given: A SuggestionContext with action items that include a safety item for "Grinder 5"
      const context: SuggestionContext = {
        actions: [safetyGrinder5],
        summaryText: 'A safety incident was reported on Grinder 5.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array contains a question referencing safety and "Grinder 5"
      expect(suggestions.length).toBeGreaterThanOrEqual(1)
      const safetyQuestion = suggestions.find(
        (q) => q.toLowerCase().includes('safety') && q.includes('Grinder 5')
      )
      expect(safetyQuestion).toBeDefined()
    })

    it('19-3-context-aware-followup-suggestions-UNIT-002: generateSuggestions returns OEE question with specific asset name when OEE actions present', () => {
      // Given: A SuggestionContext with an OEE item for "Grinder 5" at 72%
      const context: SuggestionContext = {
        actions: [oeeGrinder5],
        summaryText: 'OEE was 72% on Grinder 5.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array contains a question referencing OEE/downtime for "Grinder 5"
      expect(suggestions.length).toBeGreaterThanOrEqual(1)
      const oeeQuestion = suggestions.find(
        (q) =>
          (q.toLowerCase().includes('oee') || q.toLowerCase().includes('downtime')) &&
          q.includes('Grinder 5')
      )
      expect(oeeQuestion).toBeDefined()
    })

    it('19-3-context-aware-followup-suggestions-UNIT-003: generateSuggestions returns financial question when financial actions present', () => {
      // Given: A SuggestionContext with a financial item for "Line 2" with $12,500 impact
      const context: SuggestionContext = {
        actions: [financialLine2],
        summaryText: 'Production loss estimated at $12,500 on Line 2.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array contains a question referencing financial impact and "Line 2"
      expect(suggestions.length).toBeGreaterThanOrEqual(1)
      const financialQuestion = suggestions.find(
        (q) =>
          (q.includes('$12,500') ||
            q.toLowerCase().includes('production loss') ||
            q.toLowerCase().includes('financial')) &&
          q.includes('Line 2')
      )
      expect(financialQuestion).toBeDefined()
    })

    it('19-3-context-aware-followup-suggestions-UNIT-004: generateSuggestions returns trend/comparison question as filler', () => {
      // Given: A SuggestionContext with fewer than 3 category-specific actions and a valid summary
      const context: SuggestionContext = {
        actions: [safetyGrinder5],
        summaryText: 'OEE was 78% across all lines.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array includes a trend/comparison question to fill up to 2-3
      expect(suggestions.length).toBeGreaterThanOrEqual(2)
      const trendQuestion = suggestions.find(
        (q) =>
          q.toLowerCase().includes('compare') ||
          q.toLowerCase().includes('trend') ||
          q.toLowerCase().includes('last week')
      )
      expect(trendQuestion).toBeDefined()
    })

    it('19-3-context-aware-followup-suggestions-UNIT-005: generateSuggestions respects priority ordering safety > OEE > financial > trend', () => {
      // Given: A SuggestionContext with actions spanning all three categories
      const context: SuggestionContext = {
        actions: [safetyGrinder5, oeeGrinder5, financialLine2],
        summaryText: 'Multiple issues reported today.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: Ordered with safety first, then OEE, then financial (trend excluded since 3 categories fill slots)
      expect(suggestions.length).toBe(3)

      // First question: safety-related
      expect(suggestions[0].toLowerCase()).toContain('safety')

      // Second question: OEE-related
      expect(
        suggestions[1].toLowerCase().includes('oee') ||
          suggestions[1].toLowerCase().includes('downtime')
      ).toBe(true)

      // Third question: financial-related
      expect(
        suggestions[2].toLowerCase().includes('financial') ||
          suggestions[2].toLowerCase().includes('production loss') ||
          suggestions[2].toLowerCase().includes('cost') ||
          suggestions[2].includes('$')
      ).toBe(true)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-006: generateSuggestions returns exactly 2-3 questions (not fewer, not more)', () => {
      // Given: A SuggestionContext with action items spanning all categories and valid summary
      const context: SuggestionContext = {
        actions: [safetyGrinder5, oeeGrinder5, financialLine2],
        summaryText: 'Mixed report with safety, OEE, and financial items.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array length is between 2 and 3 inclusive
      expect(suggestions.length).toBeGreaterThanOrEqual(2)
      expect(suggestions.length).toBeLessThanOrEqual(3)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-007: generateSuggestions caps output at 3 questions maximum', () => {
      // Given: A SuggestionContext with many action items across all categories (9 total)
      const manyActions = [
        createMockActionItem({ id: 's1', asset_name: 'Press 1', category: 'safety', priority_level: 'critical', priority_rank: 1 }),
        createMockActionItem({ id: 's2', asset_name: 'Press 2', category: 'safety', priority_level: 'high', priority_rank: 2 }),
        createMockActionItem({ id: 's3', asset_name: 'Press 3', category: 'safety', priority_level: 'medium', priority_rank: 3 }),
        createMockActionItem({ id: 'o1', asset_name: 'Grinder 1', category: 'oee', priority_level: 'high', priority_rank: 4 }),
        createMockActionItem({ id: 'o2', asset_name: 'Grinder 2', category: 'oee', priority_level: 'medium', priority_rank: 5 }),
        createMockActionItem({ id: 'o3', asset_name: 'Grinder 3', category: 'oee', priority_level: 'low', priority_rank: 6 }),
        createMockActionItem({ id: 'f1', asset_name: 'Line 1', category: 'financial', financial_impact_usd: 5000, priority_rank: 7 }),
        createMockActionItem({ id: 'f2', asset_name: 'Line 2', category: 'financial', financial_impact_usd: 8000, priority_rank: 8 }),
        createMockActionItem({ id: 'f3', asset_name: 'Line 3', category: 'financial', financial_impact_usd: 10000, priority_rank: 9 }),
      ]

      const context: SuggestionContext = {
        actions: manyActions,
        summaryText: 'Many issues across safety, OEE, and financial.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array has at most 3 elements
      expect(suggestions.length).toBeLessThanOrEqual(3)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-008: generateSuggestions returns empty array when no action items and no summary', () => {
      // Given: A SuggestionContext with empty actions and empty summaryText
      const context: SuggestionContext = {
        actions: [],
        summaryText: '',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The returned array is empty
      expect(suggestions).toEqual([])
    })
  })

  // =========================================================================
  // AC1 continued: Asset-specific question logic
  // =========================================================================
  describe('AC1: Asset-specific question logic', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-009: generateSuggestions uses worst-performing asset name for OEE questions', () => {
      // Given: Multiple OEE actions where "Grinder 5" has priority_rank 1 (worst performer)
      const oeeActions = [
        createMockActionItem({
          id: 'oee-grinder5',
          asset_name: 'Grinder 5',
          category: 'oee',
          priority_rank: 1,
          primary_metric_value: '62%',
        }),
        createMockActionItem({
          id: 'oee-line3',
          asset_name: 'Line 3',
          category: 'oee',
          priority_rank: 3,
          primary_metric_value: '78%',
        }),
      ]

      const context: SuggestionContext = {
        actions: oeeActions,
        summaryText: 'OEE varies across assets.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The OEE question references "Grinder 5" (worst performer), not "Line 3"
      const oeeQuestion = suggestions.find(
        (q) => q.toLowerCase().includes('oee') || q.toLowerCase().includes('downtime')
      )
      expect(oeeQuestion).toBeDefined()
      expect(oeeQuestion).toContain('Grinder 5')
      expect(oeeQuestion).not.toContain('Line 3')
    })

    it('19-3-context-aware-followup-suggestions-UNIT-010: generateSuggestions includes financial impact amount in financial questions', () => {
      // Given: A financial action with financial_impact_usd: 15000
      const action = createMockActionItem({
        id: 'fin-line1',
        asset_name: 'Line 1',
        category: 'financial',
        financial_impact_usd: 15000,
        priority_rank: 1,
      })

      const context: SuggestionContext = {
        actions: [action],
        summaryText: 'Financial impact detected on Line 1.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: The financial question includes a formatted dollar amount "$15,000"
      const financialQuestion = suggestions.find((q) => q.includes('$15,000'))
      expect(financialQuestion).toBeDefined()
    })

    it('19-3-context-aware-followup-suggestions-UNIT-011: generateSuggestions handles mixed categories correctly', () => {
      // Given: 1 safety and 2 OEE action items (no financial)
      const actions = [
        createMockActionItem({ id: 'safety-1', asset_name: 'Press 1', category: 'safety', priority_rank: 1 }),
        createMockActionItem({ id: 'oee-1', asset_name: 'Grinder 5', category: 'oee', priority_rank: 2 }),
        createMockActionItem({ id: 'oee-2', asset_name: 'Line 2', category: 'oee', priority_rank: 3 }),
      ]

      const context: SuggestionContext = {
        actions,
        summaryText: 'Safety event and OEE drops reported.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: safety first, OEE second, trend third (no financial available)
      expect(suggestions.length).toBeGreaterThanOrEqual(2)
      expect(suggestions.length).toBeLessThanOrEqual(3)

      // First: safety
      expect(suggestions[0].toLowerCase()).toContain('safety')

      // Second: OEE
      expect(
        suggestions[1].toLowerCase().includes('oee') ||
          suggestions[1].toLowerCase().includes('downtime')
      ).toBe(true)

      // Third (if present): trend question
      if (suggestions.length === 3) {
        expect(
          suggestions[2].toLowerCase().includes('compare') ||
            suggestions[2].toLowerCase().includes('trend') ||
            suggestions[2].toLowerCase().includes('last week')
        ).toBe(true)
      }
    })

    it('19-3-context-aware-followup-suggestions-UNIT-012: generateSuggestions returns at least 2 questions when sufficient data exists', () => {
      // Given: Only 1 OEE action item with valid summary text
      const context: SuggestionContext = {
        actions: [oeeGrinder5],
        summaryText: 'OEE was 72% on Grinder 5, below target.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with this context
      const suggestions = generateSuggestions(context)

      // Then: At least 2 elements (OEE question + trend question)
      expect(suggestions.length).toBeGreaterThanOrEqual(2)
    })
  })

  // =========================================================================
  // AC3: Suggestions update when report content changes
  // =========================================================================
  describe('AC3: Deterministic output changes with input', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-023: generateSuggestions produces different output for different inputs', () => {
      // Given: Two different SuggestionContext objects
      const contextA: SuggestionContext = {
        actions: [createMockActionItem({ id: 'a1', category: 'safety', asset_name: 'Grinder 5', priority_rank: 1 })],
        summaryText: 'Safety incident on Grinder 5.',
        reportDate: '2026-02-13',
      }

      const contextB: SuggestionContext = {
        actions: [createMockActionItem({ id: 'b1', category: 'oee', asset_name: 'Line 2', priority_rank: 1 })],
        summaryText: 'OEE drop on Line 2.',
        reportDate: '2026-02-13',
      }

      // When: generateSuggestions() is called with each context
      const suggestionsA = generateSuggestions(contextA)
      const suggestionsB = generateSuggestions(contextB)

      // Then: The returned arrays contain different question strings
      expect(suggestionsA).not.toEqual(suggestionsB)

      // Context A should reference Grinder 5
      expect(suggestionsA.some((q) => q.includes('Grinder 5'))).toBe(true)

      // Context B should reference Line 2
      expect(suggestionsB.some((q) => q.includes('Line 2'))).toBe(true)
    })
  })
})
