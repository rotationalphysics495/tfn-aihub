'use client'

import { useCallback } from 'react'
import { Presentation } from 'lucide-react'
import { Toggle } from '@/components/ui/toggle'
import { cn } from '@/lib/utils'

interface MeetingModeToggleProps {
  pressed: boolean
  onToggle: (pressed: boolean) => void
  className?: string
}

export function MeetingModeToggle({ pressed, onToggle, className }: MeetingModeToggleProps) {
  const handlePressedChange = useCallback(
    (newPressed: boolean) => {
      onToggle(newPressed)
    },
    [onToggle]
  )

  return (
    <Toggle
      pressed={pressed}
      onPressedChange={handlePressedChange}
      variant="outline"
      size="lg"
      className={cn(
        'text-base font-medium gap-2',
        'data-[state=on]:bg-primary data-[state=on]:text-primary-foreground',
        className
      )}
      aria-label="Meeting Mode"
    >
      <Presentation className="w-5 h-5" aria-hidden="true" />
      <span>Meeting Mode</span>
    </Toggle>
  )
}
