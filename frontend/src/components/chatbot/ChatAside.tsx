// SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
// SPDX-License-Identifier: Apache-2.0

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import {
  X,
  Plus,
  ChevronDown,
  Sparkles,
  ArrowUp,
  Paperclip,
  Trash2,
  ShieldAlert,
  Terminal,
  KeyRound,
  Sliders,
  Lock,
  Bot,
  User as UserIcon,
} from 'lucide-react'
import { useChatbot } from '@/context/ChatbotContext'

interface SuggestionItem {
  icon: typeof ShieldAlert
  title: string
  subtitle: string
  prompt: string
}

const SUGGESTIONS: SuggestionItem[] = [
  {
    icon: ShieldAlert,
    title: 'An toàn thông tin LMS',
    subtitle: 'Tìm hiểu các khái niệm an ninh mạng và phòng vệ',
    prompt: 'Giải thích cho tôi các nguyên tắc an toàn thông tin cốt lõi cần chú ý trong một hệ thống LMS.',
  },
  {
    icon: Terminal,
    title: 'Phân tích lỗ hổng ứng dụng',
    subtitle: 'Cách phát hiện và phòng chống SQLi, XSS, CSRF',
    prompt: 'Cho tôi ví dụ cụ thể về cách phòng chống SQL Injection và XSS trong các ứng dụng web.',
  },
  {
    icon: KeyRound,
    title: 'Xác thực & Phân quyền',
    subtitle: 'Hướng dẫn bảo vệ tài khoản, token & mật khẩu',
    prompt: 'Các nguyên tắc thiết kế xác thực an toàn bằng JWT và quản lý session trong hệ thống là gì?',
  },
  {
    icon: Lock,
    title: 'Secure Coding & Thực hành',
    subtitle: 'Thực hành viết code an toàn và phòng thủ',
    prompt: 'Hãy chia sẻ các checklist về secure coding thực tế khi lập trình backend và frontend.',
  },
  {
    icon: Sliders,
    title: 'Kiểm tra cấu hình bảo mật',
    subtitle: 'Thiết lập an toàn cho hệ thống và môi trường',
    prompt: 'Những bước quan trọng cần làm để rà soát cấu hình bảo mật hệ thống trước khi triển khai là gì?',
  },
]

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning.'
  if (hour < 18) return 'Good afternoon.'
  return 'Good evening.'
}

