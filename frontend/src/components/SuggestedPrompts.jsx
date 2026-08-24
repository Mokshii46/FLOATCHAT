import React from 'react'
import { useChat } from '../hooks/useChat.js'
import { Compass, FlaskConical, Dices } from 'lucide-react'

const EXPLORER_PROMPTS = [
  "What's the ocean temperature near India?",
  'Show me all active floats on the map',
  'Which floats are in the Arabian Sea?',
  'Is there anything unusual in the Bay of Bengal?',
]

const RESEARCHER_PROMPTS = [
  'Compare floats 2902183 and 2902200 across depth bins',
  'Thermocline depth and MLD for float 1901234',
  'Temperature anomaly in Bay of Bengal',
  'List all BGC floats with QC flags and sensors',
]

/**
 * Mode-aware clickable prompt chips rendered above the chat input.
 * In Explorer mode, includes the "Surprise Me" button to pick a random active float.
 */
export default function SuggestedPrompts() {
  const { mode, sendMessage, messages, isLoading } = useChat()

  // Only show when chat is empty or has few messages
  if (messages.length > 4) return null

  const prompts = mode === 'researcher' ? RESEARCHER_PROMPTS : EXPLORER_PROMPTS
  const ModeIcon = mode === 'researcher' ? FlaskConical : Compass
  const label = mode === 'researcher' ? 'Research query templates' : 'Try asking'

  const handleSurpriseMe = () => {
    sendMessage("Surprise me! Pick a random active ARGO float and tell me its story in one sentence.")
  }

  return (
    <div className="suggested-prompts">
      <div className="suggested-prompts-label">
        <ModeIcon size={12} />
        <span>{label}</span>
      </div>
      <div className="suggested-prompts-chips">
        {mode !== 'researcher' && (
          <button
            className="prompt-chip surprise-chip"
            onClick={handleSurpriseMe}
            disabled={isLoading}
            title="Pick a random active float and hear its one-line story!"
          >
            <Dices size={13} style={{ marginRight: 4 }} />
            <span>Surprise Me!</span>
          </button>
        )}
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
