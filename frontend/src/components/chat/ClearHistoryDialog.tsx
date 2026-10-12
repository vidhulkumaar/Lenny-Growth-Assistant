import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Trash2,
  AlertTriangle,
  CheckSquare,
  Square,
  ShieldCheck,
  Search,
  Loader2,
  Calendar,
} from "lucide-react"
import type { Session } from "@/types"
import { ApiService } from "@/services/api"

interface ClearHistoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sessions: Session[]
  onHistoryCleared: (deletedSessionIds: string[], wasAll: boolean) => void
}

export const ClearHistoryDialog: React.FC<ClearHistoryDialogProps> = ({
  open,
  onOpenChange,
  sessions,
  onHistoryCleared,
}) => {
  const [activeTab, setActiveTab] = useState<"selected" | "all">("selected")
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [filterQuery, setFilterQuery] = useState("")
  const [isDeleting, setIsDeleting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  
  // Confirmation stages
  const [confirmingSelected, setConfirmingSelected] = useState(false)
  const [confirmingAll, setConfirmingAll] = useState(false)

  // Filtered sessions
  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(filterQuery.toLowerCase())
  )

  const handleSelectToggle = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const handleSelectAll = () => {
    const allFilteredIds = filteredSessions.map((s) => s.id)
    const isAllSelected = allFilteredIds.every((id) => selectedIds.includes(id))
    if (isAllSelected) {
      setSelectedIds((prev) => prev.filter((id) => !allFilteredIds.includes(id)))
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...allFilteredIds])))
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedIds.length === 0) return
    setIsDeleting(true)
    setErrorMessage(null)
    try {
      if (selectedIds.length === 1) {
        await ApiService.deleteSession(selectedIds[0])
      } else {
        await ApiService.batchDeleteSessions(selectedIds)
      }
      onHistoryCleared(selectedIds, false)
      setConfirmingSelected(false)
      setSelectedIds([])
      onOpenChange(false)
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to delete selected conversations")
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClearAllHistory = async () => {
    setIsDeleting(true)
    setErrorMessage(null)
    try {
      const allIds = sessions.map((s) => s.id)
      await ApiService.clearAllHistory()
      onHistoryCleared(allIds, true)
      setConfirmingAll(false)
      setSelectedIds([])
      onOpenChange(false)
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to clear all chat and search history")
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    if (isDeleting) return
    setConfirmingSelected(false)
    setConfirmingAll(false)
    setErrorMessage(null)
    onOpenChange(false)
  }

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString)
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch {
      return ""
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-red-50 text-red-600">
              <Trash2 className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-base text-slate-900">
                Clear Chat & Search History
              </DialogTitle>
              <DialogDescription className="mt-0.5">
                Manage and safely remove conversation messages and search queries.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Tab Selection */}
        <div className="flex rounded-lg bg-slate-100 p-1 mt-2">
          <button
            type="button"
            onClick={() => {
              setActiveTab("selected")
              setConfirmingSelected(false)
              setConfirmingAll(false)
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === "selected"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Clear Selected Conversations
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("all")
              setConfirmingSelected(false)
              setConfirmingAll(false)
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === "all"
                ? "bg-white text-red-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Clear All History
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-800 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
            <span className="flex-1">{errorMessage}</span>
          </div>
        )}

        {/* TAB 1: CLEAR SELECTED CONVERSATIONS */}
        {activeTab === "selected" && (
          <div className="space-y-3 pt-1">
            {confirmingSelected ? (
              /* Selected Confirmation View */
              <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-amber-900">
                      Confirm Conversation Deletion
                    </h4>
                    <p className="text-xs text-amber-800 leading-relaxed">
                      Are you sure you want to delete{" "}
                      <strong>{selectedIds.length}</strong> selected conversation(s)?
                      All chat messages and search history within these conversations will be deleted.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-amber-200/80 text-[11px] text-emerald-800">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>
                    <strong>Safe Deletion:</strong> Uploaded documents, transcript embeddings, and generated artifacts will remain safe.
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setConfirmingSelected(false)}
                    disabled={isDeleting}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDeleteSelected}
                    disabled={isDeleting}
                    className="text-xs bg-red-600 hover:bg-red-700"
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                        Deleting...
                      </>
                    ) : (
                      `Yes, Delete ${selectedIds.length} Conversation${
                        selectedIds.length > 1 ? "s" : ""
                      }`
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              /* Selected Selection View */
              <>
                {/* Search & Select All controls */}
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Filter conversations..."
                      value={filterQuery}
                      onChange={(e) => setFilterQuery(e.target.value)}
                      className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-slate-50/50"
                    />
                  </div>
                  {filteredSessions.length > 0 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleSelectAll}
                      className="text-xs shrink-0 h-8"
                    >
                      {filteredSessions.every((s) => selectedIds.includes(s.id))
                        ? "Deselect All"
                        : "Select All"}
                    </Button>
                  )}
                </div>

                {/* Conversation List */}
                <div className="border border-slate-200 rounded-lg max-h-60 overflow-y-auto divide-y divide-slate-100 bg-white">
                  {filteredSessions.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-400">
                      {sessions.length === 0
                        ? "No conversations to display"
                        : "No matching conversations found"}
                    </div>
                  ) : (
                    filteredSessions.map((session) => {
                      const isSelected = selectedIds.includes(session.id)
                      return (
                        <div
                          key={session.id}
                          onClick={() => handleSelectToggle(session.id)}
                          className={`flex items-center gap-3 px-3 py-2.5 text-left cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-indigo-50/60"
                              : "hover:bg-slate-50"
                          }`}
                        >
                          <button
                            type="button"
                            className="text-indigo-600 focus:outline-none shrink-0"
                            aria-label={isSelected ? "Deselect" : "Select"}
                          >
                            {isSelected ? (
                              <CheckSquare className="h-4 w-4 text-indigo-600" />
                            ) : (
                              <Square className="h-4 w-4 text-slate-400" />
                            )}
                          </button>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-slate-900 truncate">
                              {session.title}
                            </p>
                            {session.updated_at && (
                              <p className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                                <Calendar className="h-3 w-3" />
                                {formatDate(session.updated_at)}
                              </p>
                            )}
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>

                <DialogFooter className="flex items-center justify-between sm:justify-between w-full pt-2">
                  <div className="text-xs text-slate-500">
                    <span className="font-semibold text-slate-800">
                      {selectedIds.length}
                    </span>{" "}
                    of {sessions.length} selected
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleClose}
                      className="text-xs"
                    >
                      Close
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setConfirmingSelected(true)}
                      disabled={selectedIds.length === 0}
                      className="text-xs bg-red-600 hover:bg-red-700"
                    >
                      Delete Selected ({selectedIds.length})
                    </Button>
                  </div>
                </DialogFooter>
              </>
            )}
          </div>
        )}

        {/* TAB 2: CLEAR ALL HISTORY */}
        {activeTab === "all" && (
          <div className="space-y-4 pt-1">
            {confirmingAll ? (
              /* Clear All Confirmation View */
              <div className="rounded-xl border border-red-300 bg-red-50 p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-6 w-6 text-red-600 shrink-0 mt-0.5" />
                  <div className="space-y-1.5">
                    <h4 className="text-sm font-semibold text-red-900">
                      Final Confirmation: Delete All Chat & Search History
                    </h4>
                    <p className="text-xs text-red-800 leading-relaxed">
                      This action will delete <strong>all {sessions.length} conversations</strong> and all associated message threads and search queries. This cannot be undone.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-red-200 text-[11px] text-emerald-800">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>
                    <strong>Guaranteed Safe:</strong> Transcripts, chunks, documents, embeddings, and generated artifacts will remain intact.
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setConfirmingAll(false)}
                    disabled={isDeleting}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleClearAllHistory}
                    disabled={isDeleting}
                    className="text-xs bg-red-600 hover:bg-red-700"
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                        Clearing All History...
                      </>
                    ) : (
                      "Yes, Delete All History"
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              /* Clear All Overview */
              <div className="space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
                    Complete History Reset
                  </h4>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Clear all conversation threads, message exchanges, and search query history in a single safe operation.
                  </p>

                  <div className="rounded-lg border border-emerald-200 bg-emerald-50/80 p-3 space-y-1.5 text-xs text-emerald-900">
                    <div className="flex items-center gap-2 font-semibold">
                      <ShieldCheck className="h-4 w-4 text-emerald-600" />
                      Preservation Guarantees
                    </div>
                    <ul className="list-disc list-inside text-[11px] text-emerald-800 space-y-0.5 pl-1">
                      <li>Uploaded documents and indexed PDF pages are preserved</li>
                      <li>Podcast transcripts and vector embeddings are preserved</li>
                      <li>All generated HTML and Markdown artifacts are safely preserved</li>
                    </ul>
                  </div>
                </div>

                <DialogFooter className="flex items-center justify-between sm:justify-between w-full pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClose}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setConfirmingAll(true)}
                    className="text-xs bg-red-600 hover:bg-red-700"
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                    Clear All Chat & Search History
                  </Button>
                </DialogFooter>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
