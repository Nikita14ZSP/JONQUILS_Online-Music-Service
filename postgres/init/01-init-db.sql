-- Создание базы данных для Airflow
CREATE USER airflow WITH ENCRYPTED PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- Создание дополнительных схем для основной базы
\c music_service_db;

-- Схема для ETL процессов
CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS data_warehouse;

-- Права для пользователя erik
GRANT ALL PRIVILEGES ON SCHEMA etl TO erik;
GRANT ALL PRIVILEGES ON SCHEMA staging TO erik;
GRANT ALL PRIVILEGES ON SCHEMA data_warehouse TO erik;

-- Создание таблиц для ETL мониторинга
CREATE TABLE IF NOT EXISTS etl.etl_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    records_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для трекинга файлов в S3
CREATE TABLE IF NOT EXISTS etl.s3_file_registry (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_size BIGINT,
    file_hash VARCHAR(64),
    bucket_name VARCHAR(255) NOT NULL,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'active'
);

-- Staging таблицы для загрузки данных
CREATE TABLE IF NOT EXISTS staging.track_uploads (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR(500),
    s3_path VARCHAR(500),
    file_size BIGINT,
    duration_seconds INTEGER,
    metadata JSONB,
    upload_user_id INTEGER,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending'
);

-- Data Warehouse таблицы для аналитики
CREATE TABLE IF NOT EXISTS data_warehouse.daily_track_stats (
    date_key DATE PRIMARY KEY,
    total_tracks INTEGER DEFAULT 0,
    total_plays BIGINT DEFAULT 0,
    unique_listeners INTEGER DEFAULT 0,
    total_duration_hours DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_warehouse.monthly_user_stats (
    month_key DATE PRIMARY KEY,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    premium_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl.etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_job_name ON etl.etl_jobs(job_name);
CREATE INDEX IF NOT EXISTS idx_s3_file_registry_bucket ON etl.s3_file_registry(bucket_name);
CREATE INDEX IF NOT EXISTS idx_s3_file_registry_status ON etl.s3_file_registry(status);
CREATE INDEX IF NOT EXISTS idx_track_uploads_status ON staging.track_uploads(processing_status);
