#!/bin/bash
set -e

# Функция для ожидания PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if pg_isready -h postgres -p 5432 -U erik; then
            echo "PostgreSQL is ready!"
            return 0
        fi
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL did not become ready in time"
    exit 1
}

# Инициализация Airflow только один раз
if [ "$1" = "webserver" ]; then
    wait_for_postgres
    
    echo "Initializing Airflow database..."
    airflow db init || airflow db upgrade
    
    echo "Creating Airflow admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@jonquils.com \
        --password admin123 || echo "User already exists"
        
elif [ "$1" = "scheduler" ]; then
    wait_for_postgres
    
    # Ждем инициализации от webserver
    echo "Waiting for Airflow DB initialization..."
    sleep 10
fi

# Запуск команды
exec airflow "$@"
