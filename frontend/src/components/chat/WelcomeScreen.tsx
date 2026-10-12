import React from "react"
import { Sparkles, ArrowUpRight } from "lucide-react"

interface WelcomeScreenProps {
  onSelectQuestion: (question: string) => void
}

interface Suggestion {
  category: string
  question: string
}

const SUGGESTIONS: Suggestion[] = [
  {
    category: "Podcast Research",
    question: "How should a startup find product-market fit?",
  },
  {
    category: "Digital Writing",
    question: "Write a Ship 30 for 30 atomic essay about product-led growth",
  },
  {
    category: "UI Prototype",
    question: "Create a responsive HTML dashboard with KPI cards and charts",
  },
  {
    category: "Strategy Report",
    question: "Create a Markdown project report on user retention",
  },
]

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectQuestion }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[58vh] max-w-2xl mx-auto px-4 py-8 text-center select-none">
      {/* Brand Icon */}
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-500/10 via-purple-500/15 to-indigo-500/10 text-indigo-600 shadow-xs border border-indigo-100">
        <Sparkles className="h-7 w-7" />
      </div>

      {/* Main Title (Required by tests: 'The Lenny Growth Assistant') */}
      <h1 className="mb-2 text-3xl sm:text-4xl font-normal tracking-tight text-slate-800">
        The Lenny Growth Assistant
      </h1>

      {/* Gemini-Inspired Greeting */}
      <p className="mb-8 text-lg sm:text-xl text-slate-400 font-light max-w-md">
        What would you like to learn or build today?
      </p>

      {/* Gemini-Inspired Suggestion Cards Grid */}
      <div className="grid w-full grid-cols-1 sm:grid-cols-2 gap-3">
        {SUGGESTIONS.map((item) => (
          <button
            key={item.question}
            type="button"
            onClick={() => onSelectQuestion(item.question)}
            className="group flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white hover:bg-slate-50/80 hover:border-indigo-200/80 p-3.5 text-left transition-all shadow-xs hover:shadow-sm"
          >
            <div className="flex items-center justify-between w-full mb-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 group-hover:text-indigo-600 transition-colors">
                {item.category}
              </span>
              <ArrowUpRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-indigo-600 transition-colors" />
            </div>
            <span className="text-xs sm:text-sm font-medium text-slate-700 group-hover:text-slate-900 leading-snug">
              {item.question}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
