// SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
// SPDX-License-Identifier: Apache-2.0

import { Sparkles } from 'lucide-react'
import { useChatbot } from '@/context/ChatbotContext'

interface AskAiButtonProps {
  className?: string
  showText?: boolean
}

export default function AskAiButton({ className = '', showText = true }: Readonly<AskAiButtonProps>) {
  const { toggleChatbot, isOpen } = useChatbot()

  return (
    <button
      type="button"
      onClick={toggleChatbot}
      title="Ask AI"
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border cursor-pointer ${
        isOpen
          ? 'bg-blue-50 text-blue-700 border-blue-300 shadow-sm ring-2 ring-blue-500/20'
          : 'bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border-slate-200 hover:border-slate-300 shadow-sm hover:shadow'
      } ${className}`}
      aria-label="Toggle AI Chatbot"
    >
      <Sparkles className="h-3.5 w-3.5 text-amber-500 animate-pulse" />
      {showText && <span>Ask AI</span>}
    </button>
  )
}
