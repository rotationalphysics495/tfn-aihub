/**
 * Chat Components
 *
 * AI Chat Sidebar interface for natural language factory data queries.
 * Follows Industrial Clarity design system for factory floor readability.
 *
 * @see Story 4.3 - Chat Sidebar UI
 */

export { ChatSidebar } from './ChatSidebar'
export { ChatTrigger } from './ChatTrigger'
export { ChatMessage } from './ChatMessage'
export { MessageList } from './MessageList'
export { ChatInput } from './ChatInput'
export { ChatLoadingIndicator } from './ChatLoadingIndicator'

// Types
export type { Message, Citation, ChatState } from './types'

// Mock data (for development)
export { MOCK_MESSAGES, WELCOME_MESSAGE } from './mockData'
