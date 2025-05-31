from typing import List, Optional
from app.schemas.user_activity import UserActivity, UserActivityCreate

# Временное хранилище для логов активности (в памяти)
FAKE_USER_ACTIVITY_LOGS: List[UserActivity] = []

class AnalyticsService:
    def log_user_activity(self, activity_in: UserActivityCreate) -> UserActivity:
        print(f"Logging user activity: {activity_in.model_dump_json(indent=2)}")
        
        # В реальном приложении здесь будет сохранение в БД (например, ClickHouse или другую)
        # или отправка в очередь сообщений (Kafka)
        
        # Для демонстрации просто добавляем в список в памяти
        new_id = len(FAKE_USER_ACTIVITY_LOGS) + 1
        logged_activity = UserActivity(id=new_id, **activity_in.model_dump())
        FAKE_USER_ACTIVITY_LOGS.append(logged_activity)
        return logged_activity

    def get_activity_logs_for_track(self, track_id: int, limit: int = 100) -> List[UserActivity]:
        """Получить логи активности для конкретного трека (пример)."""
        return [log for log in FAKE_USER_ACTIVITY_LOGS if log.track_id == track_id][-limit:]
    
    def get_all_activity_logs(self, limit: int = 100) -> List[UserActivity]:
        """Получить все логи активности (пример)."""
        return FAKE_USER_ACTIVITY_LOGS[-limit:]

analytics_service = AnalyticsService() 