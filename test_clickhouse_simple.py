#!/usr/bin/env python3
"""
Простой тест ClickHouse подключения
"""
import sys
import os
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from clickhouse_driver import Client
from app.core.config import settings

def test_clickhouse_direct():
    """Прямой тест подключения к ClickHouse"""
    print("🔗 Тестируем прямое подключение к ClickHouse...")
    
    # Если пароль пустая строка, передаем None
    password = settings.CLICKHOUSE_PASSWORD if settings.CLICKHOUSE_PASSWORD else None
    
    print(f"Host: {settings.CLICKHOUSE_HOST}")
    print(f"Port: {settings.CLICKHOUSE_PORT}")
    print(f"User: {settings.CLICKHOUSE_USER}")
    print(f"Password: {repr(password)}")
    print(f"Database: {settings.CLICKHOUSE_DATABASE}")
    
    try:
        client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            user=settings.CLICKHOUSE_USER,
            password=password,
            database=settings.CLICKHOUSE_DATABASE
        )
        
        result = client.execute('SELECT 1')
        print(f"✅ Подключение успешно! Результат: {result}")
        
        # Проверяем базу данных
        databases = client.execute('SHOW DATABASES')
        print(f"📋 Доступные базы данных: {databases}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_clickhouse_direct()
