# Используем базовый образ Python
FROM python:3.9-slim

# Устанавливаем системные зависимости для сборки некоторых Python пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию в корень
WORKDIR /

# Копируем файлы зависимостей в корень
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения (локальная директория ./app) в /app в контейнере
COPY ./app /app

# Создаем директорию для статических файлов, если она не существует
RUN mkdir -p /app/static

# Команда для запуска приложения
# Uvicorn запускается из WORKDIR (/), приложение находится в /app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 