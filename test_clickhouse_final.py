#!/usr/bin/env python3
"""
Финальный тест ClickHouse интеграции
"""
import sys
import os
import asyncio
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_clickhouse_service():
    """Тестируем ClickHouse сервис"""
    print("🔍 Тестируем ClickHouse сервис...")
    
    try:
        from app.services.clickhouse_service import ClickHouseService
        
        # Создаем экземпляр сервиса
        service = ClickHouseService()
        
        if not service.client:
            print("❌ ClickHouse client не инициализирован")
            return False
        
        print("✅ ClickHouse сервис инициализирован")
        
        # Тестируем подключение
        await service.test_connection()
        print("✅ Подключение протестировано")
        
        # Создаем таблицы
        await service.create_tables()
        print("✅ Таблицы созданы")
        
        # Проверяем таблицы
        result = await service.execute_query("SHOW TABLES FROM jonquils_analytics")
        print(f"📊 Таблицы в базе данных: {result}")
        
        # Тестируем вставку данных
        success = await service.insert_simple_listening_event(
            user_id=1,
            track_id=1,
            played_duration=180,
            device_type='web',
            country='Russia'
        )
        
        if success:
            print("✅ Тестовые данные вставлены!")
        else:
            print("❌ Ошибка вставки данных")
        
        # Проверяем количество записей
        count_result = await service.execute_query("SELECT COUNT(*) as count FROM jonquils_analytics.listening_events")
        print(f"📊 Количество записей в listening_events: {count_result}")
        
        # Тестируем аналитику
        analytics = await service.get_track_analytics(track_id=1, days=30)
        print(f"📈 Аналитика трека: {analytics}")
        
        await service.close()
        print("🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_clickhouse_service())
