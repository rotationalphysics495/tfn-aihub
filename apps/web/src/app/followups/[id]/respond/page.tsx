'use client'

import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type PageState = 'loading' | 'error-invalid' | 'error-expired' | 'ready' | 'submitting' | 'success' | 'submit-error'

interface FollowupContext {
  action_summary: string
  asset_name: string
  category: string
  assigned_by_email: string
  assigned_by_name: string
  note: string | null
  report_date: string
  recommendation?: string
  evidence_summary?: string
  financial_impact?: string
}

export default function RespondPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const id = params?.id as string
  const token = searchParams?.get('token')

  const [state, setState] = useState<PageState>('loading')
  const [context, setContext] = useState<FollowupContext | null>(null)
  const [responseText, setResponseText] = useState('')

  useEffect(() => {
    if (!token) {
      setState('error-invalid')
      return
    }

    const fetchContext = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/v1/followups/${id}/context?token=${token}`
        )

        if (res.ok) {
          const data = await res.json()
          setContext(data)
          setState('ready')
        } else {
          const errorData = await res.json().catch(() => ({}))
          const errorReason = errorData.error_reason || errorData.detail?.error_reason
          if (res.status === 400 || errorReason === 'expired') {
            setState('error-expired')
          } else {
            setState('error-invalid')
          }
        }
      } catch {
        setState('error-invalid')
      }
    }

    fetchContext()
  }, [id, token])

  const handleSubmit = async () => {
    if (!token || !responseText.trim() || (state !== 'ready' && state !== 'submit-error')) return

    setState('submitting')

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/followups/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, response_text: responseText }),
      })

      if (res.ok) {
        setState('success')
      } else {
        setState('submit-error')
      }
    } catch {
      setState('submit-error')
    }
  }

  const isSubmitted = state === 'success'
  const isSubmitting = state === 'submitting'

  if (state === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (state === 'error-expired') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg">
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-lg">Link Expired</CardTitle>
            </CardHeader>
            <CardContent>
              <Alert variant="destructive">
                <AlertTitle>This link has expired.</AlertTitle>
                <AlertDescription>
                  Please log in to the app to respond.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (state === 'error-invalid') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg">
          <Card>
            <CardContent className="pt-6">
              <Alert variant="destructive">
                <AlertTitle>Invalid link</AlertTitle>
                <AlertDescription>
                  This response link is not valid. Please check the link in your email.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-4">
      <div className="w-full max-w-lg">
        {/* Branding Header */}
        <div className="text-center mb-6 mt-4">
          <h1 className="text-xl font-semibold text-gray-900">
            TFN AI Hub
          </h1>
          <p className="text-sm text-gray-500">Follow-Up Response</p>
        </div>

        {/* Context Card */}
        {context && (
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{context.action_summary}</CardTitle>
                <Badge variant="outline">{context.category}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">Asset</p>
                <p className="text-sm font-medium">{context.asset_name}</p>
              </div>

              {context.recommendation && (
                <div>
                  <p className="text-sm text-gray-500">Recommendation</p>
                  <p className="text-sm">{context.recommendation}</p>
                </div>
              )}

              {context.evidence_summary && (
                <div>
                  <p className="text-sm text-gray-500">Evidence</p>
                  <p className="text-sm">{context.evidence_summary}</p>
                </div>
              )}

              {context.financial_impact && (
                <div>
                  <p className="text-sm text-gray-500">Financial Impact</p>
                  <p className="text-sm">{context.financial_impact}</p>
                </div>
              )}

              <div>
                <p className="text-sm text-gray-500">Assigned By</p>
                <p className="text-sm font-medium">{context.assigned_by_name}</p>
              </div>

              {context.note && (
                <div className="border-l-2 border-blue-500 pl-3 bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                    Note
                  </p>
                  <p className="text-sm">{context.note}</p>
                </div>
              )}

              <div>
                <p className="text-sm text-gray-500">Report Date</p>
                <p className="text-sm">{context.report_date}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Submit Error Message */}
        {state === 'submit-error' && (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>Failed to submit response</AlertTitle>
            <AlertDescription>
              Something went wrong. Please try again.
            </AlertDescription>
          </Alert>
        )}

        {/* Success Message */}
        {isSubmitted && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <AlertTitle className="text-green-800">
              Your response has been recorded
            </AlertTitle>
            <AlertDescription className="text-green-700">
              Thank you for your response. The team has been notified.
            </AlertDescription>
          </Alert>
        )}

        {/* Response Form */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Your Response</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Type your response here..."
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              disabled={isSubmitted}
              rows={5}
              className="resize-none"
            />
            <Button
              onClick={handleSubmit}
              disabled={isSubmitted || isSubmitting || !responseText.trim()}
              className="w-full"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Response'}
            </Button>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6 mb-4">
          <p className="text-xs text-gray-400">
            Manufacturing Performance Assistant
          </p>
        </div>
      </div>
    </div>
  )
}
