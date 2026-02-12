/**
 * MessageThread Component Tests (Story 15.4: Message Thread UI)
 *
 * TDD tests — these MUST FAIL until the MessageThread component is implemented.
 * Tests cover chronological message rendering, alignment by direction, message type
 * badges, accessibility, empty state, and loading skeleton.
 *
 * @see Story 15.4 - Message Thread UI
 * @see AC #1 - Chronological message thread display
 * @see AC #3 - Empty state when no responses
 */

import { render, screen, within } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks (BEFORE imports)
// ---------------------------------------------------------------------------

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

interface MockMessage {
  id: string
  direction: 'outbound' | 'inbound'
  message_type: 'assignment' | 'response' | 'status_update' | 'escalation'
  sender_email: string
  subject: string | null
  body: string
  sent_at: string
}

const createMockMessage = (
  overrides: Partial<MockMessage> = {}
): MockMessage => ({
  id: 'msg-default',
  direction: 'outbound',
  message_type: 'assignment',
  sender_email: 'manager@plant.com',
  subject: 'Follow-up: Replace bearing',
  body: 'Please inspect the bearing on Pump-101',
  sent_at: '2026-02-10T08:00:00Z',
  ...overrides,
})

const createOutboundAssignment = (overrides: Partial<MockMessage> = {}): MockMessage =>
  createMockMessage({
    id: 'msg-outbound-1',
    direction: 'outbound',
    message_type: 'assignment',
    sender_email: 'manager@plant.com',
    subject: 'Follow-up: Replace bearing',
    body: 'Please inspect the bearing on Pump-101',
    sent_at: '2026-02-10T08:00:00Z',
    ...overrides,
  })

const createInboundResponse = (overrides: Partial<MockMessage> = {}): MockMessage =>
  createMockMessage({
    id: 'msg-inbound-1',
    direction: 'inbound',
    message_type: 'response',
    sender_email: 'assignee@plant.com',
    subject: null,
    body: 'Bearing replaced and tested',
    sent_at: '2026-02-10T14:30:00Z',
    ...overrides,
  })

const createStatusUpdate = (overrides: Partial<MockMessage> = {}): MockMessage =>
  createMockMessage({
    id: 'msg-status-1',
    direction: 'outbound',
    message_type: 'status_update',
    sender_email: 'assignee@plant.com',
    body: 'in_progress',
    sent_at: '2026-02-10T10:00:00Z',
    ...overrides,
  })

const createEscalation = (overrides: Partial<MockMessage> = {}): MockMessage =>
  createMockMessage({
    id: 'msg-escalation-1',
    direction: 'outbound',
    message_type: 'escalation',
    sender_email: 'manager@plant.com',
    body: 'Escalating to maintenance lead',
    sent_at: '2026-02-10T16:00:00Z',
    ...overrides,
  })

// ---------------------------------------------------------------------------
// Import component AFTER mocks are set up
// ---------------------------------------------------------------------------

