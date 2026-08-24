import React, { useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat.js'
import MessageBubble from './MessageBubble.jsx'
import VoiceInput from './VoiceInput.jsx'
import ExportButton from './ExportButton.jsx'
import SuggestedPrompts from './SuggestedPrompts.jsx'
import { Send, Trash2, Compass, FlaskConical, Sparkles, History, X, Clock, Plus } from 'lucide-react'

export default function ChatPanel() {
  const { t } = useTranslation()
  const { messages, isLoading, sendMessage, clearChat, lastSql, rowCount, mode,
          sessions, loadSession, deleteSession } = useChat()
  const [input, setInput] = useState('')
  const [showHistory, setShowHistory] = useState(false)
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

  const handleNewChat = () => {
    clearChat()
    setShowHistory(false)
  }

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <button
            className="new-chat-btn"
            onClick={handleNewChat}
            title="Start new chat"
          >
            <Plus size={14} />
            <span>New Chat</span>
          </button>
          {sessions.length > 0 && (
            <button
              className="icon-btn"
              onClick={() => setShowHistory(!showHistory)}
              title="Chat history"
            >
              <History size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Session history dropdown */}
      {showHistory && (
        <div className="session-history">
          <div className="session-history-header">
            <span>Chat History</span>
            <button className="icon-btn" onClick={() => setShowHistory(false)}>
              <X size={14} />
            </button>
          </div>
          {sessions.map((s) => (
            <div key={s.id} className="session-item">
              <button
                className="session-item-btn"
                onClick={() => { loadSession(s.id); setShowHistory(false) }}
              >
                <Clock size={12} />
                <span className="session-title">{s.title}</span>
              </button>
              <button
                className="session-delete-btn"
                onClick={() => deleteSession(s.id)}
                title="Delete session"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

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
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={`${i}-${msg.content?.slice(0,20)}`} message={msg} index={i} />
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

      {/* Suggested prompts above input */}
      <SuggestedPrompts />

      {/* Input row */}
      <div className="input-row">
        {mode !== 'researcher' ? (
          <VoiceInput onTranscribed={(text) => setInput(text)} />
        ) : (
          <div className="researcher-input-badge" title="Researcher NL2SQL Mode Active">
            <FlaskConical size={16} />
          </div>
        )}
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
