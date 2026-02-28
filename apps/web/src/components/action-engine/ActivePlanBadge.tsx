'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ClipboardList } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useActiveActionPlans } from '@/hooks/useActiveActionPlans'

interface ActivePlanBadgeProps {
  assetId: string
  className?: string
}

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ')
}

export function ActivePlanBadge({ assetId, className }: ActivePlanBadgeProps) {
  const { plans, isLoading, error } = useActiveActionPlans(assetId || undefined)
  const router = useRouter()
  const [showDetails, setShowDetails] = useState(false)

  if (!assetId) return null

  if (isLoading) {
    return (
      <div
        data-testid="active-plan-badge-loading"
        role="status"
        className="inline-flex items-center h-5 w-24 animate-pulse rounded-md bg-muted"
      />
    )
  }

  if (error || plans.length === 0) return null

  // Single plan badge
  if (plans.length === 1) {
    const plan = plans[0]
    return (
      <Badge
        variant="info"
        className={cn('gap-1.5 cursor-pointer', className)}
        role="link"
        aria-label={`Action plan: ${plan.title}, ${formatStatus(plan.status)}, due ${plan.due_date}`}
        onClick={(e) => {
          e.stopPropagation()
          router.push(`/action-plans?plan=${plan.id}`)
        }}
      >
        <ClipboardList className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
        <span>{plan.title}</span>
        <span aria-hidden="true">&middot;</span>
        <span>due {plan.due_date}</span>
        <span aria-hidden="true">&middot;</span>
        <span>{formatStatus(plan.status)}</span>
      </Badge>
    )
  }

  // Multiple plans badge
  const count = plans.length
  return (
    <div className={cn('relative inline-flex', className)}>
      <Badge
        variant="info"
        className="gap-1.5 cursor-pointer"
        role="link"
        aria-label={`${count} active action plans for this asset`}
        onClick={(e) => {
          e.stopPropagation()
          setShowDetails((prev) => !prev)
        }}
      >
        <ClipboardList className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
        <span>{count} active plans</span>
      </Badge>
      {showDetails && (
        <div className="absolute top-full left-0 mt-1 z-50 rounded-md border bg-popover p-2 text-sm shadow-md min-w-[200px]">
          <ul className="space-y-1">
            {plans.map((plan) => (
              <li key={plan.id}>
                <button
                  type="button"
                  className="w-full text-left px-2 py-1 rounded hover:bg-muted text-popover-foreground"
                  onClick={(e) => {
                    e.stopPropagation()
                    router.push(`/action-plans?plan=${plan.id}`)
                  }}
                >
                  {plan.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
