'use client'

import { cn } from '@/lib/utils'
import type { AssetDetail } from '@/hooks/useWorkcenterSummary'

interface AssetDetailTableProps {
  assets: AssetDetail[]
}

export function AssetDetailTable({ assets }: AssetDetailTableProps) {
  return (
    <table className="w-full text-base">
      <thead>
        <tr className="border-b text-left text-sm text-muted-foreground">
          <th className="pb-2 font-medium">Asset</th>
          <th className="pb-2 font-medium">Actual / Target</th>
          <th className="pb-2 font-medium">OEE %</th>
          <th className="pb-2 font-medium">Downtime</th>
        </tr>
      </thead>
      <tbody>
        {assets.map(asset => {
          const hitTarget = asset.actual >= asset.target

          return (
            <tr
              key={asset.asset_name}
              className={cn(
                'border-b last:border-b-0',
                hitTarget
                  ? 'bg-success-green-light/20'
                  : 'bg-safety-red-light/20'
              )}
            >
              <td className="py-2 pr-4">{asset.asset_name}</td>
              <td className="py-2 pr-4 tabular-nums">
                {asset.actual.toLocaleString()} / {asset.target.toLocaleString()}
              </td>
              <td className="py-2 pr-4 tabular-nums">
                {asset.oee != null ? `${asset.oee.toFixed(1)}%` : '\u2014'}
              </td>
              <td className="py-2 tabular-nums">
                {asset.downtime_minutes != null
                  ? `${asset.downtime_minutes} min`
                  : '\u2014'}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
