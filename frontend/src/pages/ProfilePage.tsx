import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ArtistDashboard from '../components/ArtistDashboard';

const ProfilePage: React.FC = () => {
  const [userRole, setUserRole] = useState<string | null>(null); 
  const [userName, setUserName] = useState<string | null>(null); 
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

        const response = await fetch('http://localhost:8000/api/v1/auth/me', { // Исправлен порт
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('Данные пользователя из /api/v1/auth/me:', userData);
          setUserRole(userData.role);
          setUserName(userData.username || userData.full_name);
          if (userData.artist_profile_id) {
            setArtistId(userData.artist_profile_id.toString());
          } else {
            setArtistId(null); // Очищаем artistId, если пользователь не артист или нет профиля
          }
          // Также можно сохранить роль в localStorage, если она нужна для других частей приложения
          localStorage.setItem('user_role', userData.role);
          localStorage.setItem('user_name', userData.username || userData.full_name);
          if (userData.artist_profile_id) {
            localStorage.setItem('artist_id', userData.artist_profile_id.toString());
          } else {
            localStorage.removeItem('artist_id');
          }

        } else {
          const errorData = await response.json();
          setError(`Не удалось получить данные профиля: ${errorData.detail || response.statusText}`);
          // Очищаем локальное хранилище при ошибке, чтобы принудить повторный вход
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_role');
          localStorage.removeItem('user_name');
          localStorage.removeItem('artist_id');
        }
      } catch (err: any) {
        setError(`Ошибка сети или сервера: ${err.message}`);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_name');
        localStorage.removeItem('artist_id');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []); // Пустой массив зависимостей, чтобы эффект запускался только один раз при монтировании

  if (loading) {
    return <div className="profile-container">Загрузка профиля...</div>;
  }

  if (error) {
    return <div className="profile-container" style={{ color: 'red' }}>Ошибка: {error}</div>;
  }

  return (
    <div className="profile-container" style={{ padding: '20px', color: '#fff' }}>
      <h1>Профиль</h1>
      <p>Добро пожаловать, {userName || 'Пользователь'}!</p>
      <p>Ваша роль: {userRole === 'artist' ? 'Артист' : 'Слушатель'}</p>

      {userRole === 'artist' && artistId && (
        <ArtistDashboard />
      )}

      {userRole === 'listener' && (
        <div className="listener-profile-info" style={{ marginTop: '20px' }}>
          <h2>Ваши плейлисты и история</h2>
          <p>Скоро здесь появится больше информации о вашей активности.</p>
        </div>
      )}
       <Link to="/" style={{ marginTop: '20px', display: 'inline-block' }}>На главную</Link>
    </div>
  );
};

export default ProfilePage;
