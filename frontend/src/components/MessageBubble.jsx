import React, { useState } from 'react'
import AnomalyBanner from './AnomalyBanner.jsx'
import ExplainabilityPanel from './ExplainabilityPanel.jsx'
import { useChat } from '../hooks/useChat.js'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function MessageBubble({ message }) {
  const { mode } = useChat()
  const isUser = message.role === 'user'

  // In researcher mode, auto-expand explainability by default
  const [showExplain, setShowExplain] = useState(mode === 'researcher')

  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="bubble-content">
        <p>{message.content}</p>
      </div>

      {/* Anomaly banner — assistant only */}
      {!isUser && message.anomaly && message.anomaly.severity !== 'normal' && (
        <AnomalyBanner anomaly={message.anomaly} />
      )}

      {/* Explainability toggle — assistant only */}
      {!isUser && message.explainability && (
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
    </div>
  )
}
