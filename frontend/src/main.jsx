import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { ChatProvider } from './context/ChatContext.jsx'
import './i18n/index.js'
import 'leaflet/dist/leaflet.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChatProvider>
      <App />
    </ChatProvider>
  </React.StrictMode>
)