export default function ChatAside() {
  const {
    isOpen,
    closeChatbot,
    conversations,
    activeConversation,
    activeConversationId,
    messages,
    isLoading,
    error,
    startNewConversation,
    selectConversation,
    sendMessage,
    removeConversation,
  } = useChatbot()

  const [input, setInput] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!dropdownOpen) return
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [dropdownOpen])

  // Focus textarea when aside opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 150)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    await sendMessage(text)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const currentTitle =
    activeConversation?.title ||
    (activeConversationId
      ? conversations.find((c) => c.id === activeConversationId)?.title
      : 'New conversation') ||
    'New conversation'

  return (
    <>
      {/* Backdrop for mobile */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 sm:hidden"
        onClick={closeChatbot}
        aria-hidden="true"
      />

      {/* Main Chat Aside - Light Theme */}
      <aside
        className="fixed top-0 right-0 bottom-0 z-50 w-full sm:w-[440px] md:w-[460px] bg-white text-slate-800 border-l border-slate-200/90 shadow-2xl flex flex-col font-sans animate-in slide-in-from-right duration-300"
        aria-label="AI Chatbot"
      >
        {/* Top Header */}
        <div className="h-14 border-b border-slate-200/80 px-4 flex items-center justify-between shrink-0 bg-white/95 backdrop-blur sticky top-0 z-10">
          {/* Conversation dropdown selector */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-semibold text-slate-800 hover:bg-slate-100 transition-colors max-w-[260px] cursor-pointer"
            >
              <span className="truncate">{currentTitle}</span>
              <ChevronDown className="h-4 w-4 text-slate-500 shrink-0" />
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 top-full mt-1.5 w-72 max-h-80 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-xl py-2 z-50 animate-in fade-in-50 zoom-in-95">
                <div className="px-3 py-1.5 border-b border-slate-100 flex items-center justify-between text-xs text-slate-500 font-semibold tracking-wider uppercase">
                  <span>Lịch sử hội thoại</span>
                  <button
                    type="button"
                    onClick={() => {
                      startNewConversation()
                      setDropdownOpen(false)
                    }}
                    className="text-blue-600 hover:text-blue-700 normal-case font-medium text-xs flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="h-3 w-3" /> Mới
                  </button>
                </div>

                {conversations.length === 0 ? (
                  <p className="px-3 py-4 text-xs text-slate-400 text-center">
                    Chưa có cuộc trò chuyện nào trước đó
                  </p>
                ) : (
                  conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`group flex items-center justify-between px-3 py-2 text-xs cursor-pointer hover:bg-slate-50 transition-colors ${
                        activeConversationId === conv.id
                          ? 'bg-blue-50/70 text-blue-700 font-semibold'
                          : 'text-slate-700'
                      }`}
                      onClick={() => {
                        selectConversation(conv.id)
                        setDropdownOpen(false)
                      }}
                    >
                      <div className="min-w-0 pr-2">
                        <p className="truncate">{conv.title}</p>
                        <p className="text-[10px] text-slate-400">
                          {new Date(conv.updated_at).toLocaleDateString('vi-VN')}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          removeConversation(conv.id)
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 transition-opacity cursor-pointer"
                        title="Xóa"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Action buttons on right */}
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={startNewConversation}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Cuộc trò chuyện mới"
            >
              <Plus className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={closeChatbot}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Đóng"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Aside Body */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-slate-50/40">
          {/* Support Banner (matches screenshot) */}
          <div className="flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-white border border-slate-200/80 shadow-xs text-xs text-slate-700">
            <span className="font-medium">Need more help?</span>
            <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200/80 text-slate-700 font-medium hover:bg-slate-200 transition-colors cursor-pointer">
              Support
            </span>
          </div>

          {/* Empty state: 3D mascot + suggestions */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center pt-3 pb-2 text-center animate-in fade-in duration-300">
              {/* Sunset Cloud Mascot Graphic */}
              <div className="relative w-28 h-20 mb-3 flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-tr from-amber-400/25 via-orange-400/25 to-rose-400/15 rounded-full blur-xl" />
                <svg
                  className="w-24 h-16 drop-shadow-[0_8px_16px_rgba(249,115,22,0.25)]"
                  viewBox="0 0 120 80"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <defs>
                    <linearGradient id="cloudGlowLight" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#ffedd5" />
                      <stop offset="35%" stopColor="#fb923c" />
                      <stop offset="100%" stopColor="#ea580c" />
                    </linearGradient>
                    <linearGradient id="cloudSecondaryLight" x1="0%" y1="100%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#f97316" />
                      <stop offset="100%" stopColor="#fdba74" />
                    </linearGradient>
                  </defs>
                  {/* Stylized layered 3D Cloud bubbles */}
                  <ellipse cx="40" cy="52" rx="22" ry="18" fill="url(#cloudSecondaryLight)" opacity="0.95" />
                  <ellipse cx="80" cy="54" rx="20" ry="16" fill="url(#cloudSecondaryLight)" opacity="0.95" />
                  <circle cx="58" cy="38" r="24" fill="url(#cloudGlowLight)" />
                  <ellipse cx="60" cy="56" rx="42" ry="18" fill="url(#cloudGlowLight)" />
                </svg>
              </div>

              {/* Greeting */}
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">{getGreeting()}</h2>
              <p className="text-xs text-slate-500 mt-0.5 mb-5 font-normal">What are we doing today?</p>

              {/* Suggestion Chips */}
              <div className="w-full space-y-2 text-left">
                {SUGGESTIONS.map((item, idx) => {
                  const Icon = item.icon
                  return (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => sendMessage(item.prompt)}
                      className="w-full flex items-center gap-3 p-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-200/80 hover:border-slate-300 shadow-xs hover:shadow transition-all text-left group cursor-pointer"
                    >
                      <div className="p-2 rounded-lg bg-slate-100 group-hover:bg-blue-50 text-slate-600 group-hover:text-blue-600 transition-colors shrink-0">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-slate-800 group-hover:text-blue-700 transition-colors truncate">
                          {item.title}
                        </p>
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">
                          {item.subtitle}
                        </p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            /* Active message list */
            <div className="space-y-4 pt-1">
              {messages.map((msg) => {
                const isUser = msg.role === 'user'
                return (
                  <div
                    key={msg.id}
                    className={`flex gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser && (
                      <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-xs">
                        <Sparkles className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed whitespace-pre-wrap ${
                        isUser
                          ? 'bg-blue-600 text-white rounded-tr-sm shadow-xs'
                          : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-sm shadow-xs'
                      }`}
                    >
                      {msg.content}
                    </div>
                    {isUser && (
                      <div className="h-7 w-7 rounded-lg bg-slate-200 flex items-center justify-center text-slate-600 shrink-0 mt-0.5">
                        <UserIcon className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                )
              })}

              {/* Thinking / Loading indicator */}
              {isLoading && (
                <div className="flex gap-2.5 justify-start items-center">
                  <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-white shrink-0 shadow-xs animate-pulse">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-white border border-slate-200/90 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-xs text-slate-500 flex items-center gap-1.5 shadow-xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-bounce [animation-delay:0.4s]" />
                    <span className="ml-1 text-[11px] font-medium">AI đang suy nghĩ...</span>
                  </div>
                </div>
              )}

              {error && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs text-center font-medium">
                  {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Footer Input Area */}
        <div className="p-3 border-t border-slate-200/80 bg-white shrink-0">
          <div className="relative rounded-2xl bg-slate-50 border border-slate-200 focus-within:bg-white focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 p-2.5 transition-all shadow-xs">
            <textarea
              ref={textareaRef}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type @ to tag a resource or ? for shortcuts"
              className="w-full bg-transparent resize-none outline-none text-xs text-slate-800 placeholder:text-slate-400 leading-relaxed"
            />

            {/* Input Toolbar */}
            <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 mt-1">
              <button
                type="button"
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-700 bg-white hover:bg-slate-100 disabled:opacity-40 transition-colors border border-slate-200 shadow-xs cursor-pointer"
              >
                <Sparkles className="h-3 w-3 text-amber-500" />
                <span>Ask</span>
              </button>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
                  title="Đính kèm"
                >
                  <Paperclip className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="p-1.5 rounded-full bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white transition-all shadow-sm shadow-blue-500/30 cursor-pointer"
                  title="Gửi"
                >
                  <ArrowUp className="h-3.5 w-3.5" strokeWidth={2.5} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
