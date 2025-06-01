import React from 'react';
import '../App.css'; // Подключаем стили

// Предположим, что ваше изображение доступно по этому пути (нужно будет заменить на реальный путь)
// import userImage from '../assets/user-image.jpg'; 
// Временно используем placeholder
const userImagePlaceholder = 'https://via.placeholder.com/150'; // Заглушка для изображения

const HomePage: React.FC = () => {
  return (
    <div className="app-container">
      {/* Боковая панель */}
      <div className="sidebar">
        <div className="logo">
          {/* Здесь будет ваше изображение или логотип */}
          {/* <img src={userImagePlaceholder} alt="User" className="user-image" /> */}
          <h2>JONQUILS</h2>
          <p>Online Music Service</p>
        </div>
        <nav className="navigation">
          <ul>
            <li><a href="#"><i className="fas fa-home"></i> Главная</a></li>
            <li><a href="#"><i className="fas fa-search"></i> Поиск</a></li>
            <li><a href="#"><i className="fas fa-compact-disc"></i> Новое</a></li>
            <li><a href="#"><i className="fas fa-radio"></i> Радио</a></li>
          </ul>
        </nav>
      </div>

      {/* Основной контент */}
      <div className="main-content">
        {/* Верхняя панель (пока пустая или с кнопкой Войти) */}
        <div className="top-bar">
            {/* <button>Войти</button> */}
        </div>
        
        <h1>Новинки</h1>
        {/* Раздел с новыми плейлистами/альбомами */}
        <div className="featured-section">
          <h3>Обновленный плейлист</h3>
          <h2>New Music Daily</h2>
          <p>Apple Music (заменить на наше название или оставить как есть)</p>
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
      <div className="bottom-banner">
        <p>Получите более 100 миллионов песен бесплатно на 1 месяц.</p>
        <button>Попробовать бесплатно</button>
      </div>
    </div>
  );
};

export default HomePage; 