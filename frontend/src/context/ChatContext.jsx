import React, { createContext, useContext, useReducer, useEffect } from 'react'

const ChatContext = createContext(null)

const STORAGE_KEY = 'floatchat_sessions'
const ACTIVE_SESSION_KEY = 'floatchat_active_session'

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveSessions(sessions) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  } catch {}
}

const initialState = {
  messages: [],        // [{ role: 'user'|'assistant', content, viz, anomaly, explainability }]
  mode: 'citizen',     // 'citizen' | 'researcher'
  language: 'en',      // ISO 639-1
  isLoading: false,
  lastSql: null,       // last validated SQL (for export)
  rowCount: 0,
  mapResetKey: 0,      // incremented on CLEAR to trigger map reset
  sessionId: null,     // current session ID
  sessions: loadSessions(),  // list of { id, title, messages, updatedAt }
}

function chatReducer(state, action) {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, { role: 'user', content: action.payload }] }

    case 'ADD_ASSISTANT_MESSAGE':
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            role: 'assistant',
            content: action.payload.answer,
            viz: action.payload.viz,
            anomaly: action.payload.anomaly,
            explainability: action.payload.explainability,
          },
        ],
        lastSql: action.payload.explainability?.sql || state.lastSql,
        rowCount: action.payload.row_count || 0,
      }

    case 'EDIT_USER_MESSAGE':
      // Truncate messages at the given index (remove the message at index and everything after)
      return {
        ...state,
        messages: state.messages.slice(0, action.payload.index),
      }

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }

    case 'SET_MODE':
      return { ...state, mode: action.payload }

    case 'SET_LANGUAGE':
      return { ...state, language: action.payload }

    case 'CLEAR':
      return {
        ...initialState,
        mode: state.mode,
        language: state.language,
        mapResetKey: state.mapResetKey + 1,
        sessions: state.sessions,
        sessionId: null,
      }

    case 'SAVE_SESSION': {
      const { id, title, messages: msgs } = action.payload
      const existing = state.sessions.filter((s) => s.id !== id)
      const updated = [
        { id, title, messages: msgs, updatedAt: Date.now() },
        ...existing,
      ].slice(0, 20) // keep last 20 sessions
      saveSessions(updated)
      return { ...state, sessionId: id, sessions: updated }
    }

    case 'LOAD_SESSION': {
      const session = state.sessions.find((s) => s.id === action.payload)
      if (!session) return state
      return {
        ...state,
        messages: session.messages,
        sessionId: session.id,
        lastSql: null,
        rowCount: 0,
      }
    }

    case 'DELETE_SESSION': {
      const remaining = state.sessions.filter((s) => s.id !== action.payload)
      saveSessions(remaining)
      return { ...state, sessions: remaining }
    }

    default:
      return state
  }
}

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  return <ChatContext.Provider value={{ state, dispatch }}>{children}</ChatContext.Provider>
}

export function useChatContext() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChatContext must be used inside ChatProvider')
  return ctx
}
