/**
 * MeetingModeToggle Component Tests (Story 18.1: Meeting Mode Toggle & Talking Points View)
 *
 * TDD tests — these MUST FAIL until the MeetingModeToggle component is implemented.
 * Tests cover toggle rendering, state management, callback behavior, and keyboard accessibility.
 *
 * @see Story 18.1 - Meeting Mode Toggle & Talking Points View
 * @see AC #1 - Toggle button in report header switches to meeting mode
 * @see AC #3 - Toggle back restores normal view
 */

import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// ---------------------------------------------------------------------------
// Imports (AFTER mocks)
// ---------------------------------------------------------------------------

import { MeetingModeToggle } from '../MeetingModeToggle'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: Meeting Mode Toggle (Story 18.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Toggle button rendering and behavior
  // =========================================================================
  describe('AC1: MeetingModeToggle rendering and interaction', () => {
    it('UNIT-001: MeetingModeToggle renders with Presentation icon and label', () => {
      // Given: MeetingModeToggle component is rendered with pressed=false and an onToggle callback
      const onToggle = vi.fn()

      // When: The component mounts
      render(<MeetingModeToggle pressed={false} onToggle={onToggle} />)

      // Then: A toggle button is visible with the text "Meeting Mode"
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      expect(toggleButton).toBeInTheDocument()

      // And: The button has text "Meeting Mode"
      expect(screen.getByText(/meeting mode/i)).toBeInTheDocument()

      // And: The button has aria-pressed="false"
      expect(toggleButton).toHaveAttribute('aria-pressed', 'false')

      // And: Text is at least 18px (text-base or text-lg class)
      expect(toggleButton.className).toMatch(/text-base|text-lg/)
    })

    it('UNIT-002: MeetingModeToggle emits onToggle(true) when clicked from unpressed state', () => {
      // Given: MeetingModeToggle is rendered with pressed=false and an onToggle spy
      const onToggle = vi.fn()
      render(<MeetingModeToggle pressed={false} onToggle={onToggle} />)

      // When: The user clicks the toggle button
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: The onToggle callback is called with true
      expect(onToggle).toHaveBeenCalledTimes(1)
      expect(onToggle).toHaveBeenCalledWith(true)
    })

    it('UNIT-003: MeetingModeToggle shows pressed state when pressed prop is true', () => {
      // Given: MeetingModeToggle is rendered with pressed=true
      const onToggle = vi.fn()
      render(<MeetingModeToggle pressed={true} onToggle={onToggle} />)

      // When: The component mounts
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })

      // Then: The toggle button has aria-pressed="true"
      expect(toggleButton).toHaveAttribute('aria-pressed', 'true')

      // And: Has the active/pressed visual styling (data-state="on" or pressed variant class)
      const hasActiveState =
        toggleButton.getAttribute('data-state') === 'on' ||
        toggleButton.className.includes('pressed') ||
        toggleButton.className.includes('active') ||
        toggleButton.className.includes('bg-accent') ||
        toggleButton.className.includes('bg-primary')
      expect(hasActiveState).toBe(true)
    })

    it('UNIT-004: MeetingModeToggle is keyboard accessible via Enter and Space', async () => {
      // Given: MeetingModeToggle is rendered with pressed=false and an onToggle spy
      const onToggle = vi.fn()
      render(<MeetingModeToggle pressed={false} onToggle={onToggle} />)
      const user = userEvent.setup()

      // When: The user focuses the toggle and presses Enter
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      toggleButton.focus()
      await user.keyboard('{Enter}')

      // Then: The onToggle callback is invoked
      expect(onToggle).toHaveBeenCalled()

      // When: The user presses Space
      onToggle.mockClear()
      await user.keyboard(' ')

      // Then: The onToggle callback is invoked again
      expect(onToggle).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // AC3: Toggle back emits false
  // =========================================================================
  describe('AC3: Toggle back to normal mode', () => {
    it('UNIT-017: MeetingModeToggle emits onToggle(false) when clicked from pressed state', () => {
      // Given: MeetingModeToggle is rendered with pressed=true and an onToggle spy
      const onToggle = vi.fn()
      render(<MeetingModeToggle pressed={true} onToggle={onToggle} />)

      // When: The user clicks the toggle button
      const toggleButton = screen.getByRole('button', { name: /meeting mode/i })
      fireEvent.click(toggleButton)

      // Then: The onToggle callback is called with false
      expect(onToggle).toHaveBeenCalledTimes(1)
      expect(onToggle).toHaveBeenCalledWith(false)
    })
  })
})
