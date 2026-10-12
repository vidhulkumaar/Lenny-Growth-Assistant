import React, { useState, useMemo } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  FileText,
  Code2,
  Copy,
  Check,
  Download,
  X,
  Eye,
  Layers,
  ChevronDown,
  Sparkles,
} from "lucide-react"
import type { Artifact } from "@/types"
import { Button } from "@/components/ui/button"
import { SourceCitation } from "@/components/chat/SourceCitation"
import { cn } from "@/lib/utils"

interface ArtifactViewerProps {
  artifacts: Artifact[]
  activeArtifact: Artifact | null
  onSelectArtifact: (artifact: Artifact) => void
  isOpen: boolean
  onClose: () => void
  isLoading?: boolean
  className?: string
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifacts,
  activeArtifact,
  onSelectArtifact,
  isOpen,
  onClose,
  isLoading = false,
  className,
}) => {
  const [copied, setCopied] = useState(false)
  const [viewMode, setViewMode] = useState<"preview" | "code">("preview")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  // Construct secured HTML with CSP meta-tag to enforce strict sandboxing
  const safeIframeDoc = useMemo(() => {
    if (!activeArtifact || activeArtifact.artifact_type !== "html") return ""

    const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: https:; font-src https: data:;">`
    const content = activeArtifact.content

    if (content.includes("<head>")) {
      return content.replace("<head>", `<head>${csp}`)
    } else if (content.includes("<!DOCTYPE html>")) {
      return content.replace("<!DOCTYPE html>", `<!DOCTYPE html><head>${csp}</head>`)
    }
    return `<!DOCTYPE html><html><head>${csp}</head><body>${content}</body></html>`
  }, [activeArtifact])

  if (!isOpen) return null

  const handleCopy = async () => {
    if (!activeArtifact) return
    try {
      await navigator.clipboard.writeText(activeArtifact.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy content", err)
    }
  }

  const handleDownload = () => {
    if (!activeArtifact) return
    const isHtml = activeArtifact.artifact_type === "html"
    const extension = isHtml ? "html" : "md"
    const mimeType = isHtml ? "text/html;charset=utf-8" : "text/markdown;charset=utf-8"

    const filename = `${activeArtifact.title.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "artifact"}.${extension}`
    const blob = new Blob([activeArtifact.content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <aside
      className={cn(
        "flex flex-col bg-white border-l border-slate-200 transition-all duration-300 ease-in-out shadow-xl lg:shadow-none",
        "fixed inset-0 z-50 lg:static lg:inset-auto lg:z-10 lg:w-[540px] xl:w-[640px] h-full",
        className
      )}
      aria-label="Artifact Viewer"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50/80">
        <div className="flex items-center gap-2 min-w-0">
          {activeArtifact?.artifact_type === "html" ? (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
              <Code2 className="h-4 w-4" />
            </div>
          ) : (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
              <FileText className="h-4 w-4" />
            </div>
          )}

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-900 text-sm truncate">
                {activeArtifact ? activeArtifact.title : "Artifact Viewer"}
              </h3>
              {activeArtifact && (
                <span
                  className={cn(
                    "text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider",
                    activeArtifact.artifact_type === "html"
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                      : "bg-indigo-100 text-indigo-700 border border-indigo-200"
                  )}
                >
                  {activeArtifact.artifact_type}
                </span>
              )}
            </div>

            {/* Multiple Artifact Selector Dropdown */}
            {artifacts.length > 1 && (
              <div className="relative mt-1">
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 transition-colors"
                >
                  <Layers className="h-3 w-3" />
                  <span>{artifacts.length} artifacts in this chat</span>
                  <ChevronDown className="h-3 w-3" />
                </button>

                {isDropdownOpen && (
                  <div className="absolute left-0 top-full mt-1 w-64 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1 max-h-60 overflow-y-auto">
                    {artifacts.map((art) => (
                      <button
                        key={art.id}
                        onClick={() => {
                          onSelectArtifact(art)
                          setIsDropdownOpen(false)
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors",
                          art.id === activeArtifact?.id && "bg-slate-100 font-medium text-indigo-600"
                        )}
                      >
                        <span className="truncate">{art.title}</span>
                        <span className="text-[10px] uppercase font-semibold text-slate-400">
                          {art.artifact_type}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1">
          {/* HTML view mode toggles */}
          {activeArtifact?.artifact_type === "html" && (
            <div className="flex items-center bg-slate-200/70 p-0.5 rounded-lg mr-2 text-xs">
              <button
                onClick={() => setViewMode("preview")}
                className={cn(
                  "flex items-center gap-1 px-2.5 py-1 rounded-md transition-colors",
                  viewMode === "preview" ? "bg-white text-slate-900 shadow-sm font-medium" : "text-slate-600 hover:text-slate-900"
                )}
                title="Rendered sandboxed preview"
              >
                <Eye className="h-3.5 w-3.5" />
                <span>Preview</span>
              </button>
              <button
                onClick={() => setViewMode("code")}
                className={cn(
                  "flex items-center gap-1 px-2.5 py-1 rounded-md transition-colors",
                  viewMode === "code" ? "bg-white text-slate-900 shadow-sm font-medium" : "text-slate-600 hover:text-slate-900"
                )}
                title="View raw HTML/CSS source"
              >
                <Code2 className="h-3.5 w-3.5" />
                <span>Source</span>
              </button>
            </div>
          )}

          {activeArtifact && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-8 px-2 text-slate-600 hover:text-slate-900"
                title="Copy artifact content"
              >
                {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                <span className="ml-1 text-xs">{copied ? "Copied" : "Copy"}</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleDownload}
                className="h-8 px-2 text-slate-600 hover:text-slate-900"
                title="Download artifact file"
              >
                <Download className="h-4 w-4" />
                <span className="ml-1 text-xs">Export</span>
              </Button>
            </>
          )}

          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 text-slate-500 hover:text-slate-900"
            title="Close viewer"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-slate-50">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-3">
            <Sparkles className="h-8 w-8 animate-spin text-indigo-500" />
            <p className="text-sm font-medium">Generating artifact...</p>
          </div>
        ) : !activeArtifact ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 text-center px-6">
            <FileText className="h-12 w-12 text-slate-300 mb-3" />
            <p className="text-sm font-medium text-slate-600">No artifact selected</p>
            <p className="text-xs text-slate-400 mt-1">
              Ask the assistant to generate a product report, landing page, or dashboard mockup.
            </p>
          </div>
        ) : activeArtifact.artifact_type === "html" ? (
          viewMode === "preview" ? (
            <div className="h-full min-h-[480px] w-full rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm flex flex-col">
              <div className="flex items-center justify-between px-3 py-1.5 bg-slate-100 border-b border-slate-200 text-[11px] text-slate-500">
                <span className="font-mono">Sandboxed HTML/CSS Preview</span>
                <span className="bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded font-mono text-[10px]">
                  Scripts Restricted
                </span>
              </div>
              {/* Security Boundary: Sandboxed Iframe without allow-scripts or allow-same-origin */}
              <iframe
                title={activeArtifact.title}
                srcDoc={safeIframeDoc}
                sandbox=""
                className="w-full flex-1 border-0 bg-white min-h-[440px]"
              />
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs font-mono text-slate-200 overflow-x-auto shadow-sm">
              <pre className="whitespace-pre-wrap break-words">{activeArtifact.content}</pre>
            </div>
          )
        ) : (
          /* Markdown Document Rendering */
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <article className="prose prose-slate max-w-none text-slate-800 break-words prose-headings:font-semibold prose-h1:text-2xl prose-h2:text-xl prose-p:leading-relaxed prose-table:border prose-th:bg-slate-50">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {activeArtifact.content}
              </ReactMarkdown>
            </article>

            {/* Citations Footer */}
            {activeArtifact.citations && activeArtifact.citations.length > 0 && (
              <div className="mt-8 pt-4 border-t border-slate-200">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  Document Evidence Citations
                </h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {activeArtifact.citations.map((citation, idx) => (
                    <SourceCitation key={idx} citation={citation} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
