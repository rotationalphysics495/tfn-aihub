/**
 * Action Engine Components
 *
 * Components for displaying Insight + Evidence cards.
 *
 * @see Story 3.4 - Insight + Evidence Cards
 */

// Main card components
export { InsightEvidenceCard, InsightEvidenceCardSkeleton } from './InsightEvidenceCard'
export { ActionCardList, ActionCardListWithData } from './ActionCardList'
export { InsightEvidenceCardList } from './InsightEvidenceCardList'

// Subcomponents
export { InsightSection } from './InsightSection'
export { EvidenceSection } from './EvidenceSection'
export { PriorityBadge, getPriorityBorderColor, getPriorityAccentBg } from './PriorityBadge'

// Types
export type { PriorityType } from './PriorityBadge'
export type {
  ActionItem,
  SafetyEvidence,
  OEEEvidence,
  FinancialEvidence,
  Evidence,
  EvidenceSource,
  AssetReference,
  Recommendation,
  DailyActionListResponse,
} from './types'
export { isSafetyEvidence, isOEEEvidence, isFinancialEvidence } from './types'

// Data transformers
export { transformAPIActionItem, transformAPIActionItems } from './transformers'
