"""
DAG для мониторинга системы и управления данными
Включает в себя:
1. Мониторинг состояния сервисов
2. Генерацию отчетов
3. Очистку старых данных
4. Резервное копирование
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
import boto3
import pandas as pd
import json
import logging
import requests
from clickhouse_driver import Client

# Конфигурация DAG
default_args = {
    'owner': 'jonquils-monitoring',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'max_active_runs': 1
}

dag = DAG(
    'system_monitoring_and_maintenance',
    default_args=default_args,
    description='Мониторинг системы и обслуживание данных',
    schedule_interval=timedelta(hours=6),  # Запуск каждые 6 часов
    catchup=False,
    tags=['monitoring', 'maintenance', 'system']
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

def check_services_health(**context):
    """Проверка состояния всех сервисов"""
    logger = logging.getLogger(__name__)
    
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    # Проверка PostgreSQL
    try:
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        pg_hook.run("SELECT 1")
        health_status['services']['postgresql'] = {'status': 'healthy', 'response_time': 'fast'}
        logger.info("PostgreSQL: healthy")
    except Exception as e:
        health_status['services']['postgresql'] = {'status': 'unhealthy', 'error': str(e)}
        logger.error(f"PostgreSQL: unhealthy - {e}")
    
    # Проверка ClickHouse
    try:
        ch_client = Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DB
        )
        ch_client.execute("SELECT 1")
        health_status['services']['clickhouse'] = {'status': 'healthy', 'response_time': 'fast'}
        logger.info("ClickHouse: healthy")
    except Exception as e:
        health_status['services']['clickhouse'] = {'status': 'unhealthy', 'error': str(e)}
        logger.error(f"ClickHouse: unhealthy - {e}")
    
    # Проверка Elasticsearch
    try:
        response = requests.get('http://elasticsearch:9200/_cluster/health', timeout=10)
        if response.status_code == 200:
            es_health = response.json()
            health_status['services']['elasticsearch'] = {
                'status': 'healthy',
                'cluster_status': es_health.get('status', 'unknown'),
                'nodes': es_health.get('number_of_nodes', 0)
            }
            logger.info("Elasticsearch: healthy")
        else:
            health_status['services']['elasticsearch'] = {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        health_status['services']['elasticsearch'] = {'status': 'unhealthy', 'error': str(e)}
        logger.error(f"Elasticsearch: unhealthy - {e}")
    
    # Проверка MinIO
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY
        )
        buckets = s3_client.list_buckets()
        health_status['services']['minio'] = {
            'status': 'healthy',
            'buckets_count': len(buckets.get('Buckets', []))
        }
        logger.info("MinIO: healthy")
    except Exception as e:
        health_status['services']['minio'] = {'status': 'unhealthy', 'error': str(e)}
        logger.error(f"MinIO: unhealthy - {e}")
    
    # Проверка Redis
    try:
        response = requests.get('http://redis:6379/ping', timeout=5)
        health_status['services']['redis'] = {'status': 'healthy'}
        logger.info("Redis: healthy")
    except Exception as e:
        health_status['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}
        logger.error(f"Redis: unhealthy - {e}")
    
    # Сохраняем статус для следующих задач
    context['task_instance'].xcom_push(key='health_status', value=health_status)
    
    # Подсчитываем общий статус
    unhealthy_services = [name for name, status in health_status['services'].items() 
                         if status['status'] == 'unhealthy']
    
    if unhealthy_services:
        logger.warning(f"Unhealthy services detected: {unhealthy_services}")
        # Здесь можно добавить отправку уведомлений
    
    return health_status

def generate_system_metrics(**context):
    """Генерация системных метрик"""
    logger = logging.getLogger(__name__)
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'database_metrics': {},
        'storage_metrics': {},
        'usage_metrics': {}
    }
    
    try:
        # Метрики PostgreSQL
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        
        # Размер базы данных
        db_size_result = pg_hook.get_pandas_df("""
            SELECT 
                pg_size_pretty(pg_database_size('music_service_db')) as database_size,
                pg_database_size('music_service_db') as database_size_bytes
        """)
        
        # Количество пользователей
        users_count = pg_hook.get_pandas_df("SELECT COUNT(*) as count FROM users")
        
        # Количество треков в staging
        tracks_count = pg_hook.get_pandas_df("SELECT COUNT(*) as count FROM staging.track_uploads")
        
        metrics['database_metrics'] = {
            'database_size': db_size_result.iloc[0]['database_size'],
            'database_size_bytes': int(db_size_result.iloc[0]['database_size_bytes']),
            'total_users': int(users_count.iloc[0]['count']),
            'total_tracks_staged': int(tracks_count.iloc[0]['count'])
        }
        
        # Метрики ClickHouse
        ch_client = Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DB
        )
        
        # Количество записей в аналитических таблицах
        track_analytics_count = ch_client.execute("SELECT COUNT(*) FROM track_analytics")[0][0]
        user_analytics_count = ch_client.execute("SELECT COUNT(*) FROM user_analytics")[0][0]
        
        metrics['database_metrics']['clickhouse'] = {
            'track_analytics_records': track_analytics_count,
            'user_analytics_records': user_analytics_count
        }
        
        # Метрики S3/MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY
        )
        
        storage_stats = {}
        buckets = ['tracks', 'covers', 'playlists', 'temp']
        
        for bucket_name in buckets:
            try:
                response = s3_client.list_objects_v2(Bucket=bucket_name)
                objects = response.get('Contents', [])
                
                total_size = sum(obj['Size'] for obj in objects)
                object_count = len(objects)
                
                storage_stats[bucket_name] = {
                    'objects_count': object_count,
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }
                
            except Exception as e:
                storage_stats[bucket_name] = {'error': str(e)}
        
        metrics['storage_metrics'] = storage_stats
        
        # Метрики использования за последние 24 часа
        usage_metrics = ch_client.execute("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT track_id) as unique_tracks
            FROM track_analytics 
            WHERE timestamp >= now() - INTERVAL 1 DAY
        """)[0]
        
        metrics['usage_metrics'] = {
            'last_24h_events': usage_metrics[0],
            'last_24h_unique_users': usage_metrics[1],
            'last_24h_unique_tracks': usage_metrics[2]
        }
        
        logger.info("System metrics generated successfully")
        
        # Сохраняем метрики в PostgreSQL для истории
        metrics_json = json.dumps(metrics)
        pg_hook.run("""
            INSERT INTO etl.etl_jobs (job_name, status, records_processed, error_message)
            VALUES ('system_metrics', 'completed', 1, %s)
        """, parameters=[metrics_json])
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating system metrics: {e}")
        return {'error': str(e)}

