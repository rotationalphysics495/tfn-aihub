'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { OEEStatusBadge, OEEStatusDot } from './OEEStatusBadge'

/**
 * Asset OEE List Component
 *
 * Displays per-asset OEE breakdown in a table/card format.
 * Shows all three OEE components for each asset.
 *
 * @see Story 2.4 - OEE Metrics View
 * @see AC #4 - Individual asset OEE breakdown showing each component's contribution
 * @see AC #7 - OEE targets shown alongside actual values
 * @see AC #9 - "Industrial Clarity" design - readable from 3 feet
 */

export interface AssetOEEData {
  asset_id: string
  name: string
  area: string | null
  oee: number | null
  availability: number | null
  performance: number | null
  quality: number | null
  target: number
  status: string
}

interface AssetOEEListProps {
  /** List of asset OEE data */
  assets: AssetOEEData[]
  /** Whether this is live data */
  isLive?: boolean
  /** Optional additional class names */
  className?: string
}

interface AssetOEECardProps {
  asset: AssetOEEData
  isLive: boolean
}

function formatValue(value: number | null): string {
  return value !== null ? value.toFixed(1) : '--'
}

function AssetOEECard({ asset, isLive }: AssetOEECardProps) {
  const variance = asset.oee !== null ? asset.oee - asset.target : null
  const varianceSign = variance !== null && variance >= 0 ? '+' : ''

  return (
    <Card mode={isLive ? 'live' : 'retrospective'} className="h-full">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h4 className="card-title text-foreground">{asset.name}</h4>
            {asset.area && (
              <p className="text-sm text-muted-foreground">{asset.area}</p>
            )}
          </div>
          <OEEStatusBadge status={asset.status} size="sm" />
        </div>

        {/* Main OEE Value */}
        <div className="text-center py-4 mb-4 rounded-lg bg-muted/50">
          <p className="text-4xl font-bold tabular-nums text-foreground">
            {formatValue(asset.oee)}%
          </p>
          <p className="text-sm text-muted-foreground mt-1">Overall OEE</p>
        </div>

        {/* Components Grid */}
        <div className="grid grid-cols-3 gap-2 text-center mb-4">
          <div className="p-2 rounded-md bg-muted/30">
            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatValue(asset.availability)}%
            </p>
            <p className="text-xs text-muted-foreground">Availability</p>
          </div>
          <div className="p-2 rounded-md bg-muted/30">
            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatValue(asset.performance)}%
            </p>
            <p className="text-xs text-muted-foreground">Performance</p>
          </div>
          <div className="p-2 rounded-md bg-muted/30">
            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatValue(asset.quality)}%
            </p>
            <p className="text-xs text-muted-foreground">Quality</p>
          </div>
        </div>

        {/* Target Comparison */}
        <div className="flex items-center justify-between pt-3 border-t border-border">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Target:</span>
            <span className="text-sm font-medium text-foreground">
              {asset.target.toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Variance:</span>
            <span
              className={cn(
                'text-sm font-medium',
                variance !== null && variance >= 0
                  ? 'text-success-green'
                  : variance !== null
                    ? 'text-warning-amber'
                    : 'text-muted-foreground',
              )}
            >
              {variance !== null ? `${varianceSign}${variance.toFixed(1)}%` : '--'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Table row view for compact display
 */
function AssetOEETableRow({ asset, isLive }: AssetOEECardProps) {
  const variance = asset.oee !== null ? asset.oee - asset.target : null
  const varianceSign = variance !== null && variance >= 0 ? '+' : ''

  return (
    <tr className="border-b border-border hover:bg-muted/30 transition-colors">
      <td className="py-4 px-4">
        <div className="flex items-center gap-3">
          <OEEStatusDot status={asset.status} size="md" />
          <div>
            <p className="font-medium text-foreground">{asset.name}</p>
            {asset.area && (
              <p className="text-sm text-muted-foreground">{asset.area}</p>
            )}
          </div>
        </div>
      </td>
      <td className="py-4 px-4 text-right">
        <span className="text-xl font-bold tabular-nums text-foreground">
          {formatValue(asset.oee)}%
        </span>
      </td>
      <td className="py-4 px-4 text-right tabular-nums text-foreground">
        {formatValue(asset.availability)}%
      </td>
      <td className="py-4 px-4 text-right tabular-nums text-foreground">
        {formatValue(asset.performance)}%
      </td>
      <td className="py-4 px-4 text-right tabular-nums text-foreground">
        {formatValue(asset.quality)}%
      </td>
      <td className="py-4 px-4 text-right">
        <span className="text-sm text-muted-foreground">
          {asset.target.toFixed(0)}%
        </span>
      </td>
      <td className="py-4 px-4 text-right">
        <span
          className={cn(
            'font-medium',
            variance !== null && variance >= 0
              ? 'text-success-green'
              : variance !== null
                ? 'text-warning-amber'
                : 'text-muted-foreground',
          )}
        >
          {variance !== null ? `${varianceSign}${variance.toFixed(1)}%` : '--'}
        </span>
      </td>
      <td className="py-4 px-4">
        <OEEStatusBadge status={asset.status} size="sm" />
      </td>
    </tr>
  )
}

export function AssetOEEList({ assets, isLive = false, className }: AssetOEEListProps) {
  if (assets.length === 0) {
    return (
      <Card mode={isLive ? 'live' : 'retrospective'} className={className}>
        <CardContent className="py-12 text-center">
          <svg
            className="w-12 h-12 text-muted-foreground mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <p className="text-lg text-foreground">No asset OEE data available</p>
          <p className="text-sm text-muted-foreground mt-1">
            Data will appear once production summaries are processed.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Card Grid for smaller screens / summary view */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:hidden">
        {assets.map((asset) => (
          <AssetOEECard key={asset.asset_id} asset={asset} isLive={isLive} />
        ))}
      </div>

      {/* Table for larger screens */}
      <Card
        mode={isLive ? 'live' : 'retrospective'}
        className="hidden lg:block overflow-hidden"
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            Asset OEE Breakdown ({assets.length} assets)
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="py-3 px-4 text-left font-semibold text-foreground">
                  Asset
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  OEE
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  Avail.
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  Perf.
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  Quality
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  Target
                </th>
                <th className="py-3 px-4 text-right font-semibold text-foreground">
                  Variance
                </th>
                <th className="py-3 px-4 text-left font-semibold text-foreground">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <AssetOEETableRow key={asset.asset_id} asset={asset} isLive={isLive} />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
