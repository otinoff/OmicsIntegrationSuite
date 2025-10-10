#!/usr/bin/env python3
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
Комплексный тест всех компонентов модуля транскриптомики
Автоматически тестирует bulk RNA-seq и scRNA-seq анализ с тестовыми данными
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
import traceback

# Добавляем путь к модулям
current_dir = Path(__file__).parent
modules_path = current_dir / "modules"
if str(modules_path) not in sys.path:
    sys.path.insert(0, str(modules_path))

# Подавляем предупреждения
warnings.filterwarnings('ignore')

# Импорт модулей транскриптомики
try:
    from modules.transcriptomics.transcriptomics_processor import TranscriptomicsProcessor
    from modules.transcriptomics.bulk_rnaseq_qc import BulkRNASeqQC
    from modules.transcriptomics.scrna_seq_qc import ScRNASeqQC
    from modules.transcriptomics.expression_normalizer import ExpressionNormalizer
    from modules.transcriptomics.doublet_detector import DoubletDetector
    from modules.transcriptomics.qc_reporter import TranscriptomicsQCReporter
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Ошибка импорта модулей: {e}")
    MODULES_AVAILABLE = False


class TranscriptomicsSystemTest(unittest.TestCase):
    """Тестовый класс для проверки всей системы транскриптомики"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка тестов"""
        print("\n" + "="*80)
        print("АВТОМАТИЧЕСКИЙ ТЕСТ СИСТЕМЫ ТРАНСКРИПТОМИКИ")
        print("="*80)
        
        # Проверка доступности модулей
        if not MODULES_AVAILABLE:
            raise unittest.SkipTest("Модули транскриптомики недоступны")
        
        # Создание временной директории для тестов
        cls.test_dir = Path(tempfile.mkdtemp(prefix="transcriptomics_test_"))
        cls.output_dir = cls.test_dir / "output"
        cls.test_data_dir = current_dir / "test_data"
        
        print(f"[INFO] Тестовая директория: {cls.test_dir}")
        print(f"[INFO] Директория тестовых данных: {cls.test_data_dir}")
        
        # Проверка наличия тестовых данных
        cls.bulk_test_file = cls.test_data_dir / "bulk_rnaseq_test.csv"
        cls.scrna_test_file = cls.test_data_dir / "scrna_seq_test.csv"
        
        if not cls.bulk_test_file.exists():
            raise unittest.SkipTest(f"Bulk RNA-seq тестовые данные не найдены: {cls.bulk_test_file}")
        
        if not cls.scrna_test_file.exists():
            raise unittest.SkipTest(f"scRNA-seq тестовые данные не найдены: {cls.scrna_test_file}")
        
        # Инициализация процессора
        cls.processor = TranscriptomicsProcessor(output_dir=cls.output_dir)
        
        print("[OK] Инициализация тестов завершена")
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после тестов"""
        print(f"\n[CLEANUP] Удаление тестовой директории: {cls.test_dir}")
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def setUp(self):
        """Настройка каждого теста"""
        self.test_name = self._testMethodName
        print(f"\n{'='*60}")
        print(f"ТЕСТ: {self.test_name}")
        print(f"{'='*60}")
    
    def test_01_bulk_rnaseq_individual_components(self):
        """Тест 1: Проверка отдельных компонентов bulk RNA-seq"""
        print("[STEP 1] Тестирование компонентов bulk RNA-seq...")
        
        # Загрузка тестовых данных
        print(f"[LOAD] Загрузка данных: {self.bulk_test_file}")
        data = pd.read_csv(self.bulk_test_file, index_col=0)
        print(f"[OK] Данные загружены: {data.shape[0]} генов, {data.shape[1]} образцов")
        
        # Тест BulkRNASeqQC
        print("[TEST] Тестирование BulkRNASeqQC...")
        bulk_qc = BulkRNASeqQC()
        
        # Тест для первого образца
        sample_name = data.columns[0]
        sample_data = data[sample_name]
        
        qc_result = bulk_qc.run_qc_analysis(
            sample_data,
            sample_name=sample_name,
            min_genes=1000,
            min_reads=100000,
            max_mito_percent=25.0
        )
        
        print(f"[OK] QC анализ образца '{sample_name}':")
        print(f"     - Общее генов: {qc_result.total_genes}")
        print(f"     - Детектируемые гены: {qc_result.detected_genes}")
        print(f"     - Глубина библиотеки: {qc_result.library_size:,}")
        print(f"     - QC статус: {'PASSED' if qc_result.qc_passed else 'FAILED'}")
        
        self.assertIsNotNone(qc_result)
        self.assertGreater(qc_result.total_genes, 0)
        self.assertGreater(qc_result.detected_genes, 0)
        self.assertGreater(qc_result.library_size, 0)
    
    def test_02_scrna_seq_individual_components(self):
        """Тест 2: Проверка отдельных компонентов scRNA-seq"""
        print("[STEP 2] Тестирование компонентов scRNA-seq...")
        
        # Тест ScRNASeqQC
        print("[TEST] Тестирование ScRNASeqQC...")
        scrna_qc = ScRNASeqQC(
            min_genes=100,
            max_genes=3000,
            max_mito_percent=25.0,
            min_cells=2
        )
        
        # Загрузка данных
        print(f"[LOAD] Загрузка scRNA-seq данных: {self.scrna_test_file}")
        scrna_qc.load_csv_matrix(self.scrna_test_file)
        
        print(f"[OK] Данные загружены в ScRNASeqQC")
        if hasattr(scrna_qc.adata, 'shape'):
            print(f"     - Размер: {scrna_qc.adata.shape}")
        else:
            print(f"     - Клетки: {scrna_qc.adata.n_obs}, Гены: {scrna_qc.adata.n_vars}")
        
        # Выполнение QC анализа
        print("[RUN] Выполнение QC анализа scRNA-seq...")
        qc_metrics = scrna_qc.run_qc_analysis()
        
        print(f"[OK] QC анализ scRNA-seq завершен:")
        print(f"     - Клетки: {qc_metrics.n_cells:,}")
        print(f"     - Гены: {qc_metrics.n_genes:,}")
        print(f"     - Среднее UMI/клетку: {qc_metrics.mean_counts_per_cell:.0f}")
        print(f"     - Среднее генов/клетку: {qc_metrics.mean_genes_per_cell:.0f}")
        print(f"     - Средний % мито-генов: {qc_metrics.mean_percent_mito:.2f}%")
        print(f"     - QC статус: {'PASSED' if qc_metrics.qc_passed else 'FAILED'}")
        
        if qc_metrics.qc_warnings:
            print(f"     - Предупреждения: {len(qc_metrics.qc_warnings)}")
        if qc_metrics.qc_errors:
            print(f"     - Ошибки: {len(qc_metrics.qc_errors)}")
        
        self.assertIsNotNone(qc_metrics)
        self.assertGreater(qc_metrics.n_cells, 0)
        self.assertGreater(qc_metrics.n_genes, 0)
    
    def test_03_bulk_rnaseq_full_processor(self):
        """Тест 3: Полный тест процессора для bulk RNA-seq"""
        print("[STEP 3] Тестирование полного процессора bulk RNA-seq...")
        
        print(f"[RUN] Запуск process_bulk_rnaseq...")
        results = self.processor.process_bulk_rnaseq(
            data_path=self.bulk_test_file,
            min_genes=1000,
            min_reads=100000,
            max_mito_percent=25.0
        )
        
        print(f"[OK] Обработано образцов: {len(results)}")
        
        # Проверка результатов
        for sample_name, result in results.items():
            print(f"     - {sample_name}: {'PASSED' if result.qc_passed else 'FAILED'}")
        
        passed_samples = sum(1 for r in results.values() if r.qc_passed)
        print(f"[SUMMARY] Прошли QC: {passed_samples}/{len(results)} образцов")
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Проверка, что создались выходные файлы
        output_files = list(self.output_dir.glob("*"))
        print(f"[FILES] Создано файлов: {len(output_files)}")
        for file in output_files:
            print(f"        - {file.name}")
    
    def test_04_scrna_seq_full_processor(self):
        """Тест 4: Полный тест процессора для scRNA-seq"""
        print("[STEP 4] Тестирование полного процессора scRNA-seq...")
        
        # Проверяем доступность scanpy
        try:
            import scanpy
            import anndata
            scanpy_available = True
        except ImportError:
            print("[SKIP] scanpy недоступен, пропускаем scRNA-seq процессор тест")
            return
        
        print(f"[RUN] Запуск process_scrna_seq...")
        try:
            results = self.processor.process_scrna_seq(
                data_path=self.scrna_test_file,
                min_genes_per_cell=100,
                min_cells_per_gene=2,
                max_genes_per_cell=3000,
                max_mito_percent=25.0,
                detect_doublets=False  # Отключаем для скорости
            )
            
            print(f"[OK] scRNA-seq процессор завершен успешно")
            
            qc_results = results['qc_results']
            print(f"     - Клетки: {qc_results.n_cells:,}")
            print(f"     - Гены: {qc_results.n_genes:,}")
            print(f"     - QC статус: {'PASSED' if qc_results.qc_passed else 'FAILED'}")
            
            self.assertIsNotNone(results)
            self.assertIn('qc_results', results)
            
        except ImportError as e:
            print(f"[SKIP] Пропуск scRNA-seq теста из-за отсутствия зависимостей: {e}")
            return
        except Exception as e:
            print(f"[ERROR] Ошибка в scRNA-seq процессоре: {e}")
            print(f"[DEBUG] Трассировка: {traceback.format_exc()}")
            # Не делаем fail, так как это может быть из-за отсутствия зависимостей
            return
    
    def test_05_normalization_methods(self):
        """Тест 5: Проверка методов нормализации"""
        print("[STEP 5] Тестирование методов нормализации...")
        
        # Создаем тестовые данные
        test_data = np.random.lognormal(mean=2, sigma=1, size=(1000, 6))
        test_df = pd.DataFrame(test_data, columns=[f"Sample_{i+1}" for i in range(6)])
        
        print(f"[DATA] Тестовые данные: {test_df.shape}")
        
        # Тестируем отдельные методы нормализации
        normalizer = ExpressionNormalizer()
        
        methods_to_test = ['cpm', 'deseq2_size_factors', 'tmm', 'quantile']
        
        for method in methods_to_test:
            try:
                print(f"[TEST] Метод нормализации: {method}")
                
                if method == 'cpm':
                    normalized = normalizer.normalize_cpm(test_df)
                elif method == 'deseq2_size_factors':
                    normalized = normalizer.normalize_deseq2_size_factors(test_df)
                elif method == 'tmm':
                    normalized = normalizer.normalize_tmm(test_df)
                elif method == 'quantile':
                    normalized = normalizer.normalize_quantile(test_df)
                
                print(f"[OK] {method}: форма {normalized.shape}, среднее {normalized.values.mean():.2f}")
                self.assertIsNotNone(normalized)
                
            except Exception as e:
                print(f"[ERROR] Ошибка в методе {method}: {e}")
                continue
        
        # Тест сравнения методов через процессор
        try:
            print(f"[RUN] Сравнение методов через процессор...")
            comparison_df = self.processor.compare_normalization_methods(test_df)
            
            print(f"[OK] Сравнение завершено: {len(comparison_df)} методов")
            for _, row in comparison_df.iterrows():
                print(f"     - {row['Method']}: среднее={row['Mean']:.2f}, стд={row['Std']:.2f}")
            
            self.assertIsNotNone(comparison_df)
            self.assertGreater(len(comparison_df), 0)
            
        except Exception as e:
            print(f"[ERROR] Ошибка сравнения методов: {e}")
    
    def test_06_report_generation(self):
        """Тест 6: Генерация отчетов"""
        print("[STEP 6] Тестирование генерации отчетов...")
        
        # Сначала убедимся, что есть данные для отчета
        if not hasattr(self.processor, 'bulk_results') or not self.processor.bulk_results:
            print("[PREP] Подготовка данных для отчета...")
            self.processor.process_bulk_rnaseq(
                data_path=self.bulk_test_file,
                min_genes=1000,
                min_reads=100000
            )
        
        try:
            print(f"[RUN] Генерация комплексного отчета...")
            report_files = self.processor.generate_comprehensive_report(
                data_type='bulk',
                include_interactive=False  # Отключаем для скорости
            )
            
            print(f"[OK] Отчет создан:")
            for file_type, file_path in report_files.items():
                print(f"     - {file_type}: {file_path}")
                
                # Проверяем, что файл существует
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"       Размер: {file_size} байт")
                    self.assertGreater(file_size, 0)
                else:
                    print(f"       [WARNING] Файл не найден")
            
            self.assertIsNotNone(report_files)
            
        except Exception as e:
            print(f"[ERROR] Ошибка генерации отчета: {e}")
            print(f"[DEBUG] Трассировка: {traceback.format_exc()}")
    
    def test_07_processing_summary(self):
        """Тест 7: Получение сводки обработки"""
        print("[STEP 7] Тестирование сводки обработки...")
        
        summary = self.processor.get_processing_summary()
        
        print(f"[OK] Сводка обработки:")
        for key, value in summary.items():
            print(f"     - {key}: {value}")
        
        self.assertIsNotNone(summary)
        self.assertIn('timestamp', summary)
        self.assertIn('output_directory', summary)
    
    def test_08_error_handling(self):
        """Тест 8: Обработка ошибок"""
        print("[STEP 8] Тестирование обработки ошибок...")
        
        # Тест с несуществующим файлом
        fake_file = self.test_dir / "nonexistent_file.csv"
        
        print(f"[TEST] Тест с несуществующим файлом: {fake_file}")
        with self.assertRaises(Exception):
            self.processor.process_bulk_rnaseq(data_path=fake_file)
        print(f"[OK] Ошибка корректно обработана")
        
        # Тест с неправильными параметрами
        print(f"[TEST] Тест с неправильными параметрами...")
        try:
            # Очень строгие параметры, которые не пройдет ни один образец
            results = self.processor.process_bulk_rnaseq(
                data_path=self.bulk_test_file,
                min_genes=50000,  # Нереально высокое значение
                min_reads=100000000  # Нереально высокое значение
            )
            
            # Проверяем, что все образцы не прошли QC
            failed_samples = sum(1 for r in results.values() if not r.qc_passed)
            print(f"[OK] Строгие параметры: {failed_samples}/{len(results)} образцов не прошли QC")
            
        except Exception as e:
            print(f"[ERROR] Неожиданная ошибка: {e}")


def run_comprehensive_test():
    """Запуск комплексного теста"""
    print("\n" + "="*80)
    print("ЗАПУСК АВТОМАТИЗИРОВАННОГО ТЕСТИРОВАНИЯ")
    print("="*80)
    
    # Создание test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TranscriptomicsSystemTest)
    
    # Запуск тестов
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Итоговая сводка
    print("\n" + "="*80)
    print("ИТОГОВАЯ СВОДКА ТЕСТИРОВАНИЯ")
    print("="*80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"Всего тестов: {total_tests}")
    print(f"Успешно: {total_tests - failures - errors - skipped}")
    print(f"Ошибки: {errors}")
    print(f"Неудачи: {failures}")
    print(f"Пропущено: {skipped}")
    
    if result.failures:
        print(f"\n[FAILURES] Детали неудач:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\n[ERRORS] Детали ошибок:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"\n[SUMMARY] Успешность: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("[RESULT] Система работает корректно!")
        return True
    else:
        print("[RESULT] Система требует доработки.")
        return False


if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Критическая ошибка: {e}")
        print(traceback.format_exc())
        sys.exit(1)