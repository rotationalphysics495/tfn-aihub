'use client'

/**
 * SupervisorAssetsStep Component (Story 8.8)
 *
 * Step 3 of the onboarding flow: Display assigned assets for supervisors.
 *
 * AC#2 - Step 3: For Supervisor: display assigned assets (from supervisor_assignments)
 * - Fetch assigned assets from supervisor_assignments table
 * - Display read-only list of assigned assets/areas
 * - Handle case when no assets are assigned
 * - Only render for Supervisor role
 *
 * Dependencies:
 * - Story 8.5 (Supervisor Scoped Briefings) for supervisor_assignments table
 * - Gracefully handles missing table by showing "No assets assigned yet" message
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Role-Based Access Control]
 * - [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
 */

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { createClient } from '@/lib/supabase/client'

interface SupervisedAsset {
  id: string
  name: string
  area?: string
}

interface SupervisorAssetsStepProps {
  /** User ID for fetching assignments */
  userId: string
  /** Called when user clicks Back */
  onBack: () => void
  /** Called when user clicks Continue */
  onContinue: () => void
  /** Optional CSS class name */
  className?: string
}

export function SupervisorAssetsStep({
  userId,
  onBack,
  onContinue,
  className,
}: SupervisorAssetsStepProps) {
  const [assets, setAssets] = useState<SupervisedAsset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAssignedAssets() {
      setIsLoading(true)
      setError(null)

      try {
        const supabase = createClient()

        // Fetch supervisor assignments with asset details
        const { data, error: fetchError } = await supabase
          .from('supervisor_assignments')
          .select(`
            asset_id,
            assets (
              id,
              name,
              area
            )
          `)
          .eq('user_id', userId)

        if (fetchError) {
          // If table doesn't exist, show graceful message
          if (fetchError.code === '42P01') {
            setAssets([])
            setIsLoading(false)
            return
          }
          throw fetchError
        }

        // Transform data - Supabase returns assets as a single object (not array) for single relation
        interface AssignmentRow {
          asset_id: string
          assets: { id: string; name: string; area?: string } | null
        }

        const assignedAssets: SupervisedAsset[] = ((data || []) as AssignmentRow[])
          .filter((d) => d.assets !== null)
          .map((d) => ({
            id: d.assets!.id,
            name: d.assets!.name,
            area: d.assets!.area,
          }))

        setAssets(assignedAssets)
      } catch (err) {
        console.error('Error fetching supervisor assignments:', err)
        setError('Unable to load your assigned assets')
        setAssets([])
      } finally {
        setIsLoading(false)
      }
    }

    if (userId) {
      fetchAssignedAssets()
    }
  }, [userId])

  return (
    <Card className={cn('w-full max-w-lg mx-auto', className)}>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Your Assigned Assets</CardTitle>
        <CardDescription>
          Your briefings will focus on these assets
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm text-muted-foreground">Loading your assignments...</p>
          </div>
        ) : error ? (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 text-center">
            <svg
              className="w-8 h-8 mx-auto mb-2 text-destructive"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-sm text-destructive">{error}</p>
            <p className="text-xs text-muted-foreground mt-1">
              You can continue and update this later in Settings.
            </p>
          </div>
        ) : assets.length === 0 ? (
          <div className="bg-muted/50 rounded-lg p-6 text-center">
            <svg
              className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <h3 className="font-medium mb-1">No assets assigned yet</h3>
            <p className="text-sm text-muted-foreground">
              Your administrator will configure your assignments.
              <br />
              Until then, you&apos;ll see an overview of all areas.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              {assets.length} asset{assets.length !== 1 ? 's' : ''} assigned to you:
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2 border rounded-lg p-3">
              {assets.map((asset) => (
                <div
                  key={asset.id}
                  className="flex items-center gap-3 p-3 bg-muted/30 rounded-md"
                >
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <svg
                      className="w-5 h-5 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                      />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{asset.name}</p>
                    {asset.area && (
                      <p className="text-sm text-muted-foreground truncate">{asset.area}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground text-center">
              Contact your administrator to update your assignments
            </p>
          </div>
        )}

        <div className="flex gap-3 pt-4">
          <Button variant="outline" onClick={onBack} className="flex-1 touch-target">
            Back
          </Button>
          <Button onClick={onContinue} className="flex-1 touch-target">
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default SupervisorAssetsStep
