import React, { useState } from "react"
import { Cpu, Cloud, AlertCircle, CheckCircle2, ChevronDown } from "lucide-react"
import type { LLMProvider, ProviderDetail } from "@/types"

interface ProviderSelectorProps {
  currentProvider: LLMProvider
  onProviderChange: (provider: LLMProvider) => void
  providers: ProviderDetail[]
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  currentProvider,
  onProviderChange,
  providers,
}) => {
  const [isOpen, setIsOpen] = useState(false)

  const activeDetail = providers.find((p) => p.id === currentProvider) || {
    id: currentProvider,
    name: currentProvider === "claude" ? "Claude AI (Cloud)" : "Ollama (Local)",
    type: currentProvider === "claude" ? "cloud" : "local",
    model: currentProvider === "claude" ? "claude-3-5-sonnet-20241022" : "qwen3:4b",
    available: currentProvider === "ollama",
    description: "",
  }

  const handleSelect = (providerId: LLMProvider) => {
    onProviderChange(providerId)
    setIsOpen(false)
  }

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-all shadow-sm"
        aria-label="Select LLM Provider"
      >
        {currentProvider === "claude" ? (
          <Cloud className="h-4 w-4 text-purple-600 shrink-0" />
        ) : (
          <Cpu className="h-4 w-4 text-emerald-600 shrink-0" />
        )}
        <div className="flex flex-col items-start text-left">
          <div className="flex items-center gap-1.5 leading-none">
            <span className="font-semibold text-slate-800">
              {currentProvider === "claude" ? "Claude AI" : "Ollama"}
            </span>
            <span className="text-[10px] text-slate-500 font-normal">
              ({currentProvider === "claude" ? "Cloud" : "Local"})
            </span>
            {activeDetail.available ? (
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" title="Available & Configured" />
            ) : (
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" title="Key not configured" />
            )}
          </div>
          <span className="text-[10px] text-slate-400 font-mono mt-0.5">
            {activeDetail.model}
          </span>
        </div>
        <ChevronDown className="h-3 w-3 text-slate-400 ml-1" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-72 rounded-xl bg-white shadow-xl border border-slate-200 z-50 py-2 divide-y divide-slate-100">
            <div className="px-3 py-2">
              <p className="text-xs font-semibold text-slate-900">Select Model Provider</p>
              <p className="text-[11px] text-slate-500">
                Choose between local offline execution or cloud LLM inference.
              </p>
            </div>

            <div className="p-1.5 space-y-1">
              {/* Ollama option */}
              {(() => {
                const ollamaDetail = providers.find((p) => p.id === "ollama")
                const isSelected = currentProvider === "ollama"
                return (
                  <button
                    key="ollama"
                    type="button"
                    onClick={() => handleSelect("ollama")}
                    className={`w-full flex items-start gap-2.5 p-2 rounded-lg text-left transition-all ${
                      isSelected
                        ? "bg-emerald-50 border border-emerald-200"
                        : "hover:bg-slate-50 border border-transparent"
                    }`}
                  >
                    <div className="mt-0.5 p-1 rounded-md bg-emerald-100 text-emerald-700">
                      <Cpu className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-900">
                          Ollama — Local
                        </span>
                        {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Offline privacy · <span className="font-mono text-[10px] text-slate-600">{ollamaDetail?.model || "qwen3:4b"}</span>
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="text-[10px] text-emerald-700 font-medium">Ready (Offline)</span>
                      </div>
                    </div>
                  </button>
                )
              })()}

              {/* Claude option */}
              {(() => {
                const claudeDetail = providers.find((p) => p.id === "claude")
                const isSelected = currentProvider === "claude"
                const isConfigured = claudeDetail ? claudeDetail.available : false

                return (
                  <button
                    key="claude"
                    type="button"
                    onClick={() => handleSelect("claude")}
                    className={`w-full flex items-start gap-2.5 p-2 rounded-lg text-left transition-all ${
                      isSelected
                        ? "bg-purple-50 border border-purple-200"
                        : "hover:bg-slate-50 border border-transparent"
                    }`}
                  >
                    <div className="mt-0.5 p-1 rounded-md bg-purple-100 text-purple-700">
                      <Cloud className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-900">
                          Claude AI — Cloud
                        </span>
                        {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-purple-600" />}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Anthropic API · <span className="font-mono text-[10px] text-slate-600">{claudeDetail?.model || "claude-3-5-sonnet"}</span>
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        {isConfigured ? (
                          <>
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                            <span className="text-[10px] text-emerald-700 font-medium">API Key Configured</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-3 w-3 text-amber-500 shrink-0" />
                            <span className="text-[10px] text-amber-700 font-medium">Key missing in .env</span>
                          </>
                        )}
                      </div>
                    </div>
                  </button>
                )
              })()}
            </div>

            <div className="px-3 py-2 bg-slate-50 rounded-b-xl text-[10px] text-slate-500">
              💡 Selection applies to RAG Research, Ship 30 writing, and Artifact Generation.
            </div>
          </div>
        </>
      )}
    </div>
  )
}