// The component does not exist yet — this import will fail until it's created.
import { MessageThread } from '../MessageThread'

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe('Feature: MessageThread Component (Story 15.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // =========================================================================
  // AC1: Chronological message thread display
  // =========================================================================
  describe('AC1: Chronological Message Thread Display', () => {
    it('15-4-message-thread-ui-UNIT-001: MessageThread renders outbound assignment message right-aligned', () => {
      // Given: A MessageThread component receives a messages array containing one outbound message
      const messages = [createOutboundAssignment()]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The outbound message body is displayed
      expect(screen.getByText(/please inspect the bearing on pump-101/i)).toBeInTheDocument()

      // And: The message is right-aligned with muted background (bg-industrial-100)
      const messageBody = screen.getByText(/please inspect the bearing on pump-101/i)
      const messageContainer = messageBody.closest('[data-direction="outbound"]') ||
        messageBody.closest('[class*="right"]') ||
        messageBody.closest('[class*="justify-end"]') ||
        messageBody.closest('[class*="ml-auto"]')
      expect(messageContainer).toBeTruthy()

      // And: Shows "Sent to" label
      expect(screen.getByText(/sent to/i)).toBeInTheDocument()

      // And: Shows a blue "Assignment" badge
      const assignmentBadge = screen.getByText(/assignment/i)
      expect(assignmentBadge).toBeInTheDocument()
      const badgeEl = assignmentBadge.closest('[class*="blue"]') || assignmentBadge.closest('span')
      expect(badgeEl).toBeTruthy()
    })

    it('15-4-message-thread-ui-UNIT-002: MessageThread renders inbound response message left-aligned', () => {
      // Given: A MessageThread component receives a messages array containing one inbound message
      const messages = [createInboundResponse()]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The inbound message body is displayed
      expect(screen.getByText(/bearing replaced and tested/i)).toBeInTheDocument()

      // And: The message is left-aligned with card background
      const messageBody = screen.getByText(/bearing replaced and tested/i)
      const messageContainer = messageBody.closest('[data-direction="inbound"]') ||
        messageBody.closest('[class*="left"]') ||
        messageBody.closest('[class*="justify-start"]') ||
        messageBody.closest('[class*="mr-auto"]')
      expect(messageContainer).toBeTruthy()

      // And: Shows "{assignee} replied" label
      expect(screen.getByText(/replied/i)).toBeInTheDocument()

      // And: Shows a green "Response" badge
      const responseBadge = screen.getByText(/response/i)
      expect(responseBadge).toBeInTheDocument()
      const badgeEl = responseBadge.closest('[class*="green"]') || responseBadge.closest('span')
      expect(badgeEl).toBeTruthy()
    })

    it('15-4-message-thread-ui-UNIT-003: MessageThread renders full chronological thread with multiple message types', () => {
      // Given: A MessageThread component receives messages containing:
      //   (1) outbound assignment at 08:00, (2) status_update "in_progress" at 10:00,
      //   (3) inbound response at 14:30
      const messages = [
        createOutboundAssignment({ sent_at: '2026-02-10T08:00:00Z' }),
        createStatusUpdate({ sent_at: '2026-02-10T10:00:00Z' }),
        createInboundResponse({ sent_at: '2026-02-10T14:30:00Z' }),
      ]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: All three messages are displayed
      expect(screen.getByText(/please inspect the bearing on pump-101/i)).toBeInTheDocument()
      expect(screen.getByText(/bearing replaced and tested/i)).toBeInTheDocument()

      // And: Messages are in chronological order (top-to-bottom)
      const container = screen.getByRole('log')
      const allMessages = container.querySelectorAll('[data-message-id]')
      expect(allMessages.length).toBe(3)

      // And: First message (index 0) has the earliest sent_at
      expect(allMessages[0].getAttribute('data-message-id')).toBe('msg-outbound-1')
      // And: Last message (index 2) has the latest sent_at
      expect(allMessages[2].getAttribute('data-message-id')).toBe('msg-inbound-1')

      // And: Status update shows appropriate text and badge
      const statusBadge = screen.getByText(/status update/i)
      expect(statusBadge).toBeInTheDocument()
      // And: Status update shows "{assignee} marked as in-progress"
      expect(screen.getByText(/marked as in-progress/i)).toBeInTheDocument()
    })

    it('15-4-message-thread-ui-UNIT-004: MessageThread displays sender name/email and relative timestamps', () => {
      // Given: A MessageThread component receives messages with sender_email and sent_at timestamps
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      const messages = [
        createOutboundAssignment({
          sender_email: 'manager@plant.com',
          sent_at: twoHoursAgo,
        }),
      ]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The sender email is displayed
      expect(screen.getByText(/manager@plant\.com/)).toBeInTheDocument()

      // And: A relative timestamp (e.g., "2h ago") is displayed
      expect(screen.getByText(/2h ago/)).toBeInTheDocument()
    })

    it('15-4-message-thread-ui-UNIT-005: MessageThread renders message type badges with correct colors', () => {
      // Given: A MessageThread component receives messages with all 4 message_type values
      const messages = [
        createOutboundAssignment({ id: 'msg-1', sent_at: '2026-02-10T08:00:00Z' }),
        createInboundResponse({ id: 'msg-2', sent_at: '2026-02-10T09:00:00Z' }),
        createStatusUpdate({ id: 'msg-3', sent_at: '2026-02-10T10:00:00Z' }),
        createEscalation({ id: 'msg-4', sent_at: '2026-02-10T11:00:00Z' }),
      ]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: Assignment badge is blue
      const assignmentBadge = screen.getByText(/^assignment$/i)
      expect(assignmentBadge).toBeInTheDocument()
      const assignmentBadgeEl = assignmentBadge.closest('[class*="blue"]')
      expect(assignmentBadgeEl).toBeTruthy()

      // And: Response badge is green
      const responseBadge = screen.getByText(/^response$/i)
      expect(responseBadge).toBeInTheDocument()
      const responseBadgeEl = responseBadge.closest('[class*="green"]')
      expect(responseBadgeEl).toBeTruthy()

      // And: Status Update badge is gray
      const statusBadge = screen.getByText(/status update/i)
      expect(statusBadge).toBeInTheDocument()
      const statusBadgeEl = statusBadge.closest('[class*="gray"]') || statusBadge.closest('[class*="muted"]')
      expect(statusBadgeEl).toBeTruthy()

      // And: Escalation badge exists with appropriate styling
      const escalationBadge = screen.getByText(/escalation/i)
      expect(escalationBadge).toBeInTheDocument()
    })

    it('15-4-message-thread-ui-UNIT-006: MessageThread has correct accessibility attributes', () => {
      // Given: A MessageThread component receives messages
      const messages = [
        createOutboundAssignment(),
        createInboundResponse(),
      ]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The message container has role="log"
      const logContainer = screen.getByRole('log')
      expect(logContainer).toBeInTheDocument()

      // And: Has appropriate aria-label
      expect(logContainer).toHaveAttribute('aria-label')
      expect(logContainer.getAttribute('aria-label')).toMatch(/message/i)

      // And: Individual messages have aria-labels describing sender and time
      const messageElements = logContainer.querySelectorAll('[aria-label]')
      expect(messageElements.length).toBeGreaterThanOrEqual(2)
    })
  })

  // =========================================================================
  // AC3: Empty state when no responses
  // =========================================================================
  describe('AC3: Empty State When No Responses', () => {
    it('15-4-message-thread-ui-UNIT-010: MessageThread shows empty state with "Awaiting response" when no inbound messages', () => {
      // Given: A MessageThread component receives messages containing only one outbound
      //        assignment message and assignee_name="John Smith"
      const messages = [createOutboundAssignment()]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The outbound message is displayed
      expect(screen.getByText(/please inspect the bearing on pump-101/i)).toBeInTheDocument()

      // And: Below it a centered empty state shows "Awaiting response from John Smith"
      expect(screen.getByText(/awaiting response from john smith/i)).toBeInTheDocument()

      // And: A Clock icon is present (represented as an SVG or icon component)
      // The Clock icon from lucide-react typically renders as an SVG
      const awaitingText = screen.getByText(/awaiting response from john smith/i)
      const awaitingContainer = awaitingText.closest('div')
      const svgIcon = awaitingContainer?.querySelector('svg')
      expect(svgIcon).toBeTruthy()
    })

    it('15-4-message-thread-ui-UNIT-011: MessageThread does NOT show "Awaiting response" when inbound messages exist', () => {
      // Given: A MessageThread component receives messages containing one outbound and one inbound message
      const messages = [
        createOutboundAssignment(),
        createInboundResponse(),
      ]

      // When: The component renders
      render(
        <MessageThread
          messages={messages}
          assignee_name="John Smith"
        />
      )

      // Then: The "Awaiting response" empty state text is NOT displayed
      expect(screen.queryByText(/awaiting response/i)).toBeNull()
    })

    it('15-4-message-thread-ui-UNIT-012: MessageThread shows loading skeleton state', () => {
      // Given: A MessageThread component receives loading=true
      // When: The component renders
      render(
        <MessageThread
          messages={[]}
          assignee_name="John Smith"
          loading={true}
        />
      )

      // Then: A loading skeleton is displayed instead of message content or empty state
      const skeleton = document.querySelector(
        '[class*="skeleton"], [class*="animate-pulse"], [data-testid="message-thread-skeleton"]'
      )
      expect(skeleton).toBeTruthy()

      // And: No "Awaiting response" text is shown
      expect(screen.queryByText(/awaiting response/i)).toBeNull()
    })
  })
})
