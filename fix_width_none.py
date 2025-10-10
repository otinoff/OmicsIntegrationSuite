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
Скрипт для исправления width=None на правильные параметры
"""

import os
import re
from pathlib import Path

def fix_width_none():
    """Исправляет все width=None в проекте"""
    
    # Получаем текущую директорию
    current_dir = Path(__file__).parent
    
    # Список файлов для исправления
    files_to_fix = []
    
    # Находим все Python файлы
    for file_path in current_dir.rglob("*.py"):
        if file_path.name != "fix_width_none.py":  # Исключаем сам скрипт
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
            
            # Исправляем width=None
            if "width=None" in content:
                # Удаляем width=None с запятыми
                content = re.sub(r',\s*width=None', '', content)
                content = re.sub(r'width=None,\s*', '', content)
                content = re.sub(r'width=None', '', content)
                
                file_fixes = original_content.count("width=None")
                print(f"[STREAMLIT] Исправлено width=None в {file_path.relative_to(current_dir)} ({file_fixes} исправлений)")
            
            # Сохраняем файл если были изменения
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_files += 1
                total_fixes += file_fixes
        
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке {file_path}: {e}")
    
    print(f"\n[SUMMARY] Обработано файлов: {fixed_files}/{len(files_to_fix)}")
    print(f"[SUMMARY] Всего исправлений: {total_fixes}")
    print("\n[OK] Исправление width=None завершено!")

if __name__ == "__main__":
    fix_width_none()