def cleanup_old_logs(**context):
    """Очистка старых логов и временных данных"""
    logger = logging.getLogger(__name__)
    
    cleanup_summary = {
        'timestamp': datetime.now().isoformat(),
        'cleaned_items': {}
    }
    
    try:
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        
        # Очистка старых ETL логов (старше 30 дней)
        etl_cleanup = pg_hook.run("""
            DELETE FROM etl.etl_jobs 
            WHERE created_at < NOW() - INTERVAL '30 days'
            AND job_name != 'system_metrics'
        """)
        
        cleanup_summary['cleaned_items']['etl_logs'] = f"Cleaned old ETL logs"
        
        # Очистка обработанных staging файлов (старше 7 дней)
        staging_cleanup = pg_hook.run("""
            DELETE FROM staging.track_uploads 
            WHERE processing_status = 'processed' 
            AND upload_timestamp < NOW() - INTERVAL '7 days'
        """)
        
        cleanup_summary['cleaned_items']['staging_data'] = f"Cleaned old staging data"
        
        # Очистка старых записей в ClickHouse (старше 1 года)
        ch_client = Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DB
        )
        
        old_records_count = ch_client.execute("""
            SELECT COUNT(*) FROM track_analytics 
            WHERE timestamp < now() - INTERVAL 1 YEAR
        """)[0][0]
        
        if old_records_count > 0:
            ch_client.execute("""
                DELETE FROM track_analytics 
                WHERE timestamp < now() - INTERVAL 1 YEAR
            """)
            cleanup_summary['cleaned_items']['old_analytics'] = f"Removed {old_records_count} old analytics records"
        
        # Очистка временных файлов в S3
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY
        )
        
        # Получаем файлы старше 24 часов из temp bucket
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        try:
            response = s3_client.list_objects_v2(Bucket='temp')
            objects_to_delete = []
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                    objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket='temp',
                    Delete={'Objects': objects_to_delete}
                )
                cleanup_summary['cleaned_items']['temp_files'] = f"Removed {len(objects_to_delete)} temp files"
            
        except Exception as e:
            cleanup_summary['cleaned_items']['temp_files'] = f"Error cleaning temp files: {e}"
        
        logger.info("Cleanup completed successfully")
        return cleanup_summary
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {'error': str(e)}

def generate_daily_report(**context):
    """Генерация ежедневного отчета"""
    logger = logging.getLogger(__name__)
    
    try:
        # Получаем данные от предыдущих задач
        health_status = context['task_instance'].xcom_pull(key='health_status', task_ids='check_services_health')
        
        # Генерируем отчет
        report_date = datetime.now().date()
        
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        
        # Статистика за день
        daily_stats = pg_hook.get_pandas_df("""
            SELECT 
                COUNT(*) as new_tracks,
                COUNT(DISTINCT upload_user_id) as active_users
            FROM staging.track_uploads 
            WHERE DATE(upload_timestamp) = CURRENT_DATE
        """)
        
        report = {
            'date': report_date.isoformat(),
            'services_health': health_status,
            'daily_statistics': {
                'new_tracks': int(daily_stats.iloc[0]['new_tracks']) if not daily_stats.empty else 0,
                'active_users': int(daily_stats.iloc[0]['active_users']) if not daily_stats.empty else 0
            },
            'generated_at': datetime.now().isoformat()
        }
        
        # Сохраняем отчет
        report_json = json.dumps(report, indent=2)
        
        # Здесь можно добавить отправку отчета по email или в Slack
        logger.info(f"Daily report generated: {report}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {'error': str(e)}

# Определение задач
health_check_task = PythonOperator(
    task_id='check_services_health',
    python_callable=check_services_health,
    dag=dag
)

metrics_task = PythonOperator(
    task_id='generate_system_metrics',
    python_callable=generate_system_metrics,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_logs',
    python_callable=cleanup_old_logs,
    dag=dag
)

report_task = PythonOperator(
    task_id='generate_daily_report',
    python_callable=generate_daily_report,
    dag=dag
)

# Определение зависимостей
health_check_task >> [metrics_task, cleanup_task] >> report_task
