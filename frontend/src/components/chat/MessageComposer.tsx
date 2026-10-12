import React, { useRef, useEffect, useState } from "react"
import {
  SendHorizontal,
  Paperclip,
  FileText,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import type { DocumentInfo } from "@/services/api"
import { cn } from "@/lib/utils"

interface MessageComposerProps {
  onSend: (message: string) => void
  disabled?: boolean
  isConnecting?: boolean
  documents?: DocumentInfo[]
  onUploadDocument?: (file: File) => Promise<void>
  onRemoveDocument?: (id: string) => void
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSend,
  disabled = false,
  isConnecting = false,
  documents = [],
  onUploadDocument,
  onRemoveDocument,
}) => {
  const [content, setContent] = useState("")
  const [isDragging, setIsDragging] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isProcessing = documents.some((d) => d.status === "processing")

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`
    }
  }, [content])

  const handleSend = () => {
    if (content.trim() && !disabled && !isProcessing) {
      onSend(content.trim())
      setContent("")
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && onUploadDocument) {
      for (let i = 0; i < e.target.files.length; i++) {
        await onUploadDocument(e.target.files[i])
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled && onUploadDocument) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (disabled || !onUploadDocument) return

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i]
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
          await onUploadDocument(file)
        } else {
          alert("Only PDF files are supported.")
        }
      }
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-3 sm:px-4">
      {/* Hidden PDF File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="application/pdf"
        multiple
        className="hidden"
        disabled={disabled || isProcessing}
      />

      {/* Gemini-Style Rounded Pill Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col rounded-3xl border border-slate-200/90 bg-[#f0f4f9] hover:bg-[#edf2f8] focus-within:bg-white focus-within:border-slate-300 focus-within:shadow-md transition-all p-2.5 sm:p-3",
          isDragging && "ring-2 ring-indigo-500 bg-indigo-50/70 border-indigo-300"
        )}
      >
        {/* Attached Knowledge Documents Chips */}
        {documents.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2 px-1">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border shadow-xs transition-colors",
                  doc.status === "indexed"
                    ? "bg-white border-slate-200 text-slate-700"
                    : doc.status === "processing"
                    ? "bg-indigo-50 border-indigo-200 text-indigo-700"
                    : "bg-rose-50 border-rose-200 text-rose-700"
                )}
              >
                <FileText className="h-3 w-3 text-slate-500 shrink-0" />
                <span className="truncate max-w-[140px] text-[11px]" title={doc.filename}>
                  {doc.filename}
                </span>

                {doc.status === "processing" && (
                  <Loader2 className="h-3 w-3 text-indigo-600 animate-spin shrink-0" />
                )}
                {doc.status === "indexed" && (
                  <CheckCircle2 className="h-3 w-3 text-emerald-600 shrink-0" />
                )}
                {doc.status === "failed" && (
                  <span title={doc.error_message}>
                    <AlertCircle className="h-3 w-3 text-rose-600 shrink-0" />
                  </span>
                )}

                {onRemoveDocument && (
                  <button
                    type="button"
                    onClick={() => onRemoveDocument(doc.id)}
                    className="p-0.5 text-slate-400 hover:text-slate-600 rounded-full transition-colors ml-0.5"
                    title="Remove document"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Multiline Textarea */}
        <div className="relative w-full">
          <Textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Lenny anything... (Ask a question, request a Ship 30 atomic essay, or create an HTML dashboard)"
            className="min-h-[46px] w-full resize-none border-0 bg-transparent px-2 py-1.5 text-sm sm:text-base text-slate-800 placeholder:text-slate-400 focus-visible:ring-0 focus-visible:outline-none leading-relaxed shadow-none"
            disabled={disabled}
            rows={1}
          />
        </div>

        {/* Bottom Toolbar inside the Composer */}
        <div className="flex items-center justify-between pt-1 px-1 mt-1">
          {/* Left Actions: Compact PDF Attachment Button */}
          <div className="flex items-center gap-1.5">
            {onUploadDocument && (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled || isProcessing}
                className={cn(
                  "p-2 rounded-full text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 transition-colors flex items-center justify-center disabled:opacity-40",
                  isDragging && "text-indigo-600 bg-indigo-100"
                )}
                title="Add knowledge: Upload PDF document"
              >
                <Paperclip className="h-4 w-4" />
                <span className="sr-only">Attach PDF</span>
              </button>
            )}

            {isDragging && (
              <span className="text-[11px] font-medium text-indigo-600 animate-pulse">
                Drop PDF to attach
              </span>
            )}
          </div>

          {/* Right Action: Circular Send Button & Status */}
          <div className="flex items-center gap-2">
            {isConnecting && (
              <span className="text-xs text-indigo-600 font-medium italic flex items-center gap-1.5 hidden sm:inline-flex">
                <span className="inline-block h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
                Generating response...
              </span>
            )}

            <Button
              size="icon"
              className="h-8 w-8 sm:h-9 sm:w-9 rounded-full bg-slate-900 hover:bg-slate-800 text-white shadow-sm transition-transform active:scale-95 disabled:bg-slate-300 disabled:opacity-40"
              disabled={!content.trim() || disabled || isProcessing}
              onClick={handleSend}
              title="Send Message"
            >
              <SendHorizontal className="h-4 w-4" />
              <span className="sr-only">Send</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Subtle Caption / Disclaimer */}
      <div className="text-center pt-2 pb-1 text-[11px] text-slate-400">
        <span>Lenny Growth Assistant can synthesize 33 podcast transcripts, write atomic essays, and build HTML prototypes.</span>
      </div>
    </div>
  )
}
