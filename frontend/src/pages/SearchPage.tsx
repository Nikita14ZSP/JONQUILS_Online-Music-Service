import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import '../App.css'; // Для общих стилей

interface Track {
  id: number;
  title: string;
  artist_name: string;
  album_title: string;
  genre_name: string;
  duration_ms: number;
  popularity: number;
  explicit: boolean;
  tempo: number;
  energy: number;
  valence: number;
  danceability: number;
  created_at: string;
  artist_image_url?: string;
  album_cover_url?: string;
}

interface Artist {
  id: number;
  name: string;
  bio: string;
  country: string;
  image_url: string;
  created_at: string;
}

interface Album {
  id: number;
  title: string;
  artist_id: number;
  artist_name: string;
  release_date: string;
  cover_image_url: string;
  created_at: string;
}

interface SearchResults {
  tracks: Track[];
  artists: Artist[];
  albums: Album[];
}

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults>({ tracks: [], artists: [], albums: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults({ tracks: [], artists: [], albums: [] });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get<SearchResults>(`/api/v1/search/multi/?query=${query}`);
      setResults(response.data);
    } catch (err) {
      console.error('Error during search:', err);
      setError('Не удалось выполнить поиск. Пожалуйста, попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  }, [query]);

  // Запуск поиска при изменении запроса (с задержкой для debounce)
  useEffect(() => {
    const handler = setTimeout(() => {
      handleSearch();
    }, 500); // 500ms задержка

    return () => {
      clearTimeout(handler);
    };
  }, [query, handleSearch]);

  return (
    <div className="search-page">
      <div className="search-input-container">
        <input
          type="text"
          placeholder="Искать треки, артистов, альбомы..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-input"
        />
      </div>

      {loading && <p className="loading-text">Поиск...</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="search-results">
        {results.tracks.length === 0 && results.artists.length === 0 && results.albums.length === 0 && !loading && query.trim() && (
          <p className="no-results-text">По вашему запросу ничего не найдено.</p>
        )}

        {results.tracks.length > 0 && (
          <div className="results-section">
            <h2>Треки</h2>
            <div className="track-list">
              {results.tracks.map((track) => (
                <div key={track.id} className="track-item">
                  <Link to={`/tracks/${track.id}`} className="track-link">
                    <img src={track.album_cover_url || '/default-album.png'} alt={track.album_title} className="track-cover" />
                    <div className="track-info">
                      <p className="track-title">{track.title}</p>
                      <p className="track-artist">{track.artist_name}</p>
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {results.artists.length > 0 && (
          <div className="results-section">
            <h2>Артисты</h2>
            <div className="artist-list">
              {results.artists.map((artist) => (
                <div key={artist.id} className="artist-item">
                  <Link to={`/artists/${artist.id}`} className="artist-link">
                    <img src={artist.image_url || '/default-artist.png'} alt={artist.name} className="artist-image" />
                    <p className="artist-name">{artist.name}</p>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {results.albums.length > 0 && (
          <div className="results-section">
            <h2>Альбомы</h2>
            <div className="album-list">
              {results.albums.map((album) => (
                <div key={album.id} className="album-item">
                  <Link to={`/albums/${album.id}`} className="album-link">
                    <img src={album.cover_image_url || '/default-album.png'} alt={album.title} className="album-cover" />
                    <div className="album-info">
                      <p className="album-title">{album.title}</p>
                      <p className="album-artist">{album.artist_name}</p>
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
