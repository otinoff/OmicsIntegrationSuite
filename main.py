#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный файл приложения для диагональной интеграции мультимодальных биологических данных
"""

import sys
import os
import argparse
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "modules"))

def main():
    """Основная функция приложения"""
    print("Локальное приложение для диагональной интеграции мультимодальных биологических данных")
    print("=" * 80)
    
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Платформа диагональной интеграции биологических данных')
    parser.add_argument('--module', '-m', 
                       choices=['genomics', 'transcriptomics', 'mirna', 'proteomics', 'metabolomics', 'integration', 'qc', 'reporting'],
                       help='Выбор модуля для запуска')
    parser.add_argument('--input', '-i', type=str, help='Путь к входным данным')
    parser.add_argument('--output', '-o', type=str, help='Путь к выходным данным')
    
    # Парсим аргументы
    args = parser.parse_args()
    
    # Если модуль не указан, показываем меню
    if not args.module:
        show_menu()
        return
    
    # Запуск выбранного модуля
    run_module(args.module, args.input, args.output)

def show_menu():
    """Отображение меню выбора модуля"""
    print("\nДоступные модули:")
    print("1. genomics      - Обработка геномных данных")
    print("2. transcriptomics - Обработка транскриптомных данных")
    print("3. mirna         - Обработка данных микроРНК")
    print("4. proteomics    - Обработка протеомных данных")
    print("5. metabolomics  - Обработка метаболомных данных")
    print("6. integration   - Диагональная интеграция данных")
    print("7. qc            - Контроль качества")
    print("8. reporting     - Генерация отчетов")
    print("0. Выход")
    
    choice = input("\nВыберите модуль (0-8): ").strip()
    
    module_map = {
        '1': 'genomics',
        '2': 'transcriptomics',
        '3': 'mirna',
        '4': 'proteomics',
        '5': 'metabolomics',
        '6': 'integration',
        '7': 'qc',
        '8': 'reporting',
        '0': None
    }
    
    if choice in module_map:
        if module_map[choice] is None:
            print("Выход из приложения.")
            return
        run_module(module_map[choice])
    else:
        print("Неверный выбор. Пожалуйста, выберите значение от 0 до 8.")
        show_menu()

def run_module(module_name, input_path=None, output_path=None):
    """Запуск выбранного модуля"""
    print(f"\nЗапуск модуля: {module_name}")
    
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
            print(f"Модуль {module_name} не найден.")
    except ImportError as e:
        print(f"Ошибка импорта модуля {module_name}: {e}")
        print("Убедитесь, что все зависимости установлены.")
    except Exception as e:
        print(f"Ошибка при выполнении модуля {module_name}: {e}")

if __name__ == "__main__":
    main()