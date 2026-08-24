import React, { useState, useRef, useEffect } from 'react'
import AnomalyBanner from './AnomalyBanner.jsx'
import ExplainabilityPanel from './ExplainabilityPanel.jsx'
import StatCard from './StatCard.jsx'
import { useChat } from '../hooks/useChat.js'
import { ChevronDown, ChevronUp, Copy, Check, Pencil, X, Send } from 'lucide-react'

export default function MessageBubble({ message, index }) {
  const { mode, editMessage } = useChat()
  const isUser = message.role === 'user'

  // In researcher mode, auto-expand explainability by default
  const [showExplain, setShowExplain] = useState(mode === 'researcher')
  const [copied, setCopied] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(message.content)
  const editRef = useRef(null)

  useEffect(() => {
    if (isEditing && editRef.current) {
      editRef.current.focus()
      editRef.current.select()
    }
  }, [isEditing])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  const handleEdit = () => {
    setEditText(message.content)
    setIsEditing(true)
  }

  const handleEditSubmit = () => {
    if (!editText.trim()) return
    setIsEditing(false)
    editMessage(index, editText.trim())
  }

  const handleEditKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleEditSubmit()
    }
    if (e.key === 'Escape') {
      setIsEditing(false)
    }
  }

  // Editing state for user messages
  if (isUser && isEditing) {
    return (
      <div className={`message-bubble user editing`}>
        <div className="edit-container">
          <textarea
            ref={editRef}
            className="edit-input"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            onKeyDown={handleEditKeyDown}
            rows={2}
          />
          <div className="edit-actions">
            <button className="edit-action-btn cancel" onClick={() => setIsEditing(false)}>
              <X size={14} /> Cancel
            </button>
            <button className="edit-action-btn submit" onClick={handleEditSubmit}>
              <Send size={14} /> Send
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Extract one-line takeaway for Explorer mode from assistant content
  const takeaway = !isUser && mode !== 'researcher' && message.content
    ? message.content.split(/\.\s+/)[0] + '.'
    : null

  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      {/* Explorer mode: one-line takeaway for assistant */}
      {!isUser && mode !== 'researcher' && takeaway && message.content.length > 100 && (
        <div className="bubble-takeaway">
          💡 <strong>In short:</strong> {takeaway}
        </div>
      )}

      <div className="bubble-content">
        <p>{message.content}</p>
      </div>

      {/* Inline stat card for assistant messages with stat_card viz */}
      {!isUser && message.viz?.viz_type === 'stat_card' && (
        <div style={{ marginTop: '0.5rem' }}>
          <StatCard data={message.viz.data} />
        </div>
      )}

      {/* Message action buttons */}
      <div className="bubble-actions">
        <button className="bubble-action-btn" onClick={handleCopy} title="Copy message">
          {copied ? <Check size={13} /> : <Copy size={13} />}
        </button>
        {isUser && (
          <button className="bubble-action-btn" onClick={handleEdit} title="Edit message">
            <Pencil size={13} />
          </button>
        )}
      </div>

      {/* Anomaly banner — assistant only */}
      {!isUser && message.anomaly && message.anomaly.severity !== 'normal' && (
        <AnomalyBanner anomaly={message.anomaly} />
      )}

      {/* Explainability — assistant only */}
      {!isUser && message.explainability && (
        <>
          {mode === 'researcher' ? (
            /* Researcher mode: show SQL + details inline by default */
            <div className="explain-inline">
              <ExplainabilityPanel payload={message.explainability} />
            </div>
          ) : (
            /* Explorer mode: toggle to show/hide */
            <div className="explain-toggle">
              <button
                className="explain-toggle-btn"
                onClick={() => setShowExplain(!showExplain)}
              >
                {showExplain ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showExplain ? 'Hide details' : 'How did FloatChat answer this?'}
              </button>
              {showExplain && <ExplainabilityPanel payload={message.explainability} />}
            </div>
          )}
        </>
      )}
    </div>
  )
}
