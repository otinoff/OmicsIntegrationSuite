"""
Модуль контроля качества для single-cell RNA-seq данных
Поддерживает форматы 10x Genomics, H5AD, Loom
Включает детекцию дублетов и специфичные QC метрики
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
import warnings

# Импорты для работы с scRNA-seq
try:
    import scanpy as sc
    import anndata as ad
    SCANPY_AVAILABLE = True
except ImportError:
    SCANPY_AVAILABLE = False
    warnings.warn("scanpy не установлен. Установите: pip install scanpy")

try:
    import scrublet as scr
    SCRUBLET_AVAILABLE = True
except ImportError:
    SCRUBLET_AVAILABLE = False
    warnings.warn("scrublet не установлен. Установите: pip install scrublet")

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class ScRNASeqQCMetrics:
    """Метрики качества для single-cell RNA-seq"""
    
    # Базовые метрики
    n_cells: int = 0
    n_genes: int = 0
    
    # Метрики на клетку (средние)
    mean_counts_per_cell: float = 0.0
    median_counts_per_cell: float = 0.0
    mean_genes_per_cell: float = 0.0
    median_genes_per_cell: float = 0.0
    
    # Процент митохондриальных генов
    mean_percent_mito: float = 0.0
    median_percent_mito: float = 0.0
    
    # Процент рибосомальных генов
    mean_percent_ribo: float = 0.0
    median_percent_ribo: float = 0.0
    
    # Дублеты
    n_doublets: int = 0
    percent_doublets: float = 0.0
    
    # QC фильтрация
    n_cells_filtered: int = 0
    n_genes_filtered: int = 0
    
    # QC статус
    qc_passed: bool = True
    qc_warnings: List[str] = None
    qc_errors: List[str] = None
    
    def __post_init__(self):
        if self.qc_warnings is None:
            self.qc_warnings = []
        if self.qc_errors is None:
            self.qc_errors = []


class ScRNASeqQC:
    """
    Класс для контроля качества scRNA-seq данных
    Реализует функциональность аналогичную Seurat в Python
    """
    
    def __init__(self,
                 min_genes: int = 200,
                 max_genes: int = 2500,
                 max_mito_percent: float = 5.0,
                 min_cells: int = 3):
        """
        Инициализация QC модуля для scRNA-seq
        
        Args:
            min_genes: Минимальное количество генов на клетку
            max_genes: Максимальное количество генов на клетку (для фильтрации дублетов)
            max_mito_percent: Максимальный процент митохондриальных генов
            min_cells: Минимальное количество клеток для гена
        """
        self.min_genes = min_genes
        self.max_genes = max_genes
        self.max_mito_percent = max_mito_percent
        self.min_cells = min_cells
        
        self.adata = None
        self.metrics = None
        
        if not SCANPY_AVAILABLE:
            warnings.warn("scanpy не установлен. Используется ограниченная функциональность на базе pandas. Установите: pip install scanpy")
            self.fallback_mode = True
        else:
            self.fallback_mode = False
    
    def load_10x_data(self, path: Union[str, Path]):
        """
        Загрузка данных в формате 10x Genomics (Cell Ranger output)
        
        Args:
            path: Путь к директории с файлами matrix.mtx, barcodes.tsv, features.tsv
            
        Returns:
            AnnData или DataFrame: Объект с загруженными данными
        """
        if self.fallback_mode:
            raise NotImplementedError("Загрузка 10x данных требует scanpy. Установите: pip install scanpy")
        
        path = Path(path)
        
        try:
            # Загрузка данных 10x
            self.adata = sc.read_10x_mtx(
                path,
                var_names='gene_symbols',
                cache=True
            )
            
            logger.info(
                f"Загружены данные 10x: {self.adata.n_obs} клеток × {self.adata.n_vars} генов"
            )
            
            # Сохранение сырых данных
            self.adata.raw = self.adata.copy()
            
            return self.adata
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке 10x данных: {e}")
            raise
    
    def load_h5ad(self, file_path: Union[str, Path]):
        """
        Загрузка данных в формате H5AD (AnnData)
        
        Args:
            file_path: Путь к H5AD файлу
            
        Returns:
            AnnData или DataFrame: Объект с загруженными данными
        """
        if self.fallback_mode:
            raise NotImplementedError("Загрузка H5AD файлов требует scanpy. Установите: pip install scanpy")
            
        try:
            self.adata = sc.read_h5ad(file_path)
            
            logger.info(
                f"Загружен H5AD: {self.adata.n_obs} клеток × {self.adata.n_vars} генов"
            )
            
            if self.adata.raw is None:
                self.adata.raw = self.adata.copy()
                
            return self.adata
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке H5AD: {e}")
            raise
    
    def load_csv_matrix(self,
                       file_path: Union[str, Path],
                       sep: str = ',',
                       first_column_names: bool = True):
        """
        Загрузка матрицы экспрессии из CSV/TSV файла
        
        Args:
            file_path: Путь к файлу с матрицей
            sep: Разделитель
            first_column_names: Первая колонка содержит имена генов
            
        Returns:
            AnnData или DataFrame: Объект с загруженными данными
        """
        try:
            # Загрузка матрицы
            if first_column_names:
                matrix = pd.read_csv(file_path, sep=sep, index_col=0)
            else:
                matrix = pd.read_csv(file_path, sep=sep)
            
            if self.fallback_mode:
                # Fallback режим: используем pandas DataFrame
                # Транспонируем для формата клетки × гены
                self.adata = matrix.T
                self.adata.index.name = 'cell_id'
                self.adata.columns.name = 'gene_id'
                
                logger.info(
                    f"Загружена матрица (fallback): {self.adata.shape[0]} клеток × {self.adata.shape[1]} генов"
                )
                
                return self.adata
            else:
                # Стандартный режим с AnnData
                self.adata = ad.AnnData(X=matrix.T.values)
                self.adata.obs_names = matrix.columns
                self.adata.var_names = matrix.index if first_column_names else [f"Gene_{i}" for i in range(matrix.shape[0])]
                
                logger.info(
                    f"Загружена матрица: {self.adata.n_obs} клеток × {self.adata.n_vars} генов"
                )
                
                self.adata.raw = self.adata.copy()
                
                return self.adata
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке матрицы: {e}")
            raise
    
    def calculate_qc_metrics(self) -> ScRNASeqQCMetrics:
        """
        Вычисление QC метрик (аналогично Seurat)
        
        Returns:
            ScRNASeqQCMetrics: Объект с метриками
        """
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        self.metrics = ScRNASeqQCMetrics()
        
        if self.fallback_mode:
            # Fallback режим с pandas DataFrame
            self.metrics.n_cells = self.adata.shape[0]
            self.metrics.n_genes = self.adata.shape[1]
            
            # Создаем DataFrame для метрик клеток (аналог adata.obs)
            if not hasattr(self, 'cell_metrics'):
                self.cell_metrics = pd.DataFrame(index=self.adata.index)
            
            # Вычисление базовых метрик
            self.cell_metrics['n_counts'] = self.adata.sum(axis=1)
            self.cell_metrics['n_genes'] = (self.adata > 0).sum(axis=1)
            
            # Поиск митохондриальных генов
            mito_genes = self.adata.columns.str.startswith('MT-') | self.adata.columns.str.startswith('mt-')
            
            if mito_genes.any():
                mito_counts = self.adata.loc[:, mito_genes].sum(axis=1)
                self.cell_metrics['percent_mito'] = (mito_counts / self.cell_metrics['n_counts']) * 100
            else:
                self.cell_metrics['percent_mito'] = 0
                logger.warning("Митохондриальные гены не найдены (MT-/mt-)")
            
            # Поиск рибосомальных генов
            ribo_genes = self.adata.columns.str.startswith(('RPS', 'RPL', 'Rps', 'Rpl'))
            
            if ribo_genes.any():
                ribo_counts = self.adata.loc[:, ribo_genes].sum(axis=1)
                self.cell_metrics['percent_ribo'] = (ribo_counts / self.cell_metrics['n_counts']) * 100
            else:
                self.cell_metrics['percent_ribo'] = 0
                logger.warning("Рибосомальные гены не найдены (RPS/RPL)")
            
            # Статистика
            self.metrics.mean_counts_per_cell = float(self.cell_metrics['n_counts'].mean())
            self.metrics.median_counts_per_cell = float(self.cell_metrics['n_counts'].median())
            self.metrics.mean_genes_per_cell = float(self.cell_metrics['n_genes'].mean())
            self.metrics.median_genes_per_cell = float(self.cell_metrics['n_genes'].median())
            
            self.metrics.mean_percent_mito = float(self.cell_metrics['percent_mito'].mean())
            self.metrics.median_percent_mito = float(self.cell_metrics['percent_mito'].median())
            
            self.metrics.mean_percent_ribo = float(self.cell_metrics['percent_ribo'].mean())
            self.metrics.median_percent_ribo = float(self.cell_metrics['percent_ribo'].median())
            
        else:
            # Стандартный режим с AnnData
            self.metrics.n_cells = self.adata.n_obs
            self.metrics.n_genes = self.adata.n_vars
            
            # Вычисление базовых метрик (как nCount_RNA и nFeature_RNA в Seurat)
            self.adata.obs['n_counts'] = np.array(self.adata.X.sum(axis=1)).flatten()
            self.adata.obs['n_genes'] = np.array((self.adata.X > 0).sum(axis=1)).flatten()
            
            # Идентификация митохондриальных генов (как в Seurat)
            mito_genes = self.adata.var_names.str.startswith('MT-') | \
                        self.adata.var_names.str.startswith('mt-')
            
            # Вычисление процента митохондриальных генов (percent.mt в Seurat)
            if mito_genes.any():
                mito_counts = np.array(self.adata[:, mito_genes].X.sum(axis=1)).flatten()
                self.adata.obs['percent_mito'] = (mito_counts / self.adata.obs['n_counts']) * 100
            else:
                self.adata.obs['percent_mito'] = 0
                logger.warning("Митохондриальные гены не найдены (MT-/mt-)")
            
            # Идентификация рибосомальных генов
            ribo_genes = self.adata.var_names.str.startswith(('RPS', 'RPL', 'Rps', 'Rpl'))
            
            if ribo_genes.any():
                ribo_counts = np.array(self.adata[:, ribo_genes].X.sum(axis=1)).flatten()
                self.adata.obs['percent_ribo'] = (ribo_counts / self.adata.obs['n_counts']) * 100
            else:
                self.adata.obs['percent_ribo'] = 0
                logger.warning("Рибосомальные гены не найдены (RPS/RPL)")
            
            # Статистика по клеткам
            self.metrics.mean_counts_per_cell = float(self.adata.obs['n_counts'].mean())
            self.metrics.median_counts_per_cell = float(self.adata.obs['n_counts'].median())
            self.metrics.mean_genes_per_cell = float(self.adata.obs['n_genes'].mean())
            self.metrics.median_genes_per_cell = float(self.adata.obs['n_genes'].median())
            
            # Статистика по митохондриальным генам
            self.metrics.mean_percent_mito = float(self.adata.obs['percent_mito'].mean())
            self.metrics.median_percent_mito = float(self.adata.obs['percent_mito'].median())
            
            # Статистика по рибосомальным генам
            self.metrics.mean_percent_ribo = float(self.adata.obs['percent_ribo'].mean())
            self.metrics.median_percent_ribo = float(self.adata.obs['percent_ribo'].median())
        
        # Проверка качества
        self._check_quality()
        
        logger.info("QC метрики вычислены")
        
        return self.metrics
    
    def _check_quality(self):
        """Проверка качества данных по пороговым значениям"""
        
        if self.metrics.mean_genes_per_cell < 100:
            self.metrics.qc_errors.append(
                f"Очень низкое среднее количество генов на клетку: {self.metrics.mean_genes_per_cell:.0f}"
            )
            self.metrics.qc_passed = False
        
        if self.metrics.mean_percent_mito > 20:
            self.metrics.qc_errors.append(
                f"Очень высокий процент митохондриальных генов: {self.metrics.mean_percent_mito:.1f}%"
            )
            self.metrics.qc_passed = False
        
        # Предупреждения
        if self.metrics.mean_genes_per_cell < 500:
            self.metrics.qc_warnings.append(
                f"Низкое среднее количество генов на клетку: {self.metrics.mean_genes_per_cell:.0f}"
            )
        
        if self.metrics.mean_percent_mito > 10:
            self.metrics.qc_warnings.append(
                f"Высокий процент митохондриальных генов: {self.metrics.mean_percent_mito:.1f}%"
            )
        
        # Проверка низкокачественных клеток
        if self.fallback_mode:
            if hasattr(self, 'cell_metrics'):
                low_quality_cells = (
                    (self.cell_metrics['n_genes'] < self.min_genes) |
                    (self.cell_metrics['n_genes'] > self.max_genes) |
                    (self.cell_metrics['percent_mito'] > self.max_mito_percent)
                ).sum()
                
                if low_quality_cells > self.metrics.n_cells * 0.5:
                    self.metrics.qc_warnings.append(
                        f"Более 50% клеток не проходят QC фильтры ({low_quality_cells}/{self.metrics.n_cells})"
                    )
        else:
            low_quality_cells = (
                (self.adata.obs['n_genes'] < self.min_genes) |
                (self.adata.obs['n_genes'] > self.max_genes) |
                (self.adata.obs['percent_mito'] > self.max_mito_percent)
            ).sum()
            
            if low_quality_cells > self.adata.n_obs * 0.5:
                self.metrics.qc_warnings.append(
                    f"Более 50% клеток не проходят QC фильтры ({low_quality_cells}/{self.adata.n_obs})"
                )
    
    def detect_doublets(self, expected_doublet_rate: float = 0.06) -> Tuple[np.ndarray, np.ndarray]:
        """
        Детекция дублетов используя Scrublet
        
        Args:
            expected_doublet_rate: Ожидаемая доля дублетов
            
        Returns:
            Tuple: (doublet_scores, predicted_doublets)
        """
        if not SCRUBLET_AVAILABLE:
            logger.warning("Scrublet не установлен. Пропуск детекции дублетов.")
            return None, None
        
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        try:
            # Инициализация Scrublet
            scrub = scr.Scrublet(
                self.adata.X,
                expected_doublet_rate=expected_doublet_rate
            )
            
            # Детекция дублетов
            doublet_scores, predicted_doublets = scrub.scrub_doublets(
                min_counts=2,
                min_cells=3,
                min_gene_variability_pctl=85,
                n_prin_comps=30
            )
            
            # Сохранение результатов
            self.adata.obs['doublet_score'] = doublet_scores
            self.adata.obs['predicted_doublet'] = predicted_doublets
            
            # Обновление метрик
            if self.metrics:
                self.metrics.n_doublets = int(predicted_doublets.sum())
                self.metrics.percent_doublets = (self.metrics.n_doublets / self.adata.n_obs) * 100
            
            logger.info(
                f"Обнаружено дублетов: {predicted_doublets.sum()} "
                f"({predicted_doublets.sum()/len(predicted_doublets)*100:.1f}%)"
            )
            
            return doublet_scores, predicted_doublets
            
        except Exception as e:
            logger.error(f"Ошибка при детекции дублетов: {e}")
            logger.warning("Продолжение без детекции дублетов")
            return None, None
    
    def filter_cells_and_genes(self,
                              min_genes: Optional[int] = None,
                              max_genes: Optional[int] = None,
                              max_mito_percent: Optional[float] = None,
                              min_cells: Optional[int] = None,
                              remove_doublets: bool = True):
        """
        Фильтрация клеток и генов по QC критериям (как subset в Seurat)
        
        Args:
            min_genes: Минимальное количество генов на клетку
            max_genes: Максимальное количество генов на клетку
            max_mito_percent: Максимальный процент митохондриальных генов
            min_cells: Минимальное количество клеток для гена
            remove_doublets: Удалять предсказанные дублеты
            
        Returns:
            AnnData или DataFrame: Отфильтрованные данные
        """
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        # Используем значения по умолчанию если не указаны
        min_genes = min_genes or self.min_genes
        max_genes = max_genes or self.max_genes
        max_mito_percent = max_mito_percent or self.max_mito_percent
        min_cells = min_cells or self.min_cells
        
        if self.fallback_mode:
            # Fallback режим с pandas
            n_cells_before = self.adata.shape[0]
            n_genes_before = self.adata.shape[1]
            
            # Фильтрация клеток
            if hasattr(self, 'cell_metrics'):
                keep_cells = np.ones(n_cells_before, dtype=bool)
                
                keep_cells &= (self.cell_metrics['n_genes'] >= min_genes)
                keep_cells &= (self.cell_metrics['n_genes'] <= max_genes)
                keep_cells &= (self.cell_metrics['percent_mito'] <= max_mito_percent)
                
                self.adata = self.adata[keep_cells]
                self.cell_metrics = self.cell_metrics[keep_cells]
                
                # Простая фильтрация генов (встречающихся минимум в min_cells клетках)
                gene_counts = (self.adata > 0).sum(axis=0)
                keep_genes = gene_counts >= min_cells
                self.adata = self.adata.loc[:, keep_genes]
                
                logger.info(
                    f"Фильтрация (fallback): {self.adata.shape[0]}/{n_cells_before} клеток, "
                    f"{self.adata.shape[1]}/{n_genes_before} генов остались"
                )
                
                # Обновление метрик
                if self.metrics:
                    self.metrics.n_cells_filtered = n_cells_before - self.adata.shape[0]
                    self.metrics.n_genes_filtered = n_genes_before - self.adata.shape[1]
            
            return self.adata
        else:
            # Стандартный режим с AnnData
            n_cells_before = self.adata.n_obs
            n_genes_before = self.adata.n_vars
            
            # Фильтрация клеток (как в Seurat subset)
            keep_cells = np.ones(self.adata.n_obs, dtype=bool)
            
            if 'n_genes' in self.adata.obs:
                keep_cells &= (self.adata.obs['n_genes'] >= min_genes)
                keep_cells &= (self.adata.obs['n_genes'] <= max_genes)
            
            if 'percent_mito' in self.adata.obs:
                keep_cells &= (self.adata.obs['percent_mito'] <= max_mito_percent)
            
            if remove_doublets and 'predicted_doublet' in self.adata.obs:
                keep_cells &= ~self.adata.obs['predicted_doublet']
            
            self.adata = self.adata[keep_cells, :]
            
            # Фильтрация генов
            sc.pp.filter_genes(self.adata, min_cells=min_cells)
            
            # Обновление метрик
            if self.metrics:
                self.metrics.n_cells_filtered = n_cells_before - self.adata.n_obs
                self.metrics.n_genes_filtered = n_genes_before - self.adata.n_vars
            
            logger.info(
                f"Фильтрация: {self.adata.n_obs}/{n_cells_before} клеток, "
                f"{self.adata.n_vars}/{n_genes_before} генов остались"
            )
            
            return self.adata
    
    def normalize_data(self, method: str = 'log1p', target_sum: float = 1e4):
        """
        Нормализация данных (аналогично NormalizeData в Seurat)
        
        Args:
            method: Метод нормализации ('log1p', 'sqrt')
            target_sum: Целевая сумма для нормализации на клетку
            
        Returns:
            AnnData: Нормализованные данные
        """
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        # Нормализация на общее количество counts на клетку
        sc.pp.normalize_total(self.adata, target_sum=target_sum)
        
        # Логарифмирование
        if method == 'log1p':
            sc.pp.log1p(self.adata)
        elif method == 'sqrt':
            self.adata.X = np.sqrt(self.adata.X)
        
        logger.info(f"Данные нормализованы методом {method}")
        
        return self.adata
    
    def generate_qc_plots(self):
        """Генерация стандартных QC графиков (как VlnPlot в Seurat)"""
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        import matplotlib.pyplot as plt
        
        # Создание фигуры с подграфиками
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Violin plots для основных метрик (как в Seurat)
        qc_vars = ['n_genes', 'n_counts', 'percent_mito']
        titles = ['Genes per cell', 'UMI counts per cell', 'Mitochondrial genes (%)']
        
        for i, (var, title) in enumerate(zip(qc_vars[:3], titles)):
            if var in self.adata.obs:
                ax = axes[0, i]
                self.adata.obs[var].plot.hist(bins=50, ax=ax, color='skyblue', edgecolor='black')
                ax.set_xlabel(title)
                ax.set_ylabel('Number of cells')
                ax.set_title(title)
        
        # Scatter plots для корреляций
        if 'n_counts' in self.adata.obs and 'n_genes' in self.adata.obs:
            ax = axes[1, 0]
            ax.scatter(self.adata.obs['n_counts'], self.adata.obs['n_genes'], 
                      alpha=0.3, s=1, color='blue')
            ax.set_xlabel('UMI counts')
            ax.set_ylabel('Number of genes')
            ax.set_title('Genes vs UMI counts')
        
        if 'n_counts' in self.adata.obs and 'percent_mito' in self.adata.obs:
            ax = axes[1, 1]
            ax.scatter(self.adata.obs['n_counts'], self.adata.obs['percent_mito'],
                      alpha=0.3, s=1, color='red')
            ax.set_xlabel('UMI counts')
            ax.set_ylabel('Mitochondrial genes (%)')
            ax.set_title('Mitochondrial % vs UMI counts')
        
        if 'doublet_score' in self.adata.obs:
            ax = axes[1, 2]
            self.adata.obs['doublet_score'].plot.hist(bins=50, ax=ax, 
                                                      color='orange', edgecolor='black')
            ax.set_xlabel('Doublet score')
            ax.set_ylabel('Number of cells')
            ax.set_title('Doublet scores distribution')
        else:
            axes[1, 2].axis('off')
        
        plt.tight_layout()
        return fig
    
    def export_qc_report(self, output_path: Union[str, Path]):
        """
        Экспорт QC отчета
        
        Args:
            output_path: Путь для сохранения отчета
        """
        if self.metrics is None:
            raise ValueError("QC метрики не вычислены. Запустите calculate_qc_metrics()")
        
        output_path = Path(output_path)
        
        report_lines = [
            "=" * 60,
            "SINGLE-CELL RNA-SEQ QUALITY CONTROL REPORT",
            "=" * 60,
            "",
            f"Total cells: {self.metrics.n_cells:,}",
            f"Total genes: {self.metrics.n_genes:,}",
            "",
            "--- Per-cell metrics ---",
            f"Mean UMI counts per cell: {self.metrics.mean_counts_per_cell:,.0f}",
            f"Median UMI counts per cell: {self.metrics.median_counts_per_cell:,.0f}",
            f"Mean genes per cell: {self.metrics.mean_genes_per_cell:,.0f}",
            f"Median genes per cell: {self.metrics.median_genes_per_cell:,.0f}",
            "",
            "--- Mitochondrial genes ---",
            f"Mean % mitochondrial: {self.metrics.mean_percent_mito:.2f}%",
            f"Median % mitochondrial: {self.metrics.median_percent_mito:.2f}%",
            "",
            "--- Ribosomal genes ---",
            f"Mean % ribosomal: {self.metrics.mean_percent_ribo:.2f}%",
            f"Median % ribosomal: {self.metrics.median_percent_ribo:.2f}%",
            "",
            "--- Doublets ---",
            f"Predicted doublets: {self.metrics.n_doublets} ({self.metrics.percent_doublets:.2f}%)",
            "",
            "--- Filtering results ---",
            f"Cells filtered: {self.metrics.n_cells_filtered}",
            f"Genes filtered: {self.metrics.n_genes_filtered}",
            "",
            f"QC Status: {'PASSED' if self.metrics.qc_passed else 'FAILED'}",
        ]
        
        if self.metrics.qc_warnings:
            report_lines.append("\nWarnings:")
            for warning in self.metrics.qc_warnings:
                report_lines.append(f"  ⚠ {warning}")
        
        if self.metrics.qc_errors:
            report_lines.append("\nErrors:")
            for error in self.metrics.qc_errors:
                report_lines.append(f"  ✖ {error}")
        
        # Сохранение отчета
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"QC отчет сохранен: {output_path}")
        
        # Сохранение метрик в CSV
        if self.adata is not None:
            metrics_path = output_path.with_suffix('.cell_metrics.csv')
            self.adata.obs.to_csv(metrics_path)
            logger.info(f"Метрики клеток сохранены: {metrics_path}")
    
    def run_qc_analysis(self) -> ScRNASeqQCMetrics:
        """
        Полный анализ QC для scRNA-seq данных
        
        Returns:
            ScRNASeqQCMetrics: Результаты QC анализа
        """
        if self.adata is None:
            raise ValueError("Данные не загружены")
        
        logger.info("Запуск полного QC анализа scRNA-seq...")
        
        # 1. Вычисление базовых QC метрик
        self.calculate_qc_metrics()
        
        # 2. Детекция дублетов
        try:
            self.detect_doublets()
        except Exception as e:
            logger.warning(f"Ошибка при детекции дублетов: {e}")
        
        logger.info("QC анализ scRNA-seq завершен")
        
        return self.metrics