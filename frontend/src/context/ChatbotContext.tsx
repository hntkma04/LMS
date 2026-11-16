// SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
// SPDX-License-Identifier: Apache-2.0

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react'
import {
  type ChatConversation,
  type ChatMessage,
  fetchConversations,
  fetchConversationDetail,
  sendChatMessage,
  deleteConversation,
  clearConversationMessages,
} from '@/lib/api/chatbot'
import { getStoredUser } from '@/lib/auth'

export interface ChatbotContextValue {
  isOpen: boolean
  openChatbot: () => void
  closeChatbot: () => void
  toggleChatbot: () => void
  conversations: ChatConversation[]
  activeConversation: ChatConversation | null
  activeConversationId: number | null
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  startNewConversation: () => void
  loadConversations: () => Promise<void>
  selectConversation: (id: number) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  removeConversation: (id: number) => Promise<void>
  clearCurrentConversation: () => Promise<void>
}

const ChatbotContext = createContext<ChatbotContextValue>({
  isOpen: false,
  openChatbot: () => {},
  closeChatbot: () => {},
  toggleChatbot: () => {},
  conversations: [],
  activeConversation: null,
  activeConversationId: null,
  messages: [],
  isLoading: false,
  error: null,
  startNewConversation: () => {},
  loadConversations: async () => {},
  selectConversation: async () => {},
  sendMessage: async () => {},
  removeConversation: async () => {},
  clearCurrentConversation: async () => {},
})

export function ChatbotProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [isOpen, setIsOpen] = useState(false)
  const [conversations, setConversations] = useState<ChatConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [activeConversation, setActiveConversation] = useState<ChatConversation | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const openChatbot = useCallback(() => setIsOpen(true), [])
  const closeChatbot = useCallback(() => setIsOpen(false), [])
  const toggleChatbot = useCallback(() => setIsOpen((prev) => !prev), [])

  const loadConversations = useCallback(async () => {
    const user = getStoredUser()
    if (!user) return
    try {
      const data = await fetchConversations()
      setConversations(data)
    } catch {
      // ignore unauthenticated or silent fail
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      loadConversations().catch(() => {})
    }
  }, [isOpen, loadConversations])

  const selectConversation = useCallback(async (id: number) => {
    setActiveConversationId(id)
    setIsLoading(true)
    setError(null)
    try {
      const detail = await fetchConversationDetail(id)
      setActiveConversation(detail)
      setMessages(detail.messages ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể tải lịch sử trò chuyện')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const startNewConversation = useCallback(() => {
    setActiveConversationId(null)
    setActiveConversation(null)
    setMessages([])
    setError(null)
  }, [])

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim()
      if (!trimmed) return

      // Optimistic user message preview
      const tempId = Date.now()
      const optimisticMsg: ChatMessage = {
        id: tempId,
        role: 'user',
        content: trimmed,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, optimisticMsg])
      setIsLoading(true)
      setError(null)

      try {
        const response = await sendChatMessage(trimmed, activeConversationId)
        setActiveConversationId(response.conversation.id)
        setActiveConversation(response.conversation)

        // Replace optimistic with real messages
        setMessages((prev) => {
          const filtered = prev.filter((m) => m.id !== tempId)
          const newMsgs = [...filtered]
          if (response.user_message) {
            newMsgs.push(response.user_message)
          } else {
            newMsgs.push(optimisticMsg)
          }
          newMsgs.push(response.assistant_message)
          return newMsgs
        })

        // Refresh conversations list to update title and updated_at
        loadConversations().catch(() => {})
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Gửi tin nhắn thất bại')
        // Remove optimistic message if failed
        setMessages((prev) => prev.filter((m) => m.id !== tempId))
      } finally {
        setIsLoading(false)
      }
    },
    [activeConversationId, loadConversations]
  )

  const removeConversation = useCallback(
    async (id: number) => {
      try {
        await deleteConversation(id)
        setConversations((prev) => prev.filter((c) => c.id !== id))
        if (activeConversationId === id) {
          startNewConversation()
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Xóa hội thoại thất bại')
      }
    },
    [activeConversationId, startNewConversation]
  )

  const clearCurrentConversation = useCallback(async () => {
    if (!activeConversationId) {
      setMessages([])
      return
    }
    try {
      await clearConversationMessages(activeConversationId)
      setMessages([])
      loadConversations().catch(() => {})
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Không thể xóa tin nhắn')
    }
  }, [activeConversationId, loadConversations])

  const contextValue = useMemo(
    () => ({
      isOpen,
      openChatbot,
      closeChatbot,
      toggleChatbot,
      conversations,
      activeConversation,
      activeConversationId,
      messages,
      isLoading,
      error,
      startNewConversation,
      loadConversations,
      selectConversation,
      sendMessage,
      removeConversation,
      clearCurrentConversation,
    }),
    [
      isOpen,
      openChatbot,
      closeChatbot,
      toggleChatbot,
      conversations,
      activeConversation,
      activeConversationId,
      messages,
      isLoading,
      error,
      startNewConversation,
      loadConversations,
      selectConversation,
      sendMessage,
      removeConversation,
      clearCurrentConversation,
    ]
  )

  return <ChatbotContext.Provider value={contextValue}>{children}</ChatbotContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChatbot() {
  return useContext(ChatbotContext)
}
