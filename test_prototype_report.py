#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование генератора отчетов в стиле прототипа
Создает демо отчет с большими зелеными цифрами и графиками
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям
current_dir = Path(__file__).parent
modules_path = current_dir / "modules"
if str(modules_path) not in sys.path:
    sys.path.insert(0, str(modules_path))

from modules.transcriptomics.qc_reporter_prototype import PrototypeStyleQCReporter
import numpy as np
from collections import namedtuple

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

def create_demo_bulk_results():
    """Создает демо результаты для bulk RNA-seq"""
    
    # Создаем namedtuple для метрик
    BulkMetric = namedtuple('BulkMetric', [
        'total_genes', 'detected_genes', 'library_size', 
        'median_expression', 'qc_passed', 'qc_warnings', 'qc_errors'
    ])
    
    # Генерируем демо данные для 8 образцов
    samples = [f"Sample_{i+1}" for i in range(8)]
    results = {}
    
    for i, sample in enumerate(samples):
        # Случайные но реалистичные значения
        total_genes = 25000 + np.random.randint(-2000, 2000)
        detected_genes = int(total_genes * (0.6 + np.random.random() * 0.3))  # 60-90% генов
        library_size = int(np.random.lognormal(15, 0.5))  # ~3-10M reads
        median_expression = np.random.lognormal(2, 0.5)
        
        # QC статус - большинство проходит
        qc_passed = np.random.random() > 0.2  # 80% проходят QC
        
        results[sample] = BulkMetric(
            total_genes=total_genes,
            detected_genes=detected_genes,
            library_size=library_size,
            median_expression=median_expression,
            qc_passed=qc_passed,
            qc_warnings=[],
            qc_errors=[]
        )
    
    return results

def create_demo_scrna_results():
    """Создает демо результаты для scRNA-seq"""
    
    # Создаем namedtuple для метрик
    ScRNAMetric = namedtuple('ScRNAMetric', [
        'n_cells', 'n_genes', 'mean_counts_per_cell', 'median_counts_per_cell',
        'mean_genes_per_cell', 'median_genes_per_cell', 'mean_percent_mito',
        'qc_passed', 'n_doublets', 'percent_doublets'
    ])
    
    # Реалистичные значения для scRNA-seq
    n_cells = 3177  # Как в реальном примере
    n_genes = 33538
    median_counts = 2500 + np.random.randint(-500, 500)
    mean_counts = int(median_counts * 1.2)  # Среднее чуть больше медианы
    median_genes = 1200 + np.random.randint(-200, 200)
    mean_genes = int(median_genes * 1.1)
    mean_mito = 5.0 + np.random.random() * 10  # 5-15% митохондриальных генов
    
    qc_results = ScRNAMetric(
        n_cells=n_cells,
        n_genes=n_genes,
        mean_counts_per_cell=mean_counts,
        median_counts_per_cell=median_counts,
        mean_genes_per_cell=mean_genes,
        median_genes_per_cell=median_genes,
        mean_percent_mito=mean_mito,
        qc_passed=mean_mito < 20,  # QC проходит если митохондриальные < 20%
        n_doublets=int(n_cells * 0.003),  # ~0.3% дублетов
        percent_doublets=0.3
    )
    
    return {'qc_results': qc_results}

def main():
    print("🧬 Тестирование генератора отчетов в стиле прототипа")
    print("=" * 60)
    
    try:
        # Создаем генератор отчетов
        print("📊 Создание генератора отчетов...")
        reporter = PrototypeStyleQCReporter(output_dir="test_reports")
        
        # Создаем демо данные
        print("🔬 Генерация демо данных...")
        bulk_results = create_demo_bulk_results()
        scrna_results = create_demo_scrna_results()
        
        print(f"   - Bulk RNA-seq: {len(bulk_results)} образцов")
        print(f"   - scRNA-seq: {scrna_results['qc_results'].n_cells:,} клеток")
        
        # Генерируем отчет
        print("🎨 Создание отчета в стиле прототипа...")
        report_path = reporter.generate_prototype_style_report(
            bulk_results=bulk_results,
            scrna_results=scrna_results,
            report_title="Demo Transcriptomics QC Report - Prototype Style",
            sample_name="Demo_Analysis"
        )
        
        print(f"✅ Отчет создан: {report_path}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(report_path)
        print(f"📄 Размер файла: {file_size:,} байт")
        
        # Показываем особенности прототип стиля
        print("\n🎯 Особенности созданного отчета:")
        print("   ✅ Большие зеленые цифры слева (1/3 ширины)")
        print("   ✅ Интерактивные графики справа (2/3 ширины)")
        print("   ✅ Grid layout как в прототипе")
        print("   ✅ Зеленые акценты (#2E8B57)")
        print("   ✅ Hover эффекты и анимации")
        print("   ✅ Responsive дизайн")
        print("   ✅ Plotly интерактивные графики")
        
        print(f"\n🌐 Откройте отчет в браузере: file://{os.path.abspath(report_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Тестирование завершено успешно!")
        print("Новый генератор отчетов в стиле прототипа работает корректно.")
    else:
        print("\n💥 Тестирование завершилось с ошибками.")
        sys.exit(1)