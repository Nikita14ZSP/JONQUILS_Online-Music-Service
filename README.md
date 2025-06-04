# JONQUILS Online Music Service

Профессиональная платформа для онлайн-музыкального сервиса с расширенной аналитикой, ETL-процессами и микросервисной архитектурой.

## Обзор системы

JONQUILS представляет собой полнофункциональную экосистему для работы с музыкальным контентом, включающую API для управления музыкой, систему аналитики прослушиваний, ETL-пайплайны для обработки данных и фронтенд-приложение для пользователей.

## Архитектура системы

### Компоненты высокого уровня

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │   Analytics     │
│   (React.js)    │◄──►│   (FastAPI)     │◄──►│  (ClickHouse)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         └──────────────┤   (Primary DB)  │──────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   ETL System    │
                        │   (Airflow)     │
                        └─────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
         │    MinIO    │  │    Redis    │  │Elasticsearch│
         │ (Storage)   │  │  (Cache)    │  │  (Search)   │
         └─────────────┘  └─────────────┘  └─────────────┘
```

### Детальная архитектура

Система построена по принципу слоистой архитектуры с четким разделением ответственности между компонентами:

**Frontend Layer**: React.js приложение с TypeScript, обслуживаемое Nginx веб-сервером
**API Gateway Layer**: FastAPI сервер с middleware для аутентификации, аналитики и CORS
**Business Logic Layer**: Сервисы для управления пользователями, треками, артистами и аналитикой
**Data Layer**: Множественные системы хранения данных, оптимизированные под разные задачи
**ETL & Orchestration**: Apache Airflow для оркестрации процессов обработки данных

## Технический стек

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.12
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Authentication**: JWT Tokens
- **API Documentation**: OpenAPI/Swagger

### Frontend
- **Framework**: React.js 18+ with TypeScript
- **Routing**: React Router
- **HTTP Client**: Axios
- **Build Tool**: Create React App
- **Web Server**: Nginx

### Базы данных и хранилища

#### PostgreSQL (Основная БД)
- **Назначение**: Транзакционные данные
- **Схемы**:
  - `public` - основные таблицы (users, tracks, albums, artists)
  - `etl` - метаданные ETL процессов
  - `staging` - промежуточные данные для загрузки
  - `data_warehouse` - агрегированные данные

#### ClickHouse (Аналитическая БД)
- **Назначение**: High-performance analytics
- **Таблицы**:
  - `api_requests_log` - логи API запросов
  - `track_analytics` - аналитика прослушиваний
  - `search_analytics` - аналитика поиска
  - `user_analytics` - пользовательская активность
  - `artist_analytics` - аналитика артистов

#### Redis (Кеш и очереди)
- **Назначение**: Кеширование и временные данные
- **Использование**:
  - Session storage
  - API response caching
  - Airflow message broker

#### Elasticsearch (Поисковая система)
- **Назначение**: Полнотекстовый поиск
- **Индексы**:
  - Треки с метаданными
  - Артисты и альбомы
  - Пользовательские плейлисты

#### MinIO (Объектное хранилище)
- **Назначение**: S3-совместимое хранилище файлов
- **Bucket структура**:
  - `tracks` - аудио файлы
  - `covers` - обложки альбомов
  - `playlists` - экспортированные плейлисты
  - `temp` - временные файлы

## ETL Система (Apache Airflow)

### Основные DAG

#### 1. Music ETL Pipeline (music_etl_pipeline.py)
**Периодичность**: Каждый час
**Задачи**:
1. **Extract**: Извлечение новых треков из S3
2. **Transform**: Обработка метаданных аудио
3. **Load**: Загрузка в PostgreSQL и индексация в Elasticsearch
4. **Analytics**: Создание аналитических агрегатов в ClickHouse

```
S3 (New Audio Files) 
    ↓ extract_new_tracks()
Staging Table 
    ↓ process_audio_metadata()
PostgreSQL (tracks, albums, artists)
    ↓ index_to_elasticsearch()
Elasticsearch (search indices)
    ↓ create_analytics_aggregates()
