'use client'

/**
 * Chat Trigger Component
 *
 * Floating action button to open the chat sidebar.
 * Fixed position at bottom-right for easy access from any page.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #1 - Can be triggered from anywhere in the application
 * @see AC #2 - Industrial Clarity Compliance (high-contrast visibility)
 * @see AC #8 - Keyboard Accessibility (focus states)
 */

import { MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface ChatTriggerProps {
  /** Callback when trigger is clicked */
  onClick: () => void
  /** Whether the chat is currently open */
  isOpen?: boolean
  /** Optional custom class name */
  className?: string
}

/**
 * Floating action button for opening the AI chat sidebar.
 * - Fixed position at bottom-right corner
 * - High-contrast styling for factory floor visibility
 * - Accessible with keyboard focus states
 */
export function ChatTrigger({ onClick, isOpen, className }: ChatTriggerProps) {
  return (
    <Button
      onClick={onClick}
      size="icon"
      className={cn(
        // Fixed positioning
        'fixed bottom-6 right-6 z-40',
        // Size: 56px for comfortable touch target
        'h-14 w-14 rounded-full',
        // High-contrast styling with info-blue (not safety-red)
        'bg-info-blue text-white shadow-lg',
        'hover:bg-info-blue-dark hover:shadow-xl',
        'active:scale-95',
        // Focus states for accessibility
        'focus-visible:ring-2 focus-visible:ring-info-blue focus-visible:ring-offset-2',
        // Transition for smooth interactions
        'transition-all duration-200',
        // Hide when chat is open
        isOpen && 'pointer-events-none opacity-0',
        className
      )}
      aria-label="Open AI chat assistant"
      aria-expanded={isOpen}
      aria-controls="chat-sidebar"
    >
      <MessageSquare className="h-6 w-6" />
    </Button>
  )
}
