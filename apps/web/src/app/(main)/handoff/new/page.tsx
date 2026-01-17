'use client'

/**
 * Create Handoff Page (Story 9.1, Task 5)
 *
 * Page for creating a new shift handoff.
 * Protected route - only accessible to Supervisor role.
 *
 * AC#1: Create handoff flow with pre-populated assets and auto-detected shift
 * AC#2: Handoff screen with summary, notes, and confirmation
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
 */

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { HandoffCreator } from '@/components/handoff/HandoffCreator'
import { createClient } from '@/lib/supabase/client'

export default function CreateHandoffPage() {
  const router = useRouter()
  const [userId, setUserId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check authentication and get user ID
  useEffect(() => {
    async function checkAuth() {
      try {
        const supabase = createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()

        if (authError || !user) {
          // Redirect to login
          router.push('/login?redirect=/handoff/new')
          return
        }

        setUserId(user.id)
      } catch (err) {
        console.error('Auth error:', err)
        setError('Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [router])

  // Handle successful handoff creation
  const handleComplete = useCallback((handoffId: string) => {
    // Redirect to the handoff details or list page
    // For now, redirect to dashboard with success message
    router.push(`/handoff?created=${handoffId}`)
  }, [router])

  // Handle cancel
  const handleCancel = useCallback(() => {
    router.back()
  }, [router])

  // Handle redirect to edit existing handoff
  const handleEditExisting = useCallback((handoffId: string) => {
    router.push(`/handoff/${handoffId}/edit`)
  }, [router])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !userId) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-2">Error</h1>
          <p className="text-muted-foreground mb-4">
            {error || 'Unable to load user information'}
          </p>
          <button
            onClick={() => router.push('/')}
            className="text-primary hover:underline"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // Main content
  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        <HandoffCreator
          userId={userId}
          onComplete={handleComplete}
          onCancel={handleCancel}
          onEditExisting={handleEditExisting}
        />
      </div>
    </div>
  )
}
