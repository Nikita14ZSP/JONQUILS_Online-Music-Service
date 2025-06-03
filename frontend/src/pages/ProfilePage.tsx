import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ArtistDashboard from '../components/ArtistDashboard';
import UserAnalytics from '../components/UserAnalytics';

const ProfilePage: React.FC = () => {
  const [userRole, setUserRole] = useState<string | null>(null); 
  const [userName, setUserName] = useState<string | null>(null); 
  const [userId, setUserId] = useState<number | null>(null);
  const [artistId, setArtistId] = useState<string | null>(null); 
  const [loading, setLoading] = useState<boolean>(true); // Состояние загрузки
  const [error, setError] = useState<string | null>(null); // Состояние ошибки

  useEffect(() => {
    const fetchUserProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setError('Токен доступа не найден. Пожалуйста, войдите снова.');
          setLoading(false);
          return;
        }

        const response = await fetch('http://localhost:8000/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('Данные пользователя из /api/v1/auth/me:', userData);
          setUserRole(userData.role);
          setUserName(userData.username || userData.full_name);
          setUserId(userData.id);
          if (userData.artist_profile_id) {
            setArtistId(userData.artist_profile_id.toString());
          } else {
            setArtistId(null);
          }
          localStorage.setItem('user_role', userData.role);
          localStorage.setItem('user_name', userData.username || userData.full_name);
          localStorage.setItem('user_id', userData.id.toString());
          if (userData.artist_profile_id) {
            localStorage.setItem('artist_id', userData.artist_profile_id.toString());
          } else {
            localStorage.removeItem('artist_id');
          }

        } else {
          const errorData = await response.json();
          setError(`Не удалось получить данные профиля: ${errorData.detail || response.statusText}`);
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_role');
          localStorage.removeItem('user_name');
          localStorage.removeItem('user_id');
          localStorage.removeItem('artist_id');
        }
      } catch (err: any) {
        setError(`Ошибка сети или сервера: ${err.message}`);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_id');
        localStorage.removeItem('artist_id');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  if (loading) {
    return <div className="profile-container">Загрузка профиля...</div>;
  }

  if (error) {
    return <div className="profile-container" style={{ color: 'red' }}>Ошибка: {error}</div>;
  }

  return (
    <div className="main-content profile-page">
      <h1>Профиль</h1>
      <p>Добро пожаловать, {userName || 'Пользователь'}!</p>
      <p>Ваша роль: {userRole === 'artist' ? 'Артист' : 'Слушатель'}</p>

      {userRole === 'artist' && artistId && (
        <ArtistDashboard />
      )}

      {userRole === 'listener' && userId && (
        <div className="listener-profile-info">
          <UserAnalytics userId={userId} />
        </div>
      )}
       <Link to="/" className="auth-button-secondary" style={{ marginTop: '20px' }}>На главную</Link>
    </div>
  );
};

export default ProfilePage;
