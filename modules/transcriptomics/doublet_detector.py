"""
Модуль детекции дублетов для scRNA-seq данных
Поддерживает различные алгоритмы детекции дублетов
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
import warnings

# Импорты для детекции дублетов
try:
    import scrublet as scr
    SCRUBLET_AVAILABLE = True
except ImportError:
    SCRUBLET_AVAILABLE = False
    warnings.warn("scrublet не установлен. Установите: pip install scrublet")

try:
    import doubletdetection as dbldet
    DOUBLETDETECTION_AVAILABLE = True
except ImportError:
    DOUBLETDETECTION_AVAILABLE = False
    warnings.warn("doubletdetection library not installed. Install with: pip install doubletdetection")

try:
    import anndata as ad
    import scanpy as sc
    SCANPY_AVAILABLE = True
except ImportError:
    SCANPY_AVAILABLE = False
    warnings.warn("scanpy не установлен. Установите: pip install scanpy")

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class DoubletDetectionResults:
    """Результаты детекции дублетов"""
    method: str
    doublet_scores: np.ndarray
    predicted_doublets: np.ndarray
    doublet_threshold: float
    n_doublets: int
    percent_doublets: float
    simulation_params: Dict = None
    
    def __post_init__(self):
        if self.simulation_params is None:
            self.simulation_params = {}


class DoubletDetector:
    """
    Класс для детекции дублетов в scRNA-seq данных
    Поддерживает различные алгоритмы
    """
    
    def __init__(self):
        """Инициализация детектора дублетов"""
        self.adata = None
        self.results = {}
        
    def detect_scrublet(self,
                       adata: ad.AnnData,
                       expected_doublet_rate: float = 0.06,
                       min_counts: int = 2,
                       min_cells: int = 3,
                       min_gene_variability_pctl: float = 85,
                       n_prin_comps: int = 30,
                       sim_doublet_ratio: float = 2.0,
                       n_neighbors: int = 30,
                       random_state: int = 42) -> DoubletDetectionResults:
        """
        Детекция дублетов с помощью Scrublet
        
        Args:
            adata: AnnData объект с данными
            expected_doublet_rate: Ожидаемая доля дублетов
            min_counts: Минимальное количество UMI для включения клетки
            min_cells: Минимальное количество клеток для включения гена
            min_gene_variability_pctl: Процентиль вариабельности генов
            n_prin_comps: Количество главных компонент
            sim_doublet_ratio: Соотношение симулированных дублетов к клеткам
            n_neighbors: Количество соседей для KNN
            random_state: Случайное состояние для воспроизводимости
            
        Returns:
            DoubletDetectionResults: Результаты детекции
        """
        if not SCRUBLET_AVAILABLE:
            raise ImportError("scrublet не установлен. Установите: pip install scrublet")
        
        try:
            # Инициализация Scrublet
            scrub = scr.Scrublet(
                adata.X,
                expected_doublet_rate=expected_doublet_rate,
                sim_doublet_ratio=sim_doublet_ratio,
                random_state=random_state
            )
            
            # Детекция дублетов (убираем устаревший параметр n_neighbors)
            doublet_scores, predicted_doublets = scrub.scrub_doublets(
                min_counts=min_counts,
                min_cells=min_cells,
                min_gene_variability_pctl=min_gene_variability_pctl,
                n_prin_comps=n_prin_comps,
                verbose=False
            )
            
            # Создание результатов
            results = DoubletDetectionResults(
                method='Scrublet',
                doublet_scores=doublet_scores,
                predicted_doublets=predicted_doublets,
                doublet_threshold=scrub.threshold_,
                n_doublets=int(predicted_doublets.sum()),
                percent_doublets=float(predicted_doublets.sum() / len(predicted_doublets) * 100),
                simulation_params={
                    'expected_doublet_rate': expected_doublet_rate,
                    'sim_doublet_ratio': sim_doublet_ratio,
                    'n_prin_comps': n_prin_comps,
                    'threshold': scrub.threshold_
                }
            )
            
            # Сохранение в AnnData
            adata.obs['scrublet_doublet_scores'] = doublet_scores
            adata.obs['scrublet_predicted_doublets'] = predicted_doublets
            
            logger.info(
                f"Scrublet: обнаружено {results.n_doublets} дублетов "
                f"({results.percent_doublets:.2f}%) с порогом {results.doublet_threshold:.3f}"
            )
            
            self.results['scrublet'] = results
            return results
            
        except Exception as e:
            logger.error(f"Ошибка в Scrublet: {e}")
            raise
    
    def detect_doubletdetection(self,
                               adata: ad.AnnData,
                               n_iters: int = 25,
                               phenograph_parameters: Dict = None,
                               standard_scaling: bool = True,
                               p_thresh: float = 1e-16,
                               voter_thresh: float = 0.5,
                               random_state: int = 42) -> DoubletDetectionResults:
        """
        Детекция дублетов с помощью DoubletDetection
        
        Args:
            adata: AnnData объект с данными
            n_iters: Количество итераций классификатора
            phenograph_parameters: Параметры для Phenograph кластеризации
            standard_scaling: Стандартизация данных перед анализом
            p_thresh: P-value порог для статистической значимости
            voter_thresh: Порог для голосования классификаторов
            random_state: Случайное состояние
            
        Returns:
            DoubletDetectionResults: Результаты детекции
        """
        if not DOUBLETDETECTION_AVAILABLE:
            raise ImportError("doubletdetection не установлен")
        
        try:
            # Инициализация DoubletDetection (убираем устаревший параметр use_phenograph)
            clf = dbldet.BoostClassifier(
                n_iters=n_iters,
                standard_scaling=standard_scaling,
                n_jobs=-1,
                random_state=random_state
            )
            
            # Обучение и предсказание
            doublet_scores = clf.fit(adata.X).predict(p_thresh=p_thresh, voter_thresh=voter_thresh)
            
            # Преобразование в бинарные предсказания
            predicted_doublets = doublet_scores > voter_thresh
            
            # Создание результатов
            results = DoubletDetectionResults(
                method='DoubletDetection',
                doublet_scores=doublet_scores,
                predicted_doublets=predicted_doublets,
                doublet_threshold=voter_thresh,
                n_doublets=int(predicted_doublets.sum()),
                percent_doublets=float(predicted_doublets.sum() / len(predicted_doublets) * 100),
                simulation_params={
                    'n_iters': n_iters,
                    'p_thresh': p_thresh,
                    'voter_thresh': voter_thresh
                }
            )
            
            # Сохранение в AnnData
            adata.obs['doubletdetection_scores'] = doublet_scores
            adata.obs['doubletdetection_predicted_doublets'] = predicted_doublets
            
            logger.info(
                f"DoubletDetection: обнаружено {results.n_doublets} дублетов "
                f"({results.percent_doublets:.2f}%)"
            )
            
            self.results['doubletdetection'] = results
            return results
            
        except Exception as e:
            logger.error(f"Ошибка в DoubletDetection: {e}")
            raise
    
    def detect_hybrid_approach(self,
                              adata: ad.AnnData,
                              min_score_threshold: float = 0.25,
                              max_mito_percent: float = 20,
                              max_genes_per_cell: int = 5000,
                              **scrublet_kwargs) -> DoubletDetectionResults:
        """
        Гибридный подход: Scrublet + эвристические правила
        
        Args:
            adata: AnnData объект с данными
            min_score_threshold: Минимальный порог Scrublet score
            max_mito_percent: Максимальный процент митохондриальных генов
            max_genes_per_cell: Максимальное количество генов на клетку
            **scrublet_kwargs: Параметры для Scrublet
            
        Returns:
            DoubletDetectionResults: Результаты детекции
        """
        # Сначала запускаем Scrublet
        scrublet_results = self.detect_scrublet(adata, **scrublet_kwargs)
        
        # Дополнительные эвристические правила
        heuristic_doublets = np.zeros(adata.n_obs, dtype=bool)
        
        # Правило 1: высокий процент митохондриальных генов + высокий Scrublet score
        if 'percent_mito' in adata.obs:
            high_mito = adata.obs['percent_mito'] > max_mito_percent
            high_scrublet = scrublet_results.doublet_scores > min_score_threshold
            heuristic_doublets |= (high_mito & high_scrublet)
        
        # Правило 2: очень высокое количество генов на клетку
        if 'n_genes' in adata.obs:
            very_high_genes = adata.obs['n_genes'] > max_genes_per_cell
            heuristic_doublets |= very_high_genes
        
        # Правило 3: клетки с очень высокими Scrublet scores (верхние 2%)
        high_score_threshold = np.percentile(scrublet_results.doublet_scores, 98)
        very_high_scrublet = scrublet_results.doublet_scores > high_score_threshold
        heuristic_doublets |= very_high_scrublet
        
        # Комбинированные результаты
        combined_doublets = scrublet_results.predicted_doublets | heuristic_doublets
        
        # Вычисление комбинированного score (взвешенное среднее)
        heuristic_scores = np.zeros_like(scrublet_results.doublet_scores)
        heuristic_scores[heuristic_doublets] = 1.0
        
        combined_scores = (scrublet_results.doublet_scores + heuristic_scores) / 2
        
        # Создание результатов
        results = DoubletDetectionResults(
            method='Hybrid (Scrublet + Heuristics)',
            doublet_scores=combined_scores,
            predicted_doublets=combined_doublets,
            doublet_threshold=scrublet_results.doublet_threshold,
            n_doublets=int(combined_doublets.sum()),
            percent_doublets=float(combined_doublets.sum() / len(combined_doublets) * 100),
            simulation_params={
                'scrublet_threshold': scrublet_results.doublet_threshold,
                'min_score_threshold': min_score_threshold,
                'max_mito_percent': max_mito_percent,
                'max_genes_per_cell': max_genes_per_cell
            }
        )
        
        # Сохранение в AnnData
        adata.obs['hybrid_doublet_scores'] = combined_scores
        adata.obs['hybrid_predicted_doublets'] = combined_doublets
        adata.obs['heuristic_doublets'] = heuristic_doublets
        
        logger.info(
            f"Hybrid approach: обнаружено {results.n_doublets} дублетов "
            f"({results.percent_doublets:.2f}%), включая {heuristic_doublets.sum()} эвристических"
        )
        
        self.results['hybrid'] = results
        return results
    
    def detect_statistical_outliers(self,
                                   adata: ad.AnnData,
                                   features: List[str] = None,
                                   n_mads: float = 2.5) -> DoubletDetectionResults:
        """
        Детекция статистических выбросов по QC метрикам
        
        Args:
            adata: AnnData объект с данными
            features: Список метрик для анализа
            n_mads: Количество медианных абсолютных отклонений для порога
            
        Returns:
            DoubletDetectionResults: Результаты детекции
        """
        if features is None:
            features = ['n_genes', 'n_counts', 'percent_mito']
        
        # Фильтрация доступных метрик
        available_features = [f for f in features if f in adata.obs.columns]
        
        if not available_features:
            raise ValueError(f"Ни одна из метрик {features} не найдена в adata.obs")
        
        outlier_scores = np.zeros(adata.n_obs)
        outlier_mask = np.zeros(adata.n_obs, dtype=bool)
        
        for feature in available_features:
            values = adata.obs[feature].values
            
            # Вычисление медианы и MAD
            median = np.median(values)
            mad = np.median(np.abs(values - median))
            
            # Определение границ (верхние выбросы)
            upper_bound = median + n_mads * mad
            
            # Для процента митохондриальных генов используем только верхнюю границу
            if 'mito' in feature.lower():
                feature_outliers = values > upper_bound
            else:
                # Для других метрик проверяем и верхние, и нижние выбросы
                lower_bound = median - n_mads * mad
                feature_outliers = (values > upper_bound) | (values < lower_bound)
            
            # Накопление outlier score
            outlier_scores += feature_outliers.astype(float)
            outlier_mask |= feature_outliers
        
        # Нормализация scores
        outlier_scores = outlier_scores / len(available_features)
        
        # Создание результатов
        results = DoubletDetectionResults(
            method='Statistical Outliers',
            doublet_scores=outlier_scores,
            predicted_doublets=outlier_mask,
            doublet_threshold=0.5,  # Если выброс хотя бы по одной метрике
            n_doublets=int(outlier_mask.sum()),
            percent_doublets=float(outlier_mask.sum() / len(outlier_mask) * 100),
            simulation_params={
                'features': available_features,
                'n_mads': n_mads
            }
        )
        
        # Сохранение в AnnData
        adata.obs['outlier_scores'] = outlier_scores
        adata.obs['outlier_predicted_doublets'] = outlier_mask
        
        logger.info(
            f"Statistical outliers: обнаружено {results.n_doublets} выбросов "
            f"({results.percent_doublets:.2f}%) по метрикам {available_features}"
        )
        
        self.results['outliers'] = results
        return results
    
    def compare_methods(self,
                       adata: ad.AnnData,
                       methods: List[str] = None) -> pd.DataFrame:
        """
        Сравнение различных методов детекции дублетов
        
        Args:
            adata: AnnData объект с данными
            methods: Список методов для сравнения
            
        Returns:
            pd.DataFrame: Сравнительная таблица результатов
        """
        if methods is None:
            methods = ['scrublet', 'hybrid', 'outliers']
        
        results_data = []
        
        for method in methods:
            try:
                if method == 'scrublet':
                    results = self.detect_scrublet(adata)
                elif method == 'doubletdetection' and DOUBLETDETECTION_AVAILABLE:
                    results = self.detect_doubletdetection(adata)
                elif method == 'hybrid':
                    results = self.detect_hybrid_approach(adata)
                elif method == 'outliers':
                    results = self.detect_statistical_outliers(adata)
                else:
                    logger.warning(f"Неизвестный метод или недоступная библиотека: {method}")
                    continue
                
                results_data.append({
                    'Method': results.method,
                    'N_Doublets': results.n_doublets,
                    'Percent_Doublets': results.percent_doublets,
                    'Threshold': results.doublet_threshold,
                    'Mean_Score': results.doublet_scores.mean(),
                    'Max_Score': results.doublet_scores.max()
                })
                
            except Exception as e:
                logger.error(f"Ошибка в методе {method}: {e}")
                continue
        
        comparison_df = pd.DataFrame(results_data)
        
        # Анализ пересечений между методами
        if len(self.results) >= 2:
            methods_list = list(self.results.keys())
            for i, method1 in enumerate(methods_list):
                for method2 in methods_list[i+1:]:
                    overlap = np.sum(
                        self.results[method1].predicted_doublets & 
                        self.results[method2].predicted_doublets
                    )
                    total_union = np.sum(
                        self.results[method1].predicted_doublets | 
                        self.results[method2].predicted_doublets
                    )
                    
                    jaccard = overlap / total_union if total_union > 0 else 0
                    
                    logger.info(
                        f"Пересечение {method1} vs {method2}: "
                        f"{overlap} клеток, Jaccard index: {jaccard:.3f}"
                    )
        
        return comparison_df
    
    def get_consensus_doublets(self,
                              min_methods: int = 2,
                              score_threshold: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Получение консенсусных дублетов на основе нескольких методов
        
        Args:
            min_methods: Минимальное количество методов, которые должны согласиться
            score_threshold: Порог для консенсусного score
            
        Returns:
            Tuple: (consensus_scores, consensus_doublets)
        """
        if len(self.results) < 2:
            raise ValueError("Необходимо запустить минимум 2 метода для консенсуса")
        
        # Сбор всех предсказаний
        all_predictions = []
        all_scores = []
        
        for method_name, results in self.results.items():
            all_predictions.append(results.predicted_doublets.astype(int))
            # Нормализация scores к диапазону [0, 1]
            normalized_scores = (results.doublet_scores - results.doublet_scores.min()) / \
                               (results.doublet_scores.max() - results.doublet_scores.min())
            all_scores.append(normalized_scores)
        
        # Консенсусные scores (среднее)
        consensus_scores = np.mean(all_scores, axis=0)
        
        # Консенсусные предсказания (минимальное количество методов)
        vote_counts = np.sum(all_predictions, axis=0)
        consensus_doublets = vote_counts >= min_methods
        
        # Альтернативно: на основе score threshold
        score_based_doublets = consensus_scores >= score_threshold
        
        # Финальное решение: ИЛИ от обоих критериев
        final_doublets = consensus_doublets | score_based_doublets
        
        logger.info(
            f"Консенсус: {final_doublets.sum()} дублетов "
            f"({final_doublets.sum()/len(final_doublets)*100:.2f}%) "
            f"из {len(self.results)} методов"
        )
        
        return consensus_scores, final_doublets
    
    # Методы-обертки для совместимости с API
    def detect_doublets_scrublet(self, adata: ad.AnnData, **kwargs) -> DoubletDetectionResults:
        """Обертка для метода detect_scrublet"""
        return self.detect_scrublet(adata, **kwargs)
    
    def detect_doublets_doubletdetection(self, adata: ad.AnnData, **kwargs) -> DoubletDetectionResults:
        """Обертка для метода detect_doubletdetection"""
        return self.detect_doubletdetection(adata, **kwargs)
    
    def detect_doublets_statistical(self, adata: ad.AnnData, **kwargs) -> DoubletDetectionResults:
        """Обертка для метода detect_statistical_outliers"""
        return self.detect_statistical_outliers(adata, **kwargs)
    
    def export_results(self, output_path: str):
        """
        Экспорт результатов детекции дублетов
        
        Args:
            output_path: Путь для сохранения отчета
        """
        if not self.results:
            raise ValueError("Нет результатов для экспорта")
        
        report_lines = [
            "=" * 60,
            "DOUBLET DETECTION RESULTS",
            "=" * 60,
            ""
        ]
        
        for method_name, results in self.results.items():
            report_lines.extend([
                f"--- {results.method} ---",
                f"Doublets detected: {results.n_doublets}",
                f"Percentage: {results.percent_doublets:.2f}%",
                f"Threshold: {results.doublet_threshold:.4f}",
                f"Mean score: {results.doublet_scores.mean():.4f}",
                f"Max score: {results.doublet_scores.max():.4f}",
                ""
            ])
            
            if results.simulation_params:
                report_lines.append("Parameters:")
                for param, value in results.simulation_params.items():
                    report_lines.append(f"  {param}: {value}")
                report_lines.append("")
        
        # Сохранение отчета
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Отчет о детекции дублетов сохранен: {output_path}")