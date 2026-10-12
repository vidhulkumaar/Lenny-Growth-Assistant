import React from "react"
import { Sparkles } from "lucide-react"
import { SuggestedQuestionCard } from "./SuggestedQuestionCard"

interface WelcomeScreenProps {
  onSelectQuestion: (question: string) => void
}

const SUGGESTED_QUESTIONS = [
  "How should a startup find product-market fit?",
  "What makes a successful product launch?",
  "How can product teams improve user retention?",
  "What are effective strategies for product-led growth?",
]

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectQuestion }) => {
  return (
    <div className="flex h-full flex-col items-center justify-center p-4 text-center sm:p-8">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 shadow-sm">
        <Sparkles className="h-8 w-8" />
      </div>
      <h2 className="mb-2 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        The Lenny Growth Assistant
      </h2>
      <p className="mx-auto mb-8 max-w-[600px] text-base text-slate-500">
        I answer product management and growth questions using the knowledge base from Lenny's Podcast transcripts. How can I help you today?
      </p>
      
      <div className="grid w-full max-w-3xl gap-4 sm:grid-cols-2">
        {SUGGESTED_QUESTIONS.map((q) => (
          <SuggestedQuestionCard key={q} question={q} onClick={onSelectQuestion} />
        ))}
      </div>
    </div>
  )
}
