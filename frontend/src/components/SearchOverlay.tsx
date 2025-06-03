import React, { useState, useEffect, useRef } from 'react';
import '../App.css';

interface Track {
  id: number;
  title: string;
  artist_name: string;
  duration: number;
}

interface Artist {
  id: number;
  name: string;
  bio?: string;
}

interface Album {
  id: number;
  title: string;
  artist_name: string;
  release_date: string;
}

interface SearchResults {
  tracks: Track[];
  artists: Artist[];
  albums: Album[];
}

interface SearchOverlayProps {
  isVisible: boolean;
  onClose: () => void;
}

const SearchOverlay: React.FC<SearchOverlayProps> = ({ isVisible, onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults>({ tracks: [], artists: [], albums: [] });
  const [isLoading, setIsLoading] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isVisible && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isVisible]);

  useEffect(() => {
    if (query.trim().length > 0) {
      const timeoutId = setTimeout(() => {
        performSearch(query);
      }, 300); // Debounce search
      
      return () => clearTimeout(timeoutId);
    } else {
      setResults({ tracks: [], artists: [], albums: [] });
    }
  }, [query]);

  const performSearch = async (searchQuery: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/search/multi/?query=${encodeURIComponent(searchQuery)}&limit=10`);
      if (response.ok) {
        const data = await response.json();
        console.log('Search response:', data);
        setResults({
          tracks: data.tracks || [],
          artists: data.artists || [],
          albums: data.albums || []
        });
      } else {
        console.error('Search failed:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Ошибка поиска:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (!isVisible) return null;

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-overlay-content" onClick={e => e.stopPropagation()}>
        <div className="search-header">
          <input
            ref={searchInputRef}
            type="text"
            className="search-input-overlay"
            placeholder="Поиск треков, артистов, альбомов..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="search-close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        {isLoading && (
          <div className="search-loading">
            <i className="fas fa-spinner fa-spin"></i>
            Поиск...
          </div>
        )}

        {query.trim().length > 0 && !isLoading && (
          <div className="search-results">
            {/* Треки */}
            {results.tracks.length > 0 && (
              <div className="search-section">
                <h3 className="search-section-title">Треки</h3>
                {results.tracks.map((track) => (
                  <div key={track.id} className="search-item track-item">
                    <div className="search-item-icon">
                      <i className="fas fa-music"></i>
                    </div>
                    <div className="search-item-content">
                      <div className="search-item-title">{track.title}</div>
                      <div className="search-item-subtitle">{track.artist_name}</div>
                    </div>
                    <div className="search-item-duration">
                      {formatDuration(track.duration)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Альбомы */}
            {results.albums.length > 0 && (
              <div className="search-section">
                <h3 className="search-section-title">Альбомы</h3>
                {results.albums.map((album) => (
                  <div key={album.id} className="search-item album-item">
                    <div className="search-item-icon">
                      <i className="fas fa-compact-disc"></i>
                    </div>
                    <div className="search-item-content">
                      <div className="search-item-title">{album.title}</div>
                      <div className="search-item-subtitle">{album.artist_name} • {new Date(album.release_date).getFullYear()}</div>
                    </div>
                    <div className="search-item-type">
                      Альбом
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Артисты */}
            {results.artists.length > 0 && (
              <div className="search-section">
                <h3 className="search-section-title">Артисты</h3>
                {results.artists.map((artist) => (
                  <div key={artist.id} className="search-item artist-item">
                    <div className="search-item-icon">
                      <i className="fas fa-user-music"></i>
                    </div>
                    <div className="search-item-content">
                      <div className="search-item-title">{artist.name}</div>
                      <div className="search-item-subtitle">Артист</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Пустые результаты */}
            {results.tracks.length === 0 && results.albums.length === 0 && results.artists.length === 0 && (
              <div className="search-empty">
                <i className="fas fa-search"></i>
                <div>По запросу "{query}" ничего не найдено</div>
                <div className="search-empty-subtitle">Попробуйте изменить запрос</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchOverlay;
