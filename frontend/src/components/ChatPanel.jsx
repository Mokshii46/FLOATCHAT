import React, { useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat.js'
import MessageBubble from './MessageBubble.jsx'
import VoiceInput from './VoiceInput.jsx'
import ExportButton from './ExportButton.jsx'
import { Send, Trash2, Compass, FlaskConical, Sparkles } from 'lucide-react'

const EXPLORER_PROMPTS = [
  "What's the ocean temperature near India?",
  "Show me all active floats on a map",
  "Which floats are in the Arabian Sea?",
]

const RESEARCHER_PROMPTS = [
  'Temperature anomaly in Bay of Bengal',
  'List all BGC floats with their sensors',
  'Show active floats',
]

export default function ChatPanel() {
  const { t } = useTranslation()
  const { messages, isLoading, sendMessage, clearChat, lastSql, rowCount, mode } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedPrompts = mode === 'researcher' ? RESEARCHER_PROMPTS : EXPLORER_PROMPTS
  const modeLabel = mode === 'researcher' ? 'Research' : 'Explorer'
  const modeClass = mode === 'researcher' ? 'researcher' : 'citizen'

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span className="chat-title">FloatChat</span>
          <span className={`chat-mode-label ${modeClass}`}>
            {mode === 'researcher' ? <FlaskConical size={10} /> : <Compass size={10} />}
            {' '}{modeLabel}
          </span>
        </div>
        <button className="icon-btn" onClick={clearChat} title="Clear chat">
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <Sparkles size={24} />
            </div>
            <p className="empty-hint">
              {mode === 'researcher'
                ? 'Ask precise oceanographic questions'
                : 'Ask anything about ocean data'}
            </p>
            <p className="empty-sub">
              {mode === 'researcher'
                ? 'Get raw data, SQL queries, and QC-flagged results'
                : 'Get easy-to-understand answers with visualizations'}
            </p>
            <div className="suggested-queries">
              {suggestedPrompts.map((q) => (
                <button key={q} className="suggest-btn" onClick={() => sendMessage(q)}>
                  <span className="suggest-icon">→</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="loading-bubble">
            <span className="dot-flashing" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Export row */}
      {lastSql && <ExportButton sql={lastSql} rowCount={rowCount} />}

      {/* Input row */}
      <div className="input-row">
        <VoiceInput onTranscribed={setInput} />
        <textarea
          className="chat-input"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={mode === 'researcher'
            ? 'Ask about specific floats, parameters, regions…'
            : t('ask_placeholder')}
        />
        <button className="send-btn" onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
