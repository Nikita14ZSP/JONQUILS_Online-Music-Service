import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../App.css'; // Подключаем стили

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('listener'); // Новое состояние для роли
  const [artistName, setArtistName] = useState(''); // Новое состояние для имени артиста
  const [bio, setBio] = useState(''); // Новое состояние для биографии
  const [country, setCountry] = useState(''); // Новое состояние для страны
  const [imageUrl, setImageUrl] = useState(''); // Новое состояние для URL изображения
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    const requestBody: any = {
      username,
      email,
      password,
      full_name: fullName,
      role,
    };

    if (role === 'artist') {
      if (!artistName) {
        setError('Имя артиста обязательно для роли "Артист".');
        return;
      }
      requestBody.artist_name = artistName;
      if (bio) requestBody.bio = bio;
      if (country) requestBody.country = country;
      if (imageUrl) requestBody.image_url = imageUrl;
    }

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody), // Используем обновленное тело запроса
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Улучшенная обработка ошибок валидации от Pydantic
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const messages = errorData.detail.map((err: any) => {
            // Попытаемся сделать сообщение более читаемым
            if (err.loc && err.msg) {
              const field = err.loc[err.loc.length - 1]; // последнее поле в пути ошибки
              // Простое сопоставление полей с русскими названиями
              let fieldName = field;
              if (field === 'password') fieldName = 'Пароль';
              else if (field === 'username') fieldName = 'Имя пользователя';
              else if (field === 'email') fieldName = 'Email';
              else if (field === 'artist_name') fieldName = 'Имя артиста';
              
              // Пример формирования сообщения: "Пароль: должен содержать не менее 8 символов"
              // Для более сложных случаев можно добавить больше логики
              if (err.msg.includes('ensure this value has at least')) {
                const minLength = err.ctx?.limit_value;
                return `${fieldName}: должен содержать не менее ${minLength} символов.`;
              }
              if (err.msg.includes('value is not a valid email address')) {
                return `${fieldName}: неверный формат email.`;
              }
              return `${fieldName}: ${err.msg}`;
            }
            return err.msg || 'Ошибка валидации';
          }).join('\n');
          throw new Error(messages);
        }
        throw new Error(errorData.detail || 'Ошибка регистрации');
      }

      await response.json();
      setSuccess('Регистрация прошла успешно! Теперь вы можете войти.');
      // Опционально: можно автоматически перенаправить на страницу входа через несколько секунд
      setTimeout(() => {
        navigate('/login');
      }, 3000);

    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <h2>Регистрация</h2>
      <form onSubmit={handleSubmit} className="auth-form">
        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}
        
        {/* Поля для всех пользователей */}
        <div className="form-group">
          <label htmlFor="username">Имя пользователя:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Пароль:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="fullName">Полное имя (опционально):</label>
          <input
            type="text"
            id="fullName"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            // Поле fullName может быть опциональным, убираем required, если это так по схеме
          />
        </div>

        {/* Выбор роли */}
        <div className="form-group">
          <label>Я регистрируюсь как:</label>
          <div>
            <label htmlFor="role-listener" style={{ marginRight: '10px', fontWeight: 'normal' }}>
              <input 
                type="radio" 
                id="role-listener" 
                name="role" 
                value="listener"
                checked={role === 'listener'}
                onChange={(e) => setRole(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              Слушатель
            </label>
            <label htmlFor="role-artist" style={{ fontWeight: 'normal' }}>
              <input 
                type="radio" 
                id="role-artist" 
                name="role" 
                value="artist"
                checked={role === 'artist'}
                onChange={(e) => setRole(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              Артист
            </label>
          </div>
        </div>

        {/* Поля для артиста (отображаются условно) */}
        {role === 'artist' && (
          <>
            <div className="form-group">
              <label htmlFor="artistName">Имя артиста/группы *:</label>
              <input
                type="text"
                id="artistName"
                value={artistName}
                onChange={(e) => setArtistName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="bio">Биография (опционально):</label>
              <textarea
                id="bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={3}
              />
            </div>
            <div className="form-group">
              <label htmlFor="country">Страна (опционально):</label>
              <input
                type="text"
                id="country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="imageUrl">URL изображения (опционально):</label>
              <input
                type="text"
                id="imageUrl"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
              />
            </div>
          </>
        )}

        <button type="submit" className="auth-button">Зарегистрироваться</button>
      </form>
      <p>Уже есть аккаунт? <Link to="/login">Войти</Link></p>
    </div>
  );
};

export default RegisterPage;