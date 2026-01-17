'use client';

/**
 * Handoff Detail Page (Story 9.5, Task 4)
 *
 * Displays full handoff details with voice note playback.
 *
 * @see Story 9.5 - Handoff Review UI
 * @see AC#2 - Handoff Detail View
 * @see AC#3 - Voice Note Playback
 * @see AC#4 - Tablet-Optimized Layout
 */

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { HandoffViewer } from '@/components/handoff/HandoffViewer';
import { useHandoff } from '@/hooks/useHandoff';
import { createClient } from '@/lib/supabase/client';

// ============================================================================
// Component
// ============================================================================

export default function HandoffDetailPage() {
  const router = useRouter();
  const params = useParams();
  const handoffId = params.id as string;

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  const {
    data: handoff,
    isLoading,
    error,
    canAcknowledge,
    refetch,
  } = useHandoff({ handoffId });

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
          router.push(`/login?redirect=/handoff/${handoffId}`);
          return;
        }

        setIsAuthenticated(true);
      } catch (err) {
        console.error('Auth error:', err);
        router.push(`/login?redirect=/handoff/${handoffId}`);
      } finally {
        setAuthLoading(false);
      }
    }

    checkAuth();
  }, [router, handoffId]);

  // Handle acknowledge (placeholder for Story 9.7)
  const handleAcknowledge = () => {
    // Story 9.7 will implement acknowledgment flow
    // After implementation, call refetch() to update UI
  };

  // Handle back navigation
  const handleBack = () => {
    router.push('/handoff');
  };

  // Loading state
  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground">
            {authLoading ? 'Loading...' : 'Loading handoff...'}
          </p>
        </div>
      </div>
    );
  }

  // Not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card">
          <div className="container mx-auto px-4 py-4">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="min-h-[44px]"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Handoffs
            </Button>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-lg mx-auto text-center">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-destructive"
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
            </div>
            <h1 className="text-2xl font-semibold mb-2">Unable to Load Handoff</h1>
            <p className="text-muted-foreground mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={handleBack}>
                Go Back
              </Button>
              <Button onClick={() => refetch()}>Try Again</Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // No handoff data
  if (!handoff) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card">
          <div className="container mx-auto px-4 py-4">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="min-h-[44px]"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Handoffs
            </Button>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-lg mx-auto text-center">
            <h1 className="text-2xl font-semibold mb-2">Handoff Not Found</h1>
            <p className="text-muted-foreground mb-6">
              This handoff may have been deleted or you may not have access.
            </p>
            <Button onClick={handleBack}>Go Back</Button>
          </div>
        </main>
      </div>
    );
  }

  // Main content
  return (
    <div className="min-h-screen bg-background">
      {/* Page header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="min-h-[44px]"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Handoffs
          </Button>
        </div>
      </header>

      {/* Handoff viewer */}
      <main className="container mx-auto max-w-4xl">
        <HandoffViewer
          handoff={handoff}
          canAcknowledge={canAcknowledge}
          onAcknowledge={handleAcknowledge}
        />
      </main>
    </div>
  );
}
