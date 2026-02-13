'use client'

/**
 * Chat Context Provider
 *
 * React Context for cross-component communication between
 * MorningSummarySection and ChatSidebar. Enables the "Ask about this"
 * button to open the chat sidebar pre-loaded with morning report context.
 *
 * @see Story 19.1 - Ask About This Button on Smart Summary
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { ReportContext } from './types'

interface ChatContextValue {
  /** Whether the chat sidebar is open */
  isOpen: boolean
  /** Current report context (null when no report context is active) */
  reportContext: ReportContext | null
  /** Open the sidebar */
  open: () => void
  /** Close the sidebar */
  close: () => void
  /** Set open state (for Sheet onOpenChange) */
  setIsOpen: (open: boolean) => void
  /** Open the chat sidebar with morning report context */
  openChatWithContext: (context: ReportContext) => void
  /** Clear the report context (start fresh conversation) */
  clearReportContext: () => void
}

/** Default no-op context for when components are rendered outside the provider (e.g. in tests) */
const defaultChatContext: ChatContextValue = {
  isOpen: false,
  reportContext: null,
  open: () => {},
  close: () => {},
  setIsOpen: () => {},
  openChatWithContext: () => {},
  clearReportContext: () => {},
}

const ChatContext = createContext<ChatContextValue>(defaultChatContext)

export function ChatContextProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [reportContext, setReportContext] = useState<ReportContext | null>(null)

  const open = useCallback(() => {
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
  }, [])

  const openChatWithContext = useCallback((context: ReportContext) => {
    setReportContext(context)
    setIsOpen(true)
  }, [])

  const clearReportContext = useCallback(() => {
    setReportContext(null)
  }, [])

  return (
    <ChatContext.Provider
      value={{
        isOpen,
        reportContext,
        open,
        close,
        setIsOpen,
        openChatWithContext,
        clearReportContext,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChatContext(): ChatContextValue {
  return useContext(ChatContext)
}
