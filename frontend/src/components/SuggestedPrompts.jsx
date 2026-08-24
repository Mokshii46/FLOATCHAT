import React from 'react'
import { useChat } from '../hooks/useChat.js'
import { Compass, FlaskConical } from 'lucide-react'

const EXPLORER_PROMPTS = [
  "What's the ocean temperature near India?",
  'Show me all active floats on a map',
  'Which floats are in the Arabian Sea?',
  'Is there anything unusual in the Bay of Bengal?',
]

const RESEARCHER_PROMPTS = [
  'Temperature anomaly in Bay of Bengal',
  'List all BGC floats with their sensors',
  'Compare floats 2902183 and 2902200',
  'Dissolved oxygen trend in Arabian Sea',
]

/**
 * Mode-aware clickable prompt chips rendered above the chat input.
 * Explorer mode shows plain-language prompts; Researcher mode shows technical/query-style prompts.
 */
export default function SuggestedPrompts() {
  const { mode, sendMessage, messages, isLoading } = useChat()

  // Only show when chat is empty or has few messages
  if (messages.length > 4) return null

  const prompts = mode === 'researcher' ? RESEARCHER_PROMPTS : EXPLORER_PROMPTS
  const ModeIcon = mode === 'researcher' ? FlaskConical : Compass
  const label = mode === 'researcher' ? 'Research queries' : 'Try asking'

  return (
    <div className="suggested-prompts">
      <div className="suggested-prompts-label">
        <ModeIcon size={12} />
        <span>{label}</span>
      </div>
      <div className="suggested-prompts-chips">
        {prompts.map((q) => (
          <button
            key={q}
            className="prompt-chip"
            onClick={() => sendMessage(q)}
            disabled={isLoading}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
