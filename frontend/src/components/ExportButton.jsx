import React from 'react'
import { useTranslation } from 'react-i18next'
import { getExportUrl } from '../api/client.js'
import { Download } from 'lucide-react'

export default function ExportButton({ sql, rowCount }) {
  const { t } = useTranslation()
  if (!sql) return null

  const handleExport = () => {
    const url = getExportUrl(sql)
    const a = document.createElement('a')
    a.href = url
    a.download = 'floatchat_export.csv'
    a.click()
  }

  return (
    <div className="export-row">
      <button className="export-btn" onClick={handleExport}>
        <Download size={14} />
        <span>{t('export_csv')}</span>
        {rowCount > 0 && <span className="export-count">({rowCount} rows)</span>}
      </button>
    </div>
  )
}
