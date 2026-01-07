'use client'

/**
 * Citation Panel Component (Story 4.5)
 *
 * Side panel that displays full source data when a citation is clicked.
 *
 * @see Story 4.5 - Cited Response Generation
 * @see AC #4 - Clicking citation opens side panel showing source data
 */

import { useEffect, useState } from 'react'
import {
  X,
  Database,
  Brain,
  Calculator,
  Lightbulb,
  Clock,
  Hash,
  FileText,
  ExternalLink,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import type { CitationData, SourceType } from './CitationLink'

interface SourceData {
  [key: string]: unknown
}

interface CitationDetail {
  id: string
  sourceType: SourceType
  sourceData: SourceData
  relatedCitations: string[]
  fetchedAt: string
}

interface CitationPanelProps {
  /** Citation to display */
  citation: CitationData | null
  /** Whether the panel is open */
  isOpen: boolean
  /** Handler to close the panel */
  onClose: () => void
  /** Handler when a related citation is clicked */
  onRelatedCitationClick?: (citationId: string) => void
  /** Optional custom class name */
  className?: string
}

/**
 * Icon and label for each source type.
 */
const sourceTypeInfo: Record<
  SourceType,
  {
    icon: typeof Database
    label: string
    color: string
  }
> = {
  database: {
    icon: Database,
    label: 'Database Source',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  memory: {
    icon: Brain,
    label: 'Memory Source',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  },
  calculation: {
    icon: Calculator,
    label: 'Calculation',
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  },
  inference: {
    icon: Lightbulb,
    label: 'AI Inference',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  },
}

/**
 * Format a value for display based on its type.
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  if (typeof value === 'number') {
    // Format percentages
    if (value >= 0 && value <= 1) {
      return `${(value * 100).toFixed(1)}%`
    }
    // Format currency-like numbers
    if (value >= 1000) {
      return value.toLocaleString()
    }
    return value.toString()
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

/**
 * Format a key for display.
 */
function formatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .toLowerCase()
    .replace(/^\w/, (c) => c.toUpperCase())
}

/**
 * Citation detail panel that shows source data.
 *
 * Features:
 * - Displays full source record data (AC#4)
 * - Color-coded by source type
 * - Shows related citations
 * - Responsive slide-in panel
 */
export function CitationPanel({
  citation,
  isOpen,
  onClose,
  onRelatedCitationClick,
  className,
}: CitationPanelProps) {
  const [detail, setDetail] = useState<CitationDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch citation details when panel opens
  useEffect(() => {
    if (isOpen && citation) {
      fetchCitationDetail(citation.id)
    } else {
      setDetail(null)
      setError(null)
    }
  }, [isOpen, citation?.id])

  const fetchCitationDetail = async (citationId: string) => {
    setIsLoading(true)
    setError(null)

    try {
      // AC#4: Fetch source data from API (should resolve within 100ms from cache)
      const response = await fetch(`/api/citations/${citationId}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Failed to fetch citation details')
      }

      const data = await response.json()
      setDetail(data)
    } catch (err) {
      console.error('Citation fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to load citation')
      // Fallback: use citation data directly
      if (citation) {
        setDetail({
          id: citation.id,
          sourceType: citation.sourceType,
          sourceData: {
            excerpt: citation.excerpt,
            confidence: citation.confidence,
            source_table: citation.sourceTable,
            record_id: citation.recordId,
          },
          relatedCitations: [],
          fetchedAt: new Date().toISOString(),
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (!citation) return null

  const typeInfo = sourceTypeInfo[citation.sourceType] || sourceTypeInfo.database
  const Icon = typeInfo.icon

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className={cn(
          'w-full sm:w-[450px] sm:max-w-[450px]',
          'flex flex-col',
          className
        )}
        data-testid="citation-panel"
      >
        <SheetHeader className="flex-shrink-0 border-b border-industrial-200 pb-4 dark:border-industrial-700">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-lg',
                  typeInfo.color
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <SheetTitle className="text-left text-base">
                  {typeInfo.label}
                </SheetTitle>
                <SheetDescription className="text-left text-xs">
                  {citation.displayText}
                </SheetDescription>
              </div>
            </div>
          </div>

          {/* Confidence badge */}
          <div className="mt-3 flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                'text-xs',
                citation.confidence >= 0.8
                  ? 'border-green-300 bg-green-50 text-green-700 dark:border-green-700 dark:bg-green-900/20 dark:text-green-400'
                  : citation.confidence >= 0.6
                  ? 'border-yellow-300 bg-yellow-50 text-yellow-700 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400'
                  : 'border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-900/20 dark:text-red-400'
              )}
            >
              {Math.round(citation.confidence * 100)}% confidence
            </Badge>
            {citation.timestamp && (
              <Badge variant="outline" className="text-xs">
                <Clock className="mr-1 h-3 w-3" />
                {new Date(citation.timestamp).toLocaleDateString()}
              </Badge>
            )}
          </div>
        </SheetHeader>

        {/* Content */}
        <div className="flex-1 overflow-y-auto py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading source data...
              </span>
            </div>
          ) : error ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
              <p className="font-medium">Note</p>
              <p className="mt-1">
                Full source data is not available. Showing citation excerpt.
              </p>
            </div>
          ) : null}

          {/* Source data table */}
          {(detail || citation) && (
            <div className="space-y-4">
              {/* Excerpt section */}
              <div className="rounded-lg border border-industrial-200 bg-industrial-50 p-3 dark:border-industrial-700 dark:bg-industrial-900">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                  Source Excerpt
                </div>
                <p className="text-sm text-industrial-700 dark:text-industrial-300">
                  {citation.excerpt}
                </p>
              </div>

              {/* Source metadata */}
              {citation.sourceTable && (
                <div className="flex items-center gap-2 text-sm">
                  <Database className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Table:</span>
                  <code className="rounded bg-industrial-100 px-1.5 py-0.5 text-xs dark:bg-industrial-800">
                    {citation.sourceTable}
                  </code>
                </div>
              )}

              {citation.recordId && (
                <div className="flex items-center gap-2 text-sm">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Record ID:</span>
                  <code className="rounded bg-industrial-100 px-1.5 py-0.5 text-xs dark:bg-industrial-800">
                    {citation.recordId}
                  </code>
                </div>
              )}

              {citation.memoryId && (
                <div className="flex items-center gap-2 text-sm">
                  <Brain className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Memory ID:</span>
                  <code className="rounded bg-industrial-100 px-1.5 py-0.5 text-xs dark:bg-industrial-800">
                    {citation.memoryId}
                  </code>
                </div>
              )}

              {/* Full source data */}
              {detail?.sourceData && Object.keys(detail.sourceData).length > 0 && (
                <div className="mt-4">
                  <h4 className="mb-2 text-sm font-medium">Full Source Data</h4>
                  <div className="rounded-lg border border-industrial-200 dark:border-industrial-700">
                    <table className="w-full text-sm">
                      <tbody>
                        {Object.entries(detail.sourceData)
                          .filter(([key]) => !key.startsWith('_'))
                          .map(([key, value], index) => (
                            <tr
                              key={key}
                              className={cn(
                                'border-b border-industrial-100 dark:border-industrial-800',
                                index % 2 === 0
                                  ? 'bg-white dark:bg-industrial-950'
                                  : 'bg-industrial-50 dark:bg-industrial-900'
                              )}
                            >
                              <td className="px-3 py-2 font-medium text-muted-foreground">
                                {formatKey(key)}
                              </td>
                              <td className="px-3 py-2">
                                {typeof value === 'object' ? (
                                  <pre className="whitespace-pre-wrap text-xs">
                                    {formatValue(value)}
                                  </pre>
                                ) : (
                                  formatValue(value)
                                )}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Related citations */}
              {detail?.relatedCitations && detail.relatedCitations.length > 0 && (
                <div className="mt-4">
                  <h4 className="mb-2 text-sm font-medium">Related Citations</h4>
                  <div className="space-y-1">
                    {detail.relatedCitations.map((relatedId) => (
                      <Button
                        key={relatedId}
                        variant="ghost"
                        size="sm"
                        className="h-auto w-full justify-start px-2 py-1.5 text-left text-xs"
                        onClick={() => onRelatedCitationClick?.(relatedId)}
                      >
                        <ExternalLink className="mr-1.5 h-3 w-3" />
                        {relatedId}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Fetch timestamp */}
              {detail?.fetchedAt && (
                <div className="mt-4 text-xs text-muted-foreground">
                  Data fetched: {new Date(detail.fetchedAt).toLocaleString()}
                </div>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
