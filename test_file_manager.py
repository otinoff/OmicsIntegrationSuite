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
Тест файлового менеджера
"""

import tempfile
import shutil
from pathlib import Path
import json

from utils.file_manager import FileManager


def test_file_manager():
    """Тестирование основных функций файлового менеджера"""
    
    print("================================================================================")
    print("ТЕСТ ФАЙЛОВОГО МЕНЕДЖЕРА")
    print("================================================================================")
    
    # Создание временной директории для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"[INFO] Тестовая директория: {temp_dir}")
        
        # Инициализация файлового менеджера
        file_manager = FileManager(temp_dir)
        print("[OK] Файловый менеджер инициализирован")
        
        # Тест 1: Сохранение файла
        print("\n[TEST 1] Сохранение загруженного файла...")
        test_content = b"gene1,sample1,sample2\ngene2,100,200\ngene3,300,400"
        file_id = file_manager.save_uploaded_file(
            file_content=test_content,
            original_filename="test_data.csv",
            data_type="bulk_rnaseq",
            description="Тестовые данные bulk RNA-seq"
        )
        print(f"[OK] Файл сохранен с ID: {file_id}")
        
        # Тест 2: Получение списка файлов
        print("\n[TEST 2] Получение списка загруженных файлов...")
        uploaded_files = file_manager.get_uploaded_files()
        print(f"[OK] Найдено файлов: {len(uploaded_files)}")
        
        for file_info in uploaded_files:
            print(f"     - {file_info['original_filename']} (ID: {file_info['file_id']})")
            print(f"       Тип: {file_info['data_type']}, Размер: {file_info['file_size']} байт")
        
        # Тест 3: Получение пути к файлу
        print("\n[TEST 3] Получение пути к сохраненному файлу...")
        file_path = file_manager.get_file_path(file_id)
        if file_path and Path(file_path).exists():
            print(f"[OK] Файл найден: {file_path}")
            
            # Проверка содержимого
            with open(file_path, 'rb') as f:
                saved_content = f.read()
            
            if saved_content == test_content:
                print("[OK] Содержимое файла корректно")
            else:
                print("[ERROR] Содержимое файла не совпадает!")
        else:
            print("[ERROR] Файл не найден!")
        
        # Тест 4: Сохранение отчета
        print("\n[TEST 4] Сохранение отчета...")
        
        # Создание тестовых файлов отчета
        report_dir = Path(temp_dir) / "test_report"
        report_dir.mkdir()
        
        html_file = report_dir / "report.html"
        json_file = report_dir / "summary.json"
        
        html_file.write_text("<html><body><h1>Test Report</h1></body></html>", encoding='utf-8')
        json_file.write_text('{"status": "test"}', encoding='utf-8')
        
        report_files = {
            'html': str(html_file),
            'json': str(json_file)
        }
        
        report_id = file_manager.save_report(
            report_files=report_files,
            analysis_type="bulk",
            source_file_id=file_id,
            description="Тестовый отчет"
        )
        print(f"[OK] Отчет сохранен с ID: {report_id}")
        
        # Тест 5: Получение списка отчетов
        print("\n[TEST 5] Получение списка отчетов...")
        reports = file_manager.get_reports()
        print(f"[OK] Найдено отчетов: {len(reports)}")
        
        for report_info in reports:
            print(f"     - {report_info['report_id']}")
            print(f"       Тип: {report_info['analysis_type']}")
            print(f"       Исходный файл: {report_info['source_filename']}")
        
        # Тест 6: Статистика хранилища
        print("\n[TEST 6] Статистика хранилища...")
        stats = file_manager.get_storage_info()
        print(f"[OK] Файлов: {stats['uploaded_files_count']}")
        print(f"     Отчетов: {stats['reports_count']}")
        print(f"     Общий размер: {stats['total_size_mb']} МБ")
        print(f"     Базовая директория: {stats['base_dir']}")
        
        # Тест 7: Удаление файла
        print("\n[TEST 7] Удаление файла...")
        if file_manager.delete_uploaded_file(file_id):
            print("[OK] Файл удален успешно")
            
            # Проверка что файл удален
            remaining_files = file_manager.get_uploaded_files()
            if len(remaining_files) == 0:
                print("[OK] Файл удален из списка")
            else:
                print("[ERROR] Файл все еще в списке!")
        else:
            print("[ERROR] Ошибка удаления файла!")
        
        # Тест 8: Удаление отчета
        print("\n[TEST 8] Удаление отчета...")
        if file_manager.delete_report(report_id):
            print("[OK] Отчет удален успешно")
            
            # Проверка что отчет удален
            remaining_reports = file_manager.get_reports()
            if len(remaining_reports) == 0:
                print("[OK] Отчет удален из списка")
            else:
                print("[ERROR] Отчет все еще в списке!")
        else:
            print("[ERROR] Ошибка удаления отчета!")
        
        print("\n================================================================================")
        print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("================================================================================")


if __name__ == "__main__":
    test_file_manager()