'use client'

import { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ScheduleUploadZoneProps {
  onFileSelected: (file: File) => void
  disabled?: boolean
}

const ACCEPTED_EXTENSIONS = ['.csv', '.xlsx']

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(1)} MB`
}

function isValidFileType(fileName: string): boolean {
  const lower = fileName.toLowerCase()
  return ACCEPTED_EXTENSIONS.some(ext => lower.endsWith(ext))
}

export function ScheduleUploadZone({ onFileSelected, disabled }: ScheduleUploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
    setFileError(null)

    const files = e.dataTransfer?.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (!isValidFileType(file.name)) {
      setFileError('File type not supported. Please use .csv or .xlsx files.')
      return
    }

    setSelectedFile(file)
    onFileSelected(file)
  }

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (!isValidFileType(file.name)) {
      setFileError('File type not supported. Please use .csv or .xlsx files.')
      return
    }

    setFileError(null)
    setSelectedFile(file)
    onFileSelected(file)
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  const handleRemove = () => {
    setSelectedFile(null)
    setFileError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div
      data-testid="upload-zone"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center transition-colors
        ${isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-border'
        }
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {selectedFile ? (
        <div className="flex flex-col items-center gap-2">
          <Upload className="w-8 h-8 text-primary" />
          <p className="font-medium">{selectedFile.name}</p>
          <p className="text-sm text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRemove}
            aria-label="Remove"
          >
            <X className="w-4 h-4 mr-1" />
            Remove
          </Button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <Upload className="w-10 h-10 text-muted-foreground" />
          <p className="text-lg font-medium">Drop CSV or Excel file here</p>
          <p className="text-sm text-muted-foreground">or</p>
          <Button variant="outline" onClick={handleBrowseClick} disabled={disabled}>
            Browse Files
          </Button>
          <p className="text-xs text-muted-foreground">.csv, .xlsx accepted</p>
        </div>
      )}

      {fileError && (
        <p className="mt-3 text-sm text-destructive">{fileError}</p>
      )}
    </div>
  )
}
