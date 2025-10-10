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
Создание профессионального отчета для демонстрации
Генерирует enhanced отчет с тестовыми данными и сохраняет в папку reports/
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os

# Добавляем путь к модулям
current_dir = Path(__file__).parent
modules_path = current_dir / "modules"
if str(modules_path) not in sys.path:
    sys.path.insert(0, str(modules_path))

from modules.transcriptomics.qc_reporter_enhanced import EnhancedTranscriptomicsQCReporter
from modules.transcriptomics.bulk_rnaseq_qc import BulkRNASeqQC, BulkRNASeqQCMetrics
from modules.transcriptomics.scrna_seq_qc import ScRNASeqQC, ScRNASeqQCMetrics

def create_demo_bulk_metrics():
    """Создание демонстрационных bulk RNA-seq метрик"""
    mock_metrics = {}
    
    for i in range(8):
        sample_name = f"Sample_{i+1}"
        
        # Имитируем реалистичные метрики
        total_genes = np.random.randint(20000, 25000)
        detected_genes = np.random.randint(12000, 18000)
        library_size = np.random.randint(15000000, 45000000)
        median_expression = np.random.uniform(2.5, 8.5)
        
        # QC проходит если соблюдены базовые критерии
        qc_passed = (detected_genes > 10000 and 
                     library_size > 10000000 and 
                     median_expression > 1.0)
        
        # Для демонстрации делаем 2 образца неуспешными
        if i >= 6:
            detected_genes = np.random.randint(5000, 9000)
            qc_passed = False
        
        metrics = BulkRNASeqQCMetrics(
            sample_name=sample_name,
            total_genes=total_genes,
            detected_genes=detected_genes,
            library_size=library_size,
            median_expression=median_expression,
            qc_passed=qc_passed
        )
        
        mock_metrics[sample_name] = metrics
    
    return mock_metrics

def create_demo_scrna_metrics():
    """Создание демонстрационных scRNA-seq метрик"""
    
    # Имитируем высококачественные scRNA-seq данные
    n_cells = 8432  # Типичное для 10x
    n_genes = 2500
    mean_counts = 22150
    mean_genes = 2847
    mean_mito = 8.5
    n_doublets = 168
    percent_doublets = 2.0
    
    return ScRNASeqQCMetrics(
        n_cells=n_cells,
        n_genes=n_genes,
        mean_counts_per_cell=mean_counts,
        mean_genes_per_cell=mean_genes,
        mean_percent_mito=mean_mito,
        n_doublets=n_doublets,
        percent_doublets=percent_doublets,
        qc_passed=True  # Хорошие метрики
    )

def create_demo_anndata():
    """Создание демонстрационного AnnData объекта"""
    try:
        import anndata as ad
        import pandas as pd
        
        n_cells = 1000
        n_genes = 2000
        
        # Создаем матрицу экспрессии
        X = np.random.negative_binomial(5, 0.3, size=(n_cells, n_genes))
        
        # Метаданные клеток
        obs = pd.DataFrame({
            'n_counts': np.random.negative_binomial(100, 0.01, n_cells),
            'n_genes': np.random.negative_binomial(50, 0.02, n_cells),
            'percent_mito': np.random.beta(2, 20, n_cells) * 30  # 0-30%
        })
        
        # Метаданные генов
        var = pd.DataFrame(
            index=[f"Gene_{i}" for i in range(n_genes)]
        )
        
        adata = ad.AnnData(X=X, obs=obs, var=var)
        return adata
        
    except ImportError:
        print("[WARN] AnnData не доступен, создаем None")
        return None

