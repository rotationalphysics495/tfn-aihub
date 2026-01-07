'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  AlertTriangle,
  Gauge,
  DollarSign,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Database,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type {
  Evidence,
  SafetyEvidence,
  OEEEvidence,
  FinancialEvidence,
} from './types'

/**
 * Evidence Section Component (Right side of card)
 *
 * Displays the supporting data/evidence:
 * - Safety: safety_events details (time, reason code, asset)
 * - OEE: target vs actual mini-visualization
 * - Financial: cost breakdown (downtime + waste)
 * - Source citation for NFR1 compliance
 * - View Details link for drill-down
 *
 * @see Story 3.4 - Insight + Evidence Cards
 * @see AC #3 - Evidence Display (Right Side)
 * @see AC #5 - Data Source Integration
 * @see AC #6 - Interactivity (expandable section)
 */

interface EvidenceSectionProps {
  evidence: Evidence
  className?: string
  defaultExpanded?: boolean
}

// Format currency for display
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`
  }
  return `$${Math.round(value)}`
}

// Format time from ISO string
function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

/**
 * Safety Evidence Display
 */
function SafetyEvidenceDisplay({ data }: { data: SafetyEvidence }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-safety-red">
        <AlertTriangle className="w-5 h-5" aria-hidden="true" />
        <span className="font-semibold text-lg">Safety Event Details</span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-base">
        <div>
          <span className="text-muted-foreground">Detected:</span>
          <p className="font-medium text-foreground">{formatTime(data.detectedAt)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Severity:</span>
          <p className="font-medium text-foreground capitalize">{data.severity}</p>
        </div>
        <div className="col-span-2">
          <span className="text-muted-foreground">Reason Code:</span>
          <p className="font-medium text-foreground">{data.reasonCode}</p>
        </div>
        <div className="col-span-2">
          <span className="text-muted-foreground">Asset:</span>
          <p className="font-medium text-foreground">{data.assetName}</p>
        </div>
      </div>
    </div>
  )
}

/**
 * OEE Evidence Display with mini-visualization
 */
function OEEEvidenceDisplay({ data }: { data: OEEEvidence }) {
  const actualPercent = Math.min(100, Math.max(0, data.actualOEE))
  const targetPercent = Math.min(100, Math.max(0, data.targetOEE))

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-[#CA8A04] dark:text-[#EAB308]">
        <Gauge className="w-5 h-5" aria-hidden="true" />
        <span className="font-semibold text-lg">OEE Performance</span>
      </div>

      {/* Mini visualization: OEE bar comparison */}
      <div className="space-y-2">
        {/* Target bar */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground w-16">Target:</span>
          <div className="flex-1 h-4 bg-industrial-200 dark:bg-industrial-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-success-green rounded-full transition-all duration-300"
              style={{ width: `${targetPercent}%` }}
              aria-hidden="true"
            />
          </div>
          <span className="font-bold text-foreground w-14 text-right">{data.targetOEE}%</span>
        </div>

        {/* Actual bar */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground w-16">Actual:</span>
          <div className="flex-1 h-4 bg-industrial-200 dark:bg-industrial-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#EAB308] rounded-full transition-all duration-300"
              style={{ width: `${actualPercent}%` }}
              aria-hidden="true"
            />
          </div>
          <span className="font-bold text-foreground w-14 text-right">{data.actualOEE}%</span>
        </div>
      </div>

      {/* Deviation summary */}
      <div className="flex items-center justify-between p-3 bg-[#EAB308]/10 rounded-lg">
        <span className="text-muted-foreground">Deviation:</span>
        <span className="text-xl font-bold text-[#CA8A04] dark:text-[#EAB308]">
          {data.deviation >= 0 ? '+' : ''}{data.deviation.toFixed(1)}%
        </span>
      </div>

      <p className="text-sm text-muted-foreground">
        Timeframe: {data.timeframe}
      </p>
    </div>
  )
}

/**
 * Financial Evidence Display with cost breakdown
 */
function FinancialEvidenceDisplay({ data }: { data: FinancialEvidence }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-warning-amber-dark dark:text-warning-amber">
        <DollarSign className="w-5 h-5" aria-hidden="true" />
        <span className="font-semibold text-lg">Financial Impact</span>
      </div>

      {/* Cost breakdown */}
      <div className="space-y-2">
        <div className="flex justify-between items-center py-2 border-b border-border">
          <span className="text-muted-foreground">Downtime Cost:</span>
          <span className="font-medium text-foreground">{formatCurrency(data.downtimeCost)}</span>
        </div>
        <div className="flex justify-between items-center py-2 border-b border-border">
          <span className="text-muted-foreground">Waste Cost:</span>
          <span className="font-medium text-foreground">{formatCurrency(data.wasteCost)}</span>
        </div>

        {/* Additional breakdown items if available */}
        {data.breakdown.map((item, index) => (
          <div
            key={index}
            className="flex justify-between items-center py-2 border-b border-border last:border-b-0"
          >
            <span className="text-muted-foreground">{item.category}:</span>
            <span className="font-medium text-foreground">{formatCurrency(item.amount)}</span>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="flex justify-between items-center p-3 bg-warning-amber-light/20 dark:bg-warning-amber-dark/10 rounded-lg">
        <span className="font-semibold text-foreground">Total Loss:</span>
        <span className="text-2xl font-bold text-warning-amber-dark dark:text-warning-amber">
          {formatCurrency(data.totalLoss)}
        </span>
      </div>
    </div>
  )
}

export function EvidenceSection({
  evidence,
  className,
  defaultExpanded = false,
}: EvidenceSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  // Determine which evidence display to render
  const renderEvidenceContent = () => {
    const data = evidence.data

    if ('eventId' in data && 'reasonCode' in data) {
      return <SafetyEvidenceDisplay data={data as SafetyEvidence} />
    }
    if ('targetOEE' in data && 'actualOEE' in data) {
      return <OEEEvidenceDisplay data={data as OEEEvidence} />
    }
    if ('downtimeCost' in data && 'wasteCost' in data) {
      return <FinancialEvidenceDisplay data={data as FinancialEvidence} />
    }

    return null
  }

  return (
    <div className={cn('flex flex-col', className)}>
      {/* Evidence header with expand/collapse (AC #6) */}
      <Button
        variant="ghost"
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full justify-between h-auto py-3 px-4',
          'text-base font-medium',
          'hover:bg-industrial-100 dark:hover:bg-industrial-800',
          'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
        )}
        aria-expanded={isExpanded}
        aria-controls="evidence-content"
      >
        <span className="flex items-center gap-2">
          <Database className="w-4 h-4 text-muted-foreground" aria-hidden="true" />
          <span className="text-foreground">Supporting Evidence</span>
        </span>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-muted-foreground" aria-hidden="true" />
        ) : (
          <ChevronDown className="w-5 h-5 text-muted-foreground" aria-hidden="true" />
        )}
      </Button>

      {/* Expandable evidence content (AC #6) */}
      <div
        id="evidence-content"
        className={cn(
          'overflow-hidden transition-all duration-300 ease-in-out',
          isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
        )}
        aria-hidden={!isExpanded}
      >
        <div className="p-4 space-y-4">
          {/* Evidence display */}
          {renderEvidenceContent()}

          {/* Source citation - NFR1 compliance (AC #5) */}
          <div className="pt-3 border-t border-border">
            <p className="text-sm text-muted-foreground flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" aria-hidden="true" />
              Source: {evidence.source.table} ({evidence.source.date})
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Record ID: {evidence.source.recordId}
            </p>
          </div>

          {/* View Details link for drill-down (AC #3) */}
          <Link
            href={`/evidence/${evidence.source.recordId}`}
            className={cn(
              'inline-flex items-center gap-2',
              'text-base font-medium text-primary',
              'hover:underline',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'rounded-sm'
            )}
          >
            <span>View Details</span>
            <ExternalLink className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Collapsed state summary */}
      {!isExpanded && (
        <div className="px-4 pb-3">
          <p className="text-sm text-muted-foreground">
            Source: {evidence.source.table} ({evidence.source.date})
          </p>
        </div>
      )}
    </div>
  )
}
