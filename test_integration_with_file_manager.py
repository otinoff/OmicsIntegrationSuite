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
Интеграционный тест системы с файловым менеджером
Тестирует полный цикл: загрузка данных -> анализ -> генерация отчета -> сохранение
"""

import pandas as pd
import numpy as np
from pathlib import Path

from modules.transcriptomics.transcriptomics_processor import TranscriptomicsProcessor
from utils.file_manager import FileManager


def create_test_data():
    """Создание тестовых данных"""
    
    print("🧬 Создание тестовых данных...")
    
    # Создание bulk RNA-seq данных
    np.random.seed(42)
    n_genes = 1000
    n_samples = 6
    
    # Генерация имен генов
    gene_names = [f"Gene_{i:04d}" for i in range(1, n_genes + 1)]
    sample_names = [f"Sample_{i}" for i in range(1, n_samples + 1)]
    
    # Генерация данных с логнормальным распределением
    expression_data = np.random.lognormal(mean=3, sigma=1.5, size=(n_genes, n_samples))
    
    # Добавление некоторых высокоэкспрессируемых генов
    high_expr_indices = np.random.choice(n_genes, size=50, replace=False)
    expression_data[high_expr_indices] *= 10
    
    # Создание DataFrame
    bulk_df = pd.DataFrame(expression_data, index=gene_names, columns=sample_names)
    
    print(f"[OK] Bulk RNA-seq данные: {bulk_df.shape[0]} генов × {bulk_df.shape[1]} образцов")
    
    # Создание scRNA-seq данных (клетки как столбцы)
    n_cells = 200
    n_genes_sc = 500
    
    gene_names_sc = [f"Gene_{i:04d}" for i in range(1, n_genes_sc + 1)]
    cell_names = [f"Cell_{i:04d}" for i in range(1, n_cells + 1)]
    
    # Генерация sparse данных (много нулей)
    scrna_data = np.random.poisson(lam=2, size=(n_genes_sc, n_cells)).astype(float)
    
    # Добавление дропаутов (нули)
    dropout_mask = np.random.binomial(1, 0.7, size=(n_genes_sc, n_cells))
    scrna_data = scrna_data * dropout_mask
    
    scrna_df = pd.DataFrame(scrna_data, index=gene_names_sc, columns=cell_names)
    
    print(f"[OK] scRNA-seq данные: {scrna_df.shape[0]} генов × {scrna_df.shape[1]} клеток")
    
    return bulk_df, scrna_df


def test_full_integration():
    """Полный интеграционный тест с сохранением файлов и отчетов"""
    
    print("================================================================================")
    print("ИНТЕГРАЦИОННЫЙ ТЕСТ С ФАЙЛОВЫМ МЕНЕДЖЕРОМ")
    print("================================================================================")
    
    # Инициализация системы
    print("\n📁 Инициализация файлового менеджера и процессора...")
    file_manager = FileManager("test_storage")
    processor = TranscriptomicsProcessor("test_output")
    
    print(f"[OK] Файловый менеджер инициализирован: {file_manager.base_dir}")
    print(f"[OK] Процессор транскриптомики инициализирован: {processor.output_dir}")
    
    # Создание тестовых данных
    bulk_df, scrna_df = create_test_data()
    
    # === ТЕСТ 1: Bulk RNA-seq ===
    print("\n" + "="*60)
    print("ТЕСТ 1: BULK RNA-SEQ АНАЛИЗ С СОХРАНЕНИЕМ")
    print("="*60)
    
    # Сохранение bulk файла
    print("\n📤 Сохранение bulk RNA-seq файла...")
    bulk_csv_content = bulk_df.to_csv().encode('utf-8')
    bulk_file_id = file_manager.save_uploaded_file(
        file_content=bulk_csv_content,
        original_filename="test_bulk_rnaseq_data.csv",
        data_type="bulk_rnaseq",
        description="Тестовые данные bulk RNA-seq для демонстрации"
    )
    print(f"[OK] Bulk файл сохранен с ID: {bulk_file_id}")
    
    # Обработка bulk данных
    print("\n🔬 Обработка bulk RNA-seq данных...")
    bulk_file_path = file_manager.get_file_path(bulk_file_id)
    
    bulk_results = processor.process_bulk_rnaseq(
        data_path=bulk_file_path,
        min_genes=500,
        min_reads=1000000,
        max_mito_percent=20.0
    )
    
    print(f"[OK] Bulk анализ завершен. Образцов обработано: {len(bulk_results)}")
    
    passed_qc = sum(1 for m in bulk_results.values() if m.qc_passed)
    print(f"     - Прошли QC: {passed_qc}/{len(bulk_results)}")
    
    for sample_name, metrics in list(bulk_results.items())[:3]:  # Показать первые 3
        print(f"     - {sample_name}: {metrics.detected_genes:,} генов, "
              f"{metrics.library_size:,} ридов, "
              f"QC: {'✅' if metrics.qc_passed else '❌'}")
    
    # Генерация отчета для bulk
    print("\n📄 Генерация отчета для bulk RNA-seq...")
    bulk_report_files = processor.generate_comprehensive_report(
        data_type="bulk",
        include_interactive=True
    )
    
    print("[OK] Отчет создан:")
    for file_type, file_path in bulk_report_files.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size if Path(file_path).is_file() else "dir"
            print(f"     - {file_type}: {file_path} ({size} bytes)")
    
    # Сохранение отчета в архив
    print("\n💾 Сохранение отчета в архив...")
    bulk_report_id = file_manager.save_report(
        report_files=bulk_report_files,
        analysis_type="bulk",
        source_file_id=bulk_file_id,
        description="Отчет QC анализа bulk RNA-seq данных"
    )
    print(f"[OK] Bulk отчет сохранен с ID: {bulk_report_id}")
    
    # === ТЕСТ 2: scRNA-seq ===
    print("\n" + "="*60)
    print("ТЕСТ 2: SCRNA-SEQ АНАЛИЗ С СОХРАНЕНИЕМ")
    print("="*60)
    
    # Сохранение scRNA-seq файла
    print("\n📤 Сохранение scRNA-seq файла...")
    scrna_csv_content = scrna_df.to_csv().encode('utf-8')
    scrna_file_id = file_manager.save_uploaded_file(
        file_content=scrna_csv_content,
        original_filename="test_scrna_seq_data.csv",
        data_type="scrna_seq",
        description="Тестовые данные scRNA-seq (200 клеток)"
    )
    print(f"[OK] scRNA-seq файл сохранен с ID: {scrna_file_id}")
    
    # Обработка scRNA-seq данных
    print("\n🔬 Обработка scRNA-seq данных...")
    scrna_file_path = file_manager.get_file_path(scrna_file_id)
    
    scrna_results = processor.process_scrna_seq(
        data_path=scrna_file_path,
        min_genes_per_cell=50,
        min_cells_per_gene=3,
        max_genes_per_cell=2000,
        max_mito_percent=20.0,
        detect_doublets=True
    )
    
    print(f"[OK] scRNA-seq анализ завершен")
    
    qc_results = scrna_results['qc_results']
    print(f"     - Клеток: {qc_results.n_cells:,}")
    print(f"     - Генов: {qc_results.n_genes:,}")
    print(f"     - Среднее UMI/клетку: {qc_results.mean_counts_per_cell:,.0f}")
    print(f"     - Среднее генов/клетку: {qc_results.mean_genes_per_cell:,.0f}")
    print(f"     - QC статус: {'✅ PASSED' if qc_results.qc_passed else '❌ FAILED'}")
    
    if 'doublet_results' in scrna_results and scrna_results['doublet_results']:
        for method, result in scrna_results['doublet_results'].items():
            print(f"     - Дублеты ({method}): {result.n_doublets} ({result.percent_doublets:.1f}%)")
    
    # Генерация отчета для scRNA-seq
    print("\n📄 Генерация отчета для scRNA-seq...")
    scrna_report_files = processor.generate_comprehensive_report(
        data_type="scrna",
        include_interactive=True
    )
    
    print("[OK] Отчет создан:")
    for file_type, file_path in scrna_report_files.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size if Path(file_path).is_file() else "dir"
            print(f"     - {file_type}: {file_path} ({size} bytes)")
    
    # Сохранение отчета в архив
    print("\n💾 Сохранение отчета в архив...")
    scrna_report_id = file_manager.save_report(
        report_files=scrna_report_files,
        analysis_type="scrna",
        source_file_id=scrna_file_id,
        description="Отчет QC анализа scRNA-seq данных"
    )
    print(f"[OK] scRNA-seq отчет сохранен с ID: {scrna_report_id}")
    
    # === ПРОВЕРКА АРХИВА ===
    print("\n" + "="*60)
    print("ПРОВЕРКА АРХИВА ФАЙЛОВ И ОТЧЕТОВ")
    print("="*60)
    
    # Список загруженных файлов
    print("\n📁 Загруженные файлы:")
    uploaded_files = file_manager.get_uploaded_files()
    for i, file_info in enumerate(uploaded_files, 1):
        print(f"     {i}. {file_info['original_filename']}")
        print(f"        ID: {file_info['file_id']}")
        print(f"        Тип: {file_info['data_type']}")
        print(f"        Размер: {file_info['file_size']:,} байт")
        print(f"        Описание: {file_info['description']}")
        print(f"        Загружен: {file_info['upload_timestamp'][:19].replace('T', ' ')}")
        print(f"        Существует: {'✅' if file_info['exists'] else '❌'}")
        print()
    
    # Список отчетов
    print("📄 Готовые отчеты:")
    reports = file_manager.get_reports()
    for i, report_info in enumerate(reports, 1):
        print(f"     {i}. {report_info['report_id']}")
        print(f"        Тип анализа: {report_info['analysis_type']}")
        print(f"        Исходный файл: {report_info['source_filename']}")
        print(f"        Описание: {report_info['description']}")
        print(f"        Создан: {report_info['creation_timestamp'][:19].replace('T', ' ')}")
        print(f"        Существует: {'✅' if report_info['exists'] else '❌'}")
        
        # Показать файлы отчета
        report_files = file_manager.get_report_files(report_info['report_id'])
        if report_files:
            print(f"        Файлы:")
            for file_type, file_path in report_files.items():
                exists = "✅" if Path(file_path).exists() else "❌"
                print(f"          - {file_type}: {exists}")
        print()
    
    # Статистика хранилища
    print("📊 Статистика хранилища:")
    stats = file_manager.get_storage_info()
    print(f"     - Файлов: {stats['uploaded_files_count']}")
    print(f"     - Отчетов: {stats['reports_count']}")
    print(f"     - Общий размер: {stats['total_size_mb']:.2f} МБ")
    print(f"     - Базовая директория: {stats['base_dir']}")
    
    print("\n" + "="*80)
    print("✅ ИНТЕГРАЦИОННЫЙ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("✅ Все файлы и отчеты сохранены и доступны для просмотра")
    print("="*80)
    
    return {
        'file_manager': file_manager,
        'processor': processor,
        'bulk_file_id': bulk_file_id,
        'scrna_file_id': scrna_file_id,
        'bulk_report_id': bulk_report_id,
        'scrna_report_id': scrna_report_id,
        'uploaded_files': uploaded_files,
        'reports': reports,
        'stats': stats
    }


if __name__ == "__main__":
    try:
        results = test_full_integration()
        print(f"\n🎉 Тест завершен! Проверьте директорию: {results['file_manager'].base_dir}")
        print("   Все файлы и отчеты сохранены и готовы к использованию в веб-интерфейсе.")
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()