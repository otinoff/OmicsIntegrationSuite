#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Комплексный модуль обработки транскриптомных данных
Объединяет bulk RNA-seq и scRNA-seq QC анализ с интеграцией всех компонентов
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime

# Импорт компонентов QC системы
from .bulk_rnaseq_qc import BulkRNASeqQC
from .scrna_seq_qc import ScRNASeqQC
from .expression_normalizer import ExpressionNormalizer
from .doublet_detector import DoubletDetector
from .qc_reporter import TranscriptomicsQCReporter
from .qc_reporter_enhanced import EnhancedTranscriptomicsQCReporter
from .qc_reporter_10x import TenXGenomicsStyleReporter, create_10x_style_report

# Импорты для работы с данными
try:
    import scanpy as sc
    import anndata as ad
    SCANPY_AVAILABLE = True
except ImportError:
    SCANPY_AVAILABLE = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptomicsProcessor:
    """
    Комплексный процессор транскриптомных данных
    Интегрирует все QC модули и предоставляет единый интерфейс
    """
    
    def __init__(self, output_dir: Union[str, Path] = "output"):
        """
        Инициализация процессора
        
        Args:
            output_dir: Директория для выходных файлов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Инициализация компонентов
        self.bulk_qc = BulkRNASeqQC()
        self.scrna_qc = ScRNASeqQC()
        self.normalizer = ExpressionNormalizer()
        self.doublet_detector = DoubletDetector()
        self.reporter = TranscriptomicsQCReporter(self.output_dir / "reports")
        
        # Хранение результатов
        self.bulk_results = {}
        self.scrna_results = {}
        self.doublet_results = {}
        self.normalization_results = {}
        
        logger.info(f"TranscriptomicsProcessor инициализирован с output_dir: {self.output_dir}")
    
    def process_bulk_rnaseq(self, 
                           data_path: Union[str, Path],
                           min_genes: int = 10000,
                           min_reads: int = 1000000,
                           max_mito_percent: float = 20.0) -> Dict[str, Any]:
        """
        Полная обработка bulk RNA-seq данных
        
        Args:
            data_path: Путь к данным (CSV/TSV файл или директория)
            min_genes: Минимальное количество детектируемых генов
            min_reads: Минимальное количество ридов в библиотеке
            max_mito_percent: Максимальный процент митохондриальных генов
            
        Returns:
            Dict: Результаты QC анализа
        """
        logger.info(f"Начало обработки bulk RNA-seq данных: {data_path}")
        
        try:
            # Загрузка данных
            if isinstance(data_path, str):
                data_path = Path(data_path)
            
            if data_path.is_file():
                # Обработка одного файла
                results = self._process_single_bulk_file(
                    data_path, min_genes, min_reads, max_mito_percent
                )
            else:
                # Обработка директории с файлами
                results = self._process_bulk_directory(
                    data_path, min_genes, min_reads, max_mito_percent
                )
            
            self.bulk_results.update(results)
            
            # Настройка reporter для bulk данных
            self.reporter.set_bulk_rnaseq_metrics(results)
            
            logger.info(f"Обработка bulk RNA-seq завершена. Обработано образцов: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при обработке bulk RNA-seq: {e}")
            raise
    
    def process_scrna_seq(self,
                         data_path: Union[str, Path],
                         min_genes_per_cell: int = 200,
                         min_cells_per_gene: int = 3,
                         max_genes_per_cell: int = 5000,
                         max_mito_percent: float = 20.0,
                         detect_doublets: bool = True) -> Dict[str, Any]:
        """
        Полная обработка scRNA-seq данных
        
        Args:
            data_path: Путь к данным (H5AD, MTX, LOOM или CSV файл)
            min_genes_per_cell: Минимальное количество генов на клетку
            min_cells_per_gene: Минимальное количество клеток на ген
            max_genes_per_cell: Максимальное количество генов на клетку
            max_mito_percent: Максимальный процент митохондриальных генов
            detect_doublets: Выполнять ли детекцию дублетов
            
        Returns:
            Dict: Результаты QC анализа
        """
        logger.info(f"Начало обработки scRNA-seq данных: {data_path}")
        
        if not SCANPY_AVAILABLE:
            raise ImportError("scanpy и anndata необходимы для обработки scRNA-seq данных")
        
        try:
            # Загрузка данных
            adata = self._load_scrna_data(data_path)
            
            # Настройка параметров QC
            self.scrna_qc.min_genes = min_genes_per_cell
            self.scrna_qc.max_genes = max_genes_per_cell
            self.scrna_qc.max_mito_percent = max_mito_percent
            self.scrna_qc.min_cells = min_cells_per_gene
            
            # Загрузка данных в QC объект
            self.scrna_qc.adata = adata
            
            # QC анализ
            qc_results = self.scrna_qc.run_qc_analysis()
            
            # Детекция дублетов
            if detect_doublets:
                doublet_results = self._run_doublet_detection(adata)
                self.doublet_results.update(doublet_results)
                self.reporter.set_doublet_results(doublet_results)
            
            # Сохранение результатов
            self.scrna_results['main'] = qc_results
            
            # Настройка reporter для scRNA-seq данных
            self.reporter.set_scrna_seq_metrics(qc_results, adata)
            
            # Сохранение обработанных данных
            output_file = self.output_dir / "processed_scrna_data.h5ad"
            adata.write(output_file)
            logger.info(f"Обработанные данные сохранены: {output_file}")
            
            logger.info("Обработка scRNA-seq завершена")
            return {
                'qc_results': qc_results,
                'doublet_results': self.doublet_results if detect_doublets else {},
                'processed_data_path': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке scRNA-seq: {e}")
            raise
    
    def compare_normalization_methods(self,
                                    data: Union[pd.DataFrame, np.ndarray],
                                    methods: List[str] = None) -> pd.DataFrame:
        """
        Сравнение различных методов нормализации
        
        Args:
            data: Исходные данные экспрессии
            methods: Список методов для сравнения
            
        Returns:
            DataFrame: Сравнительная таблица методов нормализации
        """
        if methods is None:
            methods = ['cpm', 'tpm', 'deseq2_size_factors', 'tmm', 'quantile']
        
        logger.info(f"Сравнение методов нормализации: {methods}")
        
        try:
            comparison_results = []
            
            for method in methods:
                logger.info(f"Применение метода нормализации: {method}")
                
                if method == 'cpm':
                    normalized_data = self.normalizer.normalize_cpm(data)
                elif method == 'tpm':
                    # Для TPM нужны длины генов, используем CPM как аппроксимацию
                    normalized_data = self.normalizer.normalize_cpm(data)
                elif method == 'deseq2_size_factors':
                    normalized_data = self.normalizer.normalize_deseq2_size_factors(data)
                elif method == 'tmm':
                    normalized_data = self.normalizer.normalize_tmm(data)
                elif method == 'quantile':
                    normalized_data = self.normalizer.normalize_quantile(data)
                else:
                    logger.warning(f"Неизвестный метод нормализации: {method}")
                    continue
                
                # Вычисление статистик
                if isinstance(normalized_data, pd.DataFrame):
                    values = normalized_data.values.flatten()
                else:
                    values = normalized_data.flatten()
                
                # Фильтрация бесконечных и NaN значений
                values = values[np.isfinite(values)]
                
                stats = {
                    'Method': method,
                    'Mean': np.mean(values),
                    'Std': np.std(values),
                    'Min': np.min(values),
                    'Max': np.max(values),
                    'Median': np.median(values)
                }
                
                comparison_results.append(stats)
            
            comparison_df = pd.DataFrame(comparison_results)
            self.normalization_results['comparison'] = comparison_df
            
            # Настройка reporter для нормализации
            self.reporter.set_normalization_comparison(comparison_df)
            
            # Сохранение результатов
            output_file = self.output_dir / "normalization_comparison.csv"
            comparison_df.to_csv(output_file, index=False)
            logger.info(f"Сравнение методов нормализации сохранено: {output_file}")
            
            return comparison_df
            
        except Exception as e:
            logger.error(f"Ошибка при сравнении методов нормализации: {e}")
            raise
    
    def generate_comprehensive_report(self, 
                                    data_type: str = 'both',
                                    include_interactive: bool = True) -> Dict[str, str]:
        """
        Генерация комплексного отчета
        
        Args:
            data_type: Тип данных для включения ('bulk', 'scrna', 'both')
            include_interactive: Включать ли интерактивные элементы
            
        Returns:
            Dict: Пути к созданным файлам отчетов
        """
        logger.info(f"Генерация комплексного отчета. Тип данных: {data_type}")
        
        try:
            report_files = self.reporter.generate_comprehensive_report(
                data_type=data_type,
                include_interactive=include_interactive
            )
            
            logger.info("Комплексный отчет успешно создан")
            return report_files
            
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            raise
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Получение сводки по всем выполненным анализам
        
        Returns:
            Dict: Сводная информация
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'bulk_rnaseq_samples': len(self.bulk_results),
            'scrna_seq_processed': bool(self.scrna_results),
            'doublet_detection_methods': len(self.doublet_results),
            'normalization_methods_compared': len(self.normalization_results),
            'output_directory': str(self.output_dir)
        }
        
        if self.bulk_results:
            passed_samples = sum(1 for r in self.bulk_results.values() if r.qc_passed)
            summary['bulk_samples_passed_qc'] = passed_samples
            summary['bulk_qc_pass_rate'] = passed_samples / len(self.bulk_results)
        
        if self.scrna_results:
            main_results = self.scrna_results.get('main')
            if main_results:
                summary['scrna_cells_count'] = main_results.n_cells
                summary['scrna_genes_count'] = main_results.n_genes
                summary['scrna_qc_passed'] = main_results.qc_passed
        
        return summary
    
    # Вспомогательные методы
    
    def _process_single_bulk_file(self, file_path: Path, min_genes: int,
                                 min_reads: int, max_mito_percent: float) -> Dict[str, Any]:
        """Обработка одного bulk RNA-seq файла"""
        logger.info(f"Обработка файла: {file_path}")
        
        # Определение формата и загрузка данных
        if file_path.suffix.lower() in ['.csv']:
            data = pd.read_csv(file_path, index_col=0)
        elif file_path.suffix.lower() in ['.tsv', '.txt']:
            data = pd.read_csv(file_path, sep='\t', index_col=0)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_path.suffix}")
        
        # QC анализ для каждого образца
        results = {}
        for sample_name in data.columns:
            sample_data = data[sample_name]
            qc_result = self.bulk_qc.run_qc_analysis(
                sample_data,
                sample_name=sample_name,
                min_genes=min_genes,
                min_reads=min_reads,
                max_mito_percent=max_mito_percent
            )
            results[sample_name] = qc_result
        
        return results
    
    def _process_bulk_directory(self, dir_path: Path, min_genes: int,
                               min_reads: int, max_mito_percent: float) -> Dict[str, Any]:
        """Обработка директории с bulk RNA-seq файлами"""
        results = {}
        
        # Поиск файлов данных
        data_files = []
        for ext in ['*.csv', '*.tsv', '*.txt']:
            data_files.extend(dir_path.glob(ext))
        
        for file_path in data_files:
            file_results = self._process_single_bulk_file(
                file_path, min_genes, min_reads, max_mito_percent
            )
            results.update(file_results)
        
        return results
    
    def _load_scrna_data(self, data_path: Union[str, Path]) -> ad.AnnData:
        """Загрузка scRNA-seq данных в различных форматах"""
        data_path = Path(data_path)
        
        if data_path.suffix.lower() == '.h5ad':
            adata = ad.read_h5ad(data_path)
        elif data_path.suffix.lower() == '.loom':
            adata = ad.read_loom(data_path)
        elif data_path.suffix.lower() == '.csv':
            df = pd.read_csv(data_path, index_col=0)
            adata = ad.AnnData(df.T)  # Транспонируем: гены - колонки, клетки - строки
        elif data_path.suffix.lower() in ['.tsv', '.txt']:
            df = pd.read_csv(data_path, sep='\t', index_col=0)
            adata = ad.AnnData(df.T)
        elif data_path.is_dir():
            # Попытка загрузить как 10x данные
            adata = sc.read_10x_mtx(data_path, var_names='gene_symbols', cache=True)
            adata.var_names_unique()
        else:
            raise ValueError(f"Неподдерживаемый формат данных: {data_path}")
        
        logger.info(f"Загружены scRNA-seq данные: {adata.n_obs} клеток, {adata.n_vars} генов")
        return adata
    
    def _run_doublet_detection(self, adata: ad.AnnData) -> Dict[str, Any]:
        """Запуск детекции дублетов несколькими методами"""
        results = {}
        
        # Scrublet
        try:
            scrublet_result = self.doublet_detector.detect_doublets_scrublet(adata)
            results['scrublet'] = scrublet_result
            logger.info("Scrublet детекция дублетов выполнена")
        except Exception as e:
            logger.warning(f"Ошибка в Scrublet детекции: {e}")
        
        # DoubletDetection (если доступен и датасет не слишком большой)
        # DoubletDetection может зависать на больших датасетах (>2000 клеток)
        if adata.n_obs <= 2000:
            try:
                logger.info("Запуск DoubletDetection (может занять несколько минут)...")
                dd_result = self.doublet_detector.detect_doublets_doubletdetection(adata)
                results['doubletdetection'] = dd_result
                logger.info("DoubletDetection выполнен")
            except Exception as e:
                logger.warning(f"Ошибка в DoubletDetection: {e}")
        else:
            logger.info(f"Пропуск DoubletDetection для большого датасета ({adata.n_obs} клеток > 2000). Используется только Scrublet.")
        
        # Статистическая детекция
        try:
            stats_result = self.doublet_detector.detect_doublets_statistical(adata)
            results['statistical'] = stats_result
            logger.info("Статистическая детекция дублетов выполнена")
        except Exception as e:
            logger.warning(f"Ошибка в статистической детекции: {e}")
        
        return results


# Функции для обратной совместимости
def process(input_path=None, output_path=None):
    """
    Основная функция обработки транскриптомных данных (обратная совместимость)
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Запуск модуля обработки транскриптомных данных")
    
    if input_path is None:
        input_path = "data/input/transcriptomics"
        
    if output_path is None:
        output_path = "data/output/transcriptomics"
    
    # Создание процессора
    processor = TranscriptomicsProcessor(output_path)
    
    # Автоматическое определение типа данных и обработка
    input_path = Path(input_path)
    
    if input_path.exists():
        if input_path.is_file():
            # Определяем тип данных по расширению
            if input_path.suffix.lower() in ['.h5ad', '.loom']:
                # scRNA-seq данные
                processor.process_scrna_seq(input_path)
            else:
                # Попытка обработать как bulk RNA-seq
                processor.process_bulk_rnaseq(input_path)
        else:
            # Директория - ищем подходящие файлы
            bulk_files = list(input_path.glob("*.csv")) + list(input_path.glob("*.tsv"))
            scrna_files = list(input_path.glob("*.h5ad")) + list(input_path.glob("*.loom"))
            
            if bulk_files:
                processor.process_bulk_rnaseq(input_path)
            
            if scrna_files:
                for scrna_file in scrna_files:
                    processor.process_scrna_seq(scrna_file)
        
        # Генерация отчета
        processor.generate_comprehensive_report()
        
        # Вывод сводки
        summary = processor.get_processing_summary()
        logger.info(f"Обработка завершена. Сводка: {summary}")
    else:
        logger.error(f"Входная директория {input_path} не существует")


if __name__ == "__main__":
    process()
