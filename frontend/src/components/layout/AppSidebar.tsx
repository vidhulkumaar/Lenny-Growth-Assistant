import React from "react"
import { Plus, MessageSquare, Settings, PanelLeftClose, PanelLeft } from "lucide-react"
import type { Session } from "@/types"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface AppSidebarProps {
  sessions: Session[]
  activeSessionId?: string
  onSelectSession: (id: string) => void
  onNewChat: () => void
  onOpenSettings: () => void
  isOpen: boolean
  onToggle: () => void
}

export const AppSidebar: React.FC<AppSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onOpenSettings,
  isOpen,
  onToggle,
}) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm lg:hidden"
          onClick={onToggle}
        />
      )}
      
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-slate-50 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4">
          <span className="font-semibold text-slate-900">Growth Assistant</span>
          <Button variant="ghost" size="icon" onClick={onToggle} className="lg:hidden">
            <PanelLeftClose className="h-5 w-5 text-slate-500" />
          </Button>
        </div>

        <div className="p-4">
          <Button onClick={onNewChat} className="w-full justify-start gap-2" variant="outline">
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2">
          <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Recent
          </h3>
          <div className="space-y-1">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors text-left",
                  activeSessionId === session.id
                    ? "bg-indigo-100 text-indigo-900 font-medium"
                    : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900"
                )}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate">{session.title}</span>
              </button>
            ))}
            {sessions.length === 0 && (
              <div className="px-2 py-4 text-sm text-slate-400 text-center italic">
                No recent conversations
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-slate-200 p-4">
          <Button onClick={onOpenSettings} variant="ghost" className="w-full justify-start gap-2 text-slate-600">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>
      
      {/* Sidebar Toggle for Desktop/Mobile when closed */}
      {!isOpen && (
        <Button
          variant="outline"
          size="icon"
          onClick={onToggle}
          className="fixed left-4 top-4 z-40 bg-white/80 backdrop-blur-sm"
        >
          <PanelLeft className="h-5 w-5 text-slate-600" />
        </Button>
      )}
    </>
  )
}
