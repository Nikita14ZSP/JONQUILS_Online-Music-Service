#!/usr/bin/env python3
"""
Тест подключения к MinIO S3
"""

import boto3
from botocore.exceptions import ClientError
import sys

def test_s3_connection():
    """Тестируем подключение к MinIO S3"""
    
    # Настройки подключения
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:9002',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin123',
        region_name='us-east-1'
    )
    
    try:
        # Проверяем список buckets
        print("🔍 Проверяем подключение к MinIO...")
        response = s3_client.list_buckets()
        
        print("✅ Подключение успешно!")
        print(f"📦 Найдено buckets: {len(response['Buckets'])}")
        
        for bucket in response['Buckets']:
            print(f"   - {bucket['Name']} (создан: {bucket['CreationDate']})")
            
            # Проверяем содержимое каждого bucket
            try:
                objects = s3_client.list_objects_v2(Bucket=bucket['Name'])
                object_count = objects.get('KeyCount', 0)
                print(f"     📁 Файлов в bucket: {object_count}")
            except Exception as e:
                print(f"     ❌ Ошибка доступа к bucket: {e}")
        
        # Тестируем загрузку файла
        print("\n🧪 Тестируем загрузку файла...")
        test_content = "Test file content for JONQUILS music service"
        
        try:
            s3_client.put_object(
                Bucket='tracks',
                Key='test/test_file.txt',
                Body=test_content.encode('utf-8'),
                Metadata={
                    'test': 'true',
                    'uploader': 'system_test'
                }
            )
            print("✅ Тестовый файл загружен успешно!")
            
            # Проверяем что файл можно прочитать
            response = s3_client.get_object(Bucket='tracks', Key='test/test_file.txt')
            content = response['Body'].read().decode('utf-8')
            
            if content == test_content:
                print("✅ Тестовый файл прочитан корректно!")
            else:
                print("❌ Содержимое файла не совпадает!")
                
            # Удаляем тестовый файл
            s3_client.delete_object(Bucket='tracks', Key='test/test_file.txt')
            print("🗑️ Тестовый файл удален")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании файлов: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Ошибка подключения к MinIO: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🎵 JONQUILS Music Service - Тест MinIO S3")
    print("=" * 50)
    
    success = test_s3_connection()
    
    if success:
        print("\n🎉 Все тесты MinIO прошли успешно!")
        sys.exit(0)
    else:
        print("\n💥 Тесты MinIO завершились с ошибкой!")
        sys.exit(1)
