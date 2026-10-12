import React, { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  Sparkles,
  User,
  Copy,
  Check,
  ExternalLink,
  Cpu,
  Cloud,
  ArrowLeftRight,
} from "lucide-react"
import type { Message, LLMProvider } from "@/types"
import { SourceCitation } from "./SourceCitation"
import { cn } from "@/lib/utils"

export const ChatMessage: React.FC<{
  message: Message
  onViewArtifact?: () => void
  onSwitchProvider?: (provider: LLMProvider) => void
}> = ({ message, onViewArtifact, onSwitchProvider }) => {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === "user"
  const isSystem = message.role === "system"

  const hasArtifactMention =
    !isUser &&
    (message.content.includes("Artifact Viewer") ||
      message.content.includes("artifact"))

  const isClaudeMissingKey =
    !isUser &&
    (message.content.includes("Anthropic API key is not configured") ||
      message.content.includes("ANTHROPIC_API_KEY"))

  const provider = message.provider || (message.role === "assistant" ? "ollama" : undefined)
  const isClaude = provider === "claude"

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (e) {
      console.error("Failed to copy", e)
    }
  }

  // User Message: Gemini-Style Rounded Bubble
  if (isUser) {
    return (
      <div className="flex justify-end w-full py-1">
        <div className="flex items-start gap-2 max-w-[85%] sm:max-w-[75%]">
          <div className="bg-[#f0f4f9] text-slate-800 rounded-3xl rounded-tr-md px-4.5 py-3 text-sm sm:text-base leading-relaxed break-words shadow-2xs">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200/80 text-slate-600 mt-1">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    )
  }

  // Assistant / System Message: Gemini-Style Spacious Text Column
  return (
    <div className={cn("flex flex-col w-full py-3", isSystem && "bg-rose-50/60 p-4 rounded-2xl border border-rose-100")}>
      {/* Assistant Header: Subtle Avatar & Model Attribution */}
      {!isSystem && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <span className="text-xs font-semibold text-slate-800">
              {isClaude ? "Claude AI" : "Lenny Assistant"}
            </span>

            <div
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border",
                isClaude
                  ? "bg-purple-50 text-purple-700 border-purple-200"
                  : "bg-slate-100 text-slate-700 border-slate-200"
              )}
            >
              {isClaude ? <Cloud className="h-2.5 w-2.5" /> : <Cpu className="h-2.5 w-2.5" />}
              <span>{isClaude ? "Claude" : "Ollama"}</span>
              {message.model && (
                <>
                  <span className="text-slate-300">·</span>
                  <span className="font-mono text-[9px]">{message.model}</span>
                </>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={handleCopy}
            className="p-1 text-slate-400 hover:text-slate-700 rounded transition-colors"
            title="Copy response"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      )}

      {/* Message Content: Clean Markdown Rendering */}
      <div className="prose prose-slate prose-sm sm:prose-base max-w-none break-words pl-8 text-slate-800 leading-relaxed">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.content}
        </ReactMarkdown>
      </div>

      {/* If Claude API key is missing, offer quick one-click switch back to Ollama */}
      {isClaudeMissingKey && onSwitchProvider && (
        <div className="pl-8 pt-3">
          <button
            type="button"
            onClick={() => onSwitchProvider("ollama")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow-xs transition-all"
          >
            <ArrowLeftRight className="h-3.5 w-3.5" />
            <span>Switch back to Ollama (Local)</span>
          </button>
        </div>
      )}

      {/* Artifact Viewer Action Card */}
      {hasArtifactMention && onViewArtifact && (
        <div className="pl-8 pt-3">
          <button
            type="button"
            onClick={onViewArtifact}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/90 shadow-2xs transition-all"
          >
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>Open in Artifact Viewer</span>
            <ExternalLink className="h-3 w-3 opacity-70 ml-0.5" />
          </button>
        </div>
      )}

      {/* Grounded Source Citations */}
      {message.citations && message.citations.length > 0 && (
        <div className="pl-8 mt-4 pt-3 border-t border-slate-100 space-y-2">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Sources & Grounding ({message.citations.length})
          </h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {message.citations.map((citation, i) => (
              <SourceCitation key={i} citation={citation} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
