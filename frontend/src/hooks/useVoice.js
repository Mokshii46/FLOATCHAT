import { useState, useRef, useCallback } from 'react'
import { transcribeAudio } from '../api/client.js'

/**
 * USP 4 — Voice input hook.
 * Uses browser MediaRecorder API to capture audio, then sends to /voice/transcribe.
 */
export function useVoice({ onTranscribed } = {}) {
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setIsTranscribing(true)
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          const result = await transcribeAudio(blob)
          if (result?.text && onTranscribed) {
            onTranscribed(result.text)
          }
        } catch (err) {
          setError('Transcription failed. Please try again.')
        } finally {
          setIsTranscribing(false)
        }
      }

      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch (err) {
      setError('Microphone access denied.')
    }
  }, [onTranscribed])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }, [isRecording])

  return { isRecording, isTranscribing, error, startRecording, stopRecording }
}
