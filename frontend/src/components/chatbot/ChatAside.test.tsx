// SPDX-FileCopyrightText: 2026 Pace Wisdom Solutions Pvt. Ltd.
// SPDX-License-Identifier: Apache-2.0

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChatbotProvider, useChatbot } from '@/context/ChatbotContext'
import ChatAside from '@/components/chatbot/ChatAside'
import AskAiButton from '@/components/chatbot/AskAiButton'

function TestComponent() {
  const { openChatbot } = useChatbot()
  return (
    <div>
      <button onClick={openChatbot}>Open Chat</button>
      <ChatAside />
    </div>
  )
}

describe('Chatbot UI Components', () => {
  it('renders AskAiButton and toggles aside', () => {
    render(
      <ChatbotProvider>
        <AskAiButton />
        <ChatAside />
      </ChatbotProvider>
    )

    const btn = screen.getByTitle('Ask AI')
    expect(btn).toBeInTheDocument()
    expect(screen.queryByLabelText('AI Chatbot')).not.toBeInTheDocument()

    fireEvent.click(btn)
    expect(screen.getByLabelText('AI Chatbot')).toBeInTheDocument()
  })

  it('renders ChatAside with greeting, suggestions and support banner', () => {
    render(
      <ChatbotProvider>
        <TestComponent />
      </ChatbotProvider>
    )

    fireEvent.click(screen.getByText('Open Chat'))
    expect(screen.getByText('Need more help?')).toBeInTheDocument()
    expect(screen.getByText('What are we doing today?')).toBeInTheDocument()
    expect(screen.getByText('An toàn thông tin LMS')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Type @ to tag a resource or ? for shortcuts')).toBeInTheDocument()
  })
})
