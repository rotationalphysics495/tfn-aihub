'use client'

/**
 * AreaOrderSelector Component (Story 8.8)
 *
 * AC#2 - Step 4: Area order preference (drag-to-reorder or numbered selection)
 * - Implement drag-and-drop reordering (using native HTML5 DnD)
 * - Add numbered input fallback for accessibility
 * - Display all 7 production areas with default order
 * - Update state on order change
 *
 * The 7 production areas (from PRD):
 * 1. Packing - CAMA lines, Pack Cells, Variety Pack, Bag Lines, Nuspark
 * 2. Rychigers - 101-109, 1009
 * 3. Grinding - Grinders 1-5
 * 4. Powder - 1002-1004 Fill & Pack, Manual Bulk
 * 5. Roasting - Roasters 1-4
 * 6. Green Bean - Manual, Silo Transfer
 * 7. Flavor Room - Coffee Flavor Room (Manual)
 *
 * References:
 * - [Source: architecture/voice-briefing.md#User Preferences Architecture]
 * - [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
 */

import { useState, useCallback } from 'react'
import { cn } from '@/lib/utils'

export const DEFAULT_AREA_ORDER = [
  'Packing',
  'Rychigers',
  'Grinding',
  'Powder',
  'Roasting',
  'Green Bean',
  'Flavor Room',
]

export const AREA_DESCRIPTIONS: Record<string, string> = {
  'Packing': 'CAMA lines, Pack Cells, Variety Pack, Bag Lines, Nuspark',
  'Rychigers': '101-109, 1009',
  'Grinding': 'Grinders 1-5',
  'Powder': '1002-1004 Fill & Pack, Manual Bulk',
  'Roasting': 'Roasters 1-4',
  'Green Bean': 'Manual, Silo Transfer',
  'Flavor Room': 'Coffee Flavor Room (Manual)',
}

interface AreaOrderSelectorProps {
  /** Current area order */
  value: string[]
  /** Called when order changes */
  onChange: (newOrder: string[]) => void
  /** Optional CSS class name */
  className?: string
  /** Whether in compact mode for settings page */
  compact?: boolean
}

export function AreaOrderSelector({
  value,
  onChange,
  className,
  compact = false,
}: AreaOrderSelectorProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  // Use provided value or default
  const areas = value.length > 0 ? value : DEFAULT_AREA_ORDER

  const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', index.toString())
    // Add a slight delay to show visual feedback
    const target = e.target as HTMLElement
    setTimeout(() => {
      target.style.opacity = '0.5'
    }, 0)
  }, [])

  const handleDragEnd = useCallback((e: React.DragEvent) => {
    const target = e.target as HTMLElement
    target.style.opacity = '1'
    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverIndex(index)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, dropIndex: number) => {
    e.preventDefault()
    const dragIndex = parseInt(e.dataTransfer.getData('text/plain'), 10)

    if (dragIndex === dropIndex) return

    const newAreas = [...areas]
    const [removed] = newAreas.splice(dragIndex, 1)
    newAreas.splice(dropIndex, 0, removed)
    onChange(newAreas)

    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [areas, onChange])

  const handleMoveUp = useCallback((index: number) => {
    if (index === 0) return
    const newAreas = [...areas]
    ;[newAreas[index - 1], newAreas[index]] = [newAreas[index], newAreas[index - 1]]
    onChange(newAreas)
  }, [areas, onChange])

  const handleMoveDown = useCallback((index: number) => {
    if (index === areas.length - 1) return
    const newAreas = [...areas]
    ;[newAreas[index], newAreas[index + 1]] = [newAreas[index + 1], newAreas[index]]
    onChange(newAreas)
  }, [areas, onChange])

  return (
    <div className={cn('space-y-3', className)}>
      <div className="text-sm text-muted-foreground">
        Drag to reorder or use the arrows. Areas at the top will be covered first in your briefings.
      </div>
      <div className="space-y-2">
        {areas.map((area, index) => {
          const isDragged = draggedIndex === index
          const isDragOver = dragOverIndex === index && draggedIndex !== index
          const description = AREA_DESCRIPTIONS[area]

          return (
            <div
              key={area}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg border transition-all',
                'bg-card hover:bg-accent/50 cursor-move',
                isDragged && 'opacity-50',
                isDragOver && 'border-primary border-2',
                !isDragged && !isDragOver && 'border-border'
              )}
            >
              {/* Drag handle */}
              <div
                className="flex-shrink-0 text-muted-foreground touch-target"
                aria-hidden="true"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 8h16M4 16h16"
                  />
                </svg>
              </div>

              {/* Position number */}
              <div
                className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium',
                  index === 0
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                )}
              >
                {index + 1}
              </div>

              {/* Area info */}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{area}</p>
                {!compact && description && (
                  <p className="text-xs text-muted-foreground truncate">{description}</p>
                )}
              </div>

              {/* Keyboard navigation arrows */}
              <div className="flex flex-col gap-1 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => handleMoveUp(index)}
                  disabled={index === 0}
                  className={cn(
                    'p-1 rounded hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring',
                    'disabled:opacity-30 disabled:cursor-not-allowed'
                  )}
                  aria-label={`Move ${area} up`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={() => handleMoveDown(index)}
                  disabled={index === areas.length - 1}
                  className={cn(
                    'p-1 rounded hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring',
                    'disabled:opacity-30 disabled:cursor-not-allowed'
                  )}
                  aria-label={`Move ${area} down`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AreaOrderSelector