def create_professional_demo_report():
    """Создание профессионального демонстрационного отчета"""
    
    print("=== Создание профессионального демонстрационного отчета ===")
    print("")
    
    # Создаем директорию для отчетов
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    print(f"[OK] Создана директория для отчетов: {reports_dir.absolute()}")
    
    # Инициализируем enhanced reporter
    reporter = EnhancedTranscriptomicsQCReporter(reports_dir)
    print("[OK] Инициализирован EnhancedTranscriptomicsQCReporter")
    
    # Создаем тестовые данные
    print("\n--- Подготовка тестовых данных ---")
    
    # Bulk RNA-seq данные
    bulk_metrics = create_demo_bulk_metrics()
    reporter.set_bulk_rnaseq_metrics(bulk_metrics)
    print(f"[OK] Загружены метрики для {len(bulk_metrics)} bulk RNA-seq образцов")
    
    # scRNA-seq данные  
    scrna_metrics = create_demo_scrna_metrics()
    adata = create_demo_anndata()
    reporter.set_scrna_seq_metrics(scrna_metrics, adata)
    print("[OK] Загружены scRNA-seq метрики")
    
    # Создаем профессиональные графики
    print("\n--- Создание enhanced графиков ---")
    
    bulk_plots = reporter.create_enhanced_bulk_plots()
    print(f"[OK] Создано {len(bulk_plots)} enhanced bulk графиков:")
    for plot_name in bulk_plots.keys():
        print(f"    - {plot_name}")
    
    if adata is not None:
        scrna_plots = reporter.create_enhanced_scrna_plots()
        print(f"[OK] Создано {len(scrna_plots)} enhanced scRNA-seq графиков:")
        for plot_name in scrna_plots.keys():
            print(f"    - {plot_name}")
    
    # Генерируем профессиональный отчет
    print("\n--- Генерация профессионального отчета ---")
    
    try:
        # Создаем HTML отчет
        html_file = reporter.generate_professional_html_report(
            data_type='both',
            include_plots=True
        )
        print(f"[OK] Создан профессиональный HTML отчет")
        print(f"     Файл: {html_file}")
        
        # Проверяем размер файла
        if os.path.exists(html_file):
            file_size = os.path.getsize(html_file)
            print(f"[OK] Размер HTML файла: {file_size:,} байт")
            
            if file_size > 50000:
                print("[OK] Файл содержит интерактивные элементы")
        
        # Создаем JSON summary
        json_file = reporter.generate_enhanced_json_summary()
        print(f"[OK] Создан улучшенный JSON summary")
        print(f"     Файл: {json_file}")
        
        # Проверяем JSON структуру
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                summary = __import__('json').load(f)
            
            # Проверяем ключевые разделы
            expected_sections = ['report_info', 'qc_thresholds', 'bulk_rnaseq', 'scrna_seq', 'quality_summary']
            present_sections = [section for section in expected_sections if section in summary]
            
            print(f"[OK] JSON содержит разделы: {', '.join(present_sections)}")
            
            # Проверяем соответствие стандартам
            if 'standards_compliance' in summary.get('report_info', {}):
                standards = summary['report_info']['standards_compliance']
                print(f"[OK] Соответствие стандартам: {', '.join(standards)}")
        
        print(f"\n=== Отчет успешно создан! ===")
        print(f"📂 Папка с отчетами: {reports_dir.absolute()}")
        print(f"📄 HTML отчет: {Path(html_file).name}")
        print(f"📊 JSON summary: {Path(json_file).name}")
        print("")
        print("🎯 Особенности профессионального отчета:")
        print("  ✅ MultiQC стиль навигации и структуры")
        print("  ✅ 10x Genomics метрики и визуализация") 
        print("  ✅ ENCODE стандарты качества")
        print("  ✅ Bootstrap CSS и профессиональный дизайн")
        print("  ✅ Интерактивные Plotly графики")
        print("  ✅ Цветовое кодирование QC статусов")
        print("  ✅ Пороговые значения и рекомендации")
        print("")
        print("📖 Откройте HTML файл в браузере для просмотра!")
        
        return {
            'html': html_file,
            'json': json_file,
            'reports_dir': str(reports_dir.absolute())
        }
        
    except Exception as e:
        print(f"[ERROR] Ошибка создания отчета: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = create_professional_demo_report()
        
        if result:
            print("\n" + "="*60)
            print("🎉 ДЕМОНСТРАЦИОННЫЙ ОТЧЕТ СОЗДАН УСПЕШНО!")
            print("Теперь вы можете:")
            print(f"1. Открыть папку: {result['reports_dir']}")
            print(f"2. Найти HTML файл и открыть в браузере")
            print(f"3. Посмотреть JSON summary для анализа метрик")
            print("="*60)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()