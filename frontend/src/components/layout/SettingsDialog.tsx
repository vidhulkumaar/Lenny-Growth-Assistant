import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Database, Cpu, Globe, Braces } from "lucide-react"

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>System Status & Settings</DialogTitle>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="flex items-center gap-4 rounded-lg border border-slate-200 p-4 bg-slate-50">
            <Globe className="h-5 w-5 text-indigo-500" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">Environment</p>
              <p className="text-xs text-slate-500">Local Development</p>
            </div>
            <div className="flex h-2 w-2 rounded-full bg-green-500"></div>
          </div>

          <div className="flex items-center gap-4 rounded-lg border border-slate-200 p-4">
            <Cpu className="h-5 w-5 text-slate-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">LLM Provider</p>
              <p className="text-xs text-slate-500">Ollama (qwen3:4b)</p>
            </div>
            <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded">Not Connected</span>
          </div>

          <div className="flex items-center gap-4 rounded-lg border border-slate-200 p-4">
            <Database className="h-5 w-5 text-slate-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">Knowledge Base</p>
              <p className="text-xs text-slate-500">Lenny's Podcast Transcripts</p>
            </div>
            <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded">Pending</span>
          </div>

          <div className="flex items-center gap-4 rounded-lg border border-slate-200 p-4 bg-amber-50 border-amber-200">
            <Braces className="h-5 w-5 text-amber-500" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-900">Mock Mode Active</p>
              <p className="text-xs text-amber-700">Chat responses are currently simulated by the frontend.</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
