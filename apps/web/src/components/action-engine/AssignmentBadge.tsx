'use client'

import { User, Clock, CheckCircle2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { FollowUpData } from './types'

const STATUS_CONFIG: Record<
  FollowUpData['status'],
  { variant: 'info' | 'warning' | 'success'; label: string; Icon: typeof User }
> = {
  assigned: { variant: 'info', label: 'Assigned', Icon: User },
  in_progress: { variant: 'warning', label: 'In Progress', Icon: Clock },
  resolved: { variant: 'success', label: 'Resolved', Icon: CheckCircle2 },
}

interface AssignmentBadgeProps {
  followUp: FollowUpData
  className?: string
}

export function AssignmentBadge({ followUp, className }: AssignmentBadgeProps) {
  const config = STATUS_CONFIG[followUp.status]

  return (
    <Badge
      variant={config.variant}
      className={cn('gap-1.5', className)}
      aria-label={`Assigned to ${followUp.assignee_email}, status: ${followUp.status}`}
    >
      <config.Icon className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
      <span>{followUp.assignee_email}</span>
      <span aria-hidden="true">&middot;</span>
      <span>{config.label}</span>
    </Badge>
  )
}
