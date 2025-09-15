#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт запуска приложения диагональной интеграции мультимодальных биологических данных
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def main():
    """Основная функция запуска приложения"""
    print("Запуск приложения диагональной интеграции мультимодальных биологических данных")
    print("=" * 80)
    
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Запуск приложения диагональной интеграции биологических данных')
    parser.add_argument('--install', '-i', action='store_true', help='Установить зависимости')
    parser.add_argument('--module', '-m', 
                       choices=['genomics', 'transcriptomics', 'mirna', 'proteomics', 'metabolomics', 'integration', 'qc', 'reporting'],
                       help='Выбор модуля для запуска')
    parser.add_argument('--input', '-in', type=str, help='Путь к входным данным')
    parser.add_argument('--output', '-out', type=str, help='Путь к выходным данным')
    parser.add_argument('--gui', '-g', action='store_true', help='Запустить веб-интерфейс')
    
    # Парсим аргументы
    args = parser.parse_args()
    
    # Если указан флаг установки зависимостей
    if args.install:
        install_dependencies()
        return
    
    # Если указан флаг запуска веб-интерфейса
    if args.gui:
        run_web_interface()
        return
    
    # Если модуль не указан, запускаем основное приложение
    if not args.module:
        run_main_application(args.input, args.output)
    else:
        # Запуск выбранного модуля
        run_specific_module(args.module, args.input, args.output)

def install_dependencies():
    """Установка зависимостей приложения"""
    print("Установка зависимостей...")
    
    try:
        # Проверка наличия requirements.txt
        requirements_file = Path("requirements.txt")
        if not requirements_file.exists():
            print("Файл requirements.txt не найден")
            return
        
        # Установка зависимостей
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Зависимости успешно установлены")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки зависимостей: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка при установке зависимостей: {e}")

def run_main_application(input_path=None, output_path=None):
    """Запуск основного приложения"""
    print("Запуск основного приложения...")
    
    try:
        # Импортируем и запускаем основное приложение
        from main import main as app_main
        
        # Подготавливаем аргументы для основного приложения
        app_args = []
        if input_path:
            app_args.extend(['--input', input_path])
        if output_path:
            app_args.extend(['--output', output_path])
        
        # Запускаем основное приложение
        app_main()
        
    except ImportError as e:
        print(f"Ошибка импорта основного приложения: {e}")
        print("Убедитесь, что все файлы приложения находятся в правильных местах")
    except Exception as e:
        print(f"Ошибка запуска основного приложения: {e}")

def run_specific_module(module_name, input_path=None, output_path=None):
    """Запуск конкретного модуля"""
    print(f"Запуск модуля: {module_name}")
    
    try:
        if module_name == 'genomics':
            from modules.genomics import genomics_processor
            genomics_processor.process(input_path, output_path)
        elif module_name == 'transcriptomics':
            from modules.transcriptomics import transcriptomics_processor
            transcriptomics_processor.process(input_path, output_path)
        elif module_name == 'mirna':
            from modules.mirna import mirna_processor
            mirna_processor.process(input_path, output_path)
        elif module_name == 'proteomics':
            from modules.proteomics import proteomics_processor
            proteomics_processor.process(input_path, output_path)
        elif module_name == 'metabolomics':
            from modules.metabolomics import metabolomics_processor
            metabolomics_processor.process(input_path, output_path)
        elif module_name == 'integration':
            from modules.integration import integration_processor
            integration_processor.process(input_path, output_path)
        elif module_name == 'qc':
            from modules.quality_control import qc_processor
            qc_processor.process(input_path, output_path)
        elif module_name == 'reporting':
            from modules.reporting import reporting_processor
            reporting_processor.process(input_path, output_path)
        else:
            print(f"Неизвестный модуль: {module_name}")
            
    except ImportError as e:
        print(f"Ошибка импорта модуля {module_name}: {e}")
        print("Убедитесь, что все зависимости установлены")
    except Exception as e:
        print(f"Ошибка при выполнении модуля {module_name}: {e}")

def run_web_interface():
    """Запуск веб-интерфейса приложения"""
    print("Запуск веб-интерфейса...")
    
    try:
        # Проверка наличия Streamlit
        import streamlit
        print("Streamlit найден, запуск веб-интерфейса...")
        
        # Запуск веб-интерфейса через Streamlit
        # Для демонстрации просто выводим сообщение
        print("Веб-интерфейс будет доступен по адресу: http://localhost:8501")
        print("Для запуска веб-интерфейса используйте команду:")
        print("streamlit run web_interface.py")
        
    except ImportError:
        print("Streamlit не найден. Установите его с помощью команды:")
        print("pip install streamlit")
    except Exception as e:
        print(f"Ошибка запуска веб-интерфейса: {e}")

if __name__ == "__main__":
    main()