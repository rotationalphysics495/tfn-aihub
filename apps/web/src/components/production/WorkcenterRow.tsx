'use client'

import { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AssetDetailTable } from './AssetDetailTable'
import type { WorkcenterEntry } from '@/hooks/useWorkcenterSummary'

interface WorkcenterRowProps {
  entry: WorkcenterEntry
}

function getAttainmentColor(pct: number): string {
  if (pct >= 95) return 'text-success-green-dark dark:text-success-green'
  if (pct >= 85) return 'text-warning-amber-dark dark:text-warning-amber'
  return 'text-safety-red'
}

export function WorkcenterRow({ entry }: WorkcenterRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const totalAssets = entry.total_assets
  const attainmentColor = getAttainmentColor(entry.attainment_percentage)

  return (
    <div className="border rounded-lg p-4 md:p-6">
      <button
        type="button"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded(prev => !prev)}
        className="w-full flex items-center justify-between gap-4 min-h-[44px] min-w-[44px] text-left"
        data-clickable
      >
        <div className="flex-1 min-w-0">
          <span className="text-lg font-semibold block">
            {entry.workcenter_name}
          </span>
          <span className="text-base tabular-nums text-muted-foreground">
            {entry.total_actual.toLocaleString()} / {entry.total_target.toLocaleString()}
          </span>
        </div>

        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <span
              className={cn(
                'text-3xl font-bold tabular-nums',
                attainmentColor
              )}
            >
              {entry.attainment_percentage.toFixed(1)}%
            </span>
            <span className="block text-sm text-muted-foreground">
              {entry.assets_on_target} of {totalAssets} assets on target
            </span>
          </div>

          <ChevronRight
            className={cn(
              'w-5 h-5 transition-transform',
              isExpanded && 'rotate-90'
            )}
            aria-hidden="true"
          />
        </div>
      </button>

      {isExpanded && entry.assets.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <AssetDetailTable assets={entry.assets} />
        </div>
      )}
    </div>
  )
}
