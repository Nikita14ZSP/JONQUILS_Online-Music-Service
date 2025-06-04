import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface UserAnalyticsProps {
  userId: number;
}

interface AnalyticsData {
  total_listen_time?: number;
  tracks_played_count?: number;
  favorite_genres?: string[];
  most_played_tracks?: Array<{
    title: string;
    artist_name: string;
    play_count: number;
  }>;
  listening_history?: Array<{
    id: number;
    track_title: string;
    artist_name: string;
    listened_at: string;
    listen_duration_ms: number;
  }>;
}

const UserAnalytics: React.FC<UserAnalyticsProps> = ({ userId }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        
        if (!token) {
          setError('Токен доступа не найден');
          return;
        }

        const response = await axios.get(`/api/v1/analytics/user/${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        setAnalyticsData(response.data);
      } catch (err: any) {
        console.error('Ошибка загрузки аналитики:', err);
        setError('Не удалось загрузить данные аналитики');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchAnalytics();
    }
  }, [userId]);

  if (loading) {
    return (
      <div className="analytics-section">
        <h3>📊 Аналитика прослушивания</h3>
        <p>Загрузка данных аналитики...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-section">
        <h3>📊 Аналитика прослушивания</h3>
        <p style={{ color: '#ff6b6b' }}>Ошибка: {error}</p>
      </div>
    );
  }

  return (
    <div className="analytics-section">
      <h3>📊 Аналитика прослушивания</h3>
      
      {analyticsData ? (
        <div className="analytics-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Общая статистика */}
          <div className="analytics-card" style={{ 
            padding: '20px', 
            backgroundColor: '#333', 
            borderRadius: '8px',
            border: '1px solid #444'
          }}>
            <h4>📈 Общая статистика</h4>
            <div style={{ marginTop: '15px' }}>
              <p><strong>Общее время прослушивания:</strong> {
                analyticsData.total_listen_time 
                  ? `${Math.round(analyticsData.total_listen_time / 60)} мин`
                  : 'Нет данных'
              }</p>
              <p><strong>Треков воспроизведено:</strong> {analyticsData.tracks_played_count || 0}</p>
            </div>
          </div>

          {/* Любимые жанры */}
          <div className="analytics-card" style={{ 
            padding: '20px', 
            backgroundColor: '#333', 
            borderRadius: '8px',
            border: '1px solid #444'
          }}>
            <h4>🎵 Любимые жанры</h4>
            <div style={{ marginTop: '15px' }}>
              {analyticsData.favorite_genres && analyticsData.favorite_genres.length > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {analyticsData.favorite_genres.slice(0, 5).map((genre, index) => (
                    <li key={index} style={{ marginBottom: '5px' }}>
                      <span style={{ color: '#1DB954' }}>#{index + 1}</span> {genre}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: '#ccc' }}>Данные о жанрах пока недоступны</p>
              )}
            </div>
          </div>

          {/* Самые популярные треки */}
          <div className="analytics-card" style={{ 
            padding: '20px', 
            backgroundColor: '#333', 
            borderRadius: '8px',
            border: '1px solid #444',
            gridColumn: '1 / -1'
          }}>
            <h4>🏆 Самые прослушиваемые треки</h4>
            <div style={{ marginTop: '15px' }}>
              {analyticsData.most_played_tracks && analyticsData.most_played_tracks.length > 0 ? (
                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  {analyticsData.most_played_tracks.map((track, index) => (
                    <div key={index} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      marginBottom: '10px',
                      padding: '10px',
                      backgroundColor: '#222',
                      borderRadius: '4px'
                    }}>
                      <div>
                        <strong>{track.title}</strong>
                        <br />
                        <span style={{ color: '#ccc' }}>{track.artist_name}</span>
                      </div>
                      <span style={{ 
                        color: '#1DB954', 
                        fontWeight: 'bold' 
                      }}>
                        {track.play_count} воспр.
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#ccc' }}>История прослушивания пока пуста</p>
              )}
            </div>
          </div>

          {/* История прослушивания */}
          <div className="analytics-card" style={{ 
            padding: '20px', 
            backgroundColor: '#333', 
            borderRadius: '8px',
            border: '1px solid #444',
            gridColumn: '1 / -1'
          }}>
            <h4>🕐 Недавняя активность</h4>
            <div style={{ marginTop: '15px' }}>
              {analyticsData.listening_history && analyticsData.listening_history.length > 0 ? (
                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  {analyticsData.listening_history.slice(0, 10).map((activity) => (
                    <div key={activity.id} style={{ 
                      marginBottom: '10px',
                      padding: '10px',
                      backgroundColor: '#222',
                      borderRadius: '4px',
                      borderLeft: '3px solid #1DB954'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <strong>{activity.track_title}</strong>
                          <br />
                          <span style={{ color: '#ccc' }}>{activity.artist_name}</span>
                        </div>
                        <div style={{ textAlign: 'right', fontSize: '12px', color: '#ccc' }}>
                          <div>{new Date(activity.listened_at).toLocaleDateString()}</div>
                          <div>{Math.round(activity.listen_duration_ms / 1000)}с</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#ccc' }}>История активности пока пуста</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <p style={{ color: '#ccc' }}>Нет доступных данных аналитики</p>
      )}
    </div>
  );
};

export default UserAnalytics;