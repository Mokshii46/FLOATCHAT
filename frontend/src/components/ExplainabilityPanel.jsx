import React from 'react'
import { useTranslation } from 'react-i18next'
import { Code2, Database, Cpu } from 'lucide-react'

/**
 * USP 5 — Shows the generated SQL, routing source, and reasoning.
 */
export default function ExplainabilityPanel({ payload }) {
  const { t } = useTranslation()
  if (!payload) return null

  const {
    source, template_id, template_description,
    params_used, sql, rag_context_snippet, reasoning,
  } = payload

  return (
    <div className="explain-panel">
      <div className="explain-row">
        <Cpu size={14} />
        <span className="explain-label">{t('explain_source')}:</span>
        <span className={`explain-badge ${source}`}>
          {source === 'template' ? t('explain_template') : t('explain_llm')}
        </span>
        {template_id && <span className="template-id">({template_id})</span>}
      </div>

      {template_description && (
        <div className="explain-row">
          <Database size={14} />
          <span className="explain-label">Template:</span>
          <span className="explain-desc">{template_description}</span>
        </div>
      )}

      {reasoning && (
        <p className="explain-reasoning">{reasoning}</p>
      )}

      {sql && (
        <div className="explain-sql-block">
          <div className="explain-sql-header">
            <Code2 size={14} />
            <span>{t('explain_sql')}</span>
          </div>
          <pre className="explain-sql">{sql.trim()}</pre>
        </div>
      )}
    </div>
  )
}
