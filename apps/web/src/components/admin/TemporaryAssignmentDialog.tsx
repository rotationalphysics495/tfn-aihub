/**
 * Temporary Assignment Dialog (Story 9.13, Task 8)
 *
 * Dialog for setting expiration dates on temporary assignments.
 *
 * AC#4: Temporary assignments with expiration dates (FR49)
 *
 * Features:
 * - Task 8.1: Expiration date picker
 * - Task 8.2: Visual indicator for temporary assignments
 * - Task 8.3: Show countdown/expiration on hover
 *
 * References:
 * - [Source: prd/prd-functional-requirements.md#FR49]
 */
'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Calendar, X, Check, AlertTriangle } from 'lucide-react'

interface TemporaryAssignmentDialogProps {
  supervisorName: string
  assetName: string
  isOpen: boolean
  onClose: () => void
  onConfirm: (expiresAt: string | null) => void
}

// Preset duration options
const DURATION_PRESETS = [
  { label: '1 day', days: 1 },
  { label: '1 week', days: 7 },
  { label: '2 weeks', days: 14 },
  { label: '1 month', days: 30 },
  { label: '3 months', days: 90 },
]

export function TemporaryAssignmentDialog({
  supervisorName,
  assetName,
  isOpen,
  onClose,
  onConfirm,
}: TemporaryAssignmentDialogProps) {
  const [selectedDuration, setSelectedDuration] = useState<number | null>(null)
  const [customDate, setCustomDate] = useState<string>('')
  const [isTemporary, setIsTemporary] = useState(false)

  // Calculate expiration date based on selection
  const expirationDate = useMemo(() => {
    if (!isTemporary) return null

    if (customDate) {
      return new Date(customDate).toISOString()
    }

    if (selectedDuration !== null) {
      const date = new Date()
      date.setDate(date.getDate() + selectedDuration)
      date.setHours(23, 59, 59, 999) // End of day
      return date.toISOString()
    }

    return null
  }, [isTemporary, selectedDuration, customDate])

  // Format date for display
  const formattedDate = useMemo(() => {
    if (!expirationDate) return null
    return new Date(expirationDate).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }, [expirationDate])

  // Calculate min date (tomorrow)
  const minDate = useMemo(() => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }, [])

  const handleConfirm = () => {
    onConfirm(expirationDate)
    handleReset()
  }

  const handleReset = () => {
    setSelectedDuration(null)
    setCustomDate('')
    setIsTemporary(false)
  }

  const handleClose = () => {
    handleReset()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md mx-4 animate-in fade-in zoom-in-95">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-500" />
            Assignment Options
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Assignment Summary */}
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="text-sm text-slate-600">Assigning</div>
            <div className="font-medium text-slate-900">{supervisorName}</div>
            <div className="text-sm text-slate-600 mt-1">to</div>
            <div className="font-medium text-slate-900">{assetName}</div>
          </div>

          {/* Temporary Toggle */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsTemporary(!isTemporary)}
              className={`
                relative w-11 h-6 rounded-full transition-colors
                ${isTemporary ? 'bg-blue-500' : 'bg-slate-300'}
              `}
            >
              <span
                className={`
                  absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
                  ${isTemporary ? 'translate-x-5' : 'translate-x-0'}
                `}
              />
            </button>
            <label className="text-sm font-medium">
              Temporary Assignment
              {isTemporary && (
                <Badge variant="secondary" className="ml-2">
                  <Clock className="w-3 h-3 mr-1" />
                  Auto-reverts
                </Badge>
              )}
            </label>
          </div>

          {/* Duration Options (Task 8.1) */}
          {isTemporary && (
            <div className="space-y-3 animate-in slide-in-from-top-2">
              <div className="text-sm text-slate-600">Select duration:</div>

              {/* Preset Buttons */}
              <div className="flex flex-wrap gap-2">
                {DURATION_PRESETS.map((preset) => (
                  <button
                    key={preset.days}
                    type="button"
                    onClick={() => {
                      setSelectedDuration(preset.days)
                      setCustomDate('')
                    }}
                    className={`
                      px-3 py-1.5 rounded-full text-sm border transition-colors
                      ${
                        selectedDuration === preset.days && !customDate
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-slate-700 border-slate-300 hover:border-blue-500'
                      }
                    `}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>

              {/* Custom Date Input */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">or</span>
                <div className="relative flex-1">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="date"
                    value={customDate}
                    onChange={(e) => {
                      setCustomDate(e.target.value)
                      setSelectedDuration(null)
                    }}
                    min={minDate}
                    className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Pick a date"
                  />
                </div>
              </div>

              {/* Selected Date Preview (Task 8.3) */}
              {expirationDate && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
                  <Clock className="w-4 h-4 text-blue-500 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-blue-700">
                      Expires: {formattedDate}
                    </div>
                    <div className="text-xs text-blue-600 mt-0.5">
                      Assignment will automatically revert after this date
                    </div>
                  </div>
                </div>
              )}

              {/* Warning */}
              <div className="flex items-start gap-2 text-xs text-amber-600">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  The supervisor will lose access to this asset after the expiration date.
                  They will need to be re-assigned if continued access is needed.
                </span>
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex gap-2 pt-4 border-t">
          <Button variant="outline" className="flex-1" onClick={handleClose}>
            <X className="w-4 h-4 mr-1" />
            Cancel
          </Button>
          <Button
            className="flex-1"
            onClick={handleConfirm}
            disabled={isTemporary && !expirationDate}
          >
            <Check className="w-4 h-4 mr-1" />
            {isTemporary ? 'Add Temporary' : 'Add Permanent'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

/**
 * Visual indicator for temporary assignments in the grid (Task 8.2)
 */
interface TemporaryBadgeProps {
  expiresAt: string
  className?: string
}

export function TemporaryAssignmentBadge({ expiresAt, className }: TemporaryBadgeProps) {
  const { daysRemaining, isExpiringSoon } = useMemo(() => {
    const now = new Date()
    const expiry = new Date(expiresAt)
    const diffMs = expiry.getTime() - now.getTime()
    const days = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
    return {
      daysRemaining: Math.max(0, days),
      isExpiringSoon: days <= 7,
    }
  }, [expiresAt])

  const label = useMemo(() => {
    if (daysRemaining === 0) return 'Expires today'
    if (daysRemaining === 1) return '1 day left'
    return `${daysRemaining} days left`
  }, [daysRemaining])

  return (
    <Badge
      variant={isExpiringSoon ? 'destructive' : 'secondary'}
      className={className}
    >
      <Clock className="w-3 h-3 mr-1" />
      {label}
    </Badge>
  )
}
