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
ORDER BY (timestamp, endpoint)
;
