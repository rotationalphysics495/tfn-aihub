'use client'

/**
 * Chat Input Component
 *
 * Text input with send button for submitting natural language queries.
 * Features auto-expanding textarea and keyboard shortcuts.
 *
 * @see Story 4.3 - Chat Sidebar UI
 * @see AC #4 - Input Interface (text input with send button)
 * @see AC #8 - Keyboard Accessibility (Enter to send, Shift+Enter for newline)
 */

import { useRef, useEffect, useCallback, forwardRef, type KeyboardEvent, type ChangeEvent } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  /** Current input value */
  value: string
  /** Callback when input value changes */
  onChange: (value: string) => void
  /** Callback when message is submitted */
  onSubmit: () => void
  /** Whether input is disabled (e.g., while loading) */
  disabled?: boolean
  /** Optional custom class name */
  className?: string
}

/**
 * Chat input with auto-expanding textarea and send button.
 * - Enter submits the message
 * - Shift+Enter creates a new line
 * - Auto-expands up to max height
 * - Focus on mount when in sidebar
 */
export const ChatInput = forwardRef<HTMLTextAreaElement, ChatInputProps>(
  function ChatInput({ value, onChange, onSubmit, disabled, className }, ref) {
    const textareaRef = useRef<HTMLTextAreaElement | null>(null)
    const minHeight = 44 // Minimum touch target size
    const maxHeight = 120 // Maximum expanded height

    // Merge forwarded ref with internal ref
    const setRefs = useCallback(
      (element: HTMLTextAreaElement | null) => {
        textareaRef.current = element
        if (typeof ref === 'function') {
          ref(element)
        } else if (ref) {
          ref.current = element
        }
      },
      [ref]
    )

    // Auto-resize textarea based on content
    const adjustHeight = useCallback(() => {
      const textarea = textareaRef.current
      if (!textarea) return

      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'

      // Calculate new height, clamped between min and max
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
      textarea.style.height = `${newHeight}px`
    }, [])

    // Adjust height when value changes
    useEffect(() => {
      adjustHeight()
    }, [value, adjustHeight])

    // Handle input changes
    const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value)
    }

    // Handle keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter without Shift submits
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (value.trim() && !disabled) {
          onSubmit()
        }
      }
      // Shift+Enter creates newline (default behavior)
    }

    // Handle send button click
    const handleSendClick = () => {
      if (value.trim() && !disabled) {
        onSubmit()
        // Refocus textarea after sending
        textareaRef.current?.focus()
      }
    }

    const canSubmit = value.trim().length > 0 && !disabled

    return (
      <div
        className={cn(
          'flex items-end gap-2 border-t border-industrial-200 bg-background p-4 dark:border-industrial-700',
          className
        )}
      >
        <Textarea
          ref={setRefs}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about factory data..."
          disabled={disabled}
          rows={1}
          className={cn(
            'min-h-[44px] max-h-[120px] resize-none py-3',
            'text-base', // Minimum 16px for readability
            'focus-visible:ring-1 focus-visible:ring-info-blue'
          )}
          aria-label="Type your message"
          style={{ height: `${minHeight}px` }}
        />

        <Button
          onClick={handleSendClick}
          disabled={!canSubmit}
          size="icon"
          className={cn(
            'h-11 w-11 shrink-0', // 44px touch target
            'bg-info-blue hover:bg-info-blue-dark',
            'disabled:bg-industrial-200 disabled:text-industrial-400',
            'dark:disabled:bg-industrial-700 dark:disabled:text-industrial-500'
          )}
          aria-label="Send message"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    )
  }
)
