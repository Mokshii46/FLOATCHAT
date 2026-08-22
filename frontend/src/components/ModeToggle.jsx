import React from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat.js'
import { FlaskConical, Compass } from 'lucide-react'

/**
 * USP 6 — Toggle between Citizen (Explorer) and Researcher mode.
 * Visually distinct: teal for Explorer, amber for Researcher.
 */
export default function ModeToggle() {
  const { t } = useTranslation()
  const { mode, setMode } = useChat()

  return (
    <div className="mode-toggle">
      <button
        className={`mode-btn ${mode === 'citizen' ? 'active citizen-active' : ''}`}
        onClick={() => setMode('citizen')}
        title="Explorer mode — plain language summaries, guided experience"
      >
        <Compass size={14} />
        <span>{t('mode_citizen')}</span>
      </button>
      <button
        className={`mode-btn ${mode === 'researcher' ? 'active researcher-active' : ''}`}
        onClick={() => setMode('researcher')}
        title="Researcher mode — raw data, QC flags, SQL exposed"
      >
        <FlaskConical size={14} />
        <span>{t('mode_researcher')}</span>
      </button>
    </div>
  )
}
