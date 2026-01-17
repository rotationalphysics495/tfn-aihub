'use client';

/**
 * Handoff List Page (Story 9.5, Task 1)
 *
 * Displays list of handoffs with notification banner for pending handoffs.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#1 - Handoff Notification Banner
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Bell, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { HandoffList } from '@/components/handoff/HandoffList';
import { useHandoffList } from '@/hooks/useHandoffList';
import { createClient } from '@/lib/supabase/client';
import { cn } from '@/lib/utils';

// ============================================================================
// Component
// ============================================================================

export default function HandoffListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const createdId = searchParams.get('created');

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [showCreatedBanner, setShowCreatedBanner] = useState(!!createdId);

  const {
    data: handoffs,
    isLoading,
    error,
    pendingCount,
    hasPending,
    refetch,
  } = useHandoffList();

  // Check authentication
  useEffect(() => {
    async function checkAuth() {
      try {
        const supabase = createClient();
        const {
          data: { user },
          error: authError,
        } = await supabase.auth.getUser();

        if (authError || !user) {
          router.push('/login?redirect=/handoff');
          return;
        }

        setIsAuthenticated(true);
      } catch (err) {
        console.error('Auth error:', err);
        router.push('/login?redirect=/handoff');
      } finally {
        setAuthLoading(false);
      }
    }

    checkAuth();
  }, [router]);

  // Dismiss created banner after delay
  useEffect(() => {
    if (createdId) {
      const timer = setTimeout(() => {
        setShowCreatedBanner(false);
        // Remove query param from URL
        router.replace('/handoff', { scroll: false });
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [createdId, router]);

  // Loading state
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Page header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-6 md:py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">
                Shift Handoffs
              </h1>
              <p className="text-base text-muted-foreground mt-1">
                Review handoffs from previous shifts
              </p>
            </div>

            <Button
              onClick={() => router.push('/handoff/new')}
              size="lg"
              className="min-h-[44px]"
            >
              <Plus className="w-5 h-5 mr-2" />
              Create Handoff
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 md:py-8">
        {/* Created success banner */}
        {showCreatedBanner && (
          <div
            className={cn(
              'mb-6 p-4 rounded-lg bg-success-green-light border border-success-green',
              'flex items-center justify-between',
              'dark:bg-success-green-dark/20 dark:border-success-green'
            )}
          >
            <div className="flex items-center gap-3">
              <svg
                className="w-5 h-5 text-success-green"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span className="font-medium text-success-green-dark dark:text-success-green">
                Handoff created successfully
              </span>
            </div>
            <button
              onClick={() => setShowCreatedBanner(false)}
              className="p-1 hover:bg-success-green/20 rounded"
              aria-label="Dismiss"
            >
              <svg
                className="w-4 h-4 text-success-green-dark dark:text-success-green"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}

        {/* Pending notification banner - AC#1 */}
        {hasPending && !showCreatedBanner && (
          <div
            className={cn(
              'mb-6 p-4 rounded-lg bg-info-blue-light border border-info-blue',
              'flex items-center gap-3',
              'dark:bg-info-blue-dark/20 dark:border-info-blue'
            )}
          >
            <Bell className="w-5 h-5 text-info-blue flex-shrink-0" />
            <span className="font-medium text-info-blue-dark dark:text-info-blue">
              {pendingCount === 1
                ? 'You have 1 handoff awaiting review'
                : `You have ${pendingCount} handoffs awaiting review`}
            </span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive">
            <p className="font-medium">Error loading handoffs</p>
            <p className="text-sm mt-1">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="mt-3"
            >
              Try again
            </Button>
          </div>
        )}

        {/* Handoff list */}
        <HandoffList
          handoffs={handoffs || []}
          showSections
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