ClickHouse (analytics tables)
```

#### 2. System Monitoring (system_monitoring.py)
**Периодичность**: Каждые 15 минут
**Задачи**:
1. Мониторинг состояния сервисов
2. Проверка качества данных
3. Аналитика производительности
4. Создание алертов

### ETL Процессы в деталях

#### Извлечение данных (Extract)
- Сканирование S3 bucket 'tracks' на новые файлы
- Сравнение с таблицей etl.s3_file_registry
- Идентификация необработанных файлов
- Извлечение метаданных из аудио файлов

#### Трансформация данных (Transform)
- Извлечение ID3 тегов (название, артист, альбом)
- Определение жанра через ML модель
- Расчет аудио характеристик (tempo, energy, valence)
- Создание thumbnail обложек
- Валидация и очистка данных

#### Загрузка данных (Load)
- Создание записей в PostgreSQL (tracks, albums, artists)
- Индексация в Elasticsearch для поиска
- Создание аналитических записей в ClickHouse
- Обновление кеша Redis

## Сервисная архитектура

### Основные сервисы

#### AuthService
- Регистрация и аутентификация пользователей
- Управление JWT токенами
- Ролевая модель (user, artist, admin)

#### TrackService
- CRUD операции с треками
- Управление метаданными
- Связи с альбомами и артистами

#### ArtistService
- Управление профилями артистов
- Статистика по артистам
- Связи с пользователями

#### AlbumService
- Управление альбомами
- Группировка треков
- Метаданные релизов

#### AnalyticsService
- Запись событий прослушивания
- Агрегация статистики
- Интеграция с ClickHouse

#### SearchService
- Полнотекстовый поиск
- Фильтрация и сортировка
- Автодополнение

#### S3Service
- Загрузка и управление файлами
- Генерация presigned URLs
- Управление хранилищем

## Модель данных

### Основные сущности

```sql
-- Пользователи и аутентификация
users (id, username, email, role, is_active, created_at)
artists (id, user_id, name, bio, country, image_url)

-- Музыкальный контент
genres (id, name, description)
albums (id, artist_id, title, release_date, cover_image_url)
tracks (id, artist_id, album_id, genre_id, title, duration_ms, 
        file_path, popularity, tempo, energy, valence)

-- Пользовательская активность
playlists (id, user_id, title, description, is_public)
playlist_tracks (playlist_id, track_id, position)
listening_history (id, user_id, track_id, played_at, 
                  play_duration_ms, completion_percentage)

-- ETL метаданные
etl.etl_jobs (id, job_name, status, start_time, end_time)
etl.s3_file_registry (id, file_path, bucket_name, status)
staging.track_uploads (id, original_filename, s3_path, metadata)
```

### Аналитические таблицы (ClickHouse)

```sql
-- API запросы
api_requests_log (timestamp, user_id, method, endpoint, 
                 status_code, response_time_ms)

-- Аналитика треков
track_analytics (timestamp, track_id, user_id, action, 
                duration_played_ms, platform, device_type)

-- Поисковая аналитика
search_analytics (timestamp, user_id, query, results_count, 
                 clicked_result_id)

-- Пользовательская активность
user_analytics (timestamp, user_id, action, session_duration_minutes, 
               tracks_played, searches_made)
