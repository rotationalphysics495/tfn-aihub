/**
 * Chat Component Types
 *
 * Type definitions for the AI Chat Sidebar feature.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #3 - Message Display
 * @see AC #6 - Citation Display
 */

/**
 * Citation reference for AI responses.
 * Links AI assertions to source data for transparency and trust.
 */
export interface Citation {
  /** Data source identifier (e.g., "daily_summaries", "downtime_events") */
  source: string
  /** The specific data point being cited (e.g., "OEE: 78.3%") */
  dataPoint: string
  /** When the data was recorded (ISO string or formatted date) */
  timestamp?: string
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
