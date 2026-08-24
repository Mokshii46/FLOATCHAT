import React, { useState, useEffect } from 'react'
import { Sparkles, Globe, Compass, FlaskConical, Mic, Database, X, ChevronRight, ChevronLeft, Check } from 'lucide-react'

const TOUR_STEPS = [
  {
    title: 'Welcome to FloatChat',
    badge: 'AI Ocean Exploration',
    icon: Sparkles,
    color: '#06b6d4',
    content:
      'FloatChat gives you instant conversational access to the global ARGO float network, querying physical and biogeochemical ocean observations across the globe.',
  },
  {
    title: '360° Interactive Ocean Map',
    badge: 'Real-Time Fleet',
    icon: Globe,
    color: '#6366f1',
    content:
      'Explore 470+ live ARGO floats and all 7 world oceans. Click on any float or ocean badge to inspect surface measurements or jump straight to analysis.',
  },
  {
    title: 'Explorer vs. Researcher Modes',
    badge: 'Tailored Experience',
    icon: FlaskConical,
    color: '#f59e0b',
    content:
      'Explorer mode offers friendly plain-language summaries and voice input. Researcher mode unlocks raw tabular datasets, ARGO quality control (QC) flags, and always-on SQL.',
  },
  {
    title: 'Voice & Natural Language',
    badge: 'Ask Anything',
    icon: Mic,
    color: '#10b981',
    content:
      'Speak your question in English or regional languages, or pick from suggested prompt templates to uncover ocean temperature, salinity, thermoclines, and BGC chlorophyll.',
  },
]

export default function GuidedTour({ isOpen, onClose }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [visible, setVisible] = useState(false)

  // Auto-launch on first visit
  useEffect(() => {
    const tourDone = localStorage.getItem('floatchat_tour_completed')
    if (!tourDone) {
      setVisible(true)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0)
      setVisible(true)
    }
  }, [isOpen])

  if (!visible) return null

  const handleClose = () => {
    localStorage.setItem('floatchat_tour_completed', 'true')
    setVisible(false)
    if (onClose) onClose()
  }

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1)
    } else {
      handleClose()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const step = TOUR_STEPS[currentStep]
  const Icon = step.icon

  return (
    <div className="tour-overlay" onClick={handleClose}>
      <div className="tour-modal" onClick={(e) => e.stopPropagation()}>
        <button className="tour-close-btn" onClick={handleClose} title="Skip tour">
          <X size={16} />
        </button>

        <div className="tour-header">
          <div className="tour-icon-wrap" style={{ background: `${step.color}20`, color: step.color }}>
            <Icon size={24} />
          </div>
          <div>
            <span className="tour-badge" style={{ color: step.color, borderColor: `${step.color}40` }}>
              {step.badge}
            </span>
            <h3 className="tour-title">{step.title}</h3>
          </div>
        </div>

        <div className="tour-body">
          <p>{step.content}</p>
        </div>

        <div className="tour-footer">
          <div className="tour-dots">
            {TOUR_STEPS.map((_, i) => (
              <span
                key={i}
                className={`tour-dot ${i === currentStep ? 'active' : ''}`}
                onClick={() => setCurrentStep(i)}
              />
            ))}
          </div>

          <div className="tour-actions">
            {currentStep > 0 && (
              <button className="tour-btn tour-prev-btn" onClick={handlePrev}>
                <ChevronLeft size={14} /> Back
              </button>
            )}
            <button className="tour-btn tour-next-btn" onClick={handleNext}>
              {currentStep === TOUR_STEPS.length - 1 ? (
                <>
                  <span>Got it!</span> <Check size={14} />
                </>
              ) : (
                <>
                  <span>Next</span> <ChevronRight size={14} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
