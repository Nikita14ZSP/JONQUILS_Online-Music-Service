import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../App.css';
import logo from '../image.png';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
}

interface HomePageProps {
  setShowSearchOverlay: (show: boolean) => void;
}

const HomePage: React.FC<HomePageProps> = ({ setShowSearchOverlay }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('user_role', userData.role); // Сохраняем роль
        localStorage.setItem('user_name', userData.full_name || userData.username); // Сохраняем имя
        
        // Если пользователь - артист, пытаемся получить ID его профиля
        if (userData.role === 'artist') {
          // Предполагаем, что эндпоинт /api/v1/artists/me существует или будет создан
          // или что информация о artist_id приходит в /auth/me
          // В текущей схеме User есть artist_profile_id
          if (userData.artist_profile_id) { 
            localStorage.setItem('artist_id', userData.artist_profile_id.toString());
          } else {
            // Можно добавить логику получения artist_id, если его нет в userData
            // Например, отдельным запросом к /api/v1/artists/by-user/{user_id}
            console.warn('Artist ID not found directly in /auth/me response for artist role.');
          }
        }

      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_name');
        localStorage.removeItem('artist_id');
      }
    } catch (error) {
      console.error('Ошибка проверки авторизации:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user_name');
      localStorage.removeItem('artist_id');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('artist_id');
    setUser(null);
    navigate('/');
  };

  // Добавляем стили для контейнера кнопок аутентификации
  const authButtonsContainerStyle: React.CSSProperties = {
    position: 'absolute',
    top: '20px', // Отступ сверху
    right: '20px', // Отступ справа
    display: 'flex',
    gap: '10px', // Расстояние между кнопками
  };

  if (isLoading) {
    return (
      <div className="app-container">
        <div className="loading">Загрузка...</div>
      </div>
    );
  }
  return (
    <div className="app-container">
      {/* Боковая панель */}
      <div className="sidebar">
        <div className="logo">
          <img src={logo} alt="JONQUILS Logo" className="app-logo" />
          <h2>JONQUILS</h2>
          <p>Online Music Service</p>
        </div>
        <nav className="navigation">
          <ul>
            <li><Link to="/"><i className="fas fa-home"></i> Главная</Link></li>
            <li><Link to="/new"><i className="fas fa-compact-disc"></i> Новое</Link></li>
            <li><Link to="/radio"><i className="fas fa-radio"></i> Радио</Link></li>
          </ul>
        </nav>
      </div>

      {/* Основной контент */}
      <div className="main-content">
        {/* Верхняя панель */}
        <div className="top-bar">
          <div>
            <button onClick={() => setShowSearchOverlay(true)} className="search-button">
              <i className="fas fa-search"></i> Поиск
            </button>
          </div>
          {user ? (
            <div className="auth-buttons-group">
              <span style={{ color: '#fff', marginRight: 10 }}>Привет, {user.full_name || user.username}!</span>
              <Link to="/profile" className="auth-button profile">Профиль</Link>
              <button onClick={handleLogout} className="auth-button logout">Выйти</button>
            </div>
          ) : (
            <div className="auth-buttons-group">
              <Link to="/login" className="auth-button">Войти</Link>
              <Link to="/register" className="auth-button auth-button-secondary">Зарегистрироваться</Link>
            </div>
          )}
        </div>
        <h1>Новинки</h1>
        {/* Раздел с новыми плейлистами/альбомами */}
        <div className="featured-section">
          <h3>Обновленный плейлист</h3>
          <h2>New Music Daily</h2>
          <p>JONQUILS Online Music Service</p>
          {/* Место для картинки из плейлиста */}
          <div className="playlist-image-placeholder"></div>
        </div>
        {/* Раздел с последними треками */}
        <div className="latest-songs-section">
          <h3>Последние треки</h3>
          {/* Список треков */}
          <ul>
            <li>Трек 1</li>
            <li>Трек 2</li>
            {/* и т.д. */}
          </ul>
        </div>
      </div>

      {/* Нижний баннер */}
      {/* <div className="bottom-banner">
        <p>Получите более 100 миллионов песен бесплатно на 1 месяц.</p>
        <button>Попробовать бесплатно</button>
      </div> */}
    </div>
  );
};

export default HomePage;