import { useState, useEffect, useRef } from "react"
import { AppSidebar } from "./components/layout/AppSidebar"
import { WelcomeScreen } from "./components/chat/WelcomeScreen"
import { ChatMessage } from "./components/chat/ChatMessage"
import { MessageComposer } from "./components/chat/MessageComposer"
import { SettingsDialog } from "./components/layout/SettingsDialog"
import { ClearHistoryDialog } from "./components/chat/ClearHistoryDialog"
import { ProviderSelector } from "./components/layout/ProviderSelector"
import { ArtifactViewer } from "./components/artifacts/ArtifactViewer"
import { ApiService, type DocumentInfo } from "./services/api"
import type { Session, Message, Artifact, LLMProvider, ProviderDetail } from "./types"
import { Menu, Plus, Layers, AlertCircle, Sparkles } from "lucide-react"
import { Button } from "./components/ui/button"

function App() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>()
  const [messages, setMessages] = useState<Message[]>([])
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null)
  const [isArtifactViewerOpen, setIsArtifactViewerOpen] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isClearHistoryOpen, setIsClearHistoryOpen] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  // LLM Provider state persisted in localStorage
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>(() => {
    const saved = localStorage.getItem("preferred_llm_provider")
    return saved === "claude" || saved === "ollama" ? saved : "ollama"
  })
  const [providers, setProviders] = useState<ProviderDetail[]>([
    {
      id: "ollama",
      name: "Ollama (Local)",
      type: "local",
      model: "qwen3:4b",
      available: true,
      description: "Local offline model running directly via Ollama",
    },
    {
      id: "claude",
      name: "Claude AI (Cloud)",
      type: "cloud",
      model: "claude-3-5-sonnet-20241022",
      available: false,
      description: "Requires ANTHROPIC_API_KEY in backend/.env",
    },
  ])

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
    loadDocuments()
    loadProviders()

    // Auto-close sidebar on smaller screens
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false)
    }
  }, [])

  // Poll for document status if any is processing
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "processing")
    if (hasProcessing) {
      const timer = setInterval(() => {
        loadDocuments()
      }, 3000)
      return () => clearInterval(timer)
    }
  }, [documents])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadProviders = async () => {
    try {
      const data = await ApiService.getProviders()
      if (data && data.providers) {
        setProviders(data.providers)
      }
    } catch (e) {
      console.error("Failed to load providers", e)
    }
  }

  const handleProviderChange = (newProvider: LLMProvider) => {
    setSelectedProvider(newProvider)
    localStorage.setItem("preferred_llm_provider", newProvider)
  }

  const loadSessions = async () => {
    try {
      const data = await ApiService.getSessions()
      setSessions(data)
    } catch (e) {
      console.error(e)
    }
  }

  const loadDocuments = async () => {
    try {
      const docs = await ApiService.listDocuments()
      setDocuments(docs)
    } catch (e) {
      console.error(e)
    }
  }

  const handleNewChat = () => {
    setActiveSessionId(undefined)
    setMessages([])
    setArtifacts([])
    setActiveArtifact(null)
    setIsArtifactViewerOpen(false)
    if (window.innerWidth < 1024) setIsSidebarOpen(false)
  }

  const handleSelectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId)
    try {
      const history = await ApiService.getSessionMessages(sessionId)
      setMessages(history)
    } catch (e) {
      console.error("Failed to load session messages", e)
      setMessages([])
    }

    try {
      const sessionArtifacts = await ApiService.getSessionArtifacts(sessionId)
      setArtifacts(sessionArtifacts)
      if (sessionArtifacts.length > 0) {
        setActiveArtifact(sessionArtifacts[0])
      } else {
        setActiveArtifact(null)
        setIsArtifactViewerOpen(false)
      }
    } catch (e) {
      console.error("Failed to load session artifacts", e)
      setArtifacts([])
      setActiveArtifact(null)
      setIsArtifactViewerOpen(false)
    }

    if (window.innerWidth < 1024) setIsSidebarOpen(false)
  }

  const handleHistoryCleared = (deletedSessionIds: string[], wasAll: boolean) => {
    if (wasAll || (activeSessionId && deletedSessionIds.includes(activeSessionId))) {
      setActiveSessionId(undefined)
      setMessages([])
      setArtifacts([])
      setActiveArtifact(null)
      setIsArtifactViewerOpen(false)
    }
    loadSessions()
  }

  const handleDeleteSingleSession = async (sessionId: string) => {
    try {
      await ApiService.deleteSession(sessionId)
      if (activeSessionId === sessionId) {
        setActiveSessionId(undefined)
        setMessages([])
        setArtifacts([])
        setActiveArtifact(null)
        setIsArtifactViewerOpen(false)
      }
      await loadSessions()
    } catch (e) {
      console.error("Failed to delete conversation:", e)
      alert("Failed to delete conversation. Please try again.")
    }
  }

  const handleUploadDocument = async (file: File) => {
    try {
      const tempId = Math.random().toString()
      setDocuments((prev) => [
        ...prev,
        {
          id: tempId,
          filename: file.name,
          status: "processing",
          created_at: new Date().toISOString(),
        },
      ])

      await ApiService.uploadDocument(file)
      await loadDocuments()
    } catch (e) {
      console.error("Upload failed", e)
      alert(`Failed to upload ${file.name}`)
      await loadDocuments()
    }
  }

  const handleRemoveDocument = async (id: string) => {
    try {
      await ApiService.deleteDocument(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (e) {
      console.error("Failed to delete", e)
    }
  }

  const handleSendMessage = async (content: string) => {
    const isProcessing = documents.some((d) => d.status === "processing")
    if (isProcessing) {
      alert("Please wait until all documents are processed before sending a message.")
      return
    }

    const userMessage: Message = {
      id: Math.random().toString(),
      role: "user",
      content: content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsConnecting(true)

    try {
      const activeDocIds = documents.filter((d) => d.status === "indexed").map((d) => d.id)
      const result = await ApiService.sendMessage(
        content,
        activeSessionId,
        activeDocIds,
        "chat",
        undefined,
        undefined,
        selectedProvider
      )

      if (!activeSessionId) {
        setActiveSessionId(result.session_id)
        loadSessions()
      }

      setMessages((prev) => [...prev, result.response])

      if (result.artifact) {
        setArtifacts((prev) => {
          const exists = prev.some((a) => a.id === result.artifact!.id)
          if (exists) {
            return prev.map((a) => (a.id === result.artifact!.id ? result.artifact! : a))
          }
          return [result.artifact!, ...prev]
        })
        setActiveArtifact(result.artifact)
        setIsArtifactViewerOpen(true)
      }
    } catch (error: any) {
      console.error("Failed to send message", error)
      const errorMsg: Message = {
        id: Math.random().toString(),
        role: "system",
        content: error?.message || "Error communicating with the backend. Is FastAPI running?",
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsConnecting(false)
    }
  }

  const isClaudeUnconfigured =
    selectedProvider === "claude" &&
    providers.find((p) => p.id === "claude" && !p.available)

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const headerTitle = activeSession ? activeSession.title : "Lenny Growth Assistant"

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-slate-900 font-sans">
      {/* 1. Gemini-Style Collapsible Left Sidebar */}
      <AppSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onSelectTopicPrompt={handleSendMessage}
        artifactsCount={artifacts.length}
        onOpenArtifacts={() => {
          if (artifacts.length > 0) {
            setIsArtifactViewerOpen(true)
          } else {
            handleSendMessage("Create a responsive HTML dashboard with KPI cards and charts")
          }
        }}
        onOpenClearHistory={() => setIsClearHistoryOpen(true)}
        onDeleteSession={handleDeleteSingleSession}
      />

      {/* 2. Main Conversational Canvas */}
      <div className="flex flex-1 flex-col h-full min-w-0 overflow-hidden relative bg-white">
        {/* Minimal Gemini-Style Top Navigation Header */}
        <header className="flex h-14 shrink-0 items-center justify-between px-3 sm:px-4 border-b border-slate-100 bg-white/95 backdrop-blur-xs z-20">
          <div className="flex items-center gap-2 min-w-0">
            {/* Hamburger Button to Toggle Sidebar */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="h-9 w-9 rounded-full text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              title="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center gap-2 min-w-0">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 shrink-0">
                <Sparkles className="h-3.5 w-3.5" />
              </div>
              <h1 className="text-sm font-semibold text-slate-800 truncate" title={headerTitle}>
                {headerTitle}
              </h1>
            </div>
          </div>

          {/* Right Header Controls: Provider Selector + Artifacts Button + New Chat */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <ProviderSelector
              currentProvider={selectedProvider}
              onProviderChange={handleProviderChange}
              providers={providers}
            />

            {artifacts.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsArtifactViewerOpen(!isArtifactViewerOpen)}
                className="h-8 px-2.5 gap-1.5 rounded-full text-xs text-indigo-700 bg-indigo-50/70 border-indigo-200 hover:bg-indigo-100 shadow-2xs"
                title="Open Artifact Viewer"
              >
                <Layers className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Artifacts</span>
                <span className="font-semibold">({artifacts.length})</span>
              </Button>
            )}

            <Button
              variant="ghost"
              size="icon"
              onClick={handleNewChat}
              className="h-8 w-8 rounded-full text-slate-500 hover:text-slate-800 hover:bg-slate-100"
              title="New chat"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Missing Claude API Key Warning Banner */}
        {isClaudeUnconfigured && (
          <div className="bg-amber-50 border-b border-amber-200/90 px-4 py-2 text-xs text-amber-900 flex items-center justify-between shrink-0 z-10">
            <div className="flex items-center gap-2 min-w-0">
              <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
              <span className="truncate">
                <strong>Claude AI</strong> requires <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">ANTHROPIC_API_KEY</code> in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-[11px]">backend/.env</code>.
              </span>
            </div>
            <button
              onClick={() => handleProviderChange("ollama")}
              className="text-xs font-semibold text-emerald-800 hover:underline shrink-0 ml-2"
            >
              Switch to Ollama (Local) →
            </button>
          </div>
        )}

        {/* Centered Scrollable Conversation Canvas */}
        <main className="flex-1 overflow-y-auto px-4 pb-36 pt-2 select-text">
          {messages.length === 0 ? (
            <WelcomeScreen onSelectQuestion={handleSendMessage} />
          ) : (
            <div className="mx-auto w-full max-w-3xl space-y-4">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onViewArtifact={() => setIsArtifactViewerOpen(true)}
                  onSwitchProvider={handleProviderChange}
                />
              ))}
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </main>

        {/* Gemini-Style Fixed Floating Bottom Composer */}
        <div className="absolute bottom-0 left-0 right-0 z-30 pointer-events-none pb-3 pt-4 bg-gradient-to-t from-white via-white/95 to-transparent">
          <div className="pointer-events-auto">
            <MessageComposer
              onSend={handleSendMessage}
              disabled={isConnecting}
              isConnecting={isConnecting}
              documents={documents}
              onUploadDocument={handleUploadDocument}
              onRemoveDocument={handleRemoveDocument}
            />
          </div>
        </div>

        {/* Contextual In-App Artifact Viewer (Slide-in Drawer / Split View) */}
        {isArtifactViewerOpen && activeArtifact && (
          <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[540px] xl:w-[680px] bg-white border-l border-slate-200 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
            <ArtifactViewer
              artifacts={artifacts}
              activeArtifact={activeArtifact}
              onSelectArtifact={(art) => setActiveArtifact(art)}
              isOpen={isArtifactViewerOpen}
              onClose={() => setIsArtifactViewerOpen(false)}
              className="flex-1 w-full border-l-0 h-full"
            />
          </div>
        )}
      </div>

      {/* Settings Dialog Modal */}
      <SettingsDialog
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
        currentProvider={selectedProvider}
        onProviderChange={handleProviderChange}
        providers={providers}
        onOpenClearHistory={() => setIsClearHistoryOpen(true)}
      />

      {/* Clear History Dialog Modal */}
      <ClearHistoryDialog
        open={isClearHistoryOpen}
        onOpenChange={setIsClearHistoryOpen}
        sessions={sessions}
        onHistoryCleared={handleHistoryCleared}
      />
    </div>
  )
}

export default App
