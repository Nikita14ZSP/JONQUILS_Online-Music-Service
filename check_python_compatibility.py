#!/usr/bin/env python3
"""
Скрипт для проверки совместимости Python версий с зависимостями
"""
import sys
import subprocess
import pkg_resources

def check_python_version():
    """Проверка версии Python"""
    python_version = sys.version_info
    print(f"Python версия: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3:
        print("❌ Требуется Python 3.x")
        return False
    
    if python_version.minor < 8:
        print("❌ Требуется Python 3.8 или выше")
        return False
    
    if python_version.minor >= 12:
        print("⚠️  Python 3.12+ может иметь проблемы совместимости с некоторыми библиотеками")
    
    print("✅ Версия Python совместима")
    return True

def check_critical_packages():
    """Проверка критически важных пакетов"""
    critical_packages = [
        'fastapi',
        'sqlalchemy', 
        'pytest',
        'factory-boy'
    ]
    
    print("\nПроверка критических пакетов:")
    for package in critical_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"✅ {package}: {version}")
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package}: не установлен")
        except Exception as e:
            print(f"⚠️  {package}: ошибка проверки - {e}")

def install_compatible_versions():
    """Установка совместимых версий пакетов"""
    print("\nУстановка совместимых версий...")
    
    compatible_packages = [
        "factory-boy==3.3.0",  # Совместимая с Python 3.12
        "pytest==8.3.4",
        "fastapi==0.115.6",
        "sqlalchemy==2.0.36"
    ]
    
    for package in compatible_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✅ Установлен: {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {package}: {e}")

if __name__ == "__main__":
    print("🔍 Проверка совместимости Python окружения")
    print("=" * 50)
    
    if check_python_version():
        check_critical_packages()
        
        answer = input("\nУстановить совместимые версии пакетов? (y/n): ")
        if answer.lower() in ['y', 'yes', 'да']:
            install_compatible_versions()
    else:
        print("Обновите Python до совместимой версии")
