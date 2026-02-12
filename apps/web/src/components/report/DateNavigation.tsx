'use client'

import { useState } from 'react'
import { CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react'
import { format, subDays, addDays, startOfDay } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

interface DateNavigationProps {
  date: Date
  onDateChange: (date: Date) => void
}

export function DateNavigation({ date, onDateChange }: DateNavigationProps) {
  const [open, setOpen] = useState(false)
  const yesterday = startOfDay(subDays(new Date(), 1))
  const isAtYesterday = startOfDay(date).getTime() >= yesterday.getTime()

  const handlePrevDay = () => {
    onDateChange(subDays(date, 1))
  }

  const handleNextDay = () => {
    if (!isAtYesterday) {
      onDateChange(addDays(date, 1))
    }
  }

  const handleCalendarSelect = (selected: Date | undefined) => {
    if (selected) {
      onDateChange(selected)
      setOpen(false)
    }
  }

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        onClick={handlePrevDay}
        aria-label="Previous day"
        className="h-8 w-8"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="gap-2 h-8 px-3 text-sm">
            <CalendarIcon className="h-4 w-4" />
            {format(date, 'MMM d, yyyy')}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={date}
            onSelect={handleCalendarSelect}
            disabled={(d) => startOfDay(d) > yesterday}
            defaultMonth={date}
          />
        </PopoverContent>
      </Popover>

      <Button
        variant="ghost"
        size="icon"
        onClick={handleNextDay}
        disabled={isAtYesterday}
        aria-label="Next day"
        className="h-8 w-8"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
