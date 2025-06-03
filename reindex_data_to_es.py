import asyncio
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal
from app.services.search_service import SearchService

async def main():
    print("Starting Elasticsearch reindexing...")
    async with AsyncSessionLocal() as db:
        search_service = SearchService(db)
        await search_service.create_elasticsearch_mapping() # Убедимся, что маппинг создан
        await search_service.reindex_all_entities()
    print("Elasticsearch reindexing completed.")

if __name__ == "__main__":
    asyncio.run(main()) 