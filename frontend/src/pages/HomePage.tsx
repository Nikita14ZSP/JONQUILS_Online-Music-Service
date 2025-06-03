import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import SearchOverlay from '../components/SearchOverlay';
import '../App.css';
import logo from '../image.png';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
}

const HomePage: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showSearchOverlay, setShowSearchOverlay] = useState(false);
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
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('user_role', userData.role);
        localStorage.setItem('user_name', userData.full_name || userData.username);
        if (userData.role === 'artist' && userData.artist_profile_id) {
          localStorage.setItem('artist_id', userData.artist_profile_id.toString());
        }
      } else {
        localStorage.clear();
      }
    } catch {
      localStorage.clear();
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    navigate('/');
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
          {/* Поиск по центру */}
          <div className="search-container">
            <input
              className="search-input"
              placeholder="Поиск треков, артистов, альбомов..."
              onFocus={() => setShowSearchOverlay(true)}
              readOnly
            />
          </div>
          {/* Кнопки справа */}
          <div className="auth-buttons-group">
            {user ? (
              <>
                <span className="user-greeting">Привет, {user.full_name || user.username}!</span>
                <Link to="/profile" className="auth-button profile">Профиль</Link>
                <button onClick={handleLogout} className="auth-button logout">Выйти</button>
              </>
            ) : (
              <>
                <Link to="/login" className="auth-button">Войти</Link>
                <Link to="/register" className="auth-button auth-button-secondary">Зарегистрироваться</Link>
              </>
            )}
          </div>
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

      {/* Search Overlay */}
      <SearchOverlay 
        isVisible={showSearchOverlay} 
        onClose={() => setShowSearchOverlay(false)} 
      />
    </div>
  );
};

export default HomePage;
