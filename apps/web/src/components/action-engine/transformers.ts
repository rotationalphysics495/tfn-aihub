/**
 * Data Transformers for Action Engine
 *
 * Utilities to transform data between API response format and
 * Insight + Evidence card format.
 *
 * @see Story 3.4 - Insight + Evidence Cards
 */

import type { PriorityType } from './PriorityBadge'
import type {
  ActionItem as InsightActionItem,
  SafetyEvidence,
  OEEEvidence,
  FinancialEvidence,
  Evidence,
} from './types'
import type {
  ActionItem as APIActionItem,
  ActionCategory,
  EvidenceRef,
} from '@/hooks/useDailyActions'

/**
 * Map API category to PriorityType
 */
function mapCategoryToPriority(category: ActionCategory): PriorityType {
  switch (category) {
    case 'safety':
      return 'SAFETY'
    case 'financial':
      return 'FINANCIAL'
    case 'oee':
      return 'OEE'
    default:
      return 'OEE'
  }
}

/**
 * Map priority level to priority score (higher = more urgent)
 */
function mapPriorityLevelToScore(
  priorityLevel: string,
  category: ActionCategory,
  financialImpact: number
): number {
  // Base score from priority level
  let baseScore = 0
  switch (priorityLevel) {
    case 'critical':
      baseScore = 1000
      break
    case 'high':
      baseScore = 750
      break
    case 'medium':
      baseScore = 500
      break
    case 'low':
      baseScore = 250
      break
    default:
      baseScore = 100
  }

  // Category bonus (safety gets highest priority)
  let categoryBonus = 0
  switch (category) {
    case 'safety':
      categoryBonus = 500
      break
    case 'financial':
      categoryBonus = 200
      break
    case 'oee':
      categoryBonus = 100
      break
  }

  // Financial impact bonus (scaled, max 200 points)
  const impactBonus = Math.min(200, Math.floor(financialImpact / 100))

  return baseScore + categoryBonus + impactBonus
}

/**
 * Extract and transform evidence from API response
 */
function transformEvidence(
  category: ActionCategory,
  evidenceRefs: EvidenceRef[],
  primaryMetricValue: string,
  evidenceSummary: string,
  assetName: string,
  createdAt: string,
  financialImpact: number
): Evidence {
  // Get source info from evidence refs
  const primaryRef = evidenceRefs[0] || {
    table: 'daily_summaries',
    record_id: 'unknown',
  }

  const source = {
    table: primaryRef.source_table || primaryRef.table || 'daily_summaries',
    date: new Date(createdAt).toISOString().split('T')[0],
    recordId: primaryRef.record_id || 'unknown',
  }

  switch (category) {
    case 'safety': {
      const safetyData: SafetyEvidence = {
        eventId: primaryRef.record_id || 'SE-001',
        detectedAt: createdAt,
        reasonCode: primaryMetricValue || 'Safety Event Detected',
        severity: 'high',
        assetName: assetName,
      }
      return {
        type: 'safety_event',
        data: safetyData,
        source,
      }
    }

    case 'oee': {
      // Parse OEE values from primary metric (e.g., "OEE: 72.5%")
      const oeeMatch = primaryMetricValue.match(/(\d+\.?\d*)%/)
      const actualOEE = oeeMatch ? parseFloat(oeeMatch[1]) : 75
      // TODO: Retrieve targetOEE from asset configuration when available
      // Using standard 85% target as fallback per industry best practices
      const targetOEE = 85

      const oeeData: OEEEvidence = {
        targetOEE,
        actualOEE: actualOEE,
        deviation: actualOEE - targetOEE, // Negative when below target
        timeframe: 'Yesterday (T-1)',
      }
      return {
        type: 'oee_deviation',
        data: oeeData,
        source,
      }
    }

    case 'financial':
    default: {
      // TODO: Use actual breakdown from API when available (e.g., from cost_centers table)
      // Current fallback uses industry-typical ratios for estimation
      const downtimePortion = 0.65
      const wastePortion = 0.35

      const financialData: FinancialEvidence = {
        downtimeCost: Math.round(financialImpact * downtimePortion),
        wasteCost: Math.round(financialImpact * wastePortion),
        totalLoss: financialImpact,
        breakdown: [],
      }
      return {
        type: 'financial_loss',
        data: financialData,
        source,
      }
    }
  }
}

/**
 * Transform API ActionItem to Insight + Evidence ActionItem
 */
export function transformAPIActionItem(item: APIActionItem): InsightActionItem {
  const priority = mapCategoryToPriority(item.category)
  const priorityScore = mapPriorityLevelToScore(
    item.priority_level,
    item.category,
    item.financial_impact_usd
  )

  return {
    id: item.id,
    priority,
    priorityScore,
    recommendation: {
      text: item.recommendation_text || item.title,
      summary: item.evidence_summary || item.description,
    },
    asset: {
      id: item.asset_id,
      name: item.asset_name,
      area: '', // Would come from asset lookup
    },
    evidence: transformEvidence(
      item.category,
      item.evidence_refs,
      item.primary_metric_value,
      item.evidence_summary,
      item.asset_name,
      item.created_at,
      item.financial_impact_usd
    ),
    financialImpact: item.financial_impact_usd,
    timestamp: item.created_at,
  }
}

/**
 * Transform array of API action items
 */
export function transformAPIActionItems(items: APIActionItem[]): InsightActionItem[] {
  return items.map(transformAPIActionItem)
}
