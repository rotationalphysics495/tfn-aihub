'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useScheduleUpload } from '@/hooks/useScheduleUpload'
import { ScheduleUploadZone } from '@/components/schedule/ScheduleUploadZone'
import { SchedulePreviewTable } from '@/components/schedule/SchedulePreviewTable'
import { Button } from '@/components/ui/button'

export default function ScheduleUploadPage() {
  const router = useRouter()
  const {
    isUploading,
    isConfirming,
    error,
    previewData,
    confirmResult,
    uploadForPreview,
    confirmUpload,
    reset,
  } = useScheduleUpload()

  const redirectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Handle redirect after successful confirm
  useEffect(() => {
    if (confirmResult) {
      redirectTimeoutRef.current = setTimeout(() => {
        router.push('/morning-report')
      }, 1500)
    }

    return () => {
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current)
      }
    }
  }, [confirmResult, router])

  const handleFileSelected = (file: File) => {
    uploadForPreview(file)
  }

  const hasErrors = previewData?.has_errors ?? false

  return (
    <div className="container max-w-4xl py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Schedule Upload</h1>
        <p className="text-muted-foreground">
          Upload a CSV or Excel file to import production schedules.
        </p>
      </div>

      {/* Success message */}
      {confirmResult && (
        <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-lg flex items-center gap-3 text-primary">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>Successfully imported {confirmResult.rows_inserted} schedule rows.</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 text-destructive">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span>{error}</span>
          <Button
            variant="outline"
            size="sm"
            className="ml-auto"
            onClick={() => reset()}
          >
            Try Again
          </Button>
        </div>
      )}

      {/* Loading spinner during upload */}
      {isUploading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Uploading and parsing file...</p>
        </div>
      )}

      {/* Upload zone (shown when no preview data and not uploading) */}
      {!previewData && !isUploading && !confirmResult && (
        <ScheduleUploadZone onFileSelected={handleFileSelected} />
      )}

      {/* Preview table and actions */}
      {previewData && !confirmResult && (
        <div className="space-y-4">
          <SchedulePreviewTable previewData={previewData} />

          <div className="flex gap-3 justify-end">
            {!isConfirming && (
              <Button variant="outline" onClick={reset}>
                Upload Different File
              </Button>
            )}
            <Button
              onClick={confirmUpload}
              disabled={hasErrors || isConfirming}
            >
              {isConfirming && (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
              )}
              Confirm Upload
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
