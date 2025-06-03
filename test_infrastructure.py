#!/usr/bin/env python3
"""
Тестирование полной инфраструктуры JONQUILS Music Service
Проверяет все компоненты: PostgreSQL, ClickHouse, Elasticsearch, MinIO, Redis
"""

import asyncio
import boto3
import json
import logging
import os
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import asyncpg
import httpx
import redis
from clickhouse_driver import Client
from elasticsearch import Elasticsearch

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfrastructureTest:
    def __init__(self):
        """Инициализация тестов инфраструктуры"""
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': {}
        }
        
        # Конфигурация
        self.config = {
            'postgres': {
                'host': 'localhost',
                'port': 5432,
                'user': 'erik',
                'password': '2004',
                'database': 'music_service_db'
            },
            'clickhouse': {
                'host': 'localhost',
                'port': 9000,
                'user': 'admin',
                'password': 'admin123',
                'database': 'jonquils_analytics'
            },
            'elasticsearch': {
                'host': 'localhost',
                'port': 9200
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': 'redispass123'
            },
            'minio': {
                'endpoint': 'http://localhost:9002',
                'access_key': 'minioadmin',
                'secret_key': 'minioadmin123'
            },
            'api': {
                'base_url': 'http://localhost:8000'
            }
        }

    def test_result(self, test_name: str, success: bool, details: str = ""):
        """Записывает результат теста"""
        self.results['tests_run'] += 1
        if success:
            self.results['tests_passed'] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.results['tests_failed'] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.results['details'][test_name] = {
            'passed': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

    async def test_postgresql(self):
        """Тестирование PostgreSQL"""
        logger.info("🔍 Testing PostgreSQL...")
        
        try:
            # Подключение к PostgreSQL
            conn = await asyncpg.connect(
                host=self.config['postgres']['host'],
                port=self.config['postgres']['port'],
                user=self.config['postgres']['user'],
                password=self.config['postgres']['password'],
                database=self.config['postgres']['database']
            )
            
            # Тест базового подключения
            result = await conn.fetchval("SELECT 1")
            self.test_result("PostgreSQL Connection", result == 1)
            
            # Тест схем ETL
            schemas = await conn.fetch("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name IN ('etl', 'staging', 'data_warehouse')
            """)
            schema_names = [row['schema_name'] for row in schemas]
            self.test_result("PostgreSQL ETL Schemas", 
                           all(s in schema_names for s in ['etl', 'staging', 'data_warehouse']))
            
            # Тест таблиц
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'etl' AND table_name = 'etl_jobs'
            """)
            self.test_result("PostgreSQL ETL Tables", len(tables) > 0)
            
            await conn.close()
            
        except Exception as e:
            self.test_result("PostgreSQL Connection", False, str(e))

    def test_clickhouse(self):
        """Тестирование ClickHouse"""
        logger.info("🔍 Testing ClickHouse...")
        
        try:
            # Подключение к ClickHouse
            client = Client(
                host=self.config['clickhouse']['host'],
                port=self.config['clickhouse']['port'],
                user=self.config['clickhouse']['user'],
                password=self.config['clickhouse']['password'],
                database=self.config['clickhouse']['database']
            )
            
            # Тест базового подключения
            result = client.execute("SELECT 1")[0][0]
            self.test_result("ClickHouse Connection", result == 1)
            
            # Тест таблиц аналитики
            tables = client.execute("SHOW TABLES")
            table_names = [table[0] for table in tables]
            required_tables = ['track_analytics', 'user_analytics', 'search_analytics']
            
            self.test_result("ClickHouse Analytics Tables", 
                           all(table in table_names for table in required_tables))
            
            # Тест вставки данных
            test_data = [(
                datetime.now(),
                1,
                'test_track_1',
                'play',
                180,
                'high',
                'web',
                '{"test": true}'
            )]
            
            client.execute("""
                INSERT INTO track_analytics 
                (timestamp, user_id, track_id, event_type, duration, quality, platform, metadata)
                VALUES
            """, test_data)
            
            # Проверяем вставку
            count = client.execute("""
                SELECT COUNT(*) FROM track_analytics 
                WHERE track_id = 'test_track_1'
            """)[0][0]
            
            self.test_result("ClickHouse Data Insert", count > 0)
            
            # Очищаем тестовые данные
            client.execute("DELETE FROM track_analytics WHERE track_id = 'test_track_1'")
            
        except Exception as e:
            self.test_result("ClickHouse Connection", False, str(e))

    def test_elasticsearch(self):
        """Тестирование Elasticsearch"""
        logger.info("🔍 Testing Elasticsearch...")
        
        try:
            # Подключение к Elasticsearch
            es = Elasticsearch([
                f"http://{self.config['elasticsearch']['host']}:{self.config['elasticsearch']['port']}"
            ])
            
            # Тест базового подключения
            health = es.cluster.health()
            self.test_result("Elasticsearch Connection", health['status'] in ['green', 'yellow'])
            
            # Тест создания индекса
            index_name = 'test_tracks'
            if es.indices.exists(index=index_name):
                es.indices.delete(index=index_name)
            
            es.indices.create(index=index_name, body={
                'mappings': {
                    'properties': {
                        'title': {'type': 'text'},
                        'artist': {'type': 'text'},
                        'duration': {'type': 'integer'}
                    }
                }
            })
            
            self.test_result("Elasticsearch Index Creation", True)
            
            # Тест индексации документа
            test_doc = {
                'title': 'Test Track',
                'artist': 'Test Artist',
                'duration': 180
            }
            
            response = es.index(index=index_name, document=test_doc)
            self.test_result("Elasticsearch Document Index", response['result'] == 'created')
            
            # Ждем индексации
            time.sleep(1)
            es.indices.refresh(index=index_name)
            
            # Тест поиска
            search_result = es.search(index=index_name, body={
                'query': {'match': {'title': 'Test Track'}}
            })
            
            self.test_result("Elasticsearch Search", 
                           search_result['hits']['total']['value'] > 0)
            
            # Удаляем тестовый индекс
            es.indices.delete(index=index_name)
            
        except Exception as e:
            self.test_result("Elasticsearch Connection", False, str(e))

    def test_redis(self):
        """Тестирование Redis"""
        logger.info("🔍 Testing Redis...")
        
        try:
            # Подключение к Redis
            r = redis.Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                password=self.config['redis']['password'],
                decode_responses=True
            )
            
            # Тест базового подключения
            pong = r.ping()
            self.test_result("Redis Connection", pong)
            
            # Тест записи/чтения
            test_key = 'test_key'
            test_value = 'test_value'
            
            r.set(test_key, test_value, ex=60)  # TTL 60 секунд
            retrieved_value = r.get(test_key)
            
            self.test_result("Redis Set/Get", retrieved_value == test_value)
            
            # Тест списков (для очередей)
            queue_name = 'test_queue'
            r.lpush(queue_name, 'task1', 'task2', 'task3')
            queue_length = r.llen(queue_name)
            
            self.test_result("Redis Queue Operations", queue_length == 3)
            
            # Очистка тестовых данных
            r.delete(test_key, queue_name)
            
        except Exception as e:
            self.test_result("Redis Connection", False, str(e))

    def test_minio(self):
        """Тестирование MinIO (S3)"""
        logger.info("🔍 Testing MinIO...")
        
        try:
            # Подключение к MinIO
            s3_client = boto3.client(
                's3',
                endpoint_url=self.config['minio']['endpoint'],
                aws_access_key_id=self.config['minio']['access_key'],
                aws_secret_access_key=self.config['minio']['secret_key']
            )
            
            # Тест списка buckets
            buckets = s3_client.list_buckets()
            bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
            required_buckets = ['tracks', 'covers', 'playlists', 'temp']
            
            self.test_result("MinIO Buckets", 
                           all(bucket in bucket_names for bucket in required_buckets))
            
            # Тест загрузки файла
            test_content = b"This is a test file for MinIO"
            test_key = f"test/test_file_{int(time.time())}.txt"
            
            s3_client.put_object(
                Bucket='temp',
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            
            self.test_result("MinIO Upload", True)
            
            # Тест скачивания файла
            response = s3_client.get_object(Bucket='temp', Key=test_key)
            downloaded_content = response['Body'].read()
            
            self.test_result("MinIO Download", downloaded_content == test_content)
            
            # Тест метаданных
            head_response = s3_client.head_object(Bucket='temp', Key=test_key)
            self.test_result("MinIO Metadata", 'ContentLength' in head_response)
            
            # Удаляем тестовый файл
            s3_client.delete_object(Bucket='temp', Key=test_key)
            
        except Exception as e:
            self.test_result("MinIO Connection", False, str(e))

    async def test_fastapi(self):
        """Тестирование FastAPI"""
        logger.info("🔍 Testing FastAPI...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Тест health endpoint
                response = await client.get(f"{self.config['api']['base_url']}/health")
                if response.status_code == 404:
                    # Если нет health endpoint, тестируем docs
                    response = await client.get(f"{self.config['api']['base_url']}/docs")
                
                self.test_result("FastAPI Health", response.status_code in [200, 307])
                
                # Тест OpenAPI docs
                docs_response = await client.get(f"{self.config['api']['base_url']}/docs")
                self.test_result("FastAPI OpenAPI Docs", docs_response.status_code in [200, 307])
                
        except Exception as e:
            self.test_result("FastAPI Connection", False, str(e))

    def test_docker_services(self):
        """Тестирование Docker контейнеров"""
        logger.info("🔍 Testing Docker Services...")
        
        try:
            import subprocess
            
            # Проверяем запущенные контейнеры
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                containers = result.stdout
                required_containers = [
                    'jonquils-postgres',
                    'jonquils-clickhouse', 
                    'jonquils-elasticsearch',
                    'jonquils-redis',
                    'jonquils-minio'
                ]
                
                running_containers = []
                for container in required_containers:
                    if container in containers and 'Up' in containers:
                        running_containers.append(container)
                
                self.test_result("Docker Containers", 
                               len(running_containers) == len(required_containers),
                               f"Running: {running_containers}")
            else:
                self.test_result("Docker Containers", False, "Docker not available")
                
        except Exception as e:
            self.test_result("Docker Containers", False, str(e))

    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Starting Infrastructure Tests...")
        start_time = time.time()
        
        # Запускаем все тесты
        await self.test_postgresql()
        self.test_clickhouse()
        self.test_elasticsearch()
        self.test_redis()
        self.test_minio()
        await self.test_fastapi()
        self.test_docker_services()
        
        end_time = time.time()
        
        # Выводим результаты
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests Run: {self.results['tests_run']}")
        logger.info(f"Tests Passed: {self.results['tests_passed']}")
        logger.info(f"Tests Failed: {self.results['tests_failed']}")
        logger.info(f"Success Rate: {(self.results['tests_passed']/self.results['tests_run']*100):.1f}%")
        logger.info(f"Execution Time: {end_time - start_time:.2f} seconds")
        
        if self.results['tests_failed'] > 0:
            logger.info("\n❌ FAILED TESTS:")
            for test_name, details in self.results['details'].items():
                if not details['passed']:
                    logger.info(f"  - {test_name}: {details['details']}")
        
        # Сохраняем результаты в файл
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: test_results.json")
        
        return self.results['tests_failed'] == 0

async def main():
    """Главная функция"""
    tester = InfrastructureTest()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🎉 All tests passed! Infrastructure is ready.")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
