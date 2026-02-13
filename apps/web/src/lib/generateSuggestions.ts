/**
 * Generate Suggestions Utility (Story 19.3)
 *
 * Template-based question generation from action item categories and asset names.
 * Pure client-side logic — no LLM call. Accepts action items, summary text,
 * and report date, returning 2-3 contextual follow-up questions.
 *
 * @see Story 19.3 - Context-Aware Follow-Up Suggestions
 * @see AC #1 - 2-3 contextual follow-up questions
 * @see AC #3 - Suggestions update when report content changes
 */

import type { ActionItem } from '@/hooks/useDailyActions'

export interface SuggestionContext {
  actions: ActionItem[]
  summaryText: string
  reportDate: string
}

/**
 * Format a number as USD currency (e.g., 15000 -> "$15,000")
 */
function formatDollar(amount: number): string {
  return `$${amount.toLocaleString('en-US')}`
}

/**
 * Generate 2-3 contextual follow-up questions based on the report data.
 *
 * Priority ordering: safety > OEE > financial > trend
 * Returns an empty array when no meaningful data exists.
 */
export function generateSuggestions(context: SuggestionContext): string[] {
  const { actions, summaryText } = context

  // Return empty if no data at all
  if ((!actions || actions.length === 0) && (!summaryText || !summaryText.trim())) {
    return []
  }

  const questions: string[] = []

  // Group actions by category
  const safetyActions = actions.filter((a) => a.category === 'safety')
  const oeeActions = actions.filter((a) => a.category === 'oee')
  const financialActions = actions.filter((a) => a.category === 'financial')

  // 1. Safety question (highest priority)
  if (safetyActions.length > 0) {
    const worstSafety = [...safetyActions].sort(
      (a, b) => (a.priority_rank ?? Infinity) - (b.priority_rank ?? Infinity)
    )[0]
    const assetName = worstSafety.asset_name || 'this asset'
    questions.push(`What actions have been taken on ${assetName} safety events?`)
  }

  // 2. OEE question
  if (oeeActions.length > 0) {
    const worstOee = [...oeeActions].sort(
      (a, b) => (a.priority_rank ?? Infinity) - (b.priority_rank ?? Infinity)
    )[0]
    const assetName = worstOee.asset_name || 'this asset'
    questions.push(`What were the top downtime reasons for ${assetName}?`)
  }

  // 3. Financial question
  if (financialActions.length > 0) {
    const worstFinancial = [...financialActions].sort(
      (a, b) => (b.financial_impact_usd ?? 0) - (a.financial_impact_usd ?? 0)
    )[0]
    const assetName = worstFinancial.asset_name || 'this asset'
    const amount = worstFinancial.financial_impact_usd
    if (amount && amount > 0) {
      questions.push(
        `What is driving the ${formatDollar(amount)} production loss on ${assetName}?`
      )
    } else {
      questions.push(`What is driving the production loss on ${assetName}?`)
    }
  }

  // 4. Trend question (filler when we have fewer than 3 category-specific questions)
  if (questions.length < 3) {
    questions.push("How does today's OEE compare to last week?")
  }

  // Cap at 3 questions max
  return questions.slice(0, 3)
}
