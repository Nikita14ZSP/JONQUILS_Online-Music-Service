import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import SearchPage from './pages/SearchPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TrackDetailPage from './pages/TrackDetailPage';
import ArtistDetailPage from './pages/ArtistDetailPage';
import AlbumDetailPage from './pages/AlbumDetailPage';
import ArtistUploadPage from './pages/ArtistUploadPage';
import './App.css';

function App() {
  const [showSearchOverlay, setShowSearchOverlay] = useState(false); // Состояние для оверлея поиска

  return (
    <div className="app-container">
      {/* Проверка отображения. */}
      <Routes>
        <Route path="/" element={<HomePage setShowSearchOverlay={setShowSearchOverlay} />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/tracks/:id" element={<TrackDetailPage />} />
        <Route path="/artists/:id" element={<ArtistDetailPage />} />
        <Route path="/albums/:id" element={<AlbumDetailPage />} />
        <Route path="/artist/upload" element={<ArtistUploadPage />} />
        {/* Удаляем маршрут для SearchPage, так как она будет оверлеем */}
        {/* <Route path="/search" element={<SearchPage />} /> */}
        {/* Здесь будут другие маршруты */}
      </Routes>

      {/* Оверлей поиска */}
      {showSearchOverlay && (
        <div className="search-overlay">
          <button className="close-search-button" onClick={() => setShowSearchOverlay(false)}>
            &times;
          </button>
          <SearchPage />
        </div>
      )}
    </div>
  );
}

export default App;
