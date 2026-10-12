import React, { useRef, useEffect } from "react"
import { Sparkles, AlertCircle, PlusCircle, X } from "lucide-react"
import { ProviderSelector } from "@/components/layout/ProviderSelector"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { MessageComposer } from "@/components/chat/MessageComposer"
import { WelcomeScreen } from "@/components/chat/WelcomeScreen"
import type { Message, LLMProvider, ProviderDetail, Session } from "@/types"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ChatPanelProps {
  messages: Message[]
  sessions: Session[]
  activeSessionId?: string
  selectedProvider: LLMProvider
  onProviderChange: (provider: LLMProvider) => void
  providers: ProviderDetail[]
  onSendMessage: (content: string) => Promise<void>
  onNewChat: () => void
  onViewArtifact: () => void
  isConnecting: boolean
  isProcessingDocuments: boolean
  isClaudeUnconfigured: boolean
  onCloseMobileChat?: () => void
  className?: string
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  sessions,
  activeSessionId,
  selectedProvider,
  onProviderChange,
  providers,
  onSendMessage,
  onNewChat,
  onViewArtifact,
  isConnecting,
  isProcessingDocuments,
  isClaudeUnconfigured,
  onCloseMobileChat,
  className,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const chatTitle = activeSession ? activeSession.title : "Growth Assistant"

  return (
    <div
      className={cn(
        "flex flex-col bg-white border-l border-slate-200/90 h-full min-w-0 shadow-lg lg:shadow-none select-text",
        className
      )}
    >
      {/* Chat Panel Header */}
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200/80 px-3.5 bg-white z-10">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-50 text-indigo-600 shrink-0">
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-xs text-slate-800 truncate" title={chatTitle}>
              {chatTitle}
            </h3>
            <p className="text-[10px] text-slate-400 font-medium">
              Unified Agent Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <ProviderSelector
            currentProvider={selectedProvider}
            onProviderChange={onProviderChange}
            providers={providers}
          />

          <Button
            variant="ghost"
            size="icon"
            onClick={onNewChat}
            className="h-8 w-8 text-slate-400 hover:text-slate-700 hover:bg-slate-100"
            title="Start new conversation"
          >
            <PlusCircle className="h-4 w-4" />
          </Button>

          {onCloseMobileChat && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onCloseMobileChat}
              className="lg:hidden h-8 w-8 text-slate-400 hover:text-slate-700"
              title="Close chat panel"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Warning banner when Claude is selected but key is missing */}
      {isClaudeUnconfigured && (
        <div className="bg-amber-50 border-b border-amber-200 px-3 py-2 text-xs text-amber-900 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-1.5 min-w-0">
            <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0" />
            <span className="text-[11px] truncate">
              <strong>Claude AI</strong> requires key in <code className="bg-amber-100 px-1 rounded font-mono text-[10px]">backend/.env</code>
            </span>
          </div>
          <button
            onClick={() => onProviderChange("ollama")}
            className="text-[11px] font-semibold text-emerald-800 hover:underline shrink-0 ml-2"
          >
            Switch to Ollama →
          </button>
        </div>
      )}

      {/* Scrollable Conversation Stream */}
      <div className="flex-1 overflow-y-auto min-h-0 bg-white">
        {messages.length === 0 ? (
          <WelcomeScreen onSelectQuestion={onSendMessage} />
        ) : (
          <div className="w-full pb-4 divide-y divide-slate-100">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onViewArtifact={onViewArtifact}
                onSwitchProvider={onProviderChange}
              />
            ))}
            <div ref={messagesEndRef} className="h-2" />
          </div>
        )}
      </div>

      {/* Bottom Fixed Message Composer */}
      <div className="shrink-0 border-t border-slate-200 bg-white">
        <MessageComposer
          onSend={onSendMessage}
          disabled={isConnecting || isProcessingDocuments}
          isConnecting={isConnecting}
        />
      </div>
    </div>
  )
}
