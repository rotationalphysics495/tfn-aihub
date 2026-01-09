'use client'

/**
 * Chat Sidebar Component
 *
 * Main container for the AI chat interface.
 * Overlay/sidebar pattern using Radix Sheet primitive.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 5.7 - Agent Chat Integration
 * @see AC #1 - Collapsible sidebar/overlay component
 * @see AC #2 - Industrial Clarity Compliance
 * @see AC #7 - Responsive Design (400px desktop, 100% tablet/mobile)
 * @see AC #8 - Keyboard Accessibility (Escape to close)
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { Bot, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { ChatTrigger } from './ChatTrigger'
import { WELCOME_MESSAGE } from './mockData'
import type { Message, Citation } from './types'

/**
 * API Response format from /api/chat/query endpoint
 */
interface ChatApiResponse {
  answer: string
  sql?: string
  data?: Array<Record<string, unknown>>
  citations: Array<{
    value: string
    field: string
    table: string
    context: string
  }>
  executed_at: string
  execution_time_seconds: number
  row_count: number
  error: boolean
  suggestions?: string[]
  meta?: {
    grounding_score?: number
    follow_up_questions?: string[]
    agent_tool?: string
    ungrounded_claims?: string[]
  }
}

interface ChatSidebarProps {
  /** Optional custom class name */
  className?: string
  /** API base URL (defaults to relative path) */
  apiBaseUrl?: string
  /** Timeout for API requests in ms (default 30000) */
  requestTimeout?: number
}

/**
 * AI Chat Sidebar with Sheet overlay behavior.
 *
 * Story 5.7: Agent Chat Integration
 * - Routes messages to /api/chat/query which routes to ManufacturingAgent
 * - Displays citations from agent tools
 * - Shows follow-up question chips
 * - Handles errors with retry capability
 * - Preserves chat history in local state
 */
