# JONQUILS Online Music Service - Makefile
# Управление инфраструктурой и развертыванием

.PHONY: help build up down restart logs clean test install-deps migrate seed backup restore

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать это сообщение помощи
	@echo "$(BLUE)JONQUILS Online Music Service$(NC)"
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ================================
# Docker управление
# ================================

build: ## Собрать все Docker образы
	@echo "$(BLUE)🔨 Сборка Docker образов...$(NC)"
	docker-compose build

build-prod: ## Собрать production образы
	@echo "$(BLUE)🔨 Сборка production образов...$(NC)"
	docker-compose -f docker-compose.prod.yml build

build-backend: ## Собрать только backend
	@echo "$(BLUE)🔨 Сборка backend...$(NC)"
	docker build -f Dockerfile.backend -t jonquils-backend .

build-frontend: ## Собрать только frontend
	@echo "$(BLUE)🔨 Сборка frontend...$(NC)"
	docker build -f Dockerfile.frontend -t jonquils-frontend .

up: ## Запустить все сервисы
	@echo "$(BLUE)🚀 Запуск всех сервисов...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Сервисы запущены!$(NC)"
	@echo "$(YELLOW)Проверить статус: make status$(NC)"

up-prod: ## Запустить production сервисы
	@echo "$(BLUE)🚀 Запуск production сервисов...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Production сервисы запущены!$(NC)"

up-backend: ## Запустить только backend сервисы
	@echo "$(BLUE)🚀 Запуск backend сервисов...$(NC)"
	docker-compose up -d postgres redis minio clickhouse elasticsearch backend
	
up-frontend: ## Запустить только frontend
	@echo "$(BLUE)🚀 Запуск frontend...$(NC)"
	docker-compose up -d frontend

down: ## Остановить все сервисы
	@echo "$(RED)🛑 Остановка всех сервисов...$(NC)"
	docker-compose down

down-prod: ## Остановить production сервисы
	@echo "$(RED)🛑 Остановка production сервисов...$(NC)"
	docker-compose -f docker-compose.prod.yml down

restart: down up ## Перезапустить все сервисы

restart-backend: ## Перезапустить backend
	@echo "$(YELLOW)🔄 Перезапуск backend...$(NC)"
	docker-compose restart backend

restart-frontend: ## Перезапустить frontend
	@echo "$(YELLOW)🔄 Перезапуск frontend...$(NC)"
	docker-compose restart frontend

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-backend: ## Показать логи backend
	docker-compose logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose logs -f frontend

logs-db: ## Показать логи баз данных
	docker-compose logs -f postgres clickhouse elasticsearch

logs-storage: ## Показать логи хранилищ
	docker-compose logs -f minio redis

logs-etl: ## Показать логи ETL (Airflow)
	docker-compose logs -f airflow-webserver airflow-scheduler

status: ## Проверить статус всех сервисов
	@echo "$(BLUE)📊 Статус сервисов:$(NC)"
	docker-compose ps

# ================================
# Установка и настройка
# ================================

install-deps: ## Установить Python зависимости
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt

setup: install-deps up wait-for-services migrate seed ## Полная настройка с нуля
	@echo "$(GREEN)🎉 Настройка завершена!$(NC)"

wait-for-services: ## Ждать готовности всех сервисов
	@echo "$(YELLOW)⏳ Ожидание готовности сервисов...$(NC)"
	@sleep 30
	@echo "$(GREEN)✅ Сервисы готовы$(NC)"

# ================================
# База данных
# ================================

migrate: ## Выполнить миграции PostgreSQL
	@echo "$(BLUE)🗃️ Выполнение миграций...$(NC)"
	alembic upgrade head

migrate-create: ## Создать новую миграцию (use: make migrate-create MESSAGE="описание")
	@echo "$(BLUE)📝 Создание миграции...$(NC)"
	alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Откатить последнюю миграцию
	@echo "$(RED)⬇️ Откат миграции...$(NC)"
	alembic downgrade -1

seed: ## Заполнить базы тестовыми данными
	@echo "$(BLUE)🌱 Заполнение тестовыми данными...$(NC)"
	python create_test_analytics_data.py
	python test_clickhouse_final.py

# ================================
# Тестирование
# ================================

test: ## Запустить все тесты
	@echo "$(BLUE)🧪 Запуск тестов...$(NC)"
	python test_infrastructure.py

test-api: ## Тестировать только API
	@echo "$(BLUE)🌐 Тестирование API...$(NC)"
	pytest app/tests/ -v

