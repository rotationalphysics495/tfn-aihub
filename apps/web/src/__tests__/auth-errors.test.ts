/**
 * Tests for auth error handling
 *
 * Story 1.2 - AC#7: Error handling provides clear feedback for invalid credentials
 */
import { describe, it, expect } from 'vitest'
import { getAuthError, type AuthErrorCode } from '@/lib/supabase/auth-errors'

describe('getAuthError', () => {
  describe('invalid credentials', () => {
    it('should return invalid_credentials for invalid login credentials error', () => {
      const error = new Error('Invalid login credentials')
      const result = getAuthError(error)

      expect(result.code).toBe('invalid_credentials')
      expect(result.message).toContain('Invalid email or password')
      expect(result.action).toBeDefined()
    })

    it('should return invalid_credentials for invalid email or password error', () => {
      const error = new Error('Invalid email or password provided')
      const result = getAuthError(error)

      expect(result.code).toBe('invalid_credentials')
    })
  })

  describe('email not confirmed', () => {
    it('should return email_not_confirmed error', () => {
      const error = new Error('Email not confirmed')
      const result = getAuthError(error)

      expect(result.code).toBe('email_not_confirmed')
      expect(result.message).toContain('not been verified')
      expect(result.action).toContain('confirmation email')
    })
  })

  describe('user not found', () => {
    it('should return user_not_found error', () => {
      const error = new Error('User not found')
      const result = getAuthError(error)

      expect(result.code).toBe('user_not_found')
      expect(result.message).toContain('No account found')
    })
  })

  describe('rate limiting', () => {
    it('should return too_many_requests for rate limit errors', () => {
      const error = new Error('Too many requests')
      const result = getAuthError(error)

      expect(result.code).toBe('too_many_requests')
      expect(result.message).toContain('Too many login attempts')
      expect(result.action).toContain('wait')
    })

    it('should return too_many_requests for rate limit message', () => {
      const error = new Error('Rate limit exceeded')
      const result = getAuthError(error)

      expect(result.code).toBe('too_many_requests')
    })
  })

  describe('network errors', () => {
    it('should return network_error for network issues', () => {
      const error = new Error('Network request failed')
      const result = getAuthError(error)

      expect(result.code).toBe('network_error')
      expect(result.message).toContain('Unable to connect')
      expect(result.action).toContain('internet connection')
    })

    it('should return network_error for fetch failures', () => {
      const error = new Error('Fetch error')
      const result = getAuthError(error)

      expect(result.code).toBe('network_error')
    })

    it('should return network_error for connection issues', () => {
      const error = new Error('Connection refused')
      const result = getAuthError(error)

      expect(result.code).toBe('network_error')
    })
  })

  describe('session expired', () => {
    it('should return session_expired error', () => {
      const error = new Error('Session has expired')
      const result = getAuthError(error)

      expect(result.code).toBe('session_expired')
      expect(result.message).toContain('session has expired')
      expect(result.action).toContain('log in again')
    })
  })

  describe('unknown errors', () => {
    it('should return unknown_error for null error', () => {
      const result = getAuthError(null)

      expect(result.code).toBe('unknown_error')
      expect(result.message).toContain('unexpected error')
      expect(result.action).toBeDefined()
    })

    it('should return unknown_error for unrecognized error messages', () => {
      const error = new Error('Some unrecognized error')
      const result = getAuthError(error)

      expect(result.code).toBe('unknown_error')
      expect(result.action).toContain('contact support')
    })
  })

  describe('all errors have required properties', () => {
    const errorTypes: Array<{ message: string; expectedCode: AuthErrorCode }> = [
      { message: 'Invalid login credentials', expectedCode: 'invalid_credentials' },
      { message: 'Email not confirmed', expectedCode: 'email_not_confirmed' },
      { message: 'User not found', expectedCode: 'user_not_found' },
      { message: 'Too many requests', expectedCode: 'too_many_requests' },
      { message: 'Network error', expectedCode: 'network_error' },
      { message: 'Session expired', expectedCode: 'session_expired' },
      { message: 'Unknown', expectedCode: 'unknown_error' },
    ]

    errorTypes.forEach(({ message, expectedCode }) => {
      it(`should have code, message, and action for ${expectedCode}`, () => {
        const error = new Error(message)
        const result = getAuthError(error)

        expect(result.code).toBe(expectedCode)
        expect(result.message).toBeTruthy()
        expect(typeof result.message).toBe('string')
        // Action is optional but should be defined for user-friendly messages
        if (result.action) {
          expect(typeof result.action).toBe('string')
        }
      })
    })
  })
})
