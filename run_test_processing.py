#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run test processing with OmicsIntegrationSuite
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

def main():
    """Main function to run test processing"""
    print("Запуск тестовой обработки данных с OmicsIntegrationSuite")
    print("=" * 60)
    
    # Define paths
    project_dir = Path(__file__).parent
    input_dir = project_dir / "data" / "input" / "genomics"
    output_dir = project_dir / "data" / "output" / "genomics"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Входная директория: {input_dir}")
    print(f"Выходная директория: {output_dir}")
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"Ошибка: Входная директория {input_dir} не существует")
        return 1
    
    # Check if there are input files
    input_files = list(input_dir.iterdir())
    if not input_files:
        print(f"Ошибка: Во входной директории {input_dir} нет файлов")
        return 1
    
    print(f"Найдено файлов для обработки: {len(input_files)}")
    for file in input_files:
        print(f"  - {file.name}")
    
    # Run the genomics processor
    try:
        print("\nЗапуск модуля обработки геномных данных...")
        
        # Import the genomics processor
        sys.path.append(str(project_dir / "modules"))
        from modules.genomics.genomics_processor import process
        
        # Run processing
        process(
            input_path=str(input_dir),
            output_path=str(output_dir)
        )
        
        print("\nОбработка данных завершена успешно!")
        print(f"Результаты сохранены в: {output_dir}")
        return 0
        
    except ImportError as e:
        print(f"Ошибка импорта модуля обработки: {e}")
        print("Убедитесь, что все зависимости установлены")
        return 1
    except Exception as e:
        print(f"Ошибка при выполнении обработки: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())