import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

interface UserAnalyticsProps {
  userId: number;
}

// Определения типов данных (могут быть вынесены в отдельный файл, например, src/types/analytics.ts)
// interface Track {
//   track_id: number;
//   title: string;
//   artist_name: string;
//   duration_ms: number;
//   play_count: number;
// }

// interface Artist {
//   artist_id: number;
//   name: string;
//   play_count: number;
// }

interface ListeningHistoryItem {
  track_id: number;
  track_title: string;
  artist_name: string;
  timestamp: string;
  play_duration_ms: number;
}

interface SearchHistoryItem {
  query: string;
  timestamp: string;
  results_count: number;
}

interface UserAnalyticsData {
  user_id: number;
  total_listening_time_ms: number;
  total_tracks_played: number;
  favorite_genres: string[];
  favorite_artists: string[];
  activity_by_hour: { [key: number]: number };
}

const UserAnalytics: React.FC<UserAnalyticsProps> = ({ userId }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [userAnalytics, setUserAnalytics] = useState<UserAnalyticsData | null>(null);
  const [listeningHistory, setListeningHistory] = useState<ListeningHistoryItem[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [period, setPeriod] = useState<'week' | 'month' | 'year' | 'all'>('week');

  useEffect(() => {
    if (!userId) { // Проверяем, что userId передан
      setLoading(false);
      setError('ID пользователя не предоставлен.');
      return;
    }

    const fetchAnalyticsData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Запрос основной аналитики пользователя
        const analyticsResponse = await axios.get<UserAnalyticsData>(`/api/v1/analytics/advanced/user-analytics/${userId}?period=${period}`);
        setUserAnalytics(analyticsResponse.data);

        // Запрос истории прослушиваний
        const listeningHistoryResponse = await axios.get<{ listening_history: ListeningHistoryItem[] }>(`/api/v1/analytics/user/${userId}/listening-history?limit=20`);
        setListeningHistory(listeningHistoryResponse.data.listening_history);

        // Запрос истории поиска
        const searchHistoryResponse = await axios.get<{ search_history: SearchHistoryItem[] }>(`/api/v1/analytics/user/search-history?user_id=${userId}&limit=10`);
        setSearchHistory(searchHistoryResponse.data.search_history);

      } catch (err) {
        console.error('Ошибка при загрузке аналитики:', err);
        setError('Не удалось загрузить данные аналитики. Пожалуйста, попробуйте еще раз.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, [userId, period]);

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${(Number(seconds) < 10 ? '0' : '')}${seconds}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="user-analytics analytics-loading">
        <i className="fas fa-spinner fa-spin"></i>
        <p>Загрузка аналитики...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-analytics analytics-error">
        <i className="fas fa-exclamation-circle"></i>
        <p>{error}</p>
      </div>
    );
  }

  if (!userAnalytics) {
    return (
      <div className="user-analytics analytics-empty">
        <i className="fas fa-chart-bar"></i>
        <p>Нет данных аналитики для отображения.</p>
        <Link to="/" className="auth-button-secondary">На главную</Link>
      </div>
    );
  }

  return (
    <div className="user-analytics">
      <div className="analytics-header">
        <h2>Ваша аналитика</h2>
        <div className="period-selector">
          <span>Период:</span>
          <button onClick={() => setPeriod('week')} className={period === 'week' ? 'period-btn active' : 'period-btn'}>Неделя</button>
          <button onClick={() => setPeriod('month')} className={period === 'month' ? 'period-btn active' : 'period-btn'}>Месяц</button>
          <button onClick={() => setPeriod('year')} className={period === 'year' ? 'period-btn active' : 'period-btn'}>Год</button>
          <button onClick={() => setPeriod('all')} className={period === 'all' ? 'period-btn active' : 'period-btn'}>Все время</button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card listening-stats">
          <div className="stat-icon"><i className="fas fa-headphones-alt"></i></div>
          <div className="stat-content">
            <h3>Прослушивания</h3>
            <div className="stat-number">{userAnalytics.total_tracks_played}</div>
            <div className="stat-label">треков прослушано</div>
            <div className="stat-details">
              Всего {formatDuration(userAnalytics.total_listening_time_ms)} времени прослушивания.
            </div>
          </div>
        </div>

        <div className="stat-card search-stats">
          <div className="stat-icon"><i className="fas fa-search"></i></div>
          <div className="stat-content">
            <h3>Поиски</h3>
            <div className="stat-number">{searchHistory.length}</div>
            <div className="stat-label">запросов</div>
            <div className="stat-details">
              Вы активно ищете новую музыку.
            </div>
          </div>
        </div>

        <div className="stat-card activity-stats">
          <div className="stat-icon"><i className="fas fa-users"></i></div>
          <div className="stat-content">
            <h3>Артисты</h3>
            <div className="stat-number">{userAnalytics.favorite_artists.length}</div>
            <div className="stat-label">уникальных артистов</div>
            <div className="stat-details">
              Разнообразие в ваших предпочтениях.
            </div>
          </div>
        </div>
      </div>

      <div className="analytics-section">
        <h3><i className="fas fa-chart-line"></i>Топ треки</h3>
        {/* Топ треков нет в текущей схеме UserAnalytics, поэтому временно закомментировано. */}
        {/* userAnalytics.top_tracks.length > 0 ? (
          <div className="top-tracks">
            {userAnalytics.top_tracks.map((track, index) => (
              <div key={track.track_id} className="track-item">
                <div className="track-rank">{index + 1}</div>
                <div className="track-content">
                  <div className="track-title">{track.title}</div>
                  <div className="track-stats">
                    <span><i className="fas fa-user"></i>{track.artist_name}</span>
                    <span><i className="fas fa-clock"></i>{formatDuration(track.duration_ms)}</span>
                    <span><i className="fas fa-play-circle"></i>{track.play_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="analytics-empty-subtitle">Здесь пока нет топ-треков.</p>
        ) */}
      </div>

      <div className="analytics-section">
        <h3><i className="fas fa-microphone"></i>Топ артисты</h3>
        {userAnalytics.favorite_artists.length > 0 ? (
          <div className="top-tracks"> {/* Используем тот же класс для сетки */}
            {userAnalytics.favorite_artists.map((artist, index) => (
              <div key={index} className="track-item"> {/* Используем track-item для единообразия */}
                <div className="track-rank">{index + 1}</div>
                <div className="track-content">
                  <div className="track-title">{artist}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="analytics-empty-subtitle">Здесь пока нет топ-артистов.</p>
        )}
      </div>

      <div className="analytics-section">
        <h3><i className="fas fa-history"></i>История прослушиваний</h3>
        {listeningHistory.length > 0 ? (
          <div className="search-history"> {/* Переиспользуем класс search-history для списка */}
            {listeningHistory.map((item, index) => (
              <div key={index} className="search-item">
                <div className="search-item-content">
                  <div className="search-item-title">{item.track_title}</div>
                  <div className="search-item-subtitle">{item.artist_name}</div>
                  <div className="search-meta">
                    <span className="search-time">{formatDate(item.timestamp)} {formatTime(item.timestamp)}</span>
                    <span><i className="fas fa-clock"></i> {formatDuration(item.play_duration_ms)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="analytics-empty-subtitle">Вы еще ничего не слушали.</p>
        )}
      </div>

      <div className="analytics-section">
        <h3><i className="fas fa-history"></i>История поиска</h3>
        {searchHistory.length > 0 ? (
          <div className="search-history">
            {searchHistory.map((item, index) => (
              <div key={index} className="search-item">
                <div className="search-item-content">
                  <div className="search-item-title">{item.query}</div>
                  <div className="search-meta">
                    <span className="search-time">{formatDate(item.timestamp)} {formatTime(item.timestamp)}</span>
                    {item.results_count > 0 && (
                      <span className="search-results"><i className="fas fa-check"></i> {item.results_count} результатов</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="analytics-empty-subtitle">Вы еще ничего не искали.</p>
        )}
      </div>

      {/* Пример отображения дневной активности, если данные доступны */}
      {userAnalytics.activity_by_hour && Object.keys(userAnalytics.activity_by_hour).length > 0 && (
        <div className="analytics-section">
          <h3><i className="fas fa-chart-area"></i>Дневная активность</h3>
          <div className="activity-timeline">
            {Object.entries(userAnalytics.activity_by_hour).map(([hour, count]) => {
              const hourNum = parseInt(hour, 10); // Преобразуем ключ в число
              return (
                <div key={hourNum} className="timeline-day">
                  <div className="day-date">{hourNum}:00</div>
                  <div className="day-activities">
                    {count > 0 && (
                      <div
                        className="activity-bar"
                        style={{ height: `${Math.min(count * 2, 80)}px` }} // Масштабируем до 80px max
                      >
                        <span className="activity-count">{count} треков</span>
                      </div>
                    )}
                  </div>
                  <div className="day-total">
                      {formatDuration(count * 60000)} // Предполагаем, что каждое прослушивание в среднем 1 минута
                  </div>
                </div>
              );
            })}
          </div>
          <div className="timeline-legend">
            <div className="legend-item"><span className="legend-color"></span>Прослушивания</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserAnalytics;
