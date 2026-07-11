function Sidebar({ isOpen, onClose, history, favorites, activeFilter, onFilterChange, onSelectHistoryMood }) {
  const mediaTypes = ['all', 'movie', 'music', 'book']

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'visible' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span>Menu</span>
          <button className="sidebar-close" onClick={onClose}>×</button>
        </div>

        <div className="sidebar-section">
          <h3>Filter by type</h3>
          <div className="filter-pills">
            {mediaTypes.map((type) => (
              <button
                key={type}
                className={`filter-pill ${activeFilter === type ? 'active' : ''}`}
                onClick={() => onFilterChange(type)}
              >
                {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-section">
          <h3>Mood history</h3>
          {history.length === 0 && <p className="sidebar-empty">No moods picked yet.</p>}
          <ul className="history-list">
            {history.map((entry, i) => (
              <li key={i} onClick={() => onSelectHistoryMood(entry.mood)}>
                <span className="history-dot" style={{ background: entry.color }} />
                {entry.mood}
                <span className="history-time">{entry.time}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="sidebar-section">
          <h3>Favorites ({favorites.length})</h3>
          {favorites.length === 0 && <p className="sidebar-empty">Nothing saved yet.</p>}
          <ul className="favorites-list">
            {favorites.map((item) => (
              <li key={item.id}>
                <a href={item.source_url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </>
  )
}

export default Sidebar