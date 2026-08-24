import { useCallback } from 'react'
import { useChatContext } from '../context/ChatContext.jsx'
import { sendChat } from '../api/client.js'

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
}

export function useChat() {
  const { state, dispatch } = useChatContext()

  const sendMessage = useCallback(async (question) => {
    if (!question.trim()) return
    dispatch({ type: 'ADD_USER_MESSAGE', payload: question })
    dispatch({ type: 'SET_LOADING', payload: true })

    try {
      const response = await sendChat(question, {
        mode: state.mode,
        language: state.language,
      })
      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: response })
    } catch (err) {
      dispatch({
        type: 'ADD_ASSISTANT_MESSAGE',
        payload: {
          answer: 'Sorry, something went wrong. Please try again.',
          viz: null,
          anomaly: null,
          explainability: null,
          row_count: 0,
        },
      })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [dispatch, state.mode, state.language])

  const editMessage = useCallback(async (index, newQuestion) => {
    // Truncate messages at the given index, then send the new message
    dispatch({ type: 'EDIT_USER_MESSAGE', payload: { index } })
    // Small delay to let the truncation apply, then send new message
    dispatch({ type: 'ADD_USER_MESSAGE', payload: newQuestion })
    dispatch({ type: 'SET_LOADING', payload: true })

    try {
      const response = await sendChat(newQuestion, {
        mode: state.mode,
        language: state.language,
      })
      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: response })
    } catch (err) {
      dispatch({
        type: 'ADD_ASSISTANT_MESSAGE',
        payload: {
          answer: 'Sorry, something went wrong. Please try again.',
          viz: null,
          anomaly: null,
          explainability: null,
          row_count: 0,
        },
      })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [dispatch, state.mode, state.language])

  const setMode = useCallback((mode) => dispatch({ type: 'SET_MODE', payload: mode }), [dispatch])
  const setLanguage = useCallback((lang) => dispatch({ type: 'SET_LANGUAGE', payload: lang }), [dispatch])

  const clearChat = useCallback(() => {
    // Save current session before clearing (if there are messages)
    if (state.messages.length > 0) {
      const sessionId = state.sessionId || generateId()
      const firstUserMsg = state.messages.find((m) => m.role === 'user')
      const title = firstUserMsg
        ? firstUserMsg.content.slice(0, 60) + (firstUserMsg.content.length > 60 ? '…' : '')
        : 'Untitled conversation'
      dispatch({
        type: 'SAVE_SESSION',
        payload: { id: sessionId, title, messages: state.messages },
      })
    }
    dispatch({ type: 'CLEAR' })
  }, [dispatch, state.messages, state.sessionId])

  const loadSession = useCallback((sessionId) => {
    dispatch({ type: 'LOAD_SESSION', payload: sessionId })
  }, [dispatch])

  const deleteSession = useCallback((sessionId) => {
    dispatch({ type: 'DELETE_SESSION', payload: sessionId })
  }, [dispatch])

  return {
    messages: state.messages,
    mode: state.mode,
    language: state.language,
    isLoading: state.isLoading,
    lastSql: state.lastSql,
    rowCount: state.rowCount,
    mapResetKey: state.mapResetKey,
    sessions: state.sessions,
    sendMessage,
    editMessage,
    setMode,
    setLanguage,
    clearChat,
    loadSession,
    deleteSession,
  }
}
