import { useState, useEffect, useRef } from "react"
import { AppSidebar } from "./components/layout/AppSidebar"
import { WelcomeScreen } from "./components/chat/WelcomeScreen"
import { ChatMessage } from "./components/chat/ChatMessage"
import { MessageComposer } from "./components/chat/MessageComposer"
import { SettingsDialog } from "./components/layout/SettingsDialog"
import { DocumentUploader } from "./components/chat/DocumentUploader"
import { ArtifactViewer } from "./components/artifacts/ArtifactViewer"
import { ApiService, type DocumentInfo } from "./services/api"
import type { Session, Message, Artifact } from "./types"
import { Menu, Layers } from "lucide-react"
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
  const [isConnecting, setIsConnecting] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
    loadDocuments()
    
    // Auto-close sidebar on mobile
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false)
    }
  }, [])

  // Poll for document status if any is processing
  useEffect(() => {
    const hasProcessing = documents.some(d => d.status === 'processing')
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

  const handleUploadDocument = async (file: File) => {
    try {
      const tempId = Math.random().toString()
      setDocuments(prev => [...prev, { id: tempId, filename: file.name, status: 'processing', created_at: new Date().toISOString() }])
      
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
      setDocuments(prev => prev.filter(d => d.id !== id))
    } catch (e) {
      console.error("Failed to delete", e)
    }
  }

  const handleSendMessage = async (
    content: string,
    mode: "chat" | "ship30" = "chat",
    writingOptions?: Record<string, any>
  ) => {
    const isProcessing = documents.some(d => d.status === 'processing')
    if (isProcessing) {
      alert("Please wait until all documents are processed before sending a message.")
      return
    }

    const userMessage: Message = {
      id: Math.random().toString(),
      role: "user",
      content: mode === "ship30" ? `[Ship 30 for 30] ${content}` : content,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setIsConnecting(true)

    try {
      const activeDocIds = documents.filter(d => d.status === 'indexed').map(d => d.id)
      const result = await ApiService.sendMessage(content, activeSessionId, activeDocIds, mode, writingOptions)
      
      if (!activeSessionId) {
        setActiveSessionId(result.session_id)
        loadSessions()
      }

      setMessages(prev => [...prev, result.response])

      if (result.artifact) {
        setArtifacts(prev => [result.artifact!, ...prev])
        setActiveArtifact(result.artifact)
        setIsArtifactViewerOpen(true)
      }
    } catch (error) {
      console.error("Failed to send message", error)
      const errorMsg: Message = {
        id: Math.random().toString(),
        role: "system",
        content: "Error communicating with the backend. Is FastAPI running?",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsConnecting(false)
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-slate-900 font-sans">
      <AppSidebar 
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <div className="flex flex-1 flex-col overflow-hidden relative min-w-0">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setIsSidebarOpen(true)}>
              <Menu className="h-5 w-5 text-slate-600" />
            </Button>
            <span className="font-semibold text-slate-900">Growth Assistant</span>
          </div>

          {artifacts.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsArtifactViewerOpen(!isArtifactViewerOpen)}
              className="flex items-center gap-1.5 text-xs text-indigo-700 bg-indigo-50 border-indigo-200 hover:bg-indigo-100 shadow-sm"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Artifacts ({artifacts.length})</span>
            </Button>
          )}
        </header>

        <main className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <WelcomeScreen onSelectQuestion={handleSendMessage} />
          ) : (
            <div className="mx-auto w-full max-w-3xl pb-6">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onViewArtifact={() => setIsArtifactViewerOpen(true)}
                />
              ))}
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </main>

        <div className="mx-auto w-full max-w-3xl px-4 py-2 border-t border-slate-200 bg-white">
          <div className="mb-4">
            <DocumentUploader 
              documents={documents} 
              onUpload={handleUploadDocument} 
              onRemove={handleRemoveDocument}
              disabled={isConnecting}
            />
          </div>
          <MessageComposer 
            onSend={handleSendMessage} 
            disabled={isConnecting || documents.some(d => d.status === 'processing')}
            isConnecting={isConnecting}
          />
        </div>
      </div>

      {/* Dedicated In-App Artifact Viewer */}
      <ArtifactViewer
        artifacts={artifacts}
        activeArtifact={activeArtifact}
        onSelectArtifact={(art) => setActiveArtifact(art)}
        isOpen={isArtifactViewerOpen}
        onClose={() => setIsArtifactViewerOpen(false)}
      />

      <SettingsDialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen} />
    </div>
  )
}

export default App

