"""
Модуль контроля качества для bulk RNA-seq данных
Поддерживает FASTQ файлы и матрицы экспрессии
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class BulkRNASeqQCMetrics:
    """Метрики качества для bulk RNA-seq"""
    sample_name: str
    total_reads: int = 0
    total_genes: int = 0
    detected_genes: int = 0  # Гены с ненулевой экспрессией
    median_expression: float = 0.0
    mean_expression: float = 0.0
    zero_count_genes: int = 0
    low_expression_genes: int = 0  # < 10 counts
    highly_expressed_genes: int = 0  # > 90th percentile
    library_size: int = 0  # Общая сумма всех counts
    
    # Специфичные метрики для нормализованных данных
    is_normalized: bool = False
    normalization_method: Optional[str] = None
    
    # QC статус
    qc_passed: bool = True
    qc_warnings: List[str] = None
    qc_errors: List[str] = None
    
    def __post_init__(self):
        if self.qc_warnings is None:
            self.qc_warnings = []
        if self.qc_errors is None:
            self.qc_errors = []


class BulkRNASeqQC:
    """
    Класс для контроля качества bulk RNA-seq данных
    Поддерживает как сырые FASTQ, так и матрицы экспрессии
    """
    
    def __init__(self, min_genes: int = 200, min_counts: int = 10000):
        """
        Инициализация QC модуля для bulk RNA-seq
        
        Args:
            min_genes: Минимальное количество детектируемых генов
            min_counts: Минимальная библиотечная глубина
        """
        self.min_genes = min_genes
        self.min_counts = min_counts
        self.expression_matrix = None
        self.sample_metrics = {}
        
    def load_expression_matrix(self, 
                              file_path: Union[str, Path],
                              sep: str = '\t',
                              index_col: int = 0) -> pd.DataFrame:
        """
        Загрузка матрицы экспрессии из файла
        
        Args:
            file_path: Путь к файлу с матрицей (CSV, TSV)
            sep: Разделитель в файле
            index_col: Колонка с именами генов
            
        Returns:
            pd.DataFrame: Матрица экспрессии (гены × образцы)
        """
        try:
            file_path = Path(file_path)
            
            if file_path.suffix == '.csv':
                self.expression_matrix = pd.read_csv(file_path, index_col=index_col)
            elif file_path.suffix in ['.tsv', '.txt']:
                self.expression_matrix = pd.read_csv(file_path, sep=sep, index_col=index_col)
            elif file_path.suffix == '.xlsx':
                self.expression_matrix = pd.read_excel(file_path, index_col=index_col)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_path.suffix}")
                
            logger.info(f"Загружена матрица: {self.expression_matrix.shape[0]} генов × {self.expression_matrix.shape[1]} образцов")
            return self.expression_matrix
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке матрицы: {e}")
            raise
            
    def calculate_qc_metrics(self, expression_matrix: Optional[pd.DataFrame] = None) -> Dict[str, BulkRNASeqQCMetrics]:
        """
        Вычисление QC метрик для каждого образца
        
        Args:
            expression_matrix: Матрица экспрессии (если не загружена ранее)
            
        Returns:
            Dict: Словарь с метриками для каждого образца
        """
        if expression_matrix is not None:
            self.expression_matrix = expression_matrix
            
        if self.expression_matrix is None:
            raise ValueError("Матрица экспрессии не загружена")
            
        for sample_name in self.expression_matrix.columns:
            sample_data = self.expression_matrix[sample_name]
            
            metrics = BulkRNASeqQCMetrics(sample_name=sample_name)
            
            # Базовые метрики
            metrics.total_genes = len(sample_data)
            metrics.detected_genes = (sample_data > 0).sum()
            metrics.zero_count_genes = (sample_data == 0).sum()
            metrics.low_expression_genes = (sample_data < 10).sum()
            
            # Библиотечная глубина
            metrics.library_size = int(sample_data.sum())
            metrics.total_reads = metrics.library_size
            
            # Статистика экспрессии
            non_zero_expr = sample_data[sample_data > 0]
            if len(non_zero_expr) > 0:
                metrics.median_expression = float(non_zero_expr.median())
                metrics.mean_expression = float(non_zero_expr.mean())
                
                # Высоко экспрессируемые гены (> 90 percentile)
                threshold_90 = non_zero_expr.quantile(0.9)
                metrics.highly_expressed_genes = (non_zero_expr > threshold_90).sum()
            
            # Проверка нормализации (если значения float и < 100)
            if sample_data.dtype == float and sample_data.max() < 100:
                metrics.is_normalized = True
                # Попытка определить метод нормализации
                if sample_data.max() <= 1:
                    metrics.normalization_method = "Fraction/Probability"
                elif sample_data.sum() == 1e6:
                    metrics.normalization_method = "TPM"
                else:
                    metrics.normalization_method = "Unknown"
                    
            # QC проверки
            self._check_sample_quality(metrics)
            
            self.sample_metrics[sample_name] = metrics
            
        return self.sample_metrics
        
    def _check_sample_quality(self, metrics: BulkRNASeqQCMetrics):
        """
        Проверка качества образца по пороговым значениям
        
        Args:
            metrics: Метрики образца
        """
        # Проверка минимального количества генов
        if metrics.detected_genes < self.min_genes:
            metrics.qc_errors.append(
                f"Низкое количество детектируемых генов: {metrics.detected_genes} < {self.min_genes}"
            )
            metrics.qc_passed = False
            
        # Проверка библиотечной глубины (только для ненормализованных)
        if not metrics.is_normalized and metrics.library_size < self.min_counts:
            metrics.qc_errors.append(
                f"Низкая глубина секвенирования: {metrics.library_size} < {self.min_counts}"
            )
            metrics.qc_passed = False
            
        # Предупреждения
        if metrics.zero_count_genes / metrics.total_genes > 0.8:
            metrics.qc_warnings.append(
                f"Более 80% генов имеют нулевую экспрессию ({metrics.zero_count_genes}/{metrics.total_genes})"
            )
            
        if metrics.highly_expressed_genes < 10:
            metrics.qc_warnings.append(
                "Менее 10 высоко экспрессируемых генов"
            )
            
    def normalize_counts(self, method: str = 'TPM') -> pd.DataFrame:
        """
        Нормализация матрицы экспрессии
        
        Args:
            method: Метод нормализации ('TPM', 'RPKM', 'CPM', 'log2')
            
        Returns:
            pd.DataFrame: Нормализованная матрица
        """
        if self.expression_matrix is None:
            raise ValueError("Матрица экспрессии не загружена")
            
        if method == 'CPM':
            # Counts Per Million
            normalized = self.expression_matrix.apply(
                lambda x: (x / x.sum()) * 1e6, axis=0
            )
        elif method == 'log2':
            # Log2 трансформация с псевдо-count
            normalized = np.log2(self.expression_matrix + 1)
        elif method == 'TPM':
            # Transcripts Per Million (упрощенная версия без длин генов)
            logger.warning("TPM нормализация без длин генов - используется CPM как приближение")
            normalized = self.expression_matrix.apply(
                lambda x: (x / x.sum()) * 1e6, axis=0
            )
        elif method == 'RPKM':
            # Reads Per Kilobase Million (упрощенная версия)
            logger.warning("RPKM нормализация без длин генов - используется CPM как приближение")
            normalized = self.expression_matrix.apply(
                lambda x: (x / x.sum()) * 1e6, axis=0
            )
        else:
            raise ValueError(f"Неизвестный метод нормализации: {method}")
            
        logger.info(f"Выполнена {method} нормализация")
        return normalized
        
    def filter_low_expression_genes(self, 
                                   min_count: int = 10,
                                   min_samples: int = 2) -> pd.DataFrame:
        """
        Фильтрация генов с низкой экспрессией
        
        Args:
            min_count: Минимальное количество counts
            min_samples: Минимальное количество образцов с экспрессией
            
        Returns:
            pd.DataFrame: Отфильтрованная матрица
        """
        if self.expression_matrix is None:
            raise ValueError("Матрица экспрессии не загружена")
            
        # Гены, которые имеют >= min_count в >= min_samples образцах
        keep_genes = (self.expression_matrix >= min_count).sum(axis=1) >= min_samples
        filtered = self.expression_matrix[keep_genes]
        
        logger.info(
            f"Отфильтровано генов: {len(filtered)}/{len(self.expression_matrix)} "
            f"(удалено {len(self.expression_matrix) - len(filtered)})"
        )
        
        return filtered
        
    def get_qc_summary(self) -> pd.DataFrame:
        """
        Получение сводной таблицы QC метрик
        
        Returns:
            pd.DataFrame: Таблица с метриками всех образцов
        """
        if not self.sample_metrics:
            raise ValueError("QC метрики не вычислены. Запустите calculate_qc_metrics()")
            
        summary_data = []
        for sample_name, metrics in self.sample_metrics.items():
            summary_data.append({
                'Sample': sample_name,
                'Total Genes': metrics.total_genes,
                'Detected Genes': metrics.detected_genes,
                'Library Size': metrics.library_size,
                'Median Expression': metrics.median_expression,
                'QC Passed': metrics.qc_passed,
                'Warnings': len(metrics.qc_warnings),
                'Errors': len(metrics.qc_errors)
            })
            
        return pd.DataFrame(summary_data)
        
    def export_qc_report(self, output_path: Union[str, Path]):
        """
        Экспорт QC отчета в файл
        
        Args:
            output_path: Путь для сохранения отчета
        """
        output_path = Path(output_path)
        
        # Создание текстового отчета
        report_lines = [
            "=" * 60,
            "BULK RNA-SEQ QUALITY CONTROL REPORT",
            "=" * 60,
            ""
        ]
        
        for sample_name, metrics in self.sample_metrics.items():
            report_lines.extend([
                f"\n--- Sample: {sample_name} ---",
                f"QC Status: {'PASSED' if metrics.qc_passed else 'FAILED'}",
                f"Total Genes: {metrics.total_genes}",
                f"Detected Genes: {metrics.detected_genes}",
                f"Library Size: {metrics.library_size:,}",
                f"Median Expression: {metrics.median_expression:.2f}",
                f"Normalized: {metrics.is_normalized}",
            ])
            
            if metrics.qc_warnings:
                report_lines.append("\nWarnings:")
                for warning in metrics.qc_warnings:
                    report_lines.append(f"  ⚠ {warning}")
                    
            if metrics.qc_errors:
                report_lines.append("\nErrors:")
                for error in metrics.qc_errors:
                    report_lines.append(f"  ✖ {error}")
                    
        # Сохранение отчета
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
            
        logger.info(f"QC отчет сохранен: {output_path}")
        
        # Сохранение сводной таблицы
        summary_path = output_path.with_suffix('.summary.csv')
        summary = self.get_qc_summary()
        summary.to_csv(summary_path, index=False)
        logger.info(f"Сводная таблица сохранена: {summary_path}")
    
    def run_qc_analysis(self, sample_data: pd.Series, sample_name: str,
                       min_genes: int = None, min_reads: int = None,
                       max_mito_percent: float = None) -> BulkRNASeqQCMetrics:
        """
        Полный QC анализ для одного образца
        
        Args:
            sample_data: Данные экспрессии одного образца
            sample_name: Имя образца
            min_genes: Минимальное количество генов (переопределяет self.min_genes)
            min_reads: Минимальное количество ридов (переопределяет self.min_counts)
            max_mito_percent: Максимальный процент митохондриальных генов
            
        Returns:
            BulkRNASeqQCMetrics: Метрики QC для образца
        """
        # Использование переданных параметров или значений по умолчанию
        min_genes = min_genes or self.min_genes
        min_reads = min_reads or self.min_counts
        
        # Создание временной матрицы для анализа
        temp_matrix = pd.DataFrame({sample_name: sample_data})
        
        # Вычисление метрик
        metrics = BulkRNASeqQCMetrics(sample_name=sample_name)
        
        # Базовые метрики
        metrics.total_genes = len(sample_data)
        metrics.detected_genes = (sample_data > 0).sum()
        metrics.zero_count_genes = (sample_data == 0).sum()
        metrics.low_expression_genes = (sample_data < 10).sum()
        
        # Библиотечная глубина
        metrics.library_size = int(sample_data.sum())
        metrics.total_reads = metrics.library_size
        
        # Статистика экспрессии
        non_zero_expr = sample_data[sample_data > 0]
        if len(non_zero_expr) > 0:
            metrics.median_expression = float(non_zero_expr.median())
            metrics.mean_expression = float(non_zero_expr.mean())
            
            # Высоко экспрессируемые гены (> 90 percentile)
            threshold_90 = non_zero_expr.quantile(0.9)
            metrics.highly_expressed_genes = (non_zero_expr > threshold_90).sum()
        
        # Проверка нормализации
        if sample_data.dtype == float and sample_data.max() < 100:
            metrics.is_normalized = True
            if sample_data.max() <= 1:
                metrics.normalization_method = "Fraction/Probability"
            elif abs(sample_data.sum() - 1e6) < 1000:  # TPM обычно сумма ~1M
                metrics.normalization_method = "TPM"
            else:
                metrics.normalization_method = "Unknown"
        
        # QC проверки с переданными параметрами
        if metrics.detected_genes < min_genes:
            metrics.qc_errors.append(
                f"Низкое количество детектируемых генов: {metrics.detected_genes} < {min_genes}"
            )
            metrics.qc_passed = False
        
        if not metrics.is_normalized and metrics.library_size < min_reads:
            metrics.qc_errors.append(
                f"Низкая глубина секвенирования: {metrics.library_size} < {min_reads}"
            )
            metrics.qc_passed = False
        
        # Проверка митохондриальных генов (если задан параметр)
        if max_mito_percent is not None:
            # Поиск митохондриальных генов по индексу
            mito_mask = sample_data.index.str.startswith(('MT-', 'mt-'))
            if mito_mask.any():
                mito_expression = sample_data[mito_mask].sum()
                mito_percent = (mito_expression / metrics.library_size) * 100
                
                if mito_percent > max_mito_percent:
                    metrics.qc_errors.append(
                        f"Высокий процент митохондриальных генов: {mito_percent:.1f}% > {max_mito_percent}%"
                    )
                    metrics.qc_passed = False
        
        # Предупреждения
        if metrics.zero_count_genes / metrics.total_genes > 0.8:
            metrics.qc_warnings.append(
                f"Более 80% генов имеют нулевую экспрессию ({metrics.zero_count_genes}/{metrics.total_genes})"
            )
        
        if metrics.highly_expressed_genes < 10:
            metrics.qc_warnings.append(
                "Менее 10 высоко экспрессируемых генов"
            )
        
        logger.info(f"QC анализ образца '{sample_name}' завершен: {'PASSED' if metrics.qc_passed else 'FAILED'}")
        
        return metrics