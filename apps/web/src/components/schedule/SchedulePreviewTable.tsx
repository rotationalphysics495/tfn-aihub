'use client'

import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import type { SchedulePreviewResponse, ScheduleRowPreview } from '@/hooks/useScheduleUpload'

interface SchedulePreviewTableProps {
  previewData: SchedulePreviewResponse
}

function StatusIcon({ row }: { row: ScheduleRowPreview }) {
  if (row.errors.length > 0) {
    return <XCircle data-testid="status-icon" className="w-5 h-5 text-destructive" />
  }
  if (row.asset_match_status === 'matched') {
    return <CheckCircle data-testid="status-icon" className="w-5 h-5 text-green-500" />
  }
  if (row.asset_match_status === 'suggested') {
    return <AlertTriangle data-testid="status-icon" className="w-5 h-5 text-amber-500" />
  }
  return <XCircle data-testid="status-icon" className="w-5 h-5 text-destructive" />
}

export function SchedulePreviewTable({ previewData }: SchedulePreviewTableProps) {
  const errorCount = previewData.rows.filter(r => r.errors.length > 0).length

  return (
    <div>
      {/* Summary stats bar */}
      <div className="flex flex-wrap gap-3 mb-4 text-sm" data-testid="summary-stats">
        <span className="inline-flex items-center rounded-md border border-transparent bg-secondary px-2.5 py-0.5 text-xs font-semibold">
          {previewData.parsed_rows_count} Total Rows
        </span>
        <span className="inline-flex items-center rounded-md border border-transparent bg-secondary px-2.5 py-0.5 text-xs font-semibold text-green-600">
          {previewData.matched_assets.length} Matched Assets
        </span>
        {previewData.new_products.length > 0 && (
          <span className="inline-flex items-center rounded-md border border-transparent bg-secondary px-2.5 py-0.5 text-xs font-semibold text-blue-500">
            {previewData.new_products.length} New Products
          </span>
        )}
        {errorCount > 0 && (
          <span className="inline-flex items-center rounded-md border border-transparent bg-secondary px-2.5 py-0.5 text-xs font-semibold text-destructive">
            {errorCount} Errors
          </span>
        )}
      </div>

      {/* Scrollable table container */}
      <div className="overflow-y-auto max-h-96 border rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 sticky top-0">
            <tr>
              <th className="text-left px-3 py-2 font-medium">Status</th>
              <th className="text-left px-3 py-2 font-medium">Row #</th>
              <th className="text-left px-3 py-2 font-medium">Date</th>
              <th className="text-left px-3 py-2 font-medium">Shift</th>
              <th className="text-left px-3 py-2 font-medium">Asset</th>
              <th className="text-left px-3 py-2 font-medium">Product</th>
              <th className="text-left px-3 py-2 font-medium">Quantity</th>
              <th className="text-left px-3 py-2 font-medium">Issues</th>
            </tr>
          </thead>
          <tbody>
            {previewData.rows.map((row) => (
              <tr
                key={row.row_number}
                className={row.errors.length > 0 ? 'bg-destructive/5' : ''}
              >
                <td className="px-3 py-2">
                  <StatusIcon row={row} />
                </td>
                <td className="px-3 py-2">{row.row_number}</td>
                <td className="px-3 py-2">{row.date}</td>
                <td className="px-3 py-2">{row.shift}</td>
                <td className="px-3 py-2">
                  <span>{row.asset_name}</span>
                  {row.asset_match_status === 'suggested' && row.suggestions.length > 0 && (
                    <p className="text-xs text-amber-500 mt-1">
                      Did you mean: {row.suggestions.join(', ')}?
                    </p>
                  )}
                </td>
                <td className="px-3 py-2">
                  <span className={row.is_new_product ? 'text-blue-500 font-medium' : ''}>
                    {row.product_name}
                    {row.is_new_product && (
                      <span className="ml-1 text-xs">(new)</span>
                    )}
                  </span>
                </td>
                <td className="px-3 py-2">{row.scheduled_quantity}</td>
                <td className="px-3 py-2">
                  {row.errors.length > 0 && (
                    <div className="space-y-1">
                      {row.errors.map((err, i) => (
                        <p key={i} className="text-xs text-destructive">
                          {err.field}: {err.message}
                        </p>
                      ))}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
