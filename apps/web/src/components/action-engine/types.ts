/**
 * Insight + Evidence Card Types
 *
 * Types for the action engine card components.
 *
 * @see Story 3.4 - Insight + Evidence Cards
 */

import type { PriorityType } from './PriorityBadge'

/**
 * Evidence data for safety events
 */
export interface SafetyEvidence {
  eventId: string
  detectedAt: string
  reasonCode: string
  severity: string
  assetName: string
}

/**
 * Evidence data for OEE deviations
 */
export interface OEEEvidence {
  targetOEE: number
  actualOEE: number
  deviation: number
  timeframe: string
}

/**
 * Evidence data for financial losses
 */
export interface FinancialEvidence {
  downtimeCost: number
  wasteCost: number
  totalLoss: number
  breakdown: Array<{ category: string; amount: number }>
}

/**
 * Evidence source reference for traceability (NFR1 compliance)
 */
export interface EvidenceSource {
  table: string      // e.g., "daily_summaries"
  date: string       // e.g., "2026-01-05"
  recordId: string   // Unique record identifier
}

/**
 * Evidence container
 */
export interface Evidence {
  type: 'safety_event' | 'oee_deviation' | 'financial_loss'
  data: SafetyEvidence | OEEEvidence | FinancialEvidence
  source: EvidenceSource
}

/**
 * Asset reference
 */
export interface AssetReference {
  id: string
  name: string
  area: string
}

/**
 * Recommendation content
 */
export interface Recommendation {
  text: string      // Natural language recommendation
  summary: string   // Short version for card
}

/**
 * Trend data for action item trend indicators
 *
 * @see Story 14.4 - Trend Indicators on Action Cards
 */
export interface TrendData {
  metricHistory: (number | null)[]
  daysOnReport: number
  consecutiveDays: number
  weekOverWeekChange: number | null
}

/**
 * Acknowledgment info for an action item
 */
export interface AcknowledgmentInfo {
  user_id: string
  acknowledged_at: string
  note: string | null
}

/**
 * Action Item for Insight + Evidence Cards
 *
 * Main data structure for card components.
 */
export interface ActionItem {
  id: string
  priority: PriorityType
  priorityScore: number           // For sorting (higher = more urgent)
  recommendation: Recommendation
  asset: AssetReference
  evidence: Evidence
  financialImpact: number         // Total $ impact
  timestamp: string               // When insight was generated (ISO string)
  acknowledgment?: AcknowledgmentInfo | null
  trendData?: TrendData
}

/**
 * Daily Action List API Response
 */
export interface DailyActionListResponse {
  date: string
  generatedAt: string
  items: ActionItem[]
  summary: {
    totalItems: number
    safetyCount: number
    financialCount: number
    oeeCount: number
    totalFinancialImpact: number
  }
}

/**
 * Type guard for SafetyEvidence
 */
export function isSafetyEvidence(data: SafetyEvidence | OEEEvidence | FinancialEvidence): data is SafetyEvidence {
  return 'eventId' in data && 'reasonCode' in data
}

/**
 * Type guard for OEEEvidence
 */
export function isOEEEvidence(data: SafetyEvidence | OEEEvidence | FinancialEvidence): data is OEEEvidence {
  return 'targetOEE' in data && 'actualOEE' in data
}

/**
 * Follow-up assignment data for action items
 */
export interface FollowUpData {
  id: string
  action_item_id: string
  assigned_to: string
  assignee_email: string
  status: 'assigned' | 'in_progress' | 'resolved'
  note: string | null
  created_at: string
  updated_at: string
}

/**
 * Type guard for FinancialEvidence
 */
export function isFinancialEvidence(data: SafetyEvidence | OEEEvidence | FinancialEvidence): data is FinancialEvidence {
  return 'downtimeCost' in data && 'wasteCost' in data
}
