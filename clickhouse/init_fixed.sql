-- Создаем базу данных для аналитики
CREATE DATABASE IF NOT EXISTS jonquils_analytics;

-- Используем созданную базу данных
USE jonquils_analytics;

-- Таблица для логирования API запросов
CREATE TABLE IF NOT EXISTS api_requests_log (
    timestamp DateTime DEFAULT now(),
    request_id String,
    user_id UInt64 DEFAULT 0,
    artist_id UInt64 DEFAULT 0,
    method String,
    endpoint String,
    status_code UInt16,
    response_time_ms UInt32,
    user_agent String DEFAULT '',
    ip_address String DEFAULT '',
    request_size UInt32 DEFAULT 0,
    response_size UInt32 DEFAULT 0,
    error_message String DEFAULT '',
    session_id String DEFAULT '',
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, endpoint, user_id)
TTL date + INTERVAL 1 YEAR;

-- Таблица для аналитики треков
CREATE TABLE IF NOT EXISTS track_analytics (
    timestamp DateTime DEFAULT now(),
    track_id UInt64,
    artist_id UInt64,
    user_id UInt64 DEFAULT 0,
    action String, -- 'play', 'pause', 'skip', 'like', 'download'
    duration_played_ms UInt32 DEFAULT 0,
    track_position_ms UInt32 DEFAULT 0,
    platform String DEFAULT 'web',
    device_type String DEFAULT 'unknown',
    location String DEFAULT '',
    session_id String DEFAULT '',
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, track_id, user_id)
TTL date + INTERVAL 2 YEARS;

-- Таблица для аналитики поиска
CREATE TABLE IF NOT EXISTS search_analytics (
    timestamp DateTime DEFAULT now(),
    user_id UInt64 DEFAULT 0,
    query String,
    results_count UInt32,
    search_type String, -- 'tracks', 'artists', 'albums', 'all'
    clicked_result_id UInt64 DEFAULT 0,
    clicked_result_type String DEFAULT '', -- 'track', 'artist', 'album'
    session_id String DEFAULT '',
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, query, user_id)
TTL date + INTERVAL 1 YEAR;

-- Таблица для аналитики пользователей
CREATE TABLE IF NOT EXISTS user_analytics (
    timestamp DateTime DEFAULT now(),
    user_id UInt64,
    action String, -- 'login', 'logout', 'register', 'profile_update'
    session_duration_minutes UInt32 DEFAULT 0,
    pages_visited UInt32 DEFAULT 1,
    tracks_played UInt32 DEFAULT 0,
    searches_made UInt32 DEFAULT 0,
    session_id String DEFAULT '',
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, user_id)
TTL date + INTERVAL 2 YEARS;

-- Таблица для аналитики артистов
CREATE TABLE IF NOT EXISTS artist_analytics (
    timestamp DateTime DEFAULT now(),
    artist_id UInt64,
    action String, -- 'track_upload', 'album_create', 'profile_update', 'track_delete'
    target_id UInt64 DEFAULT 0, -- ID трека/альбома при соответствующих действиях
    metadata_key String DEFAULT '',
    metadata_value String DEFAULT '',
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, artist_id)
TTL date + INTERVAL 2 YEARS;
