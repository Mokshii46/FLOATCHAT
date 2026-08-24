import React, { useState, useRef, useEffect } from 'react'
import AnomalyBanner from './AnomalyBanner.jsx'
import ExplainabilityPanel from './ExplainabilityPanel.jsx'
import StatCard from './StatCard.jsx'
import { useChat } from '../hooks/useChat.js'
import { ChevronDown, ChevronUp, Copy, Check, Pencil, X, Send, Sparkles } from 'lucide-react'

const OCEAN_FACTS = [
  "ARGO floats drift at a parking depth of 1,000m for 9 days, dive to 2,000m, and surface in ~6 hours to beam data to satellites.",
  "The Arabian Sea contains one of the world's most intense Oxygen Minimum Zones (OMZ) between 200m and 1,000m depths.",
  "Biogeochemical (BGC) floats measure ocean pH, nitrate, and chlorophyll to monitor marine food webs and acidification.",
  "Earth's oceans absorb over 90% of excess planetary heat, which is continuously monitored by global ARGO fleets.",
  "The Southern Ocean acts as the planet's primary carbon sink, capturing ~40% of all oceanic anthropogenic CO2.",
  "The Bay of Bengal surface waters are much fresher than the Arabian Sea due to massive monsoon river discharge.",
  "Deep ARGO floats dive down to 6,000 meters to uncover deep ocean warming and abyssal current dynamics.",
  "All ARGO float observations are publicly accessible and quality-controlled within 24 hours of surfacing.",
]

export default function MessageBubble({ message, index }) {
  const { mode, editMessage } = useChat()
  const isUser = message.role === 'user'

  const [showExplain, setShowExplain] = useState(false)
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
      <div className="message-bubble user editing">
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

  const oceanFact = OCEAN_FACTS[(index * 3 + 1) % OCEAN_FACTS.length]

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

      {/* Explorer mode: "Did you know?" fact card */}
      {!isUser && mode !== 'researcher' && (
        <div className="ocean-fact-card">
          <Sparkles size={13} className="fact-icon" />
          <span className="fact-text">
            <strong>Did you know?</strong> {oceanFact}
          </span>
        </div>
      )}

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

      {/* Explainability / SQL */}
      {!isUser && message.explainability && (
        <>
          {mode === 'researcher' ? (
            /* Researcher mode: SQL is ALWAYS visible inline */
            <div className="explain-inline">
              <ExplainabilityPanel payload={message.explainability} />
            </div>
          ) : (
            /* Explorer mode: collapsible button */
            <div className="explain-toggle">
              <button
                className="explain-toggle-btn"
                onClick={() => setShowExplain(!showExplain)}
              >
                {showExplain ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showExplain ? 'Hide technical query' : 'How did FloatChat query this?'}
              </button>
              {showExplain && <ExplainabilityPanel payload={message.explainability} />}
            </div>
          )}
        </>
      )}
    </div>
  )
}
