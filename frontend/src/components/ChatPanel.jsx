import React, { useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat.js'
import MessageBubble from './MessageBubble.jsx'
import VoiceInput from './VoiceInput.jsx'
import ExportButton from './ExportButton.jsx'
import { Send, Trash2 } from 'lucide-react'

export default function ChatPanel() {
  const { t } = useTranslation()
  const { messages, isLoading, sendMessage, clearChat, lastSql, rowCount } = useChat()
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

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <span className="chat-title">FloatChat</span>
        <button className="icon-btn" onClick={clearChat} title="Clear chat">
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p className="empty-hint">{t('tagline')}</p>
            <div className="suggested-queries">
              {[
                'Temperature in Arabian Sea this year',
                'Show BGC floats on map',
                'Trajectory of float 2902183',
              ].map((q) => (
                <button key={q} className="suggest-btn" onClick={() => sendMessage(q)}>
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
          placeholder={t('ask_placeholder')}
        />
        <button className="send-btn" onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
