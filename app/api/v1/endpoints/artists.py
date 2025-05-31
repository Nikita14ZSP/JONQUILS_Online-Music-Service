from fastapi import APIRouter

router = APIRouter()

# Заглушка для эндпоинтов исполнителей
@router.get("/")
async def get_artists():
    return [{"name": "Artist Example 1"}, {"name": "Artist Example 2"}] 