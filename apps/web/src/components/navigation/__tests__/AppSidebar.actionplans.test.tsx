/**
 * AppSidebar Navigation Tests for Action Plans (Story 16.5)
 *
 * TDD tests — these MUST FAIL until the AppSidebar is updated to include
 * the Action Plans navigation link.
 *
 * @see Story 16.5 - Action Plans Dashboard
 * @see AC #1 - Navigation sidebar shows "Action Plans" link
 */

import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

let mockPathname = '/action-plans'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => mockPathname,
  useParams: () => ({}),
}))

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

import { AppSidebar } from '../AppSidebar'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: AppSidebar Action Plans Navigation (Story 16.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPathname = '/'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('16-5-action-plans-dashboard-INT-003: Navigation sidebar shows "Action Plans" link in Operations group', () => {
    // Given: The sidebar renders
    render(<AppSidebar />)

    // Then: An "Action Plans" link is visible
    const actionPlansLink = screen.getByText('Action Plans')
    expect(actionPlansLink).toBeInTheDocument()

    // And: The link points to /action-plans
    const linkElement = actionPlansLink.closest('a')
    expect(linkElement).toHaveAttribute('href', '/action-plans')
  })

  it('16-5-action-plans-dashboard-INT-004: Action Plans sidebar link highlights when on /action-plans route', () => {
    // Given: The current pathname is /action-plans
    mockPathname = '/action-plans'

    // When: The sidebar renders
    render(<AppSidebar />)

    // Then: The "Action Plans" link has active styling
    const actionPlansLink = screen.getByText('Action Plans')
    const linkContainer = actionPlansLink.closest('a')
    expect(linkContainer?.className).toMatch(/bg-primary|active|font-medium/)
  })

  it('Action Plans link is in the Operations group', () => {
    // Given: The sidebar renders
    render(<AppSidebar />)

    // Then: The Operations group header exists
    expect(screen.getByText('Operations')).toBeInTheDocument()

    // And: "Action Plans" appears as a sibling to other Operations items
    // Find the Operations section and verify Action Plans is within it
    const operationsHeader = screen.getByText('Operations')
    const operationsSection = operationsHeader.closest('div')
    expect(operationsSection).not.toBeNull()

    // The Action Plans link should be found within the same section
    const actionPlansInSection = operationsSection?.querySelector('a[href="/action-plans"]')
    expect(actionPlansInSection).not.toBeNull()
  })

  it('Action Plans link does NOT highlight when on other routes', () => {
    // Given: The current pathname is /morning-report
    mockPathname = '/morning-report'

    // When: The sidebar renders
    render(<AppSidebar />)

    // Then: The "Action Plans" link does NOT have active styling
    const actionPlansLink = screen.getByText('Action Plans')
    const linkContainer = actionPlansLink.closest('a')
    expect(linkContainer?.className).not.toMatch(/bg-primary/)
  })
})
