import React from "react"
import {
  Radio,
  TrendingUp,
  Feather,
  Layers,
  Sparkles,
  ExternalLink,
  Code2,
  FileText,
  ArrowRight,
  Menu,
  MessageSquare,
} from "lucide-react"
import type { WorkspaceNav } from "@/components/layout/AppSidebar"
import { CompactDocumentUploader } from "@/components/chat/CompactDocumentUploader"
import type { DocumentInfo } from "@/services/api"
import type { Artifact } from "@/types"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface WorkspaceBoardProps {
  activeNav: WorkspaceNav
  onSelectNav: (nav: WorkspaceNav) => void
  documents: DocumentInfo[]
  onUploadDocument: (file: File) => Promise<void>
  onRemoveDocument: (id: string) => void
  artifacts: Artifact[]
  activeArtifact: Artifact | null
  onSelectArtifact: (art: Artifact) => void
  onOpenArtifactViewer: () => void
  onExecutePrompt: (prompt: string) => void
  isConnecting: boolean
  onToggleSidebar?: () => void
  onToggleChat?: () => void
  isChatVisible?: boolean
}

export const WorkspaceBoard: React.FC<WorkspaceBoardProps> = ({
  activeNav,
  documents,
  onUploadDocument,
  onRemoveDocument,
  artifacts,
  onSelectArtifact,
  onOpenArtifactViewer,
  onExecutePrompt,
  isConnecting,
  onToggleSidebar,
  onToggleChat,
  isChatVisible = true,
}) => {
  // Titles & descriptions for each navigation section
  const sectionMeta: Record<
    WorkspaceNav,
    { title: string; subtitle: string; icon: React.FC<{ className?: string }>; badge: string }
  > = {
    podcast: {
      title: "Podcast Research",
      subtitle: "Grounded insights & verbatim citations across 33 podcast transcripts.",
      icon: Radio,
      badge: "33 Episodes • 7,023 Chunks",
    },
    growth: {
      title: "Product Growth",
      subtitle: "Strategic frameworks for PMF, retention curves, growth loops, and packaging.",
      icon: TrendingUp,
      badge: "Growth Frameworks",
    },
    writing: {
      title: "Ship 30 Writing",
      subtitle: "Transform raw growth knowledge into structured atomic essays via the 1-3-1 formula.",
      icon: Feather,
      badge: "1-3-1 Digital Writing",
    },
    artifacts: {
      title: "Artifacts",
      subtitle: "Persisted HTML UI prototypes, dashboards, and Markdown strategy documents.",
      icon: Layers,
      badge: `${artifacts.length} Generated`,
    },
  }

  const currentMeta = sectionMeta[activeNav]
  const SectionIcon = currentMeta.icon

  // Cards data for Podcast Research
  const podcastCards = [
    {
      category: "PMF & Validation",
      title: "Finding Product-Market Fit",
      description: "Diagnosing genuine market pull, flattening cohort retention curves, and validating PMF before scaling.",
      prompt: "How should a startup find product-market fit?",
    },
    {
      category: "Retention & Churn",
      title: "Retention & Churn Dynamics",
      description: "Diagnosing leaky buckets, customer payback periods, and cohort churn mechanics.",
      prompt: "What are the key lessons about customer retention from Lenny's Podcast?",
    },
    {
      category: "Growth Loops",
      title: "Self-Reinforcing Growth Loops",
      description: "Replacing traditional leaky funnels with viral, paid, and product-led growth flywheels.",
      prompt: "How do you design and optimize product-led growth loops?",
    },
    {
      category: "Monetization",
      title: "SaaS Pricing & Packaging Strategy",
      description: "Value metric alignment, tier boundaries, price elasticity, and freemium vs. reverse trials.",
      prompt: "What are key lessons on SaaS pricing and packaging from top growth leaders?",
    },
    {
      category: "Product Leadership",
      title: "High-Agency Product Management",
      description: "Prioritization frameworks, managing execution busywork, and high-impact decision heuristics.",
      prompt: "What did Shreyas Doshi share about why product managers are always busy and how to fix it?",
    },
    {
      category: "Customer Discovery",
      title: "Customer Discovery & Feedback",
      description: "Continuous interviewing techniques, uncovering latent pain points, and avoiding false validation.",
      prompt: "What are the most effective customer discovery techniques from Lenny's guests?",
    },
  ]

  // Cards data for Product Growth
  const growthCards = [
    {
      category: "PLG Engine",
      title: "Product-Led Growth Architecture",
      description: "Self-serve onboarding, frictionless time-to-value, and viral expansion mechanics.",
      prompt: "Explain the product-led growth engine and how to optimize time-to-value.",
    },
    {
      category: "Activation",
      title: "Activation Funnel Optimization",
      description: "Identifying setup moments, aha moments, and forming habitual user engagement loops.",
      prompt: "How do you systematically optimize user activation and reach the aha moment?",
    },
    {
      category: "B2B Sales",
      title: "Bottom-Up to Enterprise Expansion",
      description: "Bridging product-led user adoption into top-down six-figure enterprise contracts.",
      prompt: "How do consumer-grade products transition to enterprise sales?",
    },
    {
      category: "North Star",
      title: "North Star Metric Selection",
      description: "Choosing and cascading input metrics that align customer value with business growth.",
      prompt: "How do you choose and structure the right North Star Metric for your product?",
    },
  ]

  // Cards data for Ship 30 Writing
  const writingCards = [
    {
      category: "Atomic Essay",
      title: "1-3-1 Atomic Essay Playbook",
      description: "Headline hook, reader friction, 3-4 structured body points, and an actionable takeaway.",
      prompt: "Write a Ship 30 for 30 atomic essay about product-led growth",
    },
    {
      category: "Retention Essay",
      title: "The Silent Killer of Growth",
      description: "An atomic essay dissecting why acquisition cannot compensate for poor customer retention.",
      prompt: "Write a Ship 30 for 30 atomic essay about customer retention",
    },
    {
      category: "Playbook Breakdown",
      title: "5 Steps to Product-Market Fit",
      description: "A concise, high-signal teardown of validating market pull before scaling spend.",
      prompt: "Write a Ship 30 essay breaking down the 5 steps to product-market fit",
    },
    {
      category: "Contrarian Take",
      title: "Counter-Intuitive Growth Rules",
      description: "Challenging conventional startup playbooks with counter-intuitive data and lessons.",
      prompt: "Write a Ship 30 essay on why most growth playbooks fail",
    },
  ]

  // Prompt templates for empty Artifacts state
  const artifactStarterCards = [
    {
      category: "HTML Dashboard",
      title: "SaaS Analytics Dashboard",
      description: "Generate an interactive, responsive HTML dashboard with KPI cards and charts.",
      prompt: "Create a responsive HTML dashboard with KPI cards and charts",
    },
    {
      category: "Markdown Report",
      title: "Executive Retention Report",
      description: "Generate a structured Markdown report on customer cohort retention and churn.",
      prompt: "Create a Markdown project report on user retention",
    },
    {
      category: "HTML Interactive",
      title: "Interactive Pricing Calculator",
      description: "Generate a responsive HTML pricing and tier calculator with interactive sliders.",
      prompt: "Create an interactive HTML pricing calculator with slider controls",
    },
  ]

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-white min-w-0">
      {/* Workspace Header with Toolbar and Compact PDF Uploader */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200/80 px-4 bg-white/90 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3 min-w-0">
          {onToggleSidebar && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleSidebar}
              className="lg:hidden h-8 w-8 text-slate-500 hover:text-slate-800"
              title="Open Navigation"
            >
              <Menu className="h-4 w-4" />
            </Button>
          )}

          <div className="flex items-center gap-2 min-w-0">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-100 text-slate-700 shrink-0">
              <SectionIcon className="h-4 w-4 text-indigo-600" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-slate-900 truncate">
                {currentMeta.title}
              </h2>
            </div>
            <span className="hidden sm:inline-flex text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {currentMeta.badge}
            </span>
          </div>
        </div>

        {/* Right Toolbar: Compact PDF Uploader + Artifacts Badge + Mobile Chat Toggle */}
        <div className="flex items-center gap-2 shrink-0">
          <CompactDocumentUploader
            documents={documents}
            onUpload={onUploadDocument}
            onRemove={onRemoveDocument}
            disabled={isConnecting}
          />

          {artifacts.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenArtifactViewer}
              className="h-9 px-2.5 gap-1.5 text-xs text-indigo-700 bg-indigo-50/70 border-indigo-200 hover:bg-indigo-100 shadow-sm"
              title="Open in-app Artifact Viewer"
            >
              <Layers className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Artifacts</span>
              <span className="font-semibold">({artifacts.length})</span>
            </Button>
          )}

          {onToggleChat && (
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleChat}
              className="lg:hidden h-9 px-2.5 gap-1.5 text-xs text-slate-700 border-slate-200"
              title="Toggle Chat Panel"
            >
              <MessageSquare className="h-3.5 w-3.5 text-slate-500" />
              <span>{isChatVisible ? "Hide Chat" : "Open Chat"}</span>
            </Button>
          )}
        </div>
      </header>

      {/* Workspace Board Canvas */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#fafafa]">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Subtitle / Context description */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-2 border-b border-slate-200/60">
            <div>
              <p className="text-xs sm:text-sm text-slate-500">
                {currentMeta.subtitle}
              </p>
            </div>
            <div className="text-[11px] text-slate-400">
              Click any card to research or draft in AI Chat →
            </div>
          </div>

          {/* VIEW 1: PODCAST RESEARCH */}
          {activeNav === "podcast" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {podcastCards.map((card, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onExecutePrompt(card.prompt)}
                    disabled={isConnecting}
                    className="group flex flex-col justify-between p-4 rounded-xl bg-white border border-slate-200/90 text-left shadow-sm hover:shadow hover:border-indigo-300 transition-all active:scale-[0.99] disabled:opacity-50"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                          {card.category}
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900 mb-1 group-hover:text-indigo-950">
                        {card.title}
                      </h3>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        {card.description}
                      </p>
                    </div>
                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-indigo-600 font-medium">
                      <span>Query Podcast Vector DB</span>
                      <span>Ask →</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* VIEW 2: PRODUCT GROWTH */}
          {activeNav === "growth" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {growthCards.map((card, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onExecutePrompt(card.prompt)}
                    disabled={isConnecting}
                    className="group flex flex-col justify-between p-4.5 rounded-xl bg-white border border-slate-200/90 text-left shadow-sm hover:shadow hover:border-indigo-300 transition-all active:scale-[0.99] disabled:opacity-50"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                          {card.category}
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-emerald-700 group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900 mb-1.5 group-hover:text-emerald-950">
                        {card.title}
                      </h3>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        {card.description}
                      </p>
                    </div>
                    <div className="mt-4 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-emerald-700 font-medium">
                      <span>Synthesize Growth Playbook</span>
                      <span>Explore →</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* VIEW 3: SHIP 30 WRITING */}
          {activeNav === "writing" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {writingCards.map((card, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onExecutePrompt(card.prompt)}
                    disabled={isConnecting}
                    className="group flex flex-col justify-between p-4.5 rounded-xl bg-white border border-slate-200/90 text-left shadow-sm hover:shadow hover:border-purple-300 transition-all active:scale-[0.99] disabled:opacity-50"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                          {card.category}
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-purple-700 group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900 mb-1.5 group-hover:text-purple-950">
                        {card.title}
                      </h3>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        {card.description}
                      </p>
                    </div>
                    <div className="mt-4 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-purple-700 font-medium">
                      <span>Draft 1-3-1 Atomic Essay</span>
                      <span>Generate →</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* VIEW 4: ARTIFACTS GALLERY */}
          {activeNav === "artifacts" && (
            <div className="space-y-4">
              {artifacts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {artifacts.map((art) => (
                    <div
                      key={art.id}
                      className="flex flex-col justify-between p-4 rounded-xl bg-white border border-slate-200 text-left shadow-sm hover:shadow-md hover:border-indigo-300 transition-all"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span
                            className={cn(
                              "text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider border",
                              art.artifact_type === "html"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : "bg-indigo-50 text-indigo-700 border-indigo-200"
                            )}
                          >
                            {art.artifact_type}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {new Date(art.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 mb-1.5">
                          {art.artifact_type === "html" ? (
                            <Code2 className="h-4 w-4 text-emerald-600 shrink-0" />
                          ) : (
                            <FileText className="h-4 w-4 text-indigo-600 shrink-0" />
                          )}
                          <h3 className="text-sm font-semibold text-slate-900 truncate" title={art.title}>
                            {art.title}
                          </h3>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed font-mono text-[11px] bg-slate-50 p-2 rounded border border-slate-100 mt-2">
                          {art.content.slice(0, 160)}...
                        </p>
                      </div>

                      <div className="mt-4 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            onSelectArtifact(art)
                            onOpenArtifactViewer()
                          }}
                          className="h-8 text-xs font-medium text-indigo-700 border-indigo-200 bg-indigo-50 hover:bg-indigo-100 w-full justify-center gap-1.5"
                        >
                          <ExternalLink className="h-3 w-3" />
                          <span>Open in Artifact Viewer</span>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="p-8 text-center rounded-2xl bg-white border border-slate-200/80 shadow-sm max-w-xl mx-auto">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mx-auto mb-3">
                      <Sparkles className="h-6 w-6" />
                    </div>
                    <h3 className="text-base font-semibold text-slate-900 mb-1">
                      No Artifacts Generated Yet
                    </h3>
                    <p className="text-xs text-slate-500 mb-6 leading-relaxed max-w-md mx-auto">
                      Ask the Lenny Growth Assistant to generate a standalone HTML UI dashboard, pricing calculator, or Markdown strategy report.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
                      Quick Generation Templates
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                      {artifactStarterCards.map((card, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => onExecutePrompt(card.prompt)}
                          disabled={isConnecting}
                          className="group flex flex-col justify-between p-4 rounded-xl bg-white border border-slate-200 text-left shadow-sm hover:shadow hover:border-indigo-300 transition-all active:scale-[0.99] disabled:opacity-50"
                        >
                          <div>
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                              {card.category}
                            </span>
                            <h3 className="text-xs font-semibold text-slate-900 mt-2 mb-1 group-hover:text-indigo-900">
                              {card.title}
                            </h3>
                            <p className="text-[11px] text-slate-500">
                              {card.description}
                            </p>
                          </div>
                          <span className="text-[11px] text-indigo-600 font-medium mt-3 flex items-center gap-1">
                            Generate →
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
