'use client'

import { Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import type { FollowUpMessage } from '@/hooks/useFollowUpMessages'

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

const MESSAGE_TYPE_CONFIG: Record<string, { label: string; className: string }> = {
  assignment: { label: 'Assignment', className: 'bg-blue-100 text-blue-800 border-blue-200' },
  response: { label: 'Response', className: 'bg-green-100 text-green-800 border-green-200' },
  status_update: { label: 'Status Update', className: 'bg-gray-100 text-gray-800 border-gray-200' },
  escalation: { label: 'Escalation', className: 'bg-red-100 text-red-800 border-red-200' },
}

function formatStatusText(status: string): string {
  return status.replace(/_/g, '-')
}

function getMessageLabel(
  message: FollowUpMessage,
  assigneeName: string
): string {
  if (message.message_type === 'status_update') {
    return `${message.sender_email} marked as ${formatStatusText(message.body)} at ${formatRelativeTime(message.sent_at)}`
  }
  if (message.direction === 'outbound') {
    return `Sent to ${assigneeName}`
  }
  return `${message.sender_email} replied at ${formatRelativeTime(message.sent_at)}`
}

interface MessageThreadProps {
  messages: FollowUpMessage[]
  assignee_name: string
  loading?: boolean
}

export function MessageThread({ messages, assignee_name, loading }: MessageThreadProps) {
  const hasInbound = messages.some(m => m.direction === 'inbound')

  return (
    <ScrollArea className="max-h-[400px]">
      <div
        role="log"
        aria-label="Message thread"
        className="space-y-3 p-1"
      >
        {loading ? (
          <div data-testid="message-thread-skeleton" className="space-y-3 animate-pulse">
            <div className="h-20 bg-muted rounded-md" />
            <div className="h-16 bg-muted rounded-md" />
            <div className="h-20 bg-muted rounded-md" />
          </div>
        ) : (
          <>
            {messages.map((message) => {
              const isOutbound = message.direction === 'outbound'
              const typeConfig = MESSAGE_TYPE_CONFIG[message.message_type] || MESSAGE_TYPE_CONFIG.assignment
              const label = getMessageLabel(message, assignee_name)
              const relativeTime = formatRelativeTime(message.sent_at)

              return (
                <div
                  key={message.id}
                  data-message-id={message.id}
                  data-direction={message.direction}
                  aria-label={`${message.sender_email} at ${relativeTime}`}
                  className={cn(
                    'flex',
                    isOutbound ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      'max-w-[80%] rounded-lg p-3 space-y-1',
                      isOutbound
                        ? 'bg-industrial-100 ml-auto'
                        : 'bg-card border mr-auto'
                    )}
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border', typeConfig.className)}>
                        {typeConfig.label}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {relativeTime}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {label}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {message.sender_email}
                    </p>
                    {message.message_type !== 'status_update' && (
                      <p className="text-base mt-1">
                        {message.body}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}

            {!hasInbound && messages.length > 0 && (
              <div className="flex flex-col items-center justify-center py-4 text-muted-foreground">
                <Clock className="h-5 w-5 mb-2" />
                <p className="text-sm">Awaiting response from {assignee_name}</p>
              </div>
            )}
          </>
        )}
      </div>
    </ScrollArea>
  )
}
