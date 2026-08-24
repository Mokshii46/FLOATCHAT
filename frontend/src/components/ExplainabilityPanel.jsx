import React from 'react'
import { useTranslation } from 'react-i18next'
import { Code2, Database, Cpu, GraduationCap, Building2, User, Layers, Info } from 'lucide-react'

/**
 * USP 5 & Academic Provenance — Shows generated SQL, routing, and institutional provenance.
 */
export default function ExplainabilityPanel({ payload }) {
  const { t } = useTranslation()
  if (!payload) return null

  const {
    source, template_id, template_description,
    params_used, sql, rag_context_snippet, reasoning,
    provenance,
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

      {/* ── Academic Provenance Footer ─────────────────────────── */}
      {provenance && (
        <div className="provenance-footer">
          <div className="provenance-header">
            <GraduationCap size={14} />
            <span>Academic Provenance & Attribution</span>
          </div>
          <div className="provenance-grid">
            <div className="provenance-item">
              <User size={12} />
              <span className="prov-label">PI:</span>
              <span className="prov-val">{provenance.pi_name}</span>
            </div>
            <div className="provenance-item">
              <Building2 size={12} />
              <span className="prov-label">DAC:</span>
              <span className="prov-val">{provenance.dac}</span>
            </div>
            <div className="provenance-item">
              <Layers size={12} />
              <span className="prov-label">Project:</span>
              <span className="prov-val">{provenance.project_name}</span>
            </div>
            {provenance.platform_type && (
              <div className="provenance-item">
                <Info size={12} />
                <span className="prov-label">Platform:</span>
                <span className="prov-val">{provenance.platform_type}</span>
              </div>
            )}
          </div>
          {provenance.citation && (
            <div className="provenance-citation">
              {provenance.citation}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
