import { useChatContext } from '../context/ChatContext.jsx'
import { sendChat } from '../api/client.js'

export function useChat() {
  const { state, dispatch } = useChatContext()

  const sendMessage = async (question) => {
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
  }

  const setMode = (mode) => dispatch({ type: 'SET_MODE', payload: mode })
  const setLanguage = (lang) => dispatch({ type: 'SET_LANGUAGE', payload: lang })
  const clearChat = () => dispatch({ type: 'CLEAR' })

  return {
    messages: state.messages,
    mode: state.mode,
    language: state.language,
    isLoading: state.isLoading,
    lastSql: state.lastSql,
    rowCount: state.rowCount,
    sendMessage,
    setMode,
    setLanguage,
    clearChat,
  }
}
