import React, { createContext, useContext, useReducer } from 'react'

const ChatContext = createContext(null)

const initialState = {
  messages: [],        // [{ role: 'user'|'assistant', content, viz, anomaly, explainability }]
  mode: 'citizen',     // 'citizen' | 'researcher'
  language: 'en',      // ISO 639-1
  isLoading: false,
  lastSql: null,       // last validated SQL (for export)
  rowCount: 0,
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

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }

    case 'SET_MODE':
      return { ...state, mode: action.payload }

    case 'SET_LANGUAGE':
      return { ...state, language: action.payload }

    case 'CLEAR':
      return { ...initialState, mode: state.mode, language: state.language }

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
