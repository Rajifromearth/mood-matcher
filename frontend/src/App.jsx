import { useState } from 'react'
import Sidebar from './components/Sidebar'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

const MOODS = [
  { key: 'happy', label: 'Happy', color: '#F5B841' },
  { key: 'sad', label: 'Sad', color: '#6C7BC4' },
  { key: 'angry', label: 'Angry', color: '#E14B4B' },
  { key: 'anxious', label: 'Anxious', color: '#C4736C' },
  { key: 'relaxed', label: 'Relaxed', color: '#5FB8A8' },
  { key: 'excited', label: 'Excited', color: '#F2735C' },
  { key: 'nostalgic', label: 'Nostalgic', color: '#B58BC4' },
  { key: 'bored', label: 'Bored', color: '#8A8A8A' },
  { key: 'romantic', label: 'Romantic', color: '#E17FA6' },
  { key: 'lonely', label: 'Lonely', color: '#5C7A9E' },
  { key: 'confident', label: 'Confident', color: '#E8A23D' },
  { key: 'calm', label: 'Calm', color: '#5FA8A0' },
]

function App() {
  const [selectedMood, setSelectedMood] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState('mood')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [history, setHistory] = useState([])
  const [favorites, setFavorites] = useState([])
  const [activeFilter, setActiveFilter] = useState('all')

  const activeColor = selectedMood
    ? MOODS.find((m) => m.key === selectedMood)?.color
    : '#F5B841'

  const pickMood = async (moodKey) => {
    setMode('mood')
    setSelectedMood(moodKey)
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/mood/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: moodKey }),
      })
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)
      const data = await res.json()
      setResults(data.results)

      const moodInfo = MOODS.find((m) => m.key === moodKey)
      setHistory((prev) => [
        { mood: moodInfo.label, color: moodInfo.color, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
        ...prev,
      ].slice(0, 10))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const runSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setMode('search')
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/mood/search?q=${encodeURIComponent(searchQuery)}`)
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)
      const data = await res.json()
      setResults(data.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleFavorite = (item) => {
    setFavorites((prev) => {
      const exists = prev.find((f) => f.id === item.id)
      if (exists) return prev.filter((f) => f.id !== item.id)
      return [...prev, item]
    })
  }

  const isFavorite = (id) => favorites.some((f) => f.id === id)

  const visibleResults = activeFilter === 'all'
    ? results
    : results.filter((r) => r.media_type === activeFilter)

  return (
    <div className="app" style={{ '--accent': activeColor }}>
      <button className="menu-toggle" onClick={() => setSidebarOpen(true)}>☰ Menu</button>

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        history={history}
        favorites={favorites}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        onSelectHistoryMood={(label) => {
          const found = MOODS.find((m) => m.label === label)
          if (found) pickMood(found.key)
          setSidebarOpen(false)
        }}
      />

      <header className="hero">
        <span className="eyebrow">Mood Matcher</span>
        <h1>What's your mood right now?</h1>
        <p>Pick a feeling, or search for something specific.</p>
      </header>

      <form className="search-bar" onSubmit={runSearch}>
        <input
          type="text"
          placeholder="Search movies, music, or books..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <div className="mood-ring">
        {MOODS.map((mood, i) => (
          <button
            key={mood.key}
            className={`mood-btn ${mode === 'mood' && selectedMood === mood.key ? 'active' : ''}`}
            style={{ '--mood-color': mood.color, '--i': i }}
            onClick={() => pickMood(mood.key)}
          >
            {mood.label}
          </button>
        ))}
      </div>

      {loading && <p className="status">Finding matches...</p>}
      {error && <p className="status error">Something went wrong: {error}</p>}

      {mode === 'search' && results.length > 0 && (
        <p className="results-heading">Results for "{searchQuery}"</p>
      )}

      {visibleResults.length > 0 && (
        <div className="results-grid">
          {visibleResults.map((item) => (
            <div key={item.id} className="result-card">
              <button
                className={`favorite-btn ${isFavorite(item.id) ? 'active' : ''}`}
                onClick={(e) => {
                  e.preventDefault()
                  toggleFavorite(item)
                }}
              >
                {isFavorite(item.id) ? '♥' : '♡'}
              </button>
              <a href={item.source_url} target="_blank" rel="noopener noreferrer">
                {item.image_url && <img src={item.image_url} alt={item.title} />}
                <div className="result-info">
                  <span className="media-tag">{item.media_type}</span>
                  <p>{item.title}</p>
                  {item.match_score !== undefined && (
                    <span className="score">match {Math.round(item.match_score * 100)}%</span>
                  )}
                </div>
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App