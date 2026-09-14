import React from 'react'
import ReactDOM from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    <Toaster position="top-center" toastOptions={{ style: { fontSize: '13px', borderRadius: '10px' } }} />
  </React.StrictMode>,
)
