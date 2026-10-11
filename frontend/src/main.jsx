import { Component, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class Boundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return <pre style={{ color: 'red', padding: 16, whiteSpace: 'pre-wrap' }}>
        Crash: {String(this.state.error)}
      </pre>
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Boundary><App /></Boundary>
  </StrictMode>,
)