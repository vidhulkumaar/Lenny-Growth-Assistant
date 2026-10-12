import React from "react"
import { ExternalLink, FileText } from "lucide-react"
import type { Citation } from "@/types"

export const SourceCitation: React.FC<{ citation: Citation }> = ({ citation }) => {
  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
      <div className="flex items-center justify-between gap-2 font-medium text-slate-900 mb-1 flex-wrap">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-500 shrink-0" />
          <span className="font-semibold text-slate-800">{citation.title}</span>
        </div>
        {citation.page_number !== undefined && citation.page_number !== null && (
          <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 border border-indigo-200">
            Page {citation.page_number}
          </span>
        )}
        {citation.source_url && (
          <a
            href={citation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-800"
            title="View original source"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
      {citation.excerpt && (
        <p className="text-slate-500 italic mt-1 line-clamp-3">"{citation.excerpt}"</p>
      )}
      <div className="mt-1 text-xs text-slate-400">Source ID: {citation.source_key}</div>
    </div>
  )
}
