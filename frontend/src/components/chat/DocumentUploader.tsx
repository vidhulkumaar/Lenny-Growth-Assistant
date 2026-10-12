import React, { useRef, useState } from "react"
import { Paperclip, File, X, Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import type { DocumentInfo } from "@/services/api"

interface DocumentUploaderProps {
  documents: DocumentInfo[]
  onUpload: (file: File) => Promise<void>
  onRemove: (id: string) => void
  disabled?: boolean
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ 
  documents, 
  onUpload, 
  onRemove,
  disabled 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      for (let i = 0; i < e.target.files.length; i++) {
        await onUpload(e.target.files[i])
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i]
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith('.pdf')) {
          await onUpload(file)
        } else {
          alert("Only PDF files are supported.")
        }
      }
    }
  }

  return (
    <div className="flex flex-col gap-2 w-full">
      {documents.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {documents.map(doc => (
            <div key={doc.id} className="flex items-center gap-2 bg-slate-100 border border-slate-200 rounded-md py-1 px-2 text-sm">
              <File className="h-4 w-4 text-slate-500" />
              <span className="truncate max-w-[150px]" title={doc.filename}>{doc.filename}</span>
              
              {doc.status === 'processing' && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
              {doc.status === 'indexed' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
              {doc.status === 'failed' && (
                <div title={doc.error_message}>
                  <AlertCircle className="h-4 w-4 text-red-500" />
                </div>
              )}
              
              <button 
                onClick={() => onRemove(doc.id)} 
                className="ml-1 text-slate-400 hover:text-slate-600 focus:outline-none"
                disabled={disabled}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
      
      <div 
        className={`relative rounded-md border-2 border-dashed p-4 transition-colors ${isDragging ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-slate-50'}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          accept="application/pdf"
          multiple
          className="hidden"
          disabled={disabled}
        />
        <div className="flex flex-col items-center justify-center text-center">
          <Paperclip className="h-6 w-6 text-slate-400 mb-2" />
          <p className="text-sm text-slate-600">
            Drag & drop PDFs here, or{' '}
            <button 
              type="button" 
              className="text-indigo-600 font-medium hover:underline focus:outline-none"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
            >
              browse
            </button>
          </p>
          <p className="text-xs text-slate-400 mt-1">Supports multiple files up to 50MB</p>
        </div>
      </div>
    </div>
  )
}
