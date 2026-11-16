// SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
// SPDX-License-Identifier: Apache-2.0

import { config } from '@/config'
import { apiGet, apiPost, apiDelete } from '@/lib/api/client'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

export interface ChatConversation {
  id: number
  title: string
  is_pinned?: boolean
  created_at: string
  updated_at: string
  message_count?: number
  last_message?: {
    id: number
    role: string
    content: string
    created_at: string
  } | null
  messages?: ChatMessage[]
}

export interface SendChatResponse {
  conversation: ChatConversation
  user_message: ChatMessage | null
  assistant_message: ChatMessage
}

interface PaginatedResponse<T> {
  count?: number
  next?: string | null
  previous?: string | null
  results?: T[]
}

export async function fetchConversations(): Promise<ChatConversation[]> {
  const data = await apiGet<PaginatedResponse<ChatConversation> | ChatConversation[]>(
    config.api.endpoints.chatbot.conversations
  )
  if (Array.isArray(data)) {
    return data
  }
  return data.results ?? []
}

export async function fetchConversationDetail(id: number): Promise<ChatConversation> {
  return apiGet<ChatConversation>(config.api.endpoints.chatbot.conversationDetail(id))
}

export async function sendChatMessage(
  content: string,
  conversationId?: number | null
): Promise<SendChatResponse> {
  return apiPost<SendChatResponse>(config.api.endpoints.chatbot.chat, {
    content,
    conversation_id: conversationId ?? null,
  })
}

export async function deleteConversation(id: number): Promise<void> {
  return apiDelete(config.api.endpoints.chatbot.conversationDetail(id))
}

export async function clearConversationMessages(id: number): Promise<void> {
  return apiPost(config.api.endpoints.chatbot.clear(id), {})
}
