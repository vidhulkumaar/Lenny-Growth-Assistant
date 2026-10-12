import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { User, Bot, ExternalLink, Sparkles } from "lucide-react"
import type { Message } from "@/types"
import { SourceCitation } from "./SourceCitation"
import { cn } from "@/lib/utils"

export const ChatMessage: React.FC<{
  message: Message
  onViewArtifact?: () => void
}> = ({ message, onViewArtifact }) => {
  const isUser = message.role === "user"
  const hasArtifactMention =
    !isUser &&
    (message.content.includes("Artifact Viewer") ||
      message.content.includes("artifact"))

  return (
    <div className={cn("flex gap-4 p-4", isUser ? "bg-white" : "bg-slate-50")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
          isUser
            ? "bg-white border-slate-200"
            : "bg-indigo-100 border-indigo-200 text-indigo-600"
        )}
      >
        {isUser ? <User className="h-5 w-5 text-slate-500" /> : <Bot className="h-5 w-5" />}
      </div>
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="prose prose-slate prose-sm sm:prose-base max-w-none break-words">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {hasArtifactMention && onViewArtifact && (
          <div className="pt-2">
            <button
              onClick={onViewArtifact}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 shadow-sm transition-all hover:shadow"
            >
              <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
              <span>Open in Artifact Viewer</span>
              <ExternalLink className="h-3 w-3 opacity-70 ml-0.5" />
            </button>
          </div>
        )}

        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium text-slate-900">Sources</h4>
            <div className="grid gap-2 sm:grid-cols-2">
              {message.citations.map((citation, i) => (
                <SourceCitation key={i} citation={citation} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

