"""
Модуль нормализации экспрессионных данных
Поддерживает различные методы нормализации для bulk и scRNA-seq
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, Literal
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ExpressionNormalizer:
    """
    Класс для нормализации экспрессионных данных RNA-seq
    """
    
    def __init__(self):
        """Инициализация нормализатора"""
        self.raw_matrix = None
        self.normalized_matrix = None
        self.gene_lengths = None
        self.normalization_method = None
        
    def load_gene_lengths(self, file_path: Union[str, Path]) -> pd.Series:
        """
        Загрузка длин генов для RPKM/TPM нормализации
        
        Args:
            file_path: Путь к файлу с длинами генов (gene_id, length)
            
        Returns:
            pd.Series: Индекс - названия генов, значения - длины
        """
        try:
            lengths = pd.read_csv(file_path, sep='\t', index_col=0, header=None)
            self.gene_lengths = lengths.iloc[:, 0]
            logger.info(f"Загружены длины для {len(self.gene_lengths)} генов")
            return self.gene_lengths
        except Exception as e:
            logger.error(f"Ошибка загрузки длин генов: {e}")
            raise
    
    def cpm_normalization(self, 
                         expression_matrix: pd.DataFrame,
                         scale_factor: float = 1e6) -> pd.DataFrame:
        """
        CPM (Counts Per Million) нормализация
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            scale_factor: Масштабирующий фактор (по умолчанию 1e6)
            
        Returns:
            pd.DataFrame: Нормализованная матрица
        """
        library_sizes = expression_matrix.sum(axis=0)
        normalized = expression_matrix.div(library_sizes) * scale_factor
        
        logger.info(f"CPM нормализация выполнена для {expression_matrix.shape[1]} образцов")
        return normalized
    
    def tpm_normalization(self,
                         expression_matrix: pd.DataFrame,
                         gene_lengths: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        TPM (Transcripts Per Million) нормализация
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            gene_lengths: Длины генов в парах оснований
            
        Returns:
            pd.DataFrame: TPM-нормализованная матрица
        """
        if gene_lengths is None:
            gene_lengths = self.gene_lengths
            
        if gene_lengths is None:
            logger.warning("Длины генов не предоставлены, используется CPM вместо TPM")
            return self.cpm_normalization(expression_matrix)
        
        # Выравнивание индексов
        common_genes = expression_matrix.index.intersection(gene_lengths.index)
        if len(common_genes) < len(expression_matrix.index):
            logger.warning(
                f"Длины найдены только для {len(common_genes)}/{len(expression_matrix.index)} генов"
            )
        
        # RPK: Reads Per Kilobase
        rpk = expression_matrix.loc[common_genes].div(gene_lengths[common_genes] / 1000, axis=0)
        
        # TPM: нормализация на сумму RPK
        per_million_scaling = rpk.sum(axis=0) / 1e6
        tpm = rpk.div(per_million_scaling, axis=1)
        
        logger.info(f"TPM нормализация выполнена для {expression_matrix.shape[1]} образцов")
        return tpm
    
    def rpkm_normalization(self,
                          expression_matrix: pd.DataFrame,
                          gene_lengths: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        RPKM/FPKM (Reads/Fragments Per Kilobase Million) нормализация
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            gene_lengths: Длины генов в парах оснований
            
        Returns:
            pd.DataFrame: RPKM-нормализованная матрица
        """
        if gene_lengths is None:
            gene_lengths = self.gene_lengths
            
        if gene_lengths is None:
            logger.warning("Длины генов не предоставлены, используется CPM вместо RPKM")
            return self.cpm_normalization(expression_matrix)
        
        # Выравнивание индексов
        common_genes = expression_matrix.index.intersection(gene_lengths.index)
        
        # Нормализация на глубину секвенирования (CPM)
        cpm = self.cpm_normalization(expression_matrix.loc[common_genes])
        
        # Нормализация на длину гена (kilobases)
        rpkm = cpm.div(gene_lengths[common_genes] / 1000, axis=0)
        
        logger.info(f"RPKM нормализация выполнена для {expression_matrix.shape[1]} образцов")
        return rpkm
    
    def log_normalization(self,
                         expression_matrix: pd.DataFrame,
                         base: Literal[2, 10, 'e'] = 2,
                         pseudocount: float = 1.0) -> pd.DataFrame:
        """
        Логарифмическая трансформация
        
        Args:
            expression_matrix: Матрица экспрессии
            base: Основание логарифма (2, 10, 'e' для натурального)
            pseudocount: Псевдо-count для избежания log(0)
            
        Returns:
            pd.DataFrame: Логарифмированная матрица
        """
        matrix_with_pseudo = expression_matrix + pseudocount
        
        if base == 2:
            normalized = np.log2(matrix_with_pseudo)
        elif base == 10:
            normalized = np.log10(matrix_with_pseudo)
        elif base == 'e':
            normalized = np.log(matrix_with_pseudo)
        else:
            raise ValueError(f"Неподдерживаемое основание логарифма: {base}")
        
        logger.info(f"Log{base} трансформация выполнена (pseudocount={pseudocount})")
        return normalized
    
    def quantile_normalization(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Квантильная нормализация
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            
        Returns:
            pd.DataFrame: Квантиль-нормализованная матрица
        """
        # Сортировка значений в каждом образце
        sorted_matrix = pd.DataFrame(
            np.sort(expression_matrix.values, axis=0),
            index=expression_matrix.index,
            columns=expression_matrix.columns
        )
        
        # Вычисление средних рангов
        mean_sorted = sorted_matrix.mean(axis=1).values
        
        # Замена значений на средние ранги
        ranks = expression_matrix.rank(axis=0, method='min').astype(int) - 1
        
        normalized = pd.DataFrame(
            index=expression_matrix.index,
            columns=expression_matrix.columns,
            dtype=float
        )
        
        for col in expression_matrix.columns:
            normalized[col] = mean_sorted[ranks[col]]
        
        logger.info("Квантильная нормализация выполнена")
        return normalized
    
    def deseq2_size_factor_normalization(self, 
                                        expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализация методом size factors (аналог DESeq2)
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            
        Returns:
            pd.DataFrame: Нормализованная матрица
        """
        # Удаление генов с нулевыми counts во всех образцах
        non_zero_genes = (expression_matrix > 0).any(axis=1)
        matrix_nonzero = expression_matrix[non_zero_genes]
        
        # Вычисление геометрического среднего для каждого гена
        # Используем логарифм для стабильности вычислений
        log_matrix = np.log(matrix_nonzero.replace(0, np.nan))
        geometric_means = np.exp(log_matrix.mean(axis=1, skipna=True))
        
        # Вычисление size factors
        size_factors = pd.Series(index=expression_matrix.columns, dtype=float)
        
        for sample in expression_matrix.columns:
            # Отношение counts к геометрическому среднему
            ratios = matrix_nonzero[sample] / geometric_means
            # Медиана отношений (игнорируя inf и nan)
            ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
            size_factors[sample] = ratios.median() if len(ratios) > 0 else 1.0
        
        # Нормализация
        normalized = expression_matrix.div(size_factors, axis=1)
        
        logger.info(f"DESeq2 size factor нормализация выполнена. Size factors: {size_factors.to_dict()}")
        return normalized
    
    def tmm_normalization(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        TMM (Trimmed Mean of M-values) нормализация (аналог edgeR)
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            
        Returns:
            pd.DataFrame: TMM-нормализованная матрица
        """
        # Выбор референсного образца (с медианной библиотечной глубиной)
        library_sizes = expression_matrix.sum(axis=0)
        ref_idx = np.argmin(np.abs(library_sizes - library_sizes.median()))
        ref_sample = expression_matrix.columns[ref_idx]
        
        # Вычисление нормализующих факторов для каждого образца
        norm_factors = pd.Series(index=expression_matrix.columns, dtype=float)
        norm_factors[ref_sample] = 1.0
        
        for sample in expression_matrix.columns:
            if sample == ref_sample:
                continue
            
            # M-values (log fold change) и A-values (average expression)
            ref_data = expression_matrix[ref_sample]
            sample_data = expression_matrix[sample]
            
            # Фильтрация нулевых значений
            mask = (ref_data > 0) & (sample_data > 0)
            ref_filtered = ref_data[mask]
            sample_filtered = sample_data[mask]
            
            if len(ref_filtered) == 0:
                norm_factors[sample] = 1.0
                continue
            
            # M и A values
            M = np.log2(sample_filtered / ref_filtered)
            A = 0.5 * (np.log2(sample_filtered) + np.log2(ref_filtered))
            
            # Обрезка 30% экстремальных M-values и 5% экстремальных A-values
            M_trim = 0.3
            A_trim = 0.05
            
            M_lower = np.percentile(M, M_trim * 50)
            M_upper = np.percentile(M, 100 - M_trim * 50)
            A_lower = np.percentile(A, A_trim * 100)
            A_upper = np.percentile(A, 100 - A_trim * 100)
            
            trim_mask = (M >= M_lower) & (M <= M_upper) & (A >= A_lower) & (A <= A_upper)
            
            if trim_mask.sum() > 0:
                # Weighted mean of M-values
                M_trimmed = M[trim_mask]
                weights = 1 / (1 / sample_filtered[mask][trim_mask] + 1 / ref_filtered[mask][trim_mask])
                weighted_mean_M = np.average(M_trimmed, weights=weights)
                norm_factors[sample] = 2 ** weighted_mean_M
            else:
                norm_factors[sample] = 1.0
        
        # Применение нормализующих факторов
        effective_library_sizes = library_sizes * norm_factors
        normalized = expression_matrix.div(effective_library_sizes, axis=1) * effective_library_sizes.median()
        
        logger.info(f"TMM нормализация выполнена. Norm factors: {norm_factors.to_dict()}")
        return normalized
    
    def normalize(self,
                 expression_matrix: pd.DataFrame,
                 method: Literal['CPM', 'TPM', 'RPKM', 'log2', 'log10', 'loge', 
                               'quantile', 'DESeq2', 'TMM'] = 'CPM',
                 **kwargs) -> pd.DataFrame:
        """
        Универсальный метод нормализации
        
        Args:
            expression_matrix: Матрица экспрессии (гены × образцы)
            method: Метод нормализации
            **kwargs: Дополнительные параметры для конкретного метода
            
        Returns:
            pd.DataFrame: Нормализованная матрица
        """
        self.raw_matrix = expression_matrix.copy()
        
        method_map = {
            'CPM': self.cpm_normalization,
            'TPM': self.tpm_normalization,
            'RPKM': self.rpkm_normalization,
            'log2': lambda x: self.log_normalization(x, base=2, **kwargs),
            'log10': lambda x: self.log_normalization(x, base=10, **kwargs),
            'loge': lambda x: self.log_normalization(x, base='e', **kwargs),
            'quantile': self.quantile_normalization,
            'DESeq2': self.deseq2_size_factor_normalization,
            'TMM': self.tmm_normalization
        }
        
        if method not in method_map:
            raise ValueError(f"Неизвестный метод нормализации: {method}")
        
        self.normalized_matrix = method_map[method](expression_matrix, **kwargs)
        self.normalization_method = method
        
        return self.normalized_matrix
    
    def compare_normalizations(self,
                             expression_matrix: pd.DataFrame,
                             methods: list = None) -> pd.DataFrame:
        """
        Сравнение различных методов нормализации
        
        Args:
            expression_matrix: Матрица экспрессии
            methods: Список методов для сравнения
            
        Returns:
            pd.DataFrame: Статистика по каждому методу
        """
        if methods is None:
            methods = ['CPM', 'log2', 'quantile', 'DESeq2', 'TMM']
        
        results = []
        
        for method in methods:
            try:
                normalized = self.normalize(expression_matrix, method)
                
                results.append({
                    'Method': method,
                    'Mean': normalized.mean().mean(),
                    'Median': normalized.median().median(),
                    'Std': normalized.std().mean(),
                    'Min': normalized.min().min(),
                    'Max': normalized.max().max(),
                    'Zero_fraction': (normalized == 0).sum().sum() / normalized.size
                })
            except Exception as e:
                logger.warning(f"Ошибка при {method} нормализации: {e}")
                continue
        
        comparison_df = pd.DataFrame(results)
        logger.info(f"Выполнено сравнение {len(results)} методов нормализации")
        
        return comparison_df
    
    # Алиасы методов для обратной совместимости с процессором
    def normalize_cpm(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """Алиас для CPM нормализации"""
        return self.cpm_normalization(expression_matrix)
    
    def normalize_tpm(self, expression_matrix: pd.DataFrame, gene_lengths: Optional[pd.Series] = None) -> pd.DataFrame:
        """Алиас для TPM нормализации"""
        return self.tpm_normalization(expression_matrix, gene_lengths)
    
    def normalize_deseq2_size_factors(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """Алиас для DESeq2 size factor нормализации"""
        return self.deseq2_size_factor_normalization(expression_matrix)
    
    def normalize_tmm(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """Алиас для TMM нормализации"""
        return self.tmm_normalization(expression_matrix)
    
    def normalize_quantile(self, expression_matrix: pd.DataFrame) -> pd.DataFrame:
        """Алиас для квантильной нормализации"""
        return self.quantile_normalization(expression_matrix)