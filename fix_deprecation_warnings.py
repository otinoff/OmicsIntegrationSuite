# -*- coding: utf-8 -*-
import sys

# Исправление кодировки для Windows терминала
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
Скрипт для исправления deprecation warnings в проекте
1. Исправляет pandas freq='H' на freq='h'
2. Исправляет Streamlit use_container_width=True на 
"""

import os
import re
from pathlib import Path

def fix_deprecation_warnings():
    """Исправляет все deprecation warnings в проекте"""
    
    # Получаем текущую директорию
    current_dir = Path(__file__).parent
    
    # Список файлов для исправления
    files_to_fix = []
    
    # Находим все Python файлы
    for file_path in current_dir.rglob("*.py"):
        if file_path.name != "fix_deprecation_warnings.py":  # Исключаем сам скрипт
            files_to_fix.append(file_path)
    
    print(f"Найдено {len(files_to_fix)} Python файлов для проверки")
    
    fixed_files = 0
    total_fixes = 0
    
    for file_path in files_to_fix:
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_fixes = 0
            
            # 1. Исправляем pandas freq='H' на freq='h'
            if "freq='H'" in content:
                content = content.replace("freq='H'", "freq='h'")
                file_fixes += content.count("freq='h'") - original_content.count("freq='h'")
                print(f"[PANDAS] Исправлено freq='H' в {file_path.relative_to(current_dir)}")
            
            # 2. Исправляем Streamlit use_container_width=True - просто удаляем параметр
            if "use_container_width=True" in content:
                # Удаляем use_container_width=True с запятыми
                content = re.sub(r',\s*use_container_width=True', '', content)
                content = re.sub(r'use_container_width=True,\s*', '', content)
                content = re.sub(r'use_container_width=True', '', content)
                
                if "use_container_width=True" not in content:
                    print(f"[STREAMLIT] Исправлено use_container_width в {file_path.relative_to(current_dir)}")
                    file_fixes += 1
            
            # Сохраняем файл если были изменения
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_files += 1
                total_fixes += file_fixes
                print(f"[OK] Обновлен файл: {file_path.relative_to(current_dir)} ({file_fixes} исправлений)")
        
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке {file_path}: {e}")
    
    print(f"\n[SUMMARY] Обработано файлов: {fixed_files}/{len(files_to_fix)}")
    print(f"[SUMMARY] Всего исправлений: {total_fixes}")
    print("\n[OK] Исправление deprecation warnings завершено!")

if __name__ == "__main__":
    fix_deprecation_warnings()