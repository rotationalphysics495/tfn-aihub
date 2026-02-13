/**
 * SuggestedQuestions Component Tests (Story 19.3)
 *
 * Tests the contextual follow-up question chips rendered below
 * the smart summary "Ask about this" button area.
 * These tests MUST FAIL until the feature is implemented (TDD).
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #1 - 2-3 contextual follow-up questions shown as clickable chips
 * @see AC #3 - Suggestions update when report content changes
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SuggestedQuestions } from '../SuggestedQuestions'

// ---------------------------------------------------------------------------
// Mock generateSuggestions for component isolation where needed
// (UNIT-024 uses a spy; other tests rely on real integration via the component)
// ---------------------------------------------------------------------------
const mockGenerateSuggestions = vi.fn()
vi.mock('@/lib/generateSuggestions', () => ({
  generateSuggestions: (...args: unknown[]) => mockGenerateSuggestions(...args),
}))

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

const safetyItem = createMockActionItem({
  id: 'action-safety-1',
  asset_name: 'Grinder 5',
  category: 'safety',
  priority_level: 'critical',
  priority_rank: 1,
})

const oeeItem = createMockActionItem({
  id: 'action-oee-1',
  asset_name: 'Grinder 5',
  category: 'oee',
  priority_level: 'high',
  primary_metric_value: '72%',
  priority_rank: 2,
})

const financialItem = createMockActionItem({
  id: 'action-financial-1',
  asset_name: 'Line 2',
  category: 'financial',
  priority_level: 'high',
  financial_impact_usd: 12500,
  priority_rank: 3,
})

// Default mock suggestions matching the typical safety + OEE scenario
const defaultSuggestions = [
  'What actions have been taken on Grinder 5 safety events?',
  'What were the top downtime reasons for Grinder 5?',
  "How does today's OEE compare to last week?",
]

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: SuggestedQuestions Component (Story 19.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: generateSuggestions returns 3 suggestions
    mockGenerateSuggestions.mockReturnValue(defaultSuggestions)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Rendering suggestion chips
  // =========================================================================
  describe('AC1: Suggestion chip rendering', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-013: SuggestedQuestions renders suggestion chips when action data is provided', () => {
      // Given: SuggestedQuestions receives actionItems with safety and OEE categories
      const onQuestionSelect = vi.fn()

      // When: The component mounts
      render(
        <SuggestedQuestions
          actionItems={[safetyItem, oeeItem]}
          summaryText="Production summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: 2-3 Button elements with variant="outline" and size="sm" are visible
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
      expect(buttons.length).toBeLessThanOrEqual(3)

      // Each chip should contain question text
      buttons.forEach((button) => {
        expect(button.textContent).toBeTruthy()
        expect(button.textContent!.length).toBeGreaterThan(5)
      })
    })

    it('19-3-context-aware-followup-suggestions-UNIT-014: SuggestedQuestions calls onQuestionSelect with correct question text when chip is clicked', () => {
      // Given: SuggestedQuestions renders with valid action data and an onQuestionSelect callback
      const onQuestionSelect = vi.fn()

      render(
        <SuggestedQuestions
          actionItems={[safetyItem, oeeItem]}
          summaryText="Production summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // When: The user clicks on one of the suggestion chips
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
      fireEvent.click(buttons[0])

      // Then: onQuestionSelect is called exactly once with the question text displayed on the chip
      expect(onQuestionSelect).toHaveBeenCalledTimes(1)
      const calledWith = onQuestionSelect.mock.calls[0][0]
      expect(typeof calledWith).toBe('string')
      expect(calledWith.length).toBeGreaterThan(0)
      // The called argument should match one of the suggestions
      expect(defaultSuggestions).toContain(calledWith)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-015: SuggestedQuestions returns null when no suggestions can be generated', () => {
      // Given: generateSuggestions returns empty array for empty inputs
      mockGenerateSuggestions.mockReturnValue([])

      const onQuestionSelect = vi.fn()

      // When: The component attempts to render
      const { container } = render(
        <SuggestedQuestions
          actionItems={[]}
          summaryText=""
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: The component renders nothing (returns null)
      expect(container.firstChild).toBeNull()
    })
  })

  // =========================================================================
  // AC1: Accessibility
  // =========================================================================
  describe('AC1: Accessibility', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-016: SuggestedQuestions has proper ARIA attributes', () => {
      // Given: SuggestedQuestions renders with valid action data
      const onQuestionSelect = vi.fn()

      // When: The component mounts
      render(
        <SuggestedQuestions
          actionItems={[safetyItem, oeeItem]}
          summaryText="Production summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: Container has role="group" and correct aria-label
      const container = screen.getByRole('group')
      expect(container).toHaveAttribute(
        'aria-label',
        'Suggested follow-up questions about the morning report'
      )

      // Each chip button has aria-label starting with "Ask: " followed by question text
      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        const ariaLabel = button.getAttribute('aria-label')
        expect(ariaLabel).toBeDefined()
        expect(ariaLabel).toMatch(/^Ask: .+/)
      })
    })
  })

  // =========================================================================
  // AC1: Styling and animation
  // =========================================================================
  describe('AC1: Styling and animation', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-017: SuggestedQuestions applies animation classes', () => {
      // Given: SuggestedQuestions renders with valid action data
      const onQuestionSelect = vi.fn()

      // When: The component mounts
      render(
        <SuggestedQuestions
          actionItems={[safetyItem, oeeItem]}
          summaryText="Production summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: Each suggestion chip has animation classes
      const container = screen.getByRole('group')
      expect(container).toHaveClass('animate-in')
      expect(container).toHaveClass('fade-in')
      expect(container).toHaveClass('slide-in-from-bottom-2')
      expect(container).toHaveClass('duration-300')
    })

    it('19-3-context-aware-followup-suggestions-UNIT-018: SuggestedQuestions limits display to maximum 3 chips', () => {
      // Given: generateSuggestions would return 3 suggestions (many items across all categories)
      const manyItems = [
        safetyItem,
        oeeItem,
        financialItem,
        createMockActionItem({ id: 's2', category: 'safety', asset_name: 'Press 1', priority_rank: 4 }),
        createMockActionItem({ id: 'o2', category: 'oee', asset_name: 'Line 3', priority_rank: 5 }),
      ]

      const onQuestionSelect = vi.fn()

      // When: The component mounts
      render(
        <SuggestedQuestions
          actionItems={manyItems}
          summaryText="Full report with many items"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: At most 3 chip buttons are rendered in the DOM
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeLessThanOrEqual(3)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-019: SuggestedQuestions applies custom className', () => {
      // Given: SuggestedQuestions is rendered with a className prop
      const onQuestionSelect = vi.fn()

      // When: The component mounts
      render(
        <SuggestedQuestions
          actionItems={[safetyItem, oeeItem]}
          summaryText="Production summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
          className="mt-4 custom-class"
        />
      )

      // Then: The container element includes the custom classes
      const container = screen.getByRole('group')
      expect(container).toHaveClass('mt-4')
      expect(container).toHaveClass('custom-class')
    })
  })

  // =========================================================================
  // AC3: Suggestions update on prop changes
  // =========================================================================
  describe('AC3: Suggestions update when props change', () => {
    it('19-3-context-aware-followup-suggestions-UNIT-020: Suggestions recalculate when actionItems prop changes', () => {
      // Given: SuggestedQuestions rendered with safety action items
      const onQuestionSelect = vi.fn()

      mockGenerateSuggestions.mockReturnValue([
        'What actions have been taken on Grinder 5 safety events?',
        "How does today's OEE compare to last week?",
      ])

      const { rerender } = render(
        <SuggestedQuestions
          actionItems={[safetyItem]}
          summaryText="Safety summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Capture initial chip text
      const initialButtons = screen.getAllByRole('button')
      const initialTexts = initialButtons.map((b) => b.textContent)
      expect(initialTexts.some((t) => t?.toLowerCase().includes('safety'))).toBe(true)

      // When: The actionItems prop updates to OEE items only
      mockGenerateSuggestions.mockReturnValue([
        'What were the top downtime reasons for Line 1?',
        "How does today's OEE compare to last week?",
      ])

      const oeeOnly = createMockActionItem({
        id: 'oee-line1',
        asset_name: 'Line 1',
        category: 'oee',
        priority_rank: 1,
      })

      rerender(
        <SuggestedQuestions
          actionItems={[oeeOnly]}
          summaryText="OEE summary"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: The rendered chips show OEE questions instead of safety questions
      const updatedButtons = screen.getAllByRole('button')
      const updatedTexts = updatedButtons.map((b) => b.textContent)
      expect(updatedTexts.some((t) => t?.toLowerCase().includes('downtime'))).toBe(true)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-021: Suggestions recalculate when summaryText prop changes', () => {
      // Given: SuggestedQuestions rendered with initial summary
      const onQuestionSelect = vi.fn()

      mockGenerateSuggestions.mockReturnValue([
        'What were the top downtime reasons for Grinder 5?',
        "How does today's OEE compare to last week?",
      ])

      const { rerender } = render(
        <SuggestedQuestions
          actionItems={[oeeItem]}
          summaryText="OEE was 78% across all lines"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // When: The summaryText prop updates with new content
      mockGenerateSuggestions.mockReturnValue([
        'What actions have been taken on Grinder 5 safety events?',
        "How does today's OEE compare to last week?",
      ])

      rerender(
        <SuggestedQuestions
          actionItems={[safetyItem]}
          summaryText="Safety incident reported on Grinder 5"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: generateSuggestions is called again with updated inputs
      expect(mockGenerateSuggestions).toHaveBeenCalledTimes(2)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-022: Suggestions recalculate when reportDate prop changes', () => {
      // Given: SuggestedQuestions rendered with reportDate "2026-02-12"
      const onQuestionSelect = vi.fn()

      mockGenerateSuggestions.mockReturnValue([
        'What were the top downtime reasons for Grinder 5?',
        "How does today's OEE compare to last week?",
      ])

      const { rerender } = render(
        <SuggestedQuestions
          actionItems={[oeeItem]}
          summaryText="OEE summary"
          reportDate="2026-02-12"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // When: The reportDate changes to "2026-02-13" with different action items
      mockGenerateSuggestions.mockReturnValue([
        'What actions have been taken on Grinder 5 safety events?',
        "How does today's OEE compare to last week?",
      ])

      rerender(
        <SuggestedQuestions
          actionItems={[safetyItem]}
          summaryText="Safety incident on Grinder 5"
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: generateSuggestions is called again reflecting the new date's data
      expect(mockGenerateSuggestions).toHaveBeenCalledTimes(2)

      // The rendered chips should reflect the new content
      const buttons = screen.getAllByRole('button')
      const texts = buttons.map((b) => b.textContent)
      expect(texts.some((t) => t?.toLowerCase().includes('safety'))).toBe(true)
    })

    it('19-3-context-aware-followup-suggestions-UNIT-024: useMemo prevents unnecessary recalculation with same inputs', () => {
      // Given: SuggestedQuestions rendered with specific actionItems and summaryText
      const onQuestionSelect = vi.fn()
      const stableActionItems = [oeeItem]
      const stableSummaryText = 'OEE summary'

      mockGenerateSuggestions.mockReturnValue([
        'What were the top downtime reasons for Grinder 5?',
        "How does today's OEE compare to last week?",
      ])

      const { rerender } = render(
        <SuggestedQuestions
          actionItems={stableActionItems}
          summaryText={stableSummaryText}
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      const callCountAfterFirstRender = mockGenerateSuggestions.mock.calls.length

      // When: The parent re-renders but passes the same references
      rerender(
        <SuggestedQuestions
          actionItems={stableActionItems}
          summaryText={stableSummaryText}
          reportDate="2026-02-13"
          onQuestionSelect={onQuestionSelect}
        />
      )

      // Then: generateSuggestions is NOT called again (memoized result reused)
      // With useMemo, same references should not trigger recalculation
      expect(mockGenerateSuggestions.mock.calls.length).toBe(callCountAfterFirstRender)
    })
  })
})
