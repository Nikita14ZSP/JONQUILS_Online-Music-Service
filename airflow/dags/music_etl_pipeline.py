"""
ETL DAG для обработки музыкальных данных
Включает в себя:
1. Загрузку новых треков из S3
2. Обработку метаданных
3. Индексацию в Elasticsearch
4. Создание аналитических агрегатов в ClickHouse
5. Обновление PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
import boto3
import pandas as pd
import json
import logging
import requests
from clickhouse_driver import Client

# Конфигурация DAG
default_args = {
    'owner': 'jonquils-etl',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1
}

dag = DAG(
    'music_etl_pipeline',
    default_args=default_args,
    description='ETL пайплайн для обработки музыкальных данных',
    schedule_interval=timedelta(hours=1),  # Запуск каждый час
    catchup=False,
    tags=['etl', 'music', 'analytics']
)

# Конфигурация подключений
POSTGRES_CONN_ID = 'postgres_default'
CLICKHOUSE_HOST = 'clickhouse'
CLICKHOUSE_PORT = 9000
CLICKHOUSE_USER = 'admin'
CLICKHOUSE_PASSWORD = 'admin123'
CLICKHOUSE_DB = 'jonquils_analytics'

S3_ENDPOINT = 'http://minio:9000'
S3_ACCESS_KEY = 'minioadmin'
S3_SECRET_KEY = 'minioadmin123'

def setup_connections():
    """Настройка подключений для ETL"""
    logger = logging.getLogger(__name__)
    
    # S3 клиент
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    
    # ClickHouse клиент
    ch_client = Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB
    )
    
    return s3_client, ch_client

def extract_new_tracks(**context):
    """Извлечение новых треков из S3"""
    logger = logging.getLogger(__name__)
    s3_client, _ = setup_connections()
    
    try:
        # Получаем список новых файлов в S3
        response = s3_client.list_objects_v2(Bucket='tracks')
        
        # PostgreSQL hook для проверки уже обработанных файлов
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        
        processed_files = pg_hook.get_pandas_df(
            "SELECT file_path FROM etl.s3_file_registry WHERE status = 'processed'"
        )
        processed_paths = set(processed_files['file_path'].tolist() if not processed_files.empty else [])
        
        new_tracks = []
        
        for obj in response.get('Contents', []):
            s3_key = obj['Key']
            
            if s3_key not in processed_paths and s3_key.endswith(('.mp3', '.wav', '.flac', '.m4a')):
                # Получаем метаданные файла
                metadata_response = s3_client.head_object(Bucket='tracks', Key=s3_key)
                
                track_info = {
                    'file_path': s3_key,
                    'file_size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'metadata': metadata_response.get('Metadata', {}),
                    'bucket': 'tracks'
                }
                
                new_tracks.append(track_info)
        
        logger.info(f"Found {len(new_tracks)} new tracks to process")
        
        # Сохраняем список для следующих задач
        context['task_instance'].xcom_push(key='new_tracks', value=new_tracks)
        
        return len(new_tracks)
        
    except Exception as e:
        logger.error(f"Error extracting tracks: {e}")
        raise

def process_track_metadata(**context):
    """Обработка метаданных треков"""
    logger = logging.getLogger(__name__)
    
    new_tracks = context['task_instance'].xcom_pull(key='new_tracks', task_ids='extract_new_tracks')
    
    if not new_tracks:
        logger.info("No new tracks to process")
        return 0
    
    s3_client, _ = setup_connections()
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    processed_count = 0
    
    for track in new_tracks:
        try:
            # Здесь можно добавить извлечение метаданных с помощью библиотек типа mutagen
            # Для демонстрации используем базовую обработку
            
            metadata = track['metadata']
            
            # Извлекаем информацию о пользователе из пути
            user_id = None
            if 'user-id' in metadata:
                user_id = int(metadata['user-id'])
            
            # Подготавливаем данные для staging таблицы
            staging_data = {
                'original_filename': metadata.get('original-filename', track['file_path'].split('/')[-1]),
                's3_path': track['file_path'],
                'file_size': track['file_size'],
                'metadata': json.dumps(metadata),
                'upload_user_id': user_id,
                'processing_status': 'processed'
            }
            
            # Вставляем в staging таблицу
            insert_sql = """
            INSERT INTO staging.track_uploads 
            (original_filename, s3_path, file_size, metadata, upload_user_id, processing_status)
            VALUES (%(original_filename)s, %(s3_path)s, %(file_size)s, %(metadata)s, %(upload_user_id)s, %(processing_status)s)
            """
            
            pg_hook.run(insert_sql, parameters=staging_data)
            
            # Регистрируем файл как обработанный
            registry_sql = """
            INSERT INTO etl.s3_file_registry 
            (file_path, file_size, bucket_name, metadata, status)
            VALUES (%(file_path)s, %(file_size)s, %(bucket_name)s, %(metadata)s, 'processed')
            ON CONFLICT (file_path) DO UPDATE SET 
                last_accessed = CURRENT_TIMESTAMP,
                status = 'processed'
            """
            
            registry_data = {
                'file_path': track['file_path'],
                'file_size': track['file_size'],
                'bucket_name': track['bucket'],
                'metadata': json.dumps(metadata)
            }
            
            pg_hook.run(registry_sql, parameters=registry_data)
            
            processed_count += 1
            logger.info(f"Processed track: {track['file_path']}")
            
        except Exception as e:
            logger.error(f"Error processing track {track['file_path']}: {e}")
            # Продолжаем обработку остальных треков
    
    logger.info(f"Successfully processed {processed_count} tracks")
    return processed_count

def sync_to_clickhouse(**context):
    """Синхронизация данных в ClickHouse для аналитики"""
    logger = logging.getLogger(__name__)
    
    _, ch_client = setup_connections()
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    try:
        # Получаем новые треки из staging
        new_tracks_df = pg_hook.get_pandas_df("""
            SELECT 
                id, original_filename, s3_path, file_size, 
                upload_user_id, upload_timestamp, metadata
            FROM staging.track_uploads 
            WHERE processing_status = 'processed'
            AND upload_timestamp >= NOW() - INTERVAL '2 hours'
        """)
        
        if new_tracks_df.empty:
            logger.info("No new tracks to sync to ClickHouse")
            return 0
        
        # Подготавливаем данные для ClickHouse
        ch_data = []
        for _, row in new_tracks_df.iterrows():
            try:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                ch_record = [
                    datetime.now(),  # timestamp
                    row['upload_user_id'] or 0,  # user_id
                    f"track_{row['id']}",  # track_id (генерируем на основе staging ID)
                    'upload',  # event_type
                    metadata.get('duration', 0),  # duration
                    metadata.get('quality', 'standard'),  # quality
                    'web',  # platform
                    str(metadata)  # metadata
                ]
                ch_data.append(ch_record)
                
            except Exception as e:
                logger.error(f"Error preparing ClickHouse data for track {row['id']}: {e}")
        
        # Вставляем данные в ClickHouse
        if ch_data:
            ch_client.execute(
                """
                INSERT INTO track_analytics 
                (timestamp, user_id, track_id, event_type, duration, quality, platform, metadata)
                VALUES
                """,
                ch_data
            )
            
            logger.info(f"Synced {len(ch_data)} records to ClickHouse")
        
        return len(ch_data)
        
    except Exception as e:
        logger.error(f"Error syncing to ClickHouse: {e}")
        raise

def update_elasticsearch_index(**context):
    """Обновление индекса Elasticsearch"""
    logger = logging.getLogger(__name__)
    
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    try:
        # Получаем новые треки для индексации
        new_tracks_df = pg_hook.get_pandas_df("""
            SELECT 
                tu.id, tu.original_filename, tu.s3_path, tu.file_size, 
                tu.upload_user_id, tu.metadata, u.username, u.full_name
            FROM staging.track_uploads tu
            LEFT JOIN users u ON tu.upload_user_id = u.id
            WHERE tu.processing_status = 'processed'
            AND tu.upload_timestamp >= NOW() - INTERVAL '2 hours'
        """)
        
        if new_tracks_df.empty:
            logger.info("No new tracks to index in Elasticsearch")
            return 0
        
        indexed_count = 0
        
        # Индексируем каждый трек в Elasticsearch
        for _, track in new_tracks_df.iterrows():
            try:
                metadata = json.loads(track['metadata']) if track['metadata'] else {}
                
                doc = {
                    'track_id': f"track_{track['id']}",
                    'filename': track['original_filename'],
                    'title': metadata.get('title', track['original_filename']),
                    'artist': metadata.get('artist', track['username'] or 'Unknown'),
                    'album': metadata.get('album', ''),
                    'duration': metadata.get('duration', 0),
                    'file_size': track['file_size'],
                    'upload_user_id': track['upload_user_id'],
                    'upload_timestamp': datetime.now().isoformat(),
                    's3_path': track['s3_path'],
                    'searchable_text': f"{metadata.get('title', '')} {metadata.get('artist', '')} {metadata.get('album', '')}"
                }
                
                # Отправляем в Elasticsearch
                response = requests.post(
                    'http://elasticsearch:9200/tracks/_doc/',
                    json=doc,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201]:
                    indexed_count += 1
                    logger.info(f"Indexed track: {track['original_filename']}")
                else:
                    logger.error(f"Failed to index track {track['original_filename']}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error indexing track {track['id']}: {e}")
        
        logger.info(f"Successfully indexed {indexed_count} tracks in Elasticsearch")
        return indexed_count
        
    except Exception as e:
        logger.error(f"Error updating Elasticsearch index: {e}")
        raise

def generate_daily_aggregates(**context):
    """Генерация ежедневных агрегатов для data warehouse"""
    logger = logging.getLogger(__name__)
    
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    try:
        today = datetime.now().date()
        
        # Агрегаты по трекам
        track_stats_sql = """
        INSERT INTO data_warehouse.daily_track_stats 
        (date_key, total_tracks, total_plays, unique_listeners, total_duration_hours)
        SELECT 
            %s as date_key,
            COUNT(*) as total_tracks,
            0 as total_plays,  -- Будет обновлено из ClickHouse
            COUNT(DISTINCT upload_user_id) as unique_listeners,
            0 as total_duration_hours  -- Будет обновлено из метаданных
        FROM staging.track_uploads 
        WHERE DATE(upload_timestamp) = %s
        ON CONFLICT (date_key) DO UPDATE SET
            total_tracks = EXCLUDED.total_tracks,
            unique_listeners = EXCLUDED.unique_listeners,
            updated_at = CURRENT_TIMESTAMP
        """
        
        pg_hook.run(track_stats_sql, parameters=[today, today])
        
        logger.info(f"Generated daily aggregates for {today}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating daily aggregates: {e}")
        raise

def cleanup_old_data(**context):
    """Очистка старых данных"""
    logger = logging.getLogger(__name__)
    
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    try:
        # Очищаем старые логи ETL (старше 30 дней)
        cleanup_sql = """
        DELETE FROM etl.etl_jobs 
        WHERE created_at < NOW() - INTERVAL '30 days'
        """
        
        result = pg_hook.run(cleanup_sql)
        logger.info("Cleaned up old ETL logs")
        
        # Очищаем обработанные staging записи (старше 7 дней)
        staging_cleanup_sql = """
        DELETE FROM staging.track_uploads 
        WHERE processing_status = 'processed' 
        AND upload_timestamp < NOW() - INTERVAL '7 days'
        """
        
        pg_hook.run(staging_cleanup_sql)
        logger.info("Cleaned up old staging data")
        
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise

# Определение задач
extract_task = PythonOperator(
    task_id='extract_new_tracks',
    python_callable=extract_new_tracks,
    dag=dag
)

process_metadata_task = PythonOperator(
    task_id='process_track_metadata',
    python_callable=process_track_metadata,
    dag=dag
)

clickhouse_sync_task = PythonOperator(
    task_id='sync_to_clickhouse',
    python_callable=sync_to_clickhouse,
    dag=dag
)

elasticsearch_task = PythonOperator(
    task_id='update_elasticsearch_index',
    python_callable=update_elasticsearch_index,
    dag=dag
)

aggregates_task = PythonOperator(
    task_id='generate_daily_aggregates',
    python_callable=generate_daily_aggregates,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag
)

# Определение зависимостей
extract_task >> process_metadata_task >> [clickhouse_sync_task, elasticsearch_task] >> aggregates_task >> cleanup_task
