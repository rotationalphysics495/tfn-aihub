import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { ChatContextProvider, useChatContext } from '../ChatContextProvider'
import type { ReportContext } from '../types'

/**
 * Tests for ChatContextProvider (Story 19.1)
 *
 * AC#2: Cross-component communication via React Context
 */

// Test helper component that exposes context values
function TestConsumer() {
  const ctx = useChatContext()
  return (
    <div>
      <span data-testid="isOpen">{String(ctx.isOpen)}</span>
      <span data-testid="hasContext">{String(ctx.reportContext !== null)}</span>
      <span data-testid="reportDate">{ctx.reportContext?.reportDate ?? 'none'}</span>
      <button data-testid="open" onClick={ctx.open}>Open</button>
      <button data-testid="close" onClick={ctx.close}>Close</button>
      <button
        data-testid="openWithContext"
        onClick={() =>
          ctx.openChatWithContext({
            summaryText: 'Test summary',
            actionItems: [{ asset_name: 'Grinder 5' }],
            reportDate: '2026-02-10',
          })
        }
      >
        Open With Context
      </button>
      <button data-testid="clearContext" onClick={ctx.clearReportContext}>
        Clear Context
      </button>
    </div>
  )
}

describe('ChatContextProvider', () => {
  it('provides default state (closed, no context)', () => {
    render(
      <ChatContextProvider>
        <TestConsumer />
      </ChatContextProvider>
    )

    expect(screen.getByTestId('isOpen').textContent).toBe('false')
    expect(screen.getByTestId('hasContext').textContent).toBe('false')
  })

  it('opens sidebar via open()', () => {
    render(
      <ChatContextProvider>
        <TestConsumer />
      </ChatContextProvider>
    )

    fireEvent.click(screen.getByTestId('open'))
    expect(screen.getByTestId('isOpen').textContent).toBe('true')
  })

  it('closes sidebar via close()', () => {
    render(
      <ChatContextProvider>
        <TestConsumer />
      </ChatContextProvider>
    )

    fireEvent.click(screen.getByTestId('open'))
    expect(screen.getByTestId('isOpen').textContent).toBe('true')

    fireEvent.click(screen.getByTestId('close'))
    expect(screen.getByTestId('isOpen').textContent).toBe('false')
  })

  it('openChatWithContext sets reportContext and opens sidebar', () => {
    render(
      <ChatContextProvider>
        <TestConsumer />
      </ChatContextProvider>
    )

    fireEvent.click(screen.getByTestId('openWithContext'))

    expect(screen.getByTestId('isOpen').textContent).toBe('true')
    expect(screen.getByTestId('hasContext').textContent).toBe('true')
    expect(screen.getByTestId('reportDate').textContent).toBe('2026-02-10')
  })

  it('clearReportContext removes the report context', () => {
    render(
      <ChatContextProvider>
        <TestConsumer />
      </ChatContextProvider>
    )

    // Set context first
    fireEvent.click(screen.getByTestId('openWithContext'))
    expect(screen.getByTestId('hasContext').textContent).toBe('true')

    // Clear it
    fireEvent.click(screen.getByTestId('clearContext'))
    expect(screen.getByTestId('hasContext').textContent).toBe('false')
    expect(screen.getByTestId('reportDate').textContent).toBe('none')
  })

  it('returns safe no-op defaults when useChatContext is used outside provider', () => {
    render(<TestConsumer />)

    expect(screen.getByTestId('isOpen').textContent).toBe('false')
    expect(screen.getByTestId('hasContext').textContent).toBe('false')
    expect(screen.getByTestId('reportDate').textContent).toBe('none')
  })
})
