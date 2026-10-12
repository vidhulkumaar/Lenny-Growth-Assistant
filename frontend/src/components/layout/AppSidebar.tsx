import React, { useState } from "react"
import {
  Menu,
  Plus,
  MessageSquare,
  Radio,
  TrendingUp,
  Feather,
  Layers,
  Settings,
  HelpCircle,
  Sparkles,
  Trash2,
} from "lucide-react"
import type { Session } from "@/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

export type WorkspaceNav = "podcast" | "growth" | "writing" | "artifacts"

interface AppSidebarProps {
  sessions: Session[]
  activeSessionId?: string
  onSelectSession: (id: string) => void
  onNewChat: () => void
  onOpenSettings: () => void
  isOpen: boolean
  onToggle: () => void
  onSelectTopicPrompt?: (prompt: string) => void
  artifactsCount?: number
  onOpenArtifacts?: () => void
  onOpenHelp?: () => void
  onOpenClearHistory?: () => void
  onDeleteSession?: (id: string) => Promise<void> | void
}

export const AppSidebar: React.FC<AppSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onOpenSettings,
  isOpen,
  onToggle,
  onSelectTopicPrompt,
  artifactsCount = 0,
  onOpenArtifacts,
  onOpenHelp,
  onOpenClearHistory,
  onDeleteSession,
}) => {
  const [sessionToDelete, setSessionToDelete] = useState<Session | null>(null)
  const [isDeletingSession, setIsDeletingSession] = useState(false)

  const topicShortcuts = [
    {
      label: "Podcast Research",
      icon: Radio,
      prompt: "What are the most important frameworks for product-market fit from Lenny's Podcast?",
    },
    {
      label: "Product Growth",
      icon: TrendingUp,
      prompt: "Explain the product-led growth engine and how to optimize user time-to-value.",
    },
    {
      label: "Ship 30 Writing",
      icon: Feather,
      prompt: "Write a Ship 30 for 30 atomic essay about customer retention and churn.",
    },
  ]

  const handleConfirmSingleDelete = async () => {
    if (!sessionToDelete || !onDeleteSession) return
    setIsDeletingSession(true)
    try {
      await onDeleteSession(sessionToDelete.id)
      setSessionToDelete(null)
    } finally {
      setIsDeletingSession(false)
    }
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-xs lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Gemini-Inspired Navigation Sidebar (~250px) */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[250px] flex-col bg-[#f0f4f9] border-r border-slate-200/80 transition-all duration-200 ease-in-out select-none overflow-hidden",
          isOpen
            ? "translate-x-0 lg:static lg:w-[250px] lg:opacity-100"
            : "-translate-x-full lg:-translate-x-full lg:w-0 lg:min-w-0 lg:max-w-0 lg:border-none lg:p-0 lg:opacity-0 pointer-events-none"
        )}
        aria-label="Gemini-Style Navigation"
      >
        {/* Top Header: Hamburger & Monogram */}
        <div className="flex h-14 items-center justify-between px-3.5">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="h-9 w-9 rounded-full text-slate-600 hover:text-slate-900 hover:bg-slate-200/70"
            title="Collapse sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex items-center gap-2 mr-1">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-2xs">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <span className="font-medium text-xs text-slate-800">
              Lenny Growth
            </span>
          </div>
        </div>

        {/* Gemini-Style Pill "+ New chat" Button */}
        <div className="px-3 pt-1 pb-3">
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-3 w-full px-4 py-2.5 rounded-full bg-[#dde3ea] hover:bg-[#d0d8e2] text-slate-800 text-xs sm:text-sm font-medium transition-colors shadow-2xs active:scale-[0.99]"
          >
            <Plus className="h-4 w-4 text-slate-700" />
            <span>New chat</span>
          </button>
        </div>

        {/* Recent Conversations */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="flex items-center justify-between px-3 mb-1">
            <h2 className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
              Recent
            </h2>
            {onOpenClearHistory && sessions.length > 0 && (
              <button
                type="button"
                onClick={onOpenClearHistory}
                className="text-[11px] text-slate-400 hover:text-red-600 transition-colors flex items-center gap-1 font-medium"
                title="Clear History"
              >
                <Trash2 className="h-3 w-3" />
                <span>Clear</span>
              </button>
            )}
          </div>

          <div className="space-y-0.5">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group relative flex items-center rounded-full text-xs transition-colors",
                  activeSessionId === session.id
                    ? "bg-[#dde3ea] text-slate-900 font-medium"
                    : "text-slate-600 hover:bg-[#e4ebf3] hover:text-slate-900"
                )}
              >
                <button
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                  className="flex items-center gap-2.5 flex-1 min-w-0 px-3 py-2 text-left truncate"
                  title={session.title}
                >
                  <MessageSquare className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="truncate flex-1">{session.title}</span>
                </button>
                {onDeleteSession && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSessionToDelete(session)
                    }}
                    className="opacity-0 group-hover:opacity-100 mr-2 p-1 rounded-full text-slate-400 hover:text-red-600 hover:bg-red-100/60 transition-opacity shrink-0"
                    title={`Delete conversation "${session.title}"`}
                    aria-label={`Delete ${session.title}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            ))}

            {sessions.length === 0 && (
              <div className="px-3 py-4 text-xs text-slate-400 italic">
                No recent conversations
              </div>
            )}
          </div>

          {/* Topics & Shortcuts */}
          <div className="pt-4 border-t border-slate-200/60 mt-3">
            <h2 className="px-3 text-[11px] font-semibold tracking-wide text-slate-500 uppercase mb-1">
              Shortcuts
            </h2>
            <div className="space-y-0.5">
              {topicShortcuts.map((topic) => {
                const Icon = topic.icon
                return (
                  <button
                    key={topic.label}
                    type="button"
                    onClick={() => onSelectTopicPrompt?.(topic.prompt)}
                    className="flex items-center gap-2.5 w-full px-3 py-1.5 rounded-full text-xs text-slate-600 hover:bg-[#e4ebf3] hover:text-slate-900 transition-colors text-left"
                    title={topic.prompt}
                  >
                    <Icon className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                    <span className="truncate">{topic.label}</span>
                  </button>
                )
              })}

              {/* Artifacts Shortcut */}
              <button
                type="button"
                onClick={onOpenArtifacts}
                className="flex items-center justify-between w-full px-3 py-1.5 rounded-full text-xs text-slate-600 hover:bg-[#e4ebf3] hover:text-slate-900 transition-colors text-left"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Layers className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">Artifacts</span>
                </div>
                {artifactsCount > 0 && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                    {artifactsCount}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Actions: Clear History, Settings & Help */}
        <div className="p-3 border-t border-slate-200/80 space-y-0.5">
          {onOpenClearHistory && (
            <button
              type="button"
              onClick={onOpenClearHistory}
              className="flex items-center gap-3 w-full px-3 py-2 rounded-full text-xs text-slate-600 hover:bg-red-50 hover:text-red-700 transition-colors"
            >
              <Trash2 className="h-4 w-4 text-slate-500" />
              <span>Clear History</span>
            </button>
          )}

          <button
            type="button"
            onClick={onOpenSettings}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-full text-xs text-slate-600 hover:bg-[#e4ebf3] hover:text-slate-900 transition-colors"
          >
            <Settings className="h-4 w-4 text-slate-500" />
            <span>Settings</span>
          </button>

          {onOpenHelp && (
            <button
              type="button"
              onClick={onOpenHelp}
              className="flex items-center gap-3 w-full px-3 py-2 rounded-full text-xs text-slate-600 hover:bg-[#e4ebf3] hover:text-slate-900 transition-colors"
            >
              <HelpCircle className="h-4 w-4 text-slate-500" />
              <span>Help & Docs</span>
            </button>
          )}
        </div>
      </aside>

      {/* Individual Session Delete Confirmation Dialog */}
      <Dialog
        open={!!sessionToDelete}
        onOpenChange={(open) => !open && setSessionToDelete(null)}
      >
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-sm">Delete Conversation</DialogTitle>
            <DialogDescription className="text-xs pt-1">
              Are you sure you want to delete &ldquo;{sessionToDelete?.title}&rdquo;?
              This will remove all messages in this conversation. Any generated artifacts and documents will remain safe.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSessionToDelete(null)}
              disabled={isDeletingSession}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleConfirmSingleDelete}
              disabled={isDeletingSession}
              className="text-xs bg-red-600 hover:bg-red-700"
            >
              {isDeletingSession ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
