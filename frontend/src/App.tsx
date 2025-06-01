import React from 'react';
import { Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import './App.css';

function App() {
  return (
    <div>
      Проверка отображения.
      <Routes>
        <Route path="/" element={<HomePage />} />
        {/* Здесь будут другие маршруты */}
      </Routes>
    </div>
  );
}

export default App;