test-clickhouse: ## Тестировать ClickHouse
	@echo "$(BLUE)📊 Тестирование ClickHouse...$(NC)"
	python test_clickhouse_final.py

test-coverage: ## Запустить тесты с покрытием
	@echo "$(BLUE)📈 Тесты с покрытием...$(NC)"
	pytest --cov=app app/tests/

# ================================
# Разработка
# ================================

dev: ## Запуск в режиме разработки
	@echo "$(BLUE)💻 Запуск в режиме разработки...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Запуск фронтенда в режиме разработки
	@echo "$(BLUE)🎨 Запуск фронтенда...$(NC)"
	cd frontend && npm start

lint: ## Проверка кода
	@echo "$(BLUE)🔍 Проверка кода...$(NC)"
	flake8 app/
	black --check app/
	isort --check-only app/

format: ## Форматирование кода
	@echo "$(BLUE)✨ Форматирование кода...$(NC)"
	black app/
	isort app/

# ================================
# Мониторинг и отладка
# ================================

monitor: ## Открыть все панели мониторинга
	@echo "$(GREEN)📊 Панели мониторинга:$(NC)"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Airflow: http://localhost:8080"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Elasticsearch: http://localhost:9200"
	@echo "ClickHouse: http://localhost:8123"

debug-db: ## Подключиться к PostgreSQL
	docker-compose exec postgres psql -U erik -d music_service_db

debug-clickhouse: ## Подключиться к ClickHouse
	docker-compose exec clickhouse clickhouse-client

debug-redis: ## Подключиться к Redis
	docker-compose exec redis redis-cli -a redispass123

shell-api: ## Открыть shell в API контейнере
	docker-compose exec api bash

# ================================
# Развертывание и мониторинг
# ================================

deploy-staging: ## Развернуть на staging
	@echo "$(BLUE)🚀 Развертывание на staging...$(NC)"
	@./scripts/deploy.sh staging

deploy-prod: ## Развернуть на production
	@echo "$(BLUE)🚀 Развертывание на production...$(NC)"
	@./scripts/deploy.sh production

health: ## Проверить здоровье всех сервисов
	@echo "$(BLUE)🏥 Проверка здоровья сервисов...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)❌ Backend недоступен$(NC)"
	@curl -f http://localhost:3000/health || echo "$(RED)❌ Frontend недоступен$(NC)"
	@curl -f http://localhost:9002/minio/health/live || echo "$(RED)❌ MinIO недоступен$(NC)"
	@curl -f http://localhost:9200/_cluster/health || echo "$(RED)❌ Elasticsearch недоступен$(NC)"
	@echo "$(GREEN)✅ Проверка здоровья завершена$(NC)"

monitor: ## Открыть мониторинг в браузере
	@echo "$(BLUE)📊 Открытие панелей мониторинга...$(NC)"
	@echo "Airflow: http://localhost:8080"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Elasticsearch: http://localhost:9200"
	@echo "ClickHouse: http://localhost:8123"
	@echo "Application: http://localhost:3000"

ps: ## Показать статус контейнеров
	@echo "$(BLUE)📋 Статус контейнеров:$(NC)"
	docker-compose ps

stats: ## Показать статистику ресурсов
	@echo "$(BLUE)📊 Статистика ресурсов:$(NC)"
	docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# ================================
# Очистка и обслуживание
# ================================

clean: ## Очистить Docker ресурсы
	@echo "$(RED)🧹 Очистка Docker ресурсов...$(NC)"
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all: ## Полная очистка (включая образы)
	@echo "$(RED)🧹 Полная очистка...$(NC)"
	docker-compose down -v
	docker system prune -af
	docker volume prune -f
	docker image prune -af

reset: clean setup ## Полный сброс и пересоздание

# ================================
# Резервное копирование
# ================================

backup: ## Создать резервные копии
	@echo "$(BLUE)💾 Создание резервных копий...$(NC)"
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@./scripts/backup.sh

backup-db: ## Резервная копия PostgreSQL
	@echo "$(BLUE)💾 Резервная копия PostgreSQL...$(NC)"
	docker exec jonquils-postgres pg_dump -U erik music_service_db > backups/postgres_$(shell date +%Y%m%d_%H%M%S).sql

backup-clickhouse: ## Резервная копия ClickHouse
	@echo "$(BLUE)💾 Резервная копия ClickHouse...$(NC)"