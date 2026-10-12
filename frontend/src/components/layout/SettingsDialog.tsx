import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Database, Cpu, Cloud, CheckCircle2, AlertCircle, Info, Trash2 } from "lucide-react"
import type { LLMProvider, ProviderDetail } from "@/types"

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentProvider: LLMProvider
  onProviderChange: (provider: LLMProvider) => void
  providers: ProviderDetail[]
  onOpenClearHistory?: () => void
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({
  open,
  onOpenChange,
  currentProvider,
  onProviderChange,
  providers,
  onOpenClearHistory,
}) => {
  const ollama = providers.find((p) => p.id === "ollama")
  const claude = providers.find((p) => p.id === "claude")

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>System Status & Model Settings</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Active Provider Selector Section */}
          <div>
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-2">
              Select Active LLM Provider
            </label>
            <div className="grid grid-cols-2 gap-2">
              {/* Ollama card */}
              <button
                type="button"
                onClick={() => onProviderChange("ollama")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  currentProvider === "ollama"
                    ? "border-emerald-500 bg-emerald-50/70 shadow-sm ring-1 ring-emerald-500"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="p-1 rounded-md bg-emerald-100 text-emerald-700">
                    <Cpu className="h-4 w-4" />
                  </div>
                  {currentProvider === "ollama" && (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  )}
                </div>
                <div className="font-semibold text-xs text-slate-900">Ollama (Local)</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                  {ollama?.model || "qwen3:4b"}
                </div>
                <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-700 font-medium">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Ready
                </div>
              </button>

              {/* Claude card */}
              <button
                type="button"
                onClick={() => onProviderChange("claude")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  currentProvider === "claude"
                    ? "border-purple-500 bg-purple-50/70 shadow-sm ring-1 ring-purple-500"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="p-1 rounded-md bg-purple-100 text-purple-700">
                    <Cloud className="h-4 w-4" />
                  </div>
                  {currentProvider === "claude" && (
                    <CheckCircle2 className="h-4 w-4 text-purple-600" />
                  )}
                </div>
                <div className="font-semibold text-xs text-slate-900">Claude AI (Cloud)</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
                  {claude?.model || "claude-3-5-sonnet"}
                </div>
                <div className="mt-2 flex items-center gap-1 text-[10px] font-medium">
                  {claude?.available ? (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span className="text-emerald-700">Key Ready</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-3 w-3 text-amber-500" />
                      <span className="text-amber-700">Key Required</span>
                    </>
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Claude Notice if unconfigured and selected */}
          {currentProvider === "claude" && claude && !claude.available && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="font-medium text-amber-900">Anthropic API Key Not Set</p>
                  <p className="text-[11px] text-amber-700 leading-relaxed">
                    Set <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">ANTHROPIC_API_KEY</code> in{" "}
                    <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">backend/.env</code> to enable Cloud inference.
                  </p>
                  <button
                    type="button"
                    onClick={() => onProviderChange("ollama")}
                    className="mt-1 text-[11px] font-semibold text-emerald-800 hover:underline inline-flex items-center gap-1"
                  >
                    Switch back to Ollama (Local) →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Chat & Search History Management */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
              Chat & Search History
            </label>
            <div className="flex items-center justify-between rounded-lg border border-slate-200 p-2.5 bg-slate-50">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-md bg-red-100 text-red-700">
                  <Trash2 className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-900">Manage History</p>
                  <p className="text-[11px] text-slate-500">Clear selected or all chat and search records</p>
                </div>
              </div>
              {onOpenClearHistory && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    onOpenChange(false)
                    onOpenClearHistory()
                  }}
                  className="text-xs h-7 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 font-medium"
                >
                  Clear History...
                </Button>
              )}
            </div>
          </div>

          {/* Infrastructure status */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block">
              System Connections
            </label>

            {/* Knowledge Base */}
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-2.5 bg-slate-50">
              <Database className="h-4 w-4 text-indigo-600" />
              <div className="flex-1">
                <p className="text-xs font-medium text-slate-900">Knowledge Base (pgvector)</p>
                <p className="text-[11px] text-slate-500">PostgreSQL + 7,023 indexed chunks</p>
              </div>
              <span className="text-[10px] font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                Connected
              </span>
            </div>

            {/* Agent orchestration info */}
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-2.5 bg-slate-50">
              <Info className="h-4 w-4 text-blue-600" />
              <div className="flex-1">
                <p className="text-xs font-medium text-slate-900">Agent Routing</p>
                <p className="text-[11px] text-slate-500">RAG, Ship 30 & Artifacts all route through selected provider</p>
              </div>
              <span className="text-[10px] font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                Active
              </span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
