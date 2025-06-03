from typing import List, Union, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.track import TrackWithDetails
from app.schemas.artist import Artist
from app.schemas.album import Album
from app.services.search_service import SearchService
from app.db.database import get_db

router = APIRouter()

async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(db)

@router.get(
    "/multi/",
    response_model=Dict[str, List[Union[TrackWithDetails, Artist, Album]]],
    summary="Универсальный поиск по трекам, артистам и альбомам"
)
async def multi_entity_search_endpoint(
    query: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(default=10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Выполняет универсальный поиск по трекам, артистам и альбомам с использованием Elasticsearch.
    """
    if not search_service.es:
        raise HTTPException(status_code=503, detail="Elasticsearch service is not available")

    results = await search_service.multi_entity_search(query=query, limit=limit)
    return results 