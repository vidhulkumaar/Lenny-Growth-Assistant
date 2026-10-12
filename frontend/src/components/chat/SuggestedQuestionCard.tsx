import React from "react"

interface SuggestedQuestionCardProps {
  question: string
  onClick: (question: string) => void
}

export const SuggestedQuestionCard: React.FC<SuggestedQuestionCardProps> = ({ question, onClick }) => {
  return (
    <button
      onClick={() => onClick(question)}
      className="flex flex-col items-start justify-start rounded-xl border border-slate-200 bg-white p-4 text-left transition-all hover:border-indigo-300 hover:bg-indigo-50/50 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
    >
      <span className="text-sm font-medium text-slate-700">{question}</span>
    </button>
  )
}
