'use client'

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

interface ShiftTabsProps {
  value: string
  onValueChange: (value: string) => void
  className?: string
}

const SHIFT_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'morning', label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'night', label: 'Night' },
] as const

export function ShiftTabs({ value, onValueChange, className }: ShiftTabsProps) {
  return (
    <Tabs value={value} onValueChange={onValueChange} className={cn(className)}>
      <TabsList aria-label="Filter by shift">
        {SHIFT_OPTIONS.map(option => (
          <TabsTrigger key={option.value} value={option.value}>
            {option.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}
