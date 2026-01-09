/**
 * Chat Components
 *
 * AI Chat Sidebar interface for natural language factory data queries.
 * Follows Industrial Clarity design system for factory floor readability.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 5.7 - Agent Chat Integration
 */

export { ChatSidebar } from './ChatSidebar'
export { ChatTrigger } from './ChatTrigger'
export { ChatMessage } from './ChatMessage'
export { MessageList } from './MessageList'
export { ChatInput } from './ChatInput'
export { ChatLoadingIndicator } from './ChatLoadingIndicator'
export { FollowUpChips } from './FollowUpChips'

// Citation components (Story 4.5)
export { CitationLink, parseCitationsFromText } from './CitationLink'
export type { CitationData, SourceType } from './CitationLink'
export { CitationPanel } from './CitationPanel'

// Types
export type { Message, Citation, ChatState } from './types'

// Mock data (for development)
export { MOCK_MESSAGES, WELCOME_MESSAGE } from './mockData'
