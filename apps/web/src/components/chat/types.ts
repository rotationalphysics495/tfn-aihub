/**
 * Chat Component Types
 *
 * Type definitions for the AI Chat Sidebar feature.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 4.5 - Cited Response Generation
 * @see AC #3 - Message Display
 * @see AC #6 - Citation Display
 */

/**
 * Source type for citations (Story 4.5).
 */
export type SourceType = 'database' | 'memory' | 'calculation' | 'inference'

/**
 * Citation reference for AI responses.
 * Links AI assertions to source data for transparency and trust.
 *
 * Story 4.5: Extended with source type, confidence, and IDs for clickable citations.
 */
export interface Citation {
  /** Data source identifier (e.g., "daily_summaries", "downtime_events") */
  source: string
  /** The specific data point being cited (e.g., "OEE: 78.3%") */
  dataPoint: string
  /** When the data was recorded (ISO string or formatted date) */
  timestamp?: string

  // Story 4.5 Extended Fields
  /** Unique citation identifier (Story 4.5) */
  id?: string
  /** Type of source: database, memory, calculation, inference (Story 4.5) */
  sourceType?: SourceType
  /** Database record ID for lookup (Story 4.5) */
  recordId?: string
  /** Memory ID for Mem0 citations (Story 4.5) */
  memoryId?: string
  /** Confidence score 0-1 (Story 4.5) */
  confidence?: number
  /** Human-readable display text (Story 4.5) */
  displayText?: string
}

/**
 * Chat message structure for conversation display.
 */
export interface Message {
  /** Unique identifier for the message */
  id: string
  /** Message sender role */
  role: 'user' | 'assistant'
  /** Message content text */
  content: string
  /** When the message was sent */
  timestamp: Date
  /** Citations/evidence for AI responses (AC #6) */
  citations?: Citation[]

  // Story 4.5 Extended Fields
  /** Grounding score 0-1 indicating response reliability (Story 4.5) */
  groundingScore?: number
  /** Claims that could not be grounded (Story 4.5) */
  ungroundedClaims?: string[]
}

/**
 * Chat sidebar open/close state for context management.
 */
export interface ChatState {
  /** Whether the sidebar is currently open */
  isOpen: boolean
  /** Toggle sidebar open/close */
  toggle: () => void
  /** Open the sidebar */
  open: () => void
  /** Close the sidebar */
  close: () => void
}
