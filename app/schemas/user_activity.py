from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserActivityBase(BaseModel):
    user_id: Optional[str] = None # Может быть ID пользователя или анонимный идентификатор
    track_id: int
    action: str # e.g., "play", "pause", "skip", "like", "complete_listen"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    listen_duration_ms: Optional[int] = None # Если применимо (например, для "play" или "complete_listen")
    session_id: Optional[str] = None # Для группировки действий в рамках одной сессии

class UserActivityCreate(UserActivityBase):
    pass

class UserActivityInDB(UserActivityBase):
    id: int # Или UUID, если записей будет очень много

    class Config:
        orm_mode = True

class UserActivity(UserActivityInDB):
    pass 