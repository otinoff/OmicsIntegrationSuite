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

import os
import pandas as pd
import numpy as np
from modules.transcriptomics.qc_reporter_modern import ModernTranscriptomicsQCReporter

def create_realistic_bulk_data():
    """Создание реалистичных данных для bulk RNA-seq"""
    np.random.seed(42)
    
    samples = [f"Bulk_Sample_{i+1}" for i in range(6)]
    
    data = {
        'sample': samples,
        'total_reads': np.random.normal(25e6, 5e6, 6).astype(int),
        'alignment_rate': np.random.normal(85, 8, 6),
        'rrna_rate': np.random.exponential(3, 6),
        'duplication_rate': np.random.normal(18, 6, 6),
        'gc_content': np.random.normal(48, 5, 6)
    }
    
    # Обеспечиваем реалистичные диапазоны
    data['alignment_rate'] = np.clip(data['alignment_rate'], 60, 95)
    data['rrna_rate'] = np.clip(data['rrna_rate'], 0.5, 15)
    data['duplication_rate'] = np.clip(data['duplication_rate'], 5, 40)
    data['gc_content'] = np.clip(data['gc_content'], 35, 65)
    
    return pd.DataFrame(data)

def create_realistic_scrna_data():
    """Создание реалистичных данных для scRNA-seq"""
    np.random.seed(123)
    
    samples = [f"scRNA_Sample_{i+1}" for i in range(4)]
    
    data = {
        'sample': samples,
        'estimated_cells': np.random.normal(8000, 2000, 4).astype(int),
        'mean_reads_per_cell': np.random.normal(22000, 5000, 4).astype(int),
        'median_genes_per_cell': np.random.normal(2800, 500, 4).astype(int),
        'valid_barcodes': np.random.normal(73, 8, 4),
        'q30_bases_rna': np.random.normal(85, 5, 4),
        'reads_mapped_transcriptome': np.random.normal(75, 10, 4)
    }
    
    # Обеспечиваем реалистичные диапазоны
    data['estimated_cells'] = np.clip(data['estimated_cells'], 1000, 15000)
    data['mean_reads_per_cell'] = np.clip(data['mean_reads_per_cell'], 8000, 40000)
    data['median_genes_per_cell'] = np.clip(data['median_genes_per_cell'], 1500, 4000)
    data['valid_barcodes'] = np.clip(data['valid_barcodes'], 50, 90)
    data['q30_bases_rna'] = np.clip(data['q30_bases_rna'], 70, 95)
    data['reads_mapped_transcriptome'] = np.clip(data['reads_mapped_transcriptome'], 50, 90)
    
    return pd.DataFrame(data)

def main():
    print("=== Создание современного отчета QC ===")
    print()
    
    # Создание директории для отчетов
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    print(f"[OK] Создана директория для отчетов: {os.path.abspath(reports_dir)}")
    
    # Инициализация репортера
    reporter = ModernTranscriptomicsQCReporter()
    print("[OK] Инициализирован ModernTranscriptomicsQCReporter")
    print()
    
    print("--- Подготовка данных ---")
    
    # Создание тестовых данных
    bulk_data = create_realistic_bulk_data()
    scrna_data = create_realistic_scrna_data()
    
    print(f"[OK] Загружены метрики для {len(bulk_data)} bulk RNA-seq образцов")
    print(f"[OK] Загружены метрики для {len(scrna_data)} scRNA-seq образцов")
    print()
    
    print("--- Генерация современного отчета ---")
    
    # Генерация отчета
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(reports_dir, f"modern_qc_report_{timestamp}.html")
    
    result = reporter.generate_modern_report(
        bulk_data=bulk_data,
        scrna_data=scrna_data,
        output_path=output_path
    )
    
    print(f"[OK] Современный отчет сохранен: {result['html_path']}")
    print(f"[OK] Размер отчета: {result['file_size']:,} байт")
    print()
    
    print("=== Современный отчет создан! ===")
    print(f"📂 Папка с отчетами: {os.path.abspath(reports_dir)}")
    print(f"📄 HTML отчет: {os.path.basename(result['html_path'])}")
    print()
    print("🎯 Особенности современного дизайна:")
    print("  ✅ Темно-синий header с градиентом")
    print("  ✅ Боковое меню навигации (слева)")
    print("  ✅ Карточки метрик с цветовой индикацией")
    print("  ✅ Интерактивные графики Plotly")
    print("  ✅ Адаптивный дизайн")
    print("  ✅ Стиль MultiQC/10x Genomics")
    print()
    print("📖 Откройте HTML файл в браузере для просмотра!")
    print()
    print("=" * 60)
    print("🎉 СОВРЕМЕННЫЙ ОТЧЕТ СОЗДАН УСПЕШНО!")
    print("Отчет соответствует дизайну показанному на изображении")
    print("с темно-синим header и боковой навигацией.")
    print("=" * 60)

if __name__ == "__main__":
    main()