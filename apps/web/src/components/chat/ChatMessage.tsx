'use client'

/**
 * Chat Message Component
 *
 * Renders individual chat messages with distinct styling for user vs AI.
 * Includes collapsible citation display, markdown rendering, and follow-up chips.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see Story 4.5 - Cited Response Generation
 * @see Story 5.7 - Agent Chat Integration
 * @see AC #3 - Message Display (clear visual distinction)
 * @see AC #6 - Citation Display (structured evidence area)
 * @see AC #7 - Response Formatting (tables, lists)
 */

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChevronDown, ChevronUp, Database, AlertTriangle, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CitationLink, type CitationData } from './CitationLink'
import { CitationPanel } from './CitationPanel'
import { FollowUpChips } from './FollowUpChips'
import type { Message, Citation } from './types'

interface ChatMessageProps {
  /** The message to display */
  message: Message
  /** Handler for follow-up chip selection (Story 5.7) */
  onFollowUpSelect?: (question: string) => void
  /** Handler for retry on error (Story 5.7) */
  onRetry?: () => void
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
 *
 * Story 5.7 enhancements:
 * - Markdown rendering for structured content (AC#7)
 * - Follow-up question chips (AC#3)
 * - Error state with retry button (AC#5)
 */
export function ChatMessage({ message, onFollowUpSelect, onRetry, className }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<CitationData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  const isUser = message.role === 'user'
  const hasCitations = message.citations && message.citations.length > 0
  const hasGroundingScore = typeof message.groundingScore === 'number'
  const hasFollowUps = message.followUpQuestions && message.followUpQuestions.length > 0
  const isError = message.isError

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
            : isError
              ? 'bg-warning-amber/20 dark:bg-warning-amber/30'
              : 'bg-industrial-200 dark:bg-industrial-700'
        )}
      >
        {isError ? (
          <AlertCircle className="h-4 w-4 text-warning-amber" />
        ) : (
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
        )}
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
              : isError
                ? 'bg-warning-amber/10 border border-warning-amber/30 text-industrial-900 dark:text-industrial-100'
                : 'bg-industrial-100 text-industrial-900 dark:bg-industrial-800 dark:text-industrial-100'
          )}
        >
          {/* Story 5.7 AC#7: Markdown rendering for structured content */}
          {isUser ? (
            message.content
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Table rendering with horizontal scroll for mobile (AC#8)
                  table: ({ children }) => (
                    <div className="overflow-x-auto -mx-2 my-2">
                      <table className="min-w-full border-collapse text-sm">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-industrial-200/50 dark:bg-industrial-700/50">
                      {children}
                    </thead>
                  ),
                  th: ({ children }) => (
                    <th className="border border-industrial-300 dark:border-industrial-600 px-3 py-2 text-left font-medium">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-industrial-300 dark:border-industrial-600 px-3 py-2">
                      {children}
                    </td>
                  ),
                  // Status colors for production data (AC#7)
                  strong: ({ children }) => {
                    const text = String(children).toLowerCase()
                    if (text.includes('behind') || text.includes('down') || text.includes('critical')) {
                      return <strong className="text-warning-amber dark:text-warning-amber">{children}</strong>
                    }
                    if (text.includes('ahead') || text.includes('running') || text.includes('on target')) {
                      return <strong className="text-success-green dark:text-success-green">{children}</strong>
                    }
                    return <strong>{children}</strong>
                  },
                  // Links open in new tab
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-info-blue hover:underline"
                    >
                      {children}
                    </a>
                  ),
                  // List styling
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>
                  ),
                  // Code blocks
                  code: ({ className, children }) => {
                    const isInline = !className
                    return isInline ? (
                      <code className="bg-industrial-200 dark:bg-industrial-700 px-1 py-0.5 rounded text-sm">
                        {children}
                      </code>
                    ) : (
                      <code className="block bg-industrial-200 dark:bg-industrial-700 p-2 rounded text-sm overflow-x-auto">
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Story 5.7 AC#5: Error state with retry button */}
        {isError && onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="h-8 gap-1.5 text-xs border-warning-amber/50 hover:bg-warning-amber/10"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </Button>
        )}

        {/* Story 4.5: Grounding score indicator for AI messages */}
        {!isUser && !isError && hasGroundingScore && (
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
        {!isUser && !isError && hasCitations && (
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

        {/* Story 5.7 AC#3: Follow-up question chips */}
        {!isUser && !isError && hasFollowUps && onFollowUpSelect && (
          <FollowUpChips
            questions={message.followUpQuestions!}
            onSelect={onFollowUpSelect}
          />
        )}

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
