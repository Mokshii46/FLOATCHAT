import React from 'react'
import { useTranslation } from 'react-i18next'
import { useVoice } from '../hooks/useVoice.js'
import { useChat } from '../hooks/useChat.js'
import { Mic, MicOff, Loader, AlertCircle } from 'lucide-react'

/**
 * USP 4 — Mic button that records audio and populates/transcribes user input.
 */
export default function VoiceInput({ onTranscribed }) {
  const { t } = useTranslation()
  const { language } = useChat()
  const { isRecording, isTranscribing, error, startRecording, stopRecording } = useVoice({
    onTranscribed,
    language,
  })

  if (isTranscribing) {
    return (
      <button className="voice-btn transcribing" disabled title="Transcribing voice with Whisper…">
        <Loader size={18} className="spin" />
      </button>
    )
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        type="button"
        className={`voice-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        title={isRecording ? 'Listening... Click to stop' : 'Click to speak (Voice Input)'}
      >
        {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
      </button>
      {error && (
        <div className="voice-error-tooltip" title={error}>
          <AlertCircle size={12} />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
