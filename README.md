# 🎵 JONQUILS Online Music Service

Серверная часть онлайн-музыкального сервиса, предоставляющая REST API для работы с музыкой, исполнителями, альбомами и аналитикой прослушиваний.

## ✨ Особенности

- 🔍 **Поиск музыки** - по названию, исполнителю, альбому, жанру
- 📊 **Аналитика** - трекинг прослушиваний и статистика
- 🎯 **Рекомендации** - персональные рекомендации треков
- 👤 **Управление пользователями** - регистрация, аутентификация
- 📁 **Загрузка треков** - поддержка URL и локальных файлов
- 🎵 **Плейлисты** - создание и управление плейлистами

## 🛠 Технологии

- **Backend**: Python 3.12, FastAPI
- **База данных**: PostgreSQL, SQLAlchemy (async)
- **Миграции**: Alembic  
- **Аутентификация**: JWT токены
- **Документация**: OpenAPI/Swagger

## 📁 Структура проекта

```
app/
├── api/v1/endpoints/     # API endpoints
├── core/                 # Конфигурация и безопасность
├── db/                   # Модели базы данных
├── schemas/              # Pydantic схемы
└── services/             # Бизнес-логика
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <your-repo-url>
cd JONQUILS_Online-Music-Service
```

### 2. Виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

```bash
# Создайте PostgreSQL базу данных
sudo -u postgres createdb music_service_db

# Скопируйте и настройте конфигурацию
cp .env.example .env
# Отредактируйте .env с вашими настройками БД
```

### 5. Миграции

```bash
# Применить миграции
alembic upgrade head
```

### 6. Тестовые данные (опционально)

```bash
python create_test_data.py
```

### 7. Запуск сервера

```bash
# Развработка
python -m app.main

# Или через uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: http://localhost:8000

## 📖 Документация API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗 API Endpoints

### Аутентификация
- `POST /api/v1/auth/register` - Регистрация пользователя
- `POST /api/v1/auth/login` - Вход в систему

### Треки
- `GET /api/v1/tracks/` - Получить список треков
- `POST /api/v1/tracks/` - Создать новый трек
- `POST /api/v1/tracks/upload-from-url/` - Загрузить трек по URL
- `GET /api/v1/tracks/search/` - Поиск треков
- `GET /api/v1/tracks/popular/` - Популярные треки

### Исполнители
- `GET /api/v1/artists/` - Список исполнителей  
- `POST /api/v1/artists/` - Создать исполнителя

### Альбомы
- `GET /api/v1/albums/` - Список альбомов
- `POST /api/v1/albums/` - Создать альбом

## 🛡 Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/music_service_db
SECRET_KEY=your-super-secret-key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password  
POSTGRES_DB=music_service_db
```

## 🧪 Тестирование

```bash
# Запуск тестов (когда будут добавлены)
pytest

# Проверка кода
flake8 app/
black app/
```

## 📊 Мониторинг

- Логи сохраняются в директории `logs/`
- Метрики доступны через FastAPI встроенные endpoints

## 🤝 Разработка

1. Создайте ветку для новой функции
2. Внесите изменения  
3. Создайте Pull Request
4. После ревью код будет слит в main

## 📝 Лицензия

Этот проект создан для образовательных целей.
    uvicorn app.main:app --reload
    ```
    Сервер будет доступен по адресу `http://127.0.0.1:8000`.
    Документация API (Swagger UI) будет доступна по адресу `http://127.0.0.1:8000/docs`.
    Альтернативная документация (ReDoc) будет доступна по адресу `http://127.0.0.1:8000/redoc`.

## API Эндпоинты (v1)

*   Треки: `/api/v1/tracks/`
*   Аналитика: `/api/v1/analytics/`
*   ... (будет дополняться) 