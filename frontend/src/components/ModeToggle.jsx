import React from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat.js'
import { FlaskConical, Compass } from 'lucide-react'

/**
 * USP 6 — Toggle between Citizen (Explorer) and Researcher mode.
 */
export default function ModeToggle() {
  const { t } = useTranslation()
  const { mode, setMode } = useChat()

  return (
    <div className="mode-toggle">
      <button
        className={`mode-btn ${mode === 'citizen' ? 'active' : ''}`}
        onClick={() => setMode('citizen')}
        title="Citizen / Explorer mode — plain language summaries"
      >
        <Compass size={15} />
        <span>{t('mode_citizen')}</span>
      </button>
      <button
        className={`mode-btn ${mode === 'researcher' ? 'active' : ''}`}
        onClick={() => setMode('researcher')}
        title="Researcher mode — raw data, QC flags, SQL exposed"
      >
        <FlaskConical size={15} />
        <span>{t('mode_researcher')}</span>
      </button>
    </div>
  )
}
