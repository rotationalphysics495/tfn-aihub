'use client'

import { useMemo } from 'react'
import { MeetingTalkingPoint } from '@/components/action-list/MeetingTalkingPoint'
import { cn } from '@/lib/utils'
import type { ActionItem, FollowUpData } from '@/components/action-engine/types'

const MAX_ITEMS = 5

const PRIORITY_ORDER: Record<string, number> = {
  SAFETY: 0,
  FINANCIAL: 1,
  OEE: 2,
}

const CATEGORY_MAP: Record<string, string> = {
  SAFETY: 'safety',
  FINANCIAL: 'financial',
  OEE: 'oee',
}

interface Section {
  key: string
  title: string
  categories: string[]
}

const SECTIONS: Section[] = [
  { key: 'safety', title: 'Safety', categories: ['safety'] },
  { key: 'performance', title: "Yesterday's Performance", categories: ['oee'] },
  { key: 'priorities', title: "Today's Priorities", categories: ['financial'] },
]

interface MeetingModeViewProps {
  items: ActionItem[]
  followUps?: Map<string, FollowUpData>
  reportDate?: string
  onAssign?: (item: ActionItem) => void
  className?: string
}

export function MeetingModeView({ items, followUps, reportDate, onAssign, className }: MeetingModeViewProps) {
  const topItems = useMemo(() => {
    const sorted = [...items].sort((a, b) => {
      // Primary sort: priorityScore descending (highest urgency first)
      if (b.priorityScore !== a.priorityScore) return b.priorityScore - a.priorityScore
      // Secondary sort: category order (SAFETY > FINANCIAL > OEE)
      const orderA = PRIORITY_ORDER[a.priority] ?? 2
      const orderB = PRIORITY_ORDER[b.priority] ?? 2
      return orderA - orderB
    })
    return sorted.slice(0, MAX_ITEMS)
  }, [items])

  const groupedSections = useMemo(() => {
    return SECTIONS.map((section) => {
      const sectionItems = topItems.filter((item) => {
        const category = CATEGORY_MAP[item.priority] || 'financial'
        return section.categories.includes(category)
      })
      return { ...section, items: sectionItems }
    })
  }, [topItems])

  return (
    <div className={cn('space-y-6', className)}>
      {groupedSections.map((section) => (
        <div key={section.key}>
          <h2 className="text-xl md:text-2xl font-bold text-foreground mb-3">
            {section.title}
          </h2>
          {section.items.length === 0 ? (
            <p className="text-base text-muted-foreground">No items</p>
          ) : (
            <div className="space-y-3">
              {section.items.map((item) => (
                <MeetingTalkingPoint
                  key={item.id}
                  item={item}
                  followUp={followUps?.get(item.id)}
                  reportDate={reportDate}
                  onAssign={onAssign}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
