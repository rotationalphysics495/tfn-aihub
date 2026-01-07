'use client'

/**
 * Chat Sidebar Component
 *
 * Main container for the AI chat interface.
 * Overlay/sidebar pattern using Radix Sheet primitive.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #1 - Collapsible sidebar/overlay component
 * @see AC #2 - Industrial Clarity Compliance
 * @see AC #7 - Responsive Design (400px desktop, 100% tablet/mobile)
 * @see AC #8 - Keyboard Accessibility (Escape to close)
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { Bot, X } from 'lucide-react'
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
import { MOCK_MESSAGES, WELCOME_MESSAGE } from './mockData'
import type { Message } from './types'

interface ChatSidebarProps {
  /** Optional custom class name */
  className?: string
}

/**
 * AI Chat Sidebar with Sheet overlay behavior.
 * - Slide-in/out animation from right side
 * - Backdrop overlay for focus
 * - Keyboard navigation (Escape to close)
 * - Responsive width (400px desktop, full width mobile)
 */
export function ChatSidebar({ className }: ChatSidebarProps) {
  // State management (local for UI-only story)
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE, ...MOCK_MESSAGES])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Ref for focusing input when sidebar opens
  const inputRef = useRef<HTMLTextAreaElement>(null)

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

  // Handle opening the sidebar
  const handleOpen = useCallback(() => {
    setIsOpen(true)
  }, [])

  // Handle closing the sidebar
  const handleClose = useCallback(() => {
    setIsOpen(false)
  }, [])

  // Handle message submission
  const handleSubmit = useCallback(() => {
    if (!inputValue.trim() || isLoading) return

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Simulate AI response (will be replaced with real API in Stories 4.1-4.2)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content:
          'This is a mock response. In production, this will be powered by Mem0 and LangChain Text-to-SQL for real data queries.',
        timestamp: new Date(),
        citations: [
          { source: 'mock_data', dataPoint: 'Demo response', timestamp: new Date().toISOString() },
        ],
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }, [inputValue, isLoading])

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
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-info-blue">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div>
                  <SheetTitle className="text-left text-base font-semibold">
                    Factory AI Assistant
                  </SheetTitle>
                  <SheetDescription
                    id="chat-sidebar-description"
                    className="text-left text-xs"
                  >
                    Ask about production data
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
