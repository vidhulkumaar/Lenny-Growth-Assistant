import React, { useRef, useEffect, useState } from "react"
import { SendHorizontal, Sparkles, MessageSquare, Feather } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface MessageComposerProps {
  onSend: (message: string, mode?: "chat" | "ship30", writingOptions?: Record<string, any>) => void
  disabled?: boolean
  isConnecting?: boolean
}

export const MessageComposer: React.FC<MessageComposerProps> = ({ onSend, disabled, isConnecting }) => {
  const [content, setContent] = useState("")
  const [mode, setMode] = useState<"chat" | "ship30">("chat")
  const [formatStyle, setFormatStyle] = useState<string>("Atomic Essay")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [content])

  const handleSend = () => {
    if (content.trim() && !disabled) {
      const writingOptions = mode === "ship30" ? { format_style: formatStyle } : undefined
      onSend(content.trim(), mode, writingOptions)
      setContent("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="relative flex flex-col w-full bg-white border-t border-slate-200">
      {/* Mode Selector Header */}
      <div className="flex items-center justify-between px-4 pt-2.5 pb-1 gap-2 border-b border-slate-100 text-xs">
        <div className="flex items-center gap-1.5 bg-slate-100 p-0.5 rounded-lg">
          <button
            type="button"
            onClick={() => setMode("chat")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all font-medium ${
              mode === "chat"
                ? "bg-white text-slate-800 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Q&A Mode</span>
          </button>
          <button
            type="button"
            onClick={() => setMode("ship30")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all font-medium ${
              mode === "ship30"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <Feather className="h-3.5 w-3.5" />
            <span>Ship 30 for 30</span>
          </button>
        </div>

        {mode === "ship30" && (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 text-[11px] hidden sm:inline">Format:</span>
            {["Atomic Essay", "Framework Breakdown", "Actionable Steps"].map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => setFormatStyle(style)}
                className={`px-2 py-0.5 text-[11px] rounded transition-colors ${
                  formatStyle === style
                    ? "bg-indigo-100 text-indigo-700 font-medium"
                    : "text-slate-500 hover:bg-slate-100"
                }`}
              >
                {style}
              </button>
            ))}
          </div>
        )}
      </div>

      {mode === "ship30" && (
        <div className="px-4 py-1.5 bg-indigo-50/60 border-b border-indigo-100/60 text-xs text-indigo-700 flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 shrink-0 text-indigo-500" />
          <span>
            <strong>Ship 30 for 30 Skill Active:</strong> Transforming rough ideas into structured, evidence-grounded atomic writing.
          </span>
        </div>
      )}

      {/* Input Field */}
      <div className="relative flex w-full items-end gap-2 p-3">
        <div className="relative w-full">
          <Textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              mode === "ship30"
                ? "Enter your rough topic or idea to write an atomic essay on..."
                : "Ask a product or growth question..."
            }
            className="min-h-[44px] w-full resize-none bg-slate-50 pr-12 text-base py-3 leading-relaxed shadow-sm rounded-lg"
            disabled={disabled}
            rows={1}
          />
          <Button
            size="icon"
            className="absolute bottom-1 right-1 h-8 w-8 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
            disabled={!content.trim() || disabled}
            onClick={handleSend}
          >
            <SendHorizontal className="h-4 w-4" />
            <span className="sr-only">Send</span>
          </Button>
        </div>
      </div>

      {isConnecting && (
        <div className="px-4 pb-2 text-xs text-slate-500 italic flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
          {mode === "ship30" ? "Drafting Ship 30 for 30 essay..." : "Querying assistant..."}
        </div>
      )}
    </div>
  )
}
