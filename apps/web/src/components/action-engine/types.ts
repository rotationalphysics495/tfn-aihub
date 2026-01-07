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
 * Type guard for FinancialEvidence
 */
export function isFinancialEvidence(data: SafetyEvidence | OEEEvidence | FinancialEvidence): data is FinancialEvidence {
  return 'downtimeCost' in data && 'wasteCost' in data
}
