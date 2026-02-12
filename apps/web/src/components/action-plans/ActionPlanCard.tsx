'use client'

import { Calendar, User } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getDueStatus } from './types'
import type { ActionPlan, ActionPlanStatus, ActionPlanPriority } from './types'

interface ActionPlanCardProps {
  plan: ActionPlan
  onClick?: (plan: ActionPlan) => void
  hideStatusBadge?: boolean
}

const STATUS_CONFIG: Record<ActionPlanStatus, { label: string; className: string }> = {
  open: {
    label: 'Open',
    className: 'text-blue-600 bg-blue-100 border-blue-200 dark:text-blue-400 dark:bg-blue-900/30',
  },
  in_progress: {
    label: 'In Progress',
    className: 'text-amber-600 bg-amber-100 border-amber-200 dark:text-amber-400 dark:bg-amber-900/30',
  },
  completed: {
    label: 'Completed',
    className: 'text-green-600 bg-green-100 border-green-200 dark:text-green-400 dark:bg-green-900/30',
  },
  verified: {
    label: 'Verified',
    className: 'text-emerald-600 bg-emerald-100 border-emerald-200 dark:text-emerald-400 dark:bg-emerald-900/30',
  },
}

const PRIORITY_CONFIG: Record<ActionPlanPriority, { className: string }> = {
  critical: {
    className: 'text-red-600 bg-red-100 border-red-200 dark:text-red-400 dark:bg-red-900/30',
  },
  high: {
    className: 'text-amber-600 bg-amber-100 border-amber-200 dark:text-amber-400 dark:bg-amber-900/30',
  },
  medium: {
    className: 'text-yellow-600 bg-yellow-100 border-yellow-200 dark:text-yellow-400 dark:bg-yellow-900/30',
  },
  low: {
    className: 'text-blue-600 bg-blue-100 border-blue-200 dark:text-blue-400 dark:bg-blue-900/30',
  },
}

function formatDueDate(dueDate: string): string {
  const date = new Date(dueDate + 'T00:00:00')
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function ActionPlanCard({ plan, onClick, hideStatusBadge }: ActionPlanCardProps) {
  const statusConfig = STATUS_CONFIG[plan.status]
  const priorityConfig = PRIORITY_CONFIG[plan.priority]
  const dueStatus = getDueStatus(plan.due_date, plan.status)
  const isOverdue = dueStatus.variant === 'overdue'

  return (
    <Card
      className={cn(
        'cursor-pointer hover:shadow-md transition-shadow',
        isOverdue && 'border-red-300 bg-red-50/50 dark:border-red-800 dark:bg-red-950/20'
      )}
      onClick={() => onClick?.(plan)}
      role="button"
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-medium text-sm leading-tight">{plan.title}</h3>
          {!hideStatusBadge && (
            <Badge className={cn('shrink-0 text-xs', statusConfig.className)}>
              {statusConfig.label}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2 mb-2">
          <Badge className={cn('text-xs', priorityConfig.className)}>
            {plan.priority}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {plan.asset_id ? (plan.asset_name || plan.asset_id) : 'Plant-wide'}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <User className="w-3 h-3" />
            {plan.owner_email || plan.owner_id}
          </span>
          {plan.due_date && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDueDate(plan.due_date)}
            </span>
          )}
        </div>

        {dueStatus.label && (
          <div className="mt-2">
            {dueStatus.variant === 'overdue' && (
              <span className="text-xs font-medium text-destructive text-red-600">
                {dueStatus.label}
              </span>
            )}
            {dueStatus.variant === 'due-soon' && (
              <span className="text-xs font-medium text-amber-600 text-warning">
                {dueStatus.label}
              </span>
            )}
            {dueStatus.variant === 'on-track' && (
              <span className="text-xs text-muted-foreground">
                {dueStatus.label}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