```

## API Структура

### Аутентификация
```
POST /api/v1/auth/register    # Регистрация
POST /api/v1/auth/login       # Авторизация
GET  /api/v1/auth/me         # Профиль пользователя
POST /api/v1/auth/refresh    # Обновление токена
```

### Управление треками
```
GET    /api/v1/tracks/              # Список треков
POST   /api/v1/tracks/              # Создание трека
GET    /api/v1/tracks/{id}          # Получение трека
PUT    /api/v1/tracks/{id}          # Обновление трека
DELETE /api/v1/tracks/{id}          # Удаление трека
POST   /api/v1/tracks/upload        # Загрузка аудио файла
```

### Управление артистами
```
GET    /api/v1/artists/             # Список артистов
POST   /api/v1/artists/             # Создание артиста
GET    /api/v1/artists/{id}         # Профиль артиста
GET    /api/v1/artists/{id}/tracks  # Треки артиста
GET    /api/v1/artists/{id}/albums  # Альбомы артиста
```

### Поиск
```
GET /api/v1/search/tracks    # Поиск треков
GET /api/v1/search/artists   # Поиск артистов
GET /api/v1/search/albums    # Поиск альбомов
GET /api/v1/search/suggest   # Автодополнение
```

### Аналитика
```
GET /api/v1/analytics/user/{user_id}     # Пользовательская аналитика
GET /api/v1/analytics/track/{track_id}   # Аналитика трека
GET /api/v1/analytics/platform           # Общая аналитика
POST /api/v1/analytics/listen           # Запись события прослушивания
```

## Middleware и безопасность

### Analytics Middleware
Автоматически логирует все API запросы в ClickHouse:
- Время запроса и ответа
- Метод и endpoint
- Статус код
- User ID (если аутентифицирован)
- User Agent и IP адрес

### CORS Middleware
- Разрешенные origins для фронтенда
- Поддержка preflight запросов
- Настройка для development/production

### Authentication Middleware
- JWT токен валидация
- Извлечение пользователя из токена
- Ролевая проверка доступа

## Развертывание

### Docker Compose архитектура

```yaml
services:
  # Application layer
  backend:        # FastAPI сервер
  frontend:       # React + Nginx
  
  # Data layer
  postgres:       # Основная БД
  clickhouse:     # Аналитика
  redis:          # Кеш
  elasticsearch:  # Поиск
  minio:          # Файловое хранилище
  
  # ETL layer
  airflow-webserver:  # Web UI для Airflow
  airflow-scheduler:  # Планировщик задач
```

### Сетевая конфигурация
```
Frontend:     localhost:3000
Backend API:  localhost:8000
Airflow UI:   localhost:8080
PostgreSQL:   localhost:5432
ClickHouse:   localhost:8123 (HTTP), localhost:9000 (Native)
Redis:        localhost:6379
Elasticsearch: localhost:9200
MinIO Console: localhost:9001
MinIO API:    localhost:9002
```

### Health Checks
Все сервисы имеют health check эндпоинты:
- Backend: `GET /health`
- Frontend: `GET /health` (nginx)
- Databases: native health check команды

## Мониторинг и логирование

### Системные метрики
- CPU, Memory, Disk usage
- Network I/O
- Database connections
- API response times

### Бизнес метрики
- Количество активных пользователей
- Новые регистрации
- Прослушивания треков
- Поисковые запросы
- Ошибки API

### Логирование
- Структурированные логи в JSON
- Уровни: DEBUG, INFO, WARNING, ERROR
- Ротация логов по размеру/времени
- Централизованное хранение в `/app/logs`

## Производительность и масштабирование

### Оптимизации базы данных
- Индексы на часто запрашиваемых полях
- Партиционирование ClickHouse таблиц по дате
- Connection pooling для PostgreSQL
- Read replicas для читающих запросов

### Кеширование
- Redis для сессий пользователей
- API response caching
- Static files caching в nginx
- CDN для медиа файлов (в production)

### Асинхронная обработка
- Async/await в FastAPI
- Фоновые задачи через Airflow
- Событийно-ориентированная архитектура

## Безопасность

### Аутентификация и авторизация
- JWT токены с коротким временем жизни
- Refresh tokens для продления сессий
- Ролевая модель доступа
- Rate limiting на API endpoints

### Защита данных
- Хеширование паролей (bcrypt)
- SQL injection protection (SQLAlchemy ORM)
- XSS protection через Content Security Policy
- HTTPS в production

### Аудит безопасности
- Логирование всех действий пользователей
- Мониторинг подозрительной активности
- Регулярные backup данных

## Установка и запуск

### Предварительные требования
- Docker 20.10+
- Docker Compose 2.0+
- Git
- 8GB RAM (рекомендуется)
- 20GB свободного места

### Быстрый старт

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

## Документация API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

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

## Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/music_service_db
SECRET_KEY=your-super-secret-key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password  
POSTGRES_DB=music_service_db
```

## Тестирование

```bash
# Запуск тестов (когда будут добавлены)
pytest

# Проверка кода
flake8 app/
black app/
```

## Мониторинг

- Логи сохраняются в директории `logs/`
- Метрики доступны через FastAPI встроенные endpoints

## Разработка

1. Создайте ветку для новой функции
2. Внесите изменения  
3. Создайте Pull Request
4. После ревью код будет слит в main

## Лицензия

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
