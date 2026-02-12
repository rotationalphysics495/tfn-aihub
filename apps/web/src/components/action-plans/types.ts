'use client'

export type ActionPlanStatus = 'open' | 'in_progress' | 'completed' | 'verified'
export type ActionPlanPriority = 'low' | 'medium' | 'high' | 'critical'

export interface ActionPlan {
  id: string
  title: string
  description: string | null
  asset_id: string | null
  asset_name: string | null
  category: string
  root_cause: string | null
  corrective_action: string | null
  preventive_action: string | null
  source_followup_id: string | null
  owner_id: string
  owner_email: string
  status: ActionPlanStatus
  priority: ActionPlanPriority
  due_date: string | null
  completed_at: string | null
  verified_by: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

export interface ActionPlanUpdate {
  id: string
  action_plan_id: string
  author_id: string
  author_email: string
  update_text: string | null
  status_change: string | null
  created_at: string
}

export interface ActionPlanListResponse {
  plans: ActionPlan[]
  total_count: number
  counts_by_status: Record<string, number>
}

export interface GroupedPlans {
  open: ActionPlan[]
  in_progress: ActionPlan[]
  completed: ActionPlan[]
  verified: ActionPlan[]
}

export interface DueStatus {
  label: string
  variant: 'overdue' | 'due-soon' | 'on-track' | null
}

export function groupPlans(plans: ActionPlan[]): GroupedPlans {
  return {
    open: plans.filter(p => p.status === 'open'),
    in_progress: plans.filter(p => p.status === 'in_progress'),
    completed: plans.filter(p => p.status === 'completed'),
    verified: plans.filter(p => p.status === 'verified'),
  }
}

export function getDueStatus(dueDate: string | null, status: string): DueStatus {
  if (!dueDate) return { label: '', variant: null }
  if (['completed', 'verified'].includes(status)) return { label: '', variant: null }

  const due = new Date(dueDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  due.setHours(0, 0, 0, 0)

  const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    const absDays = Math.abs(diffDays)
    return { label: `${absDays} day${absDays !== 1 ? 's' : ''} overdue`, variant: 'overdue' }
  }
  if (diffDays <= 3) {
    return { label: `Due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`, variant: 'due-soon' }
  }
  return { label: `Due in ${diffDays} days`, variant: 'on-track' }
}

export function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
