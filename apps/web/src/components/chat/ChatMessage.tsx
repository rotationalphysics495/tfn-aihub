'use client'

/**
 * Chat Message Component
 *
 * Renders individual chat messages with distinct styling for user vs AI.
 * Includes collapsible citation display for AI responses.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 4.5 - Cited Response Generation
 * @see AC #3 - Message Display (clear visual distinction)
 * @see AC #6 - Citation Display (structured evidence area)
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp, Database, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CitationLink, type CitationData } from './CitationLink'
import { CitationPanel } from './CitationPanel'
import type { Message, Citation } from './types'

interface ChatMessageProps {
  /** The message to display */
  message: Message
  /** Optional custom class name */
  className?: string
}

/**
 * Convert legacy Citation to CitationData format for new components.
 */
function convertToCitationData(citation: Citation, index: number): CitationData {
  return {
    id: citation.id || `cit-${index}`,
    sourceType: citation.sourceType || 'database',
    sourceTable: citation.source,
    recordId: citation.recordId,
    memoryId: citation.memoryId,
    timestamp: citation.timestamp,
    excerpt: citation.dataPoint,
    confidence: citation.confidence || 0.8,
    displayText: citation.displayText || `[Source: ${citation.source}]`,
  }
}

/**
 * Individual chat message bubble with role-based styling.
 * - User messages: right-aligned, info-blue background
 * - AI messages: left-aligned, industrial-gray background with citations
 *
 * Story 4.5 enhancements:
 * - Clickable citation links (AC#4)
 * - Grounding score display (AC#3)
 * - Citation panel on click (AC#4)
 */
export function ChatMessage({ message, className }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<CitationData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  const isUser = message.role === 'user'
  const hasCitations = message.citations && message.citations.length > 0
  const hasGroundingScore = typeof message.groundingScore === 'number'

  // Convert citations to CitationData format
  const citationData: CitationData[] = hasCitations
    ? message.citations!.map((c, i) => convertToCitationData(c, i))
    : []

  // Handle citation click - open panel
  const handleCitationClick = (citationId: string) => {
    const citation = citationData.find((c) => c.id === citationId)
    if (citation) {
      setSelectedCitation(citation)
      setIsPanelOpen(true)
    }
  }

  // Get grounding status
  const getGroundingStatus = () => {
    if (!hasGroundingScore) return null
    if (message.groundingScore! >= 0.8) return 'high'
    if (message.groundingScore! >= 0.6) return 'medium'
    return 'low'
  }

  const groundingStatus = getGroundingStatus()

  return (
    <div
      className={cn(
        'flex w-full gap-3 py-2',
        isUser ? 'flex-row-reverse' : 'flex-row',
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser
            ? 'bg-info-blue text-white'
            : 'bg-industrial-200 dark:bg-industrial-700'
        )}
      >
        <span
          className={cn(
            'text-xs font-semibold',
            isUser
              ? 'text-white'
              : 'text-industrial-600 dark:text-industrial-300'
          )}
        >
          {isUser ? 'You' : 'AI'}
        </span>
      </div>

      {/* Message content */}
      <div
        className={cn(
          'flex max-w-[80%] flex-col gap-1',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            'rounded-lg px-4 py-3 text-base leading-relaxed',
            isUser
              ? 'bg-info-blue text-white'
              : 'bg-industrial-100 text-industrial-900 dark:bg-industrial-800 dark:text-industrial-100'
          )}
        >
          {message.content}
        </div>

        {/* Story 4.5: Grounding score indicator for AI messages */}
        {!isUser && hasGroundingScore && (
          <div className="flex items-center gap-1.5">
            {groundingStatus === 'high' && (
              <Badge
                variant="outline"
                className="h-5 gap-1 border-green-300 bg-green-50 px-1.5 text-[10px] text-green-700 dark:border-green-700 dark:bg-green-900/20 dark:text-green-400"
              >
                <CheckCircle2 className="h-2.5 w-2.5" />
                Verified
              </Badge>
            )}
            {groundingStatus === 'medium' && (
              <Badge
                variant="outline"
                className="h-5 gap-1 border-yellow-300 bg-yellow-50 px-1.5 text-[10px] text-yellow-700 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400"
              >
                <Database className="h-2.5 w-2.5" />
                Partial
              </Badge>
            )}
            {groundingStatus === 'low' && (
              <Badge
                variant="outline"
                className="h-5 gap-1 border-amber-300 bg-amber-50 px-1.5 text-[10px] text-amber-700 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-400"
              >
                <AlertTriangle className="h-2.5 w-2.5" />
                Limited
              </Badge>
            )}
          </div>
        )}

        {/* Citations section for AI messages */}
        {!isUser && hasCitations && (
          <div className="w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCitations(!showCitations)}
              className="h-auto gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
              aria-expanded={showCitations}
              aria-controls={`citations-${message.id}`}
            >
              <Database className="h-3 w-3" />
              <span>
                {message.citations!.length} source
                {message.citations!.length !== 1 ? 's' : ''}
              </span>
              {showCitations ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>

            {/* Collapsible citations list with clickable links (Story 4.5 AC#4) */}
            {showCitations && (
              <div
                id={`citations-${message.id}`}
                className="mt-2 rounded-md border border-industrial-200 bg-industrial-50 p-3 dark:border-industrial-700 dark:bg-industrial-900"
                role="region"
                aria-label="Data sources"
              >
                <ul className="space-y-2">
                  {citationData.map((citation) => (
                    <li key={citation.id} className="flex items-start gap-2">
                      <CitationLink
                        citation={citation}
                        onClick={handleCitationClick}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Citation Panel (Story 4.5 AC#4) */}
        <CitationPanel
          citation={selectedCitation}
          isOpen={isPanelOpen}
          onClose={() => {
            setIsPanelOpen(false)
            setSelectedCitation(null)
          }}
          onRelatedCitationClick={handleCitationClick}
        />

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}


/**
 * Format timestamp for display.
 * Shows relative time for recent messages, otherwise HH:MM.
 */
function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
