import React, { useRef, useState, useEffect } from "react"
import { FileUp, FileText, X, Loader2, CheckCircle2, AlertCircle, ChevronDown } from "lucide-react"
import type { DocumentInfo } from "@/services/api"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface CompactDocumentUploaderProps {
  documents: DocumentInfo[]
  onUpload: (file: File) => Promise<void>
  onRemove: (id: string) => void
  disabled?: boolean
}

export const CompactDocumentUploader: React.FC<CompactDocumentUploaderProps> = ({
  documents,
  onUpload,
  onRemove,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isDocsOpen, setIsDocsOpen] = useState(false)

  const isProcessing = documents.some((d) => d.status === "processing")
  const indexedCount = documents.filter((d) => d.status === "indexed").length

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsDocsOpen(false)
      }
    }
    if (isDocsOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isDocsOpen])

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
    e.stopPropagation()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (disabled) return

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i]
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
          await onUpload(file)
        } else {
          alert("Only PDF files are supported.")
        }
      }
    }
  }

  return (
    <div className="relative inline-flex items-center gap-1.5" ref={popoverRef}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="application/pdf"
        multiple
        className="hidden"
        disabled={disabled}
      />

      {/* Compact Upload Target Button with Drag & Drop */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          "relative inline-flex items-center rounded-lg transition-all",
          isDragging && "ring-2 ring-indigo-500 ring-offset-1 scale-[1.02]"
        )}
      >
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isProcessing}
          className={cn(
            "h-9 px-3 gap-1.5 text-xs font-medium border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-sm transition-all",
            isDragging && "border-indigo-400 bg-indigo-50/80 text-indigo-700",
            isProcessing && "bg-slate-50 text-slate-500"
          )}
          title="Click to browse or drop PDF here to upload"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600 shrink-0" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <FileUp className={cn("h-4 w-4 shrink-0", isDragging ? "text-indigo-600" : "text-slate-500")} />
              <span>{isDragging ? "Drop PDF" : "Upload PDF"}</span>
            </>
          )}
        </Button>
      </div>

      {/* Documents Badge and Management Popover Trigger */}
      {documents.length > 0 && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setIsDocsOpen(!isDocsOpen)}
          className={cn(
            "h-9 px-2.5 gap-1 text-xs border border-slate-200 bg-white hover:bg-slate-50 shadow-sm transition-colors",
            isDocsOpen && "bg-slate-100 border-slate-300"
          )}
          title="Manage uploaded knowledge documents"
        >
          <FileText className="h-3.5 w-3.5 text-slate-500" />
          <span className="font-medium text-slate-700">{documents.length}</span>
          <ChevronDown className={cn("h-3 w-3 text-slate-400 transition-transform", isDocsOpen && "rotate-180")} />
        </Button>
      )}

      {/* Popover Document Management List */}
      {isDocsOpen && documents.length > 0 && (
        <div className="absolute right-0 top-full mt-1.5 w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-slate-600" />
              <h4 className="text-xs font-semibold text-slate-800">Knowledge Documents</h4>
            </div>
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {indexedCount}/{documents.length} indexed
            </span>
          </div>

          <div className="max-h-56 overflow-y-auto space-y-1.5 pr-0.5">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-50/80 border border-slate-100 text-xs hover:bg-slate-100/70 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  {doc.status === "processing" && (
                    <Loader2 className="h-3.5 w-3.5 text-indigo-500 animate-spin shrink-0" />
                  )}
                  {doc.status === "indexed" && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                  )}
                  {doc.status === "failed" && (
                    <AlertCircle className="h-3.5 w-3.5 text-rose-500 shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-slate-700" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {doc.status === "indexed"
                        ? "Indexed & searchable"
                        : doc.status === "processing"
                        ? "Extracting & embedding..."
                        : doc.error_message || "Processing failed"}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onRemove(doc.id)}
                  disabled={disabled}
                  className="p-1 text-slate-400 hover:text-rose-600 hover:bg-white rounded transition-colors"
                  title="Remove document"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
            <span>Embedded with pgvector</span>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="font-medium text-indigo-600 hover:text-indigo-700"
            >
              + Add PDF
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
