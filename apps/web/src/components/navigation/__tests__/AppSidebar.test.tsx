/**
 * AppSidebar Navigation Tests (Story 12.4: Schedule Upload UI)
 *
 * TDD tests — these MUST FAIL until the Schedule Upload nav link is added.
 *
 * @see Story 12.4 - Schedule Upload UI
 * @see AC #1 - Navigation link in Settings group
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AppSidebar } from '../AppSidebar'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => '/settings/schedule-upload',
  useSearchParams: () => ({
    get: vi.fn().mockReturnValue(null),
  }),
}))

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Schedule Upload UI (Story 12.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AC1: Navigation', () => {
    it('UNIT-005: AppSidebar includes Schedule Upload navigation link in Settings group', () => {
      // Given: The AppSidebar component is rendered
      render(<AppSidebar />)

      // Then: A "Schedule Upload" link is present
      const scheduleUploadLink = screen.getByText('Schedule Upload')
      expect(scheduleUploadLink).toBeInTheDocument()

      // And: It links to /settings/schedule-upload
      const linkElement = scheduleUploadLink.closest('a')
      expect(linkElement).toHaveAttribute('href', '/settings/schedule-upload')
    })
  })
})
