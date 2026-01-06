/**
 * Tests for health check API endpoint
 *
 * Story 1.7 - AC: Health endpoint responds with status "healthy"
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { GET } from './route'

describe('GET /api/health', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T12:00:00.000Z'))
  })

  it('should return healthy status', async () => {
    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.status).toBe('healthy')
  })

  it('should include service name', async () => {
    const response = await GET()
    const data = await response.json()

    expect(data.service).toBe('manufacturing-web')
  })

  it('should include timestamp', async () => {
    const response = await GET()
    const data = await response.json()

    expect(data.timestamp).toBe('2026-01-06T12:00:00.000Z')
  })

  it('should return JSON content type', async () => {
    const response = await GET()

    expect(response.headers.get('content-type')).toContain('application/json')
  })
})
