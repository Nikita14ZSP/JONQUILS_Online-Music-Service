import axios from 'axios';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем интерцептор для автоматического добавления токена к запросам
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Добавляем интерцептор для обработки ответов
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Токен истек или недействителен, очищаем localStorage и перенаправляем на логин
      localStorage.removeItem('token');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user_name');
      localStorage.removeItem('artist_id');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
