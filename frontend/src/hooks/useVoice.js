import { useState, useRef, useCallback, useEffect } from 'react'
import { transcribeAudio } from '../api/client.js'

/**
 * USP 4 — Voice input hook.
 * Uses Web Speech API (SpeechRecognition) when available in browser for instant live transcription,
 * or MediaRecorder + /voice/transcribe (Groq Whisper) as high-accuracy fallback.
 */
export function useVoice({ onTranscribed, language = 'en' } = {}) {
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState(null)

  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  // Clean up recognition / recorder on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop() } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop() } catch {}
      }
    }
  }, [])

  const startRecording = useCallback(async () => {
    setError(null)

    // Option A: Try browser-native Web Speech API if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = true
        recognition.lang = language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : language === 'bn' ? 'bn-IN' : 'en-US'

        let finalTranscript = ''

        recognition.onstart = () => {
          setIsRecording(true)
        }

        recognition.onresult = (event) => {
          let currentTranscript = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              finalTranscript += transcript
            } else {
              currentTranscript += transcript
            }
          }
          const text = finalTranscript || currentTranscript
          if (text && onTranscribed) {
            onTranscribed(text)
          }
        }

        recognition.onerror = (event) => {
          console.warn('Web Speech API error:', event.error)
          if (event.error === 'not-allowed') {
            setError('Microphone access denied.')
            setIsRecording(false)
          } else {
            // Fall back to MediaRecorder path if recognition errored
            recognitionRef.current = null
            startMediaRecorder()
          }
        }

        recognition.onend = () => {
          setIsRecording(false)
          recognitionRef.current = null
        }

        recognition.start()
        recognitionRef.current = recognition
        return
      } catch (err) {
        console.warn('Web Speech API init failed, falling back to MediaRecorder:', err)
      }
    }

    // Option B: Fallback to MediaRecorder + Backend Whisper API
    startMediaRecorder()
  }, [language, onTranscribed])

  const startMediaRecorder = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Determine best supported MIME type
      const mimeTypes = ['audio/webm', 'audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg', '']
      let selectedMime = ''
      for (const mime of mimeTypes) {
        if (!mime || (window.MediaRecorder && MediaRecorder.isTypeSupported(mime))) {
          selectedMime = mime
          break
        }
      }

      const options = selectedMime ? { mimeType: selectedMime } : undefined
      const recorder = new MediaRecorder(stream, options)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setIsTranscribing(true)
        try {
          const type = selectedMime.split(';')[0] || 'audio/webm'
          const blob = new Blob(chunksRef.current, { type })
          const result = await transcribeAudio(blob)
          if (result?.text && onTranscribed) {
            onTranscribed(result.text)
          } else if (!result?.text) {
            setError('No speech detected. Please speak clearly and try again.')
          }
        } catch (err) {
          console.error('Transcription API error:', err)
          setError('Transcription failed. Please check microphone and try again.')
        } finally {
          setIsTranscribing(false)
        }
      }

      recorder.start(100) // collect chunks every 100ms
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch (err) {
      console.error('Microphone error:', err)
      setError('Microphone access denied or not available.')
      setIsRecording(false)
    }
  }

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
      setIsRecording(false)
      return
    }

    if (mediaRecorderRef.current && isRecording) {
      try { mediaRecorderRef.current.stop() } catch {}
      setIsRecording(false)
    }
  }, [isRecording])

  return { isRecording, isTranscribing, error, startRecording, stopRecording }
}
