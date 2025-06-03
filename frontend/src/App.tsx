import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import EditArtistProfilePage from './pages/EditArtistProfilePage';
import UploadTrackPage from './pages/UploadTrackPage'; 
import UploadAlbumPage from './pages/UploadAlbumPage'; 
import RadioPage from './pages/RadioPage';
import SearchPage from './pages/SearchPage';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/edit-artist-profile" element={<EditArtistProfilePage />} />
        <Route path="/upload-track" element={<UploadTrackPage />} />
        <Route path="/upload-album" element={<UploadAlbumPage />} />
        <Route path="/radio" element={<RadioPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </div>
  );
};

export default App;
