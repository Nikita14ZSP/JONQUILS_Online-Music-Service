from fastapi import APIRouter

router = APIRouter()

# Заглушка для эндпоинтов альбомов
@router.get("/")
async def get_albums():
    return [{"title": "Album Example 1"}, {"title": "Album Example 2"}] 