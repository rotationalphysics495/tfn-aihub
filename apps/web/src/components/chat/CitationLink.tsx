'use client'

/**
 * Citation Link Component (Story 4.5)
 *
 * Renders inline citations as clickable links with visual distinction
 * between data citations (blue) and memory citations (purple).
 *
 * @see Story 4.5 - Cited Response Generation
 * @see AC #4 - Citation UI Rendering
 */

import { useState } from 'react'
import { Database, Brain, Calculator, Lightbulb } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

export type SourceType = 'database' | 'memory' | 'calculation' | 'inference'

export interface CitationData {
  /** Unique citation identifier */
  id: string
  /** Type of citation source */
  sourceType: SourceType
  /** Database table name (for database sources) */
  sourceTable?: string
  /** Record ID in source */
  recordId?: string
  /** Memory ID (for memory sources) */
  memoryId?: string
  /** Timestamp of source data */
  timestamp?: string
  /** Key excerpt from source */
  excerpt: string
  /** Confidence score (0-1) */
  confidence: number
  /** Human-readable display text */
  displayText: string
}

interface CitationLinkProps {
  /** Citation data to display */
  citation: CitationData
  /** Handler when citation is clicked */
  onClick?: (citationId: string) => void
  /** Optional custom class name */
  className?: string
}

/**
 * Citation styling per Industrial Clarity theme.
 * AC#4: Visual distinction between data citations (blue) and memory citations (purple).
 */
const citationStyles: Record<SourceType, {
  base: string
  hover: string
  icon: typeof Database
  label: string
}> = {
  database: {
    base: 'text-blue-600 dark:text-blue-400',
    hover: 'hover:text-blue-800 dark:hover:text-blue-300',
    icon: Database,
    label: 'Data Source',
  },
  memory: {
    base: 'text-purple-600 dark:text-purple-400',
    hover: 'hover:text-purple-800 dark:hover:text-purple-300',
    icon: Brain,
    label: 'Memory Source',
  },
  calculation: {
    base: 'text-gray-600 dark:text-gray-400',
    hover: 'hover:text-gray-800 dark:hover:text-gray-300',
    icon: Calculator,
    label: 'Calculation',
  },
  inference: {
    base: 'text-amber-600 dark:text-amber-400',
    hover: 'hover:text-amber-800 dark:hover:text-amber-300',
    icon: Lightbulb,
    label: 'AI Inference',
  },
}

/**
 * Inline citation link component.
 *
 * Features:
 * - Color-coded by source type (AC#4)
 * - Hover tooltip with summary (AC#4)
 * - Click to open citation panel (AC#4)
 */
export function CitationLink({
  citation,
  onClick,
  className,
}: CitationLinkProps) {
  const [isHovered, setIsHovered] = useState(false)

  const style = citationStyles[citation.sourceType] || citationStyles.database
  const Icon = style.icon

  // Format confidence as percentage
  const confidencePercent = Math.round(citation.confidence * 100)

  // Build tooltip content
  const tooltipContent = (
    <div className="max-w-xs space-y-1">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Icon className="h-3.5 w-3.5" />
        <span>{style.label}</span>
        <span className="text-xs text-muted-foreground">
          ({confidencePercent}% confidence)
        </span>
      </div>
      {citation.sourceTable && (
        <div className="text-xs text-muted-foreground">
          Table: {citation.sourceTable}
        </div>
      )}
      {citation.excerpt && (
        <div className="text-xs">
          {citation.excerpt.length > 100
            ? `${citation.excerpt.slice(0, 100)}...`
            : citation.excerpt}
        </div>
      )}
      {citation.timestamp && (
        <div className="text-xs text-muted-foreground">
          {new Date(citation.timestamp).toLocaleDateString()}
        </div>
      )}
    </div>
  )

  const handleClick = () => {
    if (onClick && citation.sourceType !== 'inference') {
      onClick(citation.id)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  // Inference citations are not clickable
  const isClickable = citation.sourceType !== 'inference' && onClick

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            role={isClickable ? 'button' : 'text'}
            tabIndex={isClickable ? 0 : undefined}
            onClick={handleClick}
            onKeyDown={isClickable ? handleKeyDown : undefined}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={cn(
              'inline-flex items-center gap-0.5 text-sm',
              style.base,
              isClickable && style.hover,
              isClickable && 'cursor-pointer underline underline-offset-2',
              citation.sourceType === 'inference' && 'italic cursor-default',
              'transition-colors duration-150',
              className
            )}
            aria-label={`Citation: ${citation.displayText}`}
          >
            <Icon
              className={cn(
                'inline h-3 w-3 flex-shrink-0',
                isHovered && 'animate-pulse'
              )}
            />
            <span className="truncate max-w-[200px]">
              {citation.displayText}
            </span>
          </span>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="start"
          className="bg-white dark:bg-industrial-900 border border-industrial-200 dark:border-industrial-700"
        >
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Parse citation markers from response text and return JSX with CitationLink components.
 *
 * Looks for patterns like:
 * - [Source: table_name/date/asset]
 * - [Memory: asset-history/asset-name/mem-id]
 * - [Evidence: calculation @ date]
 * - [AI Inference - description]
 */
export function parseCitationsFromText(
  text: string,
  citations: CitationData[],
  onCitationClick?: (citationId: string) => void
): React.ReactNode {
  // Pattern to match citation markers
  const citationPattern = /\[(Source|Memory|Evidence|AI Inference)[^\]]*\]/g

  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match

  // Create a map of display text to citation for quick lookup
  const citationMap = new Map<string, CitationData>()
  citations.forEach((cit) => {
    citationMap.set(cit.displayText, cit)
  })

  while ((match = citationPattern.exec(text)) !== null) {
    // Add text before the citation
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }

    // Find matching citation
    const matchedText = match[0]
    const citation = citationMap.get(matchedText)

    if (citation) {
      parts.push(
        <CitationLink
          key={`${citation.id}-${match.index}`}
          citation={citation}
          onClick={onCitationClick}
        />
      )
    } else {
      // No matching citation found, render as styled text
      const isInference = matchedText.includes('AI Inference')
      parts.push(
        <span
          key={`unknown-${match.index}`}
          className={cn(
            'text-sm',
            isInference
              ? 'text-amber-600 dark:text-amber-400 italic'
              : 'text-gray-500 dark:text-gray-400'
          )}
        >
          {matchedText}
        </span>
      )
    }

    lastIndex = match.index + matchedText.length
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return <>{parts}</>
}
