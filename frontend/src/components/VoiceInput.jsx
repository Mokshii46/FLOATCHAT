import React from 'react'
import { useTranslation } from 'react-i18next'
import { useVoice } from '../hooks/useVoice.js'
import { Mic, MicOff, Loader } from 'lucide-react'

/**
 * USP 4 — Mic button that records audio and calls onTranscribed with the result.
 */
export default function VoiceInput({ onTranscribed }) {
  const { t } = useTranslation()
  const { isRecording, isTranscribing, error, startRecording, stopRecording } = useVoice({
    onTranscribed,
  })

  if (isTranscribing) {
    return (
      <button className="voice-btn transcribing" disabled title="Transcribing…">
        <Loader size={18} className="spin" />
      </button>
    )
  }

  return (
    <button
      className={`voice-btn ${isRecording ? 'recording' : ''}`}
      onClick={isRecording ? stopRecording : startRecording}
      title={isRecording ? t('voice_stop') : t('voice_start')}
    >
      {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
    </button>
  )
}
