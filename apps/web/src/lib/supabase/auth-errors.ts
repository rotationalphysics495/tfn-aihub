/**
 * Auth error types and user-friendly messages
 * Following the "Industrial Clarity" design principle of clear, actionable feedback
 */

export type AuthErrorCode =
  | 'invalid_credentials'
  | 'email_not_confirmed'
  | 'user_not_found'
  | 'email_taken'
  | 'weak_password'
  | 'too_many_requests'
  | 'network_error'
  | 'session_expired'
  | 'unknown_error'

export interface AuthError {
  code: AuthErrorCode
  message: string
  action?: string
}

/**
 * Maps Supabase error messages to user-friendly error objects
 */
export function getAuthError(error: Error | null): AuthError {
  if (!error) {
    return {
      code: 'unknown_error',
      message: 'An unexpected error occurred.',
      action: 'Please try again.',
    }
  }

  const errorMessage = error.message.toLowerCase()

  // Invalid credentials
  if (
    errorMessage.includes('invalid login credentials') ||
    errorMessage.includes('invalid email or password')
  ) {
    return {
      code: 'invalid_credentials',
      message: 'Invalid email or password.',
      action: 'Please check your credentials and try again.',
    }
  }

  // Email not confirmed
  if (errorMessage.includes('email not confirmed')) {
    return {
      code: 'email_not_confirmed',
      message: 'Your email address has not been verified.',
      action: 'Please check your inbox for a confirmation email.',
    }
  }

  // User not found
  if (errorMessage.includes('user not found')) {
    return {
      code: 'user_not_found',
      message: 'No account found with this email.',
      action: 'Please check the email address or contact your administrator.',
    }
  }

  // Email already taken
  if (errorMessage.includes('email already registered') || errorMessage.includes('already exists')) {
    return {
      code: 'email_taken',
      message: 'An account with this email already exists.',
      action: 'Please use a different email or try logging in.',
    }
  }

  // Weak password
  if (errorMessage.includes('password') && errorMessage.includes('weak')) {
    return {
      code: 'weak_password',
      message: 'Password does not meet security requirements.',
      action: 'Please use a stronger password with at least 8 characters.',
    }
  }

  // Rate limiting
  if (errorMessage.includes('too many requests') || errorMessage.includes('rate limit')) {
    return {
      code: 'too_many_requests',
      message: 'Too many login attempts.',
      action: 'Please wait a few minutes before trying again.',
    }
  }

  // Network errors
  if (
    errorMessage.includes('network') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('connection')
  ) {
    return {
      code: 'network_error',
      message: 'Unable to connect to the server.',
      action: 'Please check your internet connection and try again.',
    }
  }

  // Session expired
  if (errorMessage.includes('session') && errorMessage.includes('expired')) {
    return {
      code: 'session_expired',
      message: 'Your session has expired.',
      action: 'Please log in again to continue.',
    }
  }

  // Default unknown error
  return {
    code: 'unknown_error',
    message: 'An unexpected error occurred.',
    action: 'Please try again or contact support if the problem persists.',
  }
}