export function ChatSidebar({
  className,
  apiBaseUrl = '',
  requestTimeout = 30000,
}: ChatSidebarProps) {
  // State management
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null)

  // Ref for focusing input when sidebar opens
  const inputRef = useRef<HTMLTextAreaElement>(null)
  // Ref to track abort controller for cancelling requests
  const abortControllerRef = useRef<AbortController | null>(null)

  // Focus input when sidebar opens (AC #4.5)
  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure Sheet animation is complete
      const timer = setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Handle opening the sidebar
  const handleOpen = useCallback(() => {
    setIsOpen(true)
  }, [])

  // Handle closing the sidebar
  const handleClose = useCallback(() => {
    setIsOpen(false)
  }, [])

  /**
   * Transform API citations to frontend Citation format
   */
  const transformCitations = (apiCitations: ChatApiResponse['citations']): Citation[] => {
    return apiCitations.map((c, index) => ({
      source: c.table,
      dataPoint: c.value,
      timestamp: new Date().toISOString(),
      id: `cit-${index}`,
      sourceType: 'database' as const,
      recordId: undefined,
      confidence: 0.8,
      displayText: `[Source: ${c.table}/${c.context}]`,
    }))
  }

  /**
   * Send message to the chat API
   * Story 5.7 AC#1: Routes to agent endpoint
   */
  const sendMessage = useCallback(async (messageContent: string): Promise<void> => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller with timeout
    abortControllerRef.current = new AbortController()
    const timeoutId = setTimeout(() => {
      abortControllerRef.current?.abort()
    }, requestTimeout)

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          question: messageContent,
        }),
        signal: abortControllerRef.current.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data: ChatApiResponse = await response.json()

      // Story 5.7 AC#2, AC#7: Create assistant message with citations and follow-ups
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        citations: transformCitations(data.citations),
        groundingScore: data.meta?.grounding_score,
        ungroundedClaims: data.meta?.ungrounded_claims,
        followUpQuestions: data.meta?.follow_up_questions || data.suggestions,
        toolUsed: data.meta?.agent_tool,
        isError: data.error,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setLastFailedMessage(null)

    } catch (error) {
      // Story 5.7 AC#5: Handle errors gracefully
      let errorContent = 'I encountered an error processing your request. Please try again.'

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorContent = 'The request timed out. Please try again with a simpler question.'
        } else if (error.message.includes('Rate limit')) {
          errorContent = 'You\'ve sent too many messages. Please wait a moment before trying again.'
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          errorContent = 'Unable to connect to the server. Please check your connection and try again.'
        }
      }

      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
        isError: true,
      }

      setMessages((prev) => [...prev, errorMessage])
      setLastFailedMessage(messageContent)

      // Log error for debugging
      console.error('Chat API error:', error)
    } finally {
      clearTimeout(timeoutId)
      abortControllerRef.current = null
    }
  }, [apiBaseUrl, requestTimeout])

  /**
   * Handle message submission
   * Story 5.7 AC#1, AC#4: Send message and show loading state
   */
  const handleSubmit = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return

    const messageContent = inputValue.trim()

    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    await sendMessage(messageContent)

    setIsLoading(false)
  }, [inputValue, isLoading, sendMessage])

  /**
   * Handle follow-up chip selection
   * Story 5.7 AC#3: Clicking a chip sends that question as the next message
   */
  const handleFollowUpSelect = useCallback(async (question: string) => {
    if (isLoading) return

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    await sendMessage(question)

    setIsLoading(false)
  }, [isLoading, sendMessage])

  /**
   * Handle retry of failed message
   * Story 5.7 AC#5: User can retry the message
   */
  const handleRetry = useCallback(async (messageId: string) => {
    if (isLoading || !lastFailedMessage) return

    // Remove the error message
    setMessages((prev) => prev.filter((m) => m.id !== messageId))
    setIsLoading(true)

    await sendMessage(lastFailedMessage)

    setIsLoading(false)
  }, [isLoading, lastFailedMessage, sendMessage])

  return (
    <>
      {/* Floating trigger button */}
      <ChatTrigger onClick={handleOpen} isOpen={isOpen} />

      {/* Sheet sidebar */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent
          id="chat-sidebar"
          side="right"
          className={cn(
            // Remove default padding for custom layout
            'p-0',
            // Responsive width: 400px desktop, full width on mobile/tablet
            'w-full sm:w-[400px] sm:max-w-[400px]',
            // Height handling
            'flex flex-col',
            // Industrial Clarity styling
            'border-l-industrial-200 dark:border-l-industrial-700',
            className
          )}
          // Override default close button (we'll add our own in header)
          aria-describedby="chat-sidebar-description"
        >
          {/* Header */}
          <SheetHeader className="flex-shrink-0 border-b border-industrial-200 px-4 py-3 dark:border-industrial-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full',
                  isLoading ? 'bg-info-blue/80' : 'bg-info-blue'
                )}>
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 text-white animate-spin" />
                  ) : (
                    <Bot className="h-4 w-4 text-white" />
                  )}
                </div>
                <div>
                  <SheetTitle className="text-left text-base font-semibold">
                    Factory AI Assistant
                  </SheetTitle>
                  <SheetDescription
                    id="chat-sidebar-description"
                    className="text-left text-xs"
                  >
                    {isLoading ? 'Thinking...' : 'Ask about production data'}
                  </SheetDescription>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClose}
                className="h-8 w-8"
                aria-label="Close chat"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </SheetHeader>

          {/* Messages area (flex-grow to fill available space) */}
          <div className="flex-1 overflow-hidden">
            <MessageList
              messages={messages}
              isLoading={isLoading}
              onFollowUpSelect={handleFollowUpSelect}
              onRetry={handleRetry}
              className="h-full"
            />
          </div>

          {/* Input area (flex-shrink-0 to stay at bottom) */}
          <ChatInput
            ref={inputRef}
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSubmit}
            disabled={isLoading}
          />
        </SheetContent>
      </Sheet>
    </>
  )
}
