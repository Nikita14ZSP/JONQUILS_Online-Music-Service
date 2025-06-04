-- Создаем базу данных для аналитики
CREATE DATABASE IF NOT EXISTS jonquils_analytics;

-- Используем созданную базу данных
USE jonquils_analytics;

-- Таблица для логирования API запросов
CREATE TABLE IF NOT EXISTS api_requests_log (
    timestamp DateTime DEFAULT now(),
    request_id String,
    user_id Nullable(UInt64),
    artist_id Nullable(UInt64),
    method String,
    endpoint String,
    status_code UInt16,
    response_time_ms UInt32,
    user_agent String,
    ip_address String,
    request_size Nullable(UInt32),
    response_size Nullable(UInt32),
    error_message Nullable(String),
    session_id Nullable(String),
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
    user_id Nullable(UInt64),
    action String, -- ('play', 'pause', 'skip', 'like', 'download')
    duration_played_ms Nullable(UInt32),
    track_position_ms Nullable(UInt32),
    platform String DEFAULT 'web',
    device_type String DEFAULT 'unknown',
    location Nullable(String),
    session_id Nullable(String),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, track_id, user_id)
TTL date + INTERVAL 2 YEARS;

-- Таблица для аналитики поиска
CREATE TABLE IF NOT EXISTS search_analytics (
    timestamp DateTime DEFAULT now(),
    user_id Nullable(UInt64),
    query String,
    results_count UInt32,
    search_type String, -- ('tracks', 'artists', 'albums', 'all')
    clicked_result_id Nullable(UInt64),
    clicked_result_type Nullable(String), -- ('track', 'artist', 'album')
    session_id Nullable(String),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, query, user_id)
TTL date + INTERVAL 1 YEAR;

-- Таблица для аналитики пользователей
CREATE TABLE IF NOT EXISTS user_analytics (
    timestamp DateTime DEFAULT now(),
    user_id UInt64,
    action String, -- ('login', 'logout', 'register', 'profile_update')
    session_duration_minutes Nullable(UInt32),
    pages_visited UInt32 DEFAULT 1,
    tracks_played UInt32 DEFAULT 0,
    searches_made UInt32 DEFAULT 0,
    session_id Nullable(String),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, user_id)
TTL date + INTERVAL 2 YEARS;

-- Таблица для аналитики артистов
CREATE TABLE IF NOT EXISTS artist_analytics (
    timestamp DateTime DEFAULT now(),
    artist_id UInt64,
    action String, -- ('track_upload', 'album_create', 'profile_update', 'track_delete')
    target_id Nullable(UInt64), 
    metadata Map(String, String),
    date Date DEFAULT toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (timestamp, artist_id)
TTL date + INTERVAL 2 YEARS;

-- Ежедневная статистика по эндпоинтам
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_endpoint_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, endpoint, status_code)
AS SELECT
    date,
    endpoint,
    status_code,
    count() as requests_count,
    avg(response_time_ms) as avg_response_time,
    max(response_time_ms) as max_response_time,
    sum(request_size) as total_request_size,
    sum(response_size) as total_response_size
FROM api_requests_log
GROUP BY date, endpoint, status_code;

-- Ежедневная статистика по трекам
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_track_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, track_id, action)
AS SELECT
    date,
    track_id,
    artist_id,
    action,
    count() as action_count,
    sum(duration_played_ms) as total_play_time,
    uniq(user_id) as unique_listeners
FROM track_analytics
GROUP BY date, track_id, artist_id, action;

-- Ежедневная статистика по поисковым запросам
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_search_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, query, search_type)
AS SELECT
    date,
    query,
    search_type,
    count() as search_count,
    avg(results_count) as avg_results,
    uniq(user_id) as unique_searchers
FROM search_analytics
GROUP BY date, query, search_type;

-- Создаем индексы для быстрого поиска
CREATE INDEX idx_api_endpoint ON api_requests_log (endpoint) TYPE bloom_filter GRANULARITY 1;
CREATE INDEX idx_track_action ON track_analytics (action) TYPE bloom_filter GRANULARITY 1;
CREATE INDEX idx_search_query ON search_analytics (query) TYPE bloom_filter GRANULARITY 1;
