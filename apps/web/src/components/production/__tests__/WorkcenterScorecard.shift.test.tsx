/**
 * WorkcenterScorecard Shift Integration Tests (Story 17.4)
 *
 * @see Story 17.4 - Shift Breakdown API & UI
 * @see AC #2 - Shift tab filtering on scorecard
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockUseWorkcenterSummary = vi.fn()
vi.mock('@/hooks/useWorkcenterSummary', () => ({
  useWorkcenterSummary: (...args: unknown[]) => mockUseWorkcenterSummary(...args),
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

// Must import after mocks
import { WorkcenterScorecard } from '../WorkcenterScorecard'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_RESPONSE = {
  workcenters: [
    {
      workcenter_name: 'Grinding',
      total_actual: 300,
      total_target: 400,
      attainment_percentage: 75.0,
      assets_on_target: 1,
      assets_missed: 1,
      total_assets: 2,
      assets: [],
      shift_breakdown: null,
    },
  ],
  date: '2026-02-10',
  total_actual: 300,
  total_target: 400,
  total_attainment: 75.0,
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('WorkcenterScorecard Shift Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseWorkcenterSummary.mockReturnValue({
      data: MOCK_RESPONSE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  it('17-4-UNIT-050: passes shift param to useWorkcenterSummary when selectedShift is not "all"', () => {
    render(<WorkcenterScorecard date="2026-02-10" selectedShift="morning" />)

    expect(mockUseWorkcenterSummary).toHaveBeenCalledWith(
      expect.objectContaining({ shift: 'morning', date: '2026-02-10' })
    )
  })

  it('17-4-UNIT-051: does not pass shift param when selectedShift is "all"', () => {
    render(<WorkcenterScorecard date="2026-02-10" selectedShift="all" />)

    const callArg = mockUseWorkcenterSummary.mock.calls[0][0]
    expect(callArg.shift).toBeUndefined()
  })

  it('17-4-UNIT-052: does not pass shift param when selectedShift is undefined', () => {
    render(<WorkcenterScorecard date="2026-02-10" />)

    const callArg = mockUseWorkcenterSummary.mock.calls[0][0]
    expect(callArg.shift).toBeUndefined()
  })

  it('17-4-UNIT-053: renders normally when shift data is present', () => {
    render(<WorkcenterScorecard date="2026-02-10" selectedShift="morning" />)

    expect(screen.getByText('Production Scorecard')).toBeInTheDocument()
  })
})
