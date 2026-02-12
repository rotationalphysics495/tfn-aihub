/**
 * InsightSection Shift Attribution Tests (Story 17.4)
 *
 * @see Story 17.4 - Shift Breakdown API & UI
 * @see AC #3 - Shift attribution badge display
 * @see AC #4 - No badge for systemic issues
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    prefetch: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/morning-report',
}))

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'test-token', user: { id: 'user-1' } } },
      }),
    },
  }),
}))

// Mock ActivePlanBadge to avoid API calls
vi.mock('../ActivePlanBadge', () => ({
  ActivePlanBadge: () => null,
}))

// Must import after mocks
import { InsightSection } from '../InsightSection'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const BASE_PROPS = {
  priority: 'OEE' as const,
  recommendation: { text: 'Review Grinder 5 — OEE 15% below target', summary: 'OEE gap' },
  asset: { id: 'asset-1', name: 'Grinder 5', area: 'Grinding' },
  financialImpact: 2500,
  timestamp: '2026-02-10T06:30:00Z',
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('InsightSection Shift Attribution', () => {
  it('17-4-UNIT-060: renders shift attribution badge when shiftAttribution is provided', () => {
    render(
      <InsightSection
        {...BASE_PROPS}
        shiftAttribution="afternoon shift — 58 min downtime"
      />
    )

    const badge = screen.getByTestId('shift-attribution-badge')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('afternoon shift — 58 min downtime')
  })

  it('17-4-UNIT-061: does not render shift badge when shiftAttribution is undefined', () => {
    render(<InsightSection {...BASE_PROPS} />)

    expect(screen.queryByTestId('shift-attribution-badge')).not.toBeInTheDocument()
  })

  it('17-4-UNIT-062: does not render shift badge when shiftAttribution is null', () => {
    render(<InsightSection {...BASE_PROPS} shiftAttribution={null} />)

    expect(screen.queryByTestId('shift-attribution-badge')).not.toBeInTheDocument()
  })

  it('17-4-UNIT-063: badge text matches the shiftAttribution prop value', () => {
    render(
      <InsightSection
        {...BASE_PROPS}
        shiftAttribution="night shift — 70 min downtime"
      />
    )

    expect(screen.getByTestId('shift-attribution-badge')).toHaveTextContent(
      'night shift — 70 min downtime'
    )
  })
})
