#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль контроля качества данных
Обеспечивает качество данных на всех этапах
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process(input_path=None, output_path=None):
    """
    Основная функция контроля качества данных
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Запуск модуля контроля качества данных")
    
    if input_path is None:
        input_path = "data/input/quality_control"
        
    if output_path is None:
        output_path = "data/output/quality_control"
    
    # Создание директорий если они не существуют
    Path(input_path).mkdir(parents=True, exist_ok=True)
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Входная директория: {input_path}")
    logger.info(f"Выходная директория: {output_path}")
    
    # Проверка наличия входных файлов
    if not os.path.exists(input_path):
        logger.error(f"Входная директория {input_path} не существует")
        return
    
    # Обработка файлов
    perform_quality_control(input_path, output_path)
    
    logger.info("Контроль качества данных завершен")

def perform_quality_control(input_path, output_path):
    """
    Выполнение контроля качества данных
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Начало контроля качества данных")
    
    # Поиск файлов данных различных модальностей
    data_files = {}
    modalities = ['genomics', 'transcriptomics', 'mirna', 'proteomics', 'metabolomics', 'integration']
    
    for modality in modalities:
        modality_path = os.path.join(input_path, modality)
        if os.path.exists(modality_path):
            data_files[modality] = []
            for root, dirs, files in os.walk(modality_path):
                for file in files:
                    if file.endswith(".tsv") or file.endswith(".csv") or file.endswith(".txt") or file.endswith(".vcf") or file.endswith(".bam") or file.endswith(".h5ad"):
                        data_files[modality].append(os.path.join(root, file))
    
    # Вывод информации о найденных файлах
    for modality, files in data_files.items():
        logger.info(f"Найдено файлов {modality}: {len(files)}")
    
    # Проверка качества для каждого файла
    qc_reports = []
    for modality, files in data_files.items():
        for file in files:
            report = check_quality(modality, file, output_path)
            if report:
                qc_reports.append(report)
    
    # Генерация сводного отчета
    generate_summary_report(qc_reports, output_path)

def check_quality(modality, file_path, output_path):
    """
    Проверка качества файла данных
    
    Args:
        modality (str): Модальность данных
        file_path (str): Путь к файлу данных
        output_path (str): Путь к выходным данным
        
    Returns:
        dict: Отчет о качестве
    """
    logger.info(f"Проверка качества файла: {file_path}")
    
    # Создание отчета о качестве
    report = {
        'file': file_path,
        'modality': modality,
        'timestamp': pd.Timestamp.now(),
        'checks': []
    }
    
    try:
        # Определение типа файла и выполнение соответствующих проверок
        if file_path.endswith(('.tsv', '.csv', '.txt')):
            checks = check_tabular_data(file_path)
        elif file_path.endswith('.vcf'):
            checks = check_vcf_data(file_path)
        elif file_path.endswith(('.bam', '.cram')):
            checks = check_alignment_data(file_path)
        elif file_path.endswith('.h5ad'):
            checks = check_h5ad_data(file_path)
        else:
            checks = [{'check': 'File type check', 'status': 'unknown', 'details': 'Unknown file type'}]
        
        report['checks'] = checks
        
        # Определение общего статуса
        passed_checks = sum(1 for check in checks if check.get('status') == 'passed')
        total_checks = len(checks)
        report['overall_status'] = f"{passed_checks}/{total_checks} checks passed"
        
        # Сохранение отчета
        save_qc_report(report, output_path)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке качества файла {file_path}: {e}")
        report['checks'].append({
            'check': 'Overall quality check',
            'status': 'failed',
            'details': f'Error during quality check: {str(e)}'
        })
        report['overall_status'] = 'Failed'
        
        # Сохранение отчета об ошибке
        save_qc_report(report, output_path)
    
    return report

def check_tabular_data(file_path):
    """
    Проверка качества табличных данных
    
    Args:
        file_path (str): Путь к файлу данных
        
    Returns:
        list: Список проверок
    """
    checks = []
    
    try:
        # Определение разделителя
        delimiter = '\t' if file_path.endswith('.tsv') else ','
        
        # Загрузка данных
        df = pd.read_csv(file_path, sep=delimiter, nrows=1000)  # Ограничиваем для производительности
        
        # Проверка базовых метрик
        checks.append({
            'check': 'File readability',
            'status': 'passed',
            'details': f'Successfully read {len(df)} rows, {len(df.columns)} columns'
        })
        
        # Проверка наличия пропущенных значений
        missing_values = df.isnull().sum().sum()
        if missing_values > 0:
            checks.append({
                'check': 'Missing values check',
                'status': 'warning',
                'details': f'Found {missing_values} missing values'
            })
        else:
            checks.append({
                'check': 'Missing values check',
                'status': 'passed',
                'details': 'No missing values found'
            })
        
        # Проверка типов данных
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        non_numeric_columns = df.select_dtypes(exclude=[np.number]).columns
        
        checks.append({
            'check': 'Data types check',
            'status': 'info',
            'details': f'Numeric columns: {len(numeric_columns)}, Non-numeric columns: {len(non_numeric_columns)}'
        })
        
    except Exception as e:
        checks.append({
            'check': 'Tabular data check',
            'status': 'failed',
            'details': f'Error reading tabular data: {str(e)}'
        })
    
    return checks

def check_vcf_data(file_path):
    """
    Проверка качества VCF данных
    
    Args:
        file_path (str): Путь к файлу данных
        
    Returns:
        list: Список проверок
    """
    checks = []
    
    try:
        # Проверка наличия файла
        if os.path.exists(file_path):
            checks.append({
                'check': 'File existence',
                'status': 'passed',
                'details': 'VCF file exists'
            })
            
            # Проверка размера файла
            file_size = os.path.getsize(file_path)
            checks.append({
                'check': 'File size',
                'status': 'info',
                'details': f'File size: {file_size / (1024*1024):.2f} MB'
            })
            
            # Проверка первых строк файла на корректность формата
            with open(file_path, 'r') as f:
                header_lines = 0
                for line in f:
                    if line.startswith('#'):
                        header_lines += 1
                    else:
                        break
            
            checks.append({
                'check': 'Header lines',
                'status': 'info',
                'details': f'Header lines: {header_lines}'
            })
        else:
            checks.append({
                'check': 'File existence',
                'status': 'failed',
                'details': 'VCF file does not exist'
            })
            
    except Exception as e:
        checks.append({
            'check': 'VCF data check',
            'status': 'failed',
            'details': f'Error checking VCF data: {str(e)}'
        })
    
    return checks

def check_alignment_data(file_path):
    """
    Проверка качества данных выравнивания (BAM/CRAM)
    
    Args:
        file_path (str): Путь к файлу данных
        
    Returns:
        list: Список проверок
    """
    checks = []
    
    try:
        # Проверка наличия файла
        if os.path.exists(file_path):
            checks.append({
                'check': 'File existence',
                'status': 'passed',
                'details': 'Alignment file exists'
            })
            
            # Проверка размера файла
            file_size = os.path.getsize(file_path)
            checks.append({
                'check': 'File size',
                'status': 'info',
                'details': f'File size: {file_size / (1024*1024):.2f} MB'
            })
            
            # Проверка наличия индексного файла
            index_file = file_path + '.bai' if file_path.endswith('.bam') else file_path + '.crai'
            if os.path.exists(index_file):
                checks.append({
                    'check': 'Index file',
                    'status': 'passed',
                    'details': 'Index file exists'
                })
            else:
                checks.append({
                    'check': 'Index file',
                    'status': 'warning',
                    'details': 'Index file does not exist'
                })
        else:
            checks.append({
                'check': 'File existence',
                'status': 'failed',
                'details': 'Alignment file does not exist'
            })
            
    except Exception as e:
        checks.append({
            'check': 'Alignment data check',
            'status': 'failed',
            'details': f'Error checking alignment data: {str(e)}'
        })
    
    return checks

def check_h5ad_data(file_path):
    """
    Проверка качества H5AD данных
    
    Args:
        file_path (str): Путь к файлу данных
        
    Returns:
        list: Список проверок
    """
    checks = []
    
    try:
        # Проверка наличия файла
        if os.path.exists(file_path):
            checks.append({
                'check': 'File existence',
                'status': 'passed',
                'details': 'H5AD file exists'
            })
            
            # Проверка размера файла
            file_size = os.path.getsize(file_path)
            checks.append({
                'check': 'File size',
                'status': 'info',
                'details': f'File size: {file_size / (1024*1024):.2f} MB'
            })
            
            # Здесь могла бы быть проверка структуры H5AD файла,
            # но для демонстрации ограничимся базовыми проверками
            
        else:
            checks.append({
                'check': 'File existence',
                'status': 'failed',
                'details': 'H5AD file does not exist'
            })
            
    except Exception as e:
        checks.append({
            'check': 'H5AD data check',
            'status': 'failed',
            'details': f'Error checking H5AD data: {str(e)}'
        })
    
    return checks

def save_qc_report(report, output_path):
    """
    Сохранение отчета о качестве
    
    Args:
        report (dict): Отчет о качестве
        output_path (str): Путь к выходным данным
    """
    try:
        # Создание имени файла для отчета
        file_name = os.path.basename(report['file'])
        file_name_no_ext = os.path.splitext(file_name)[0]
        report_file = os.path.join(output_path, f"qc_report_{file_name_no_ext}.tsv")
        
        # Преобразование отчета в DataFrame
        report_data = []
        for check in report['checks']:
            report_data.append({
                'file': report['file'],
                'modality': report['modality'],
                'check': check.get('check', ''),
                'status': check.get('status', ''),
                'details': check.get('details', '')
            })
        
        df = pd.DataFrame(report_data)
        df.to_csv(report_file, sep='\t', index=False)
        logger.info(f"Сохранен отчет о качестве: {report_file}")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения отчета о качестве: {e}")

def generate_summary_report(qc_reports, output_path):
    """
    Генерация сводного отчета о качестве
    
    Args:
        qc_reports (list): Список отчетов о качестве
        output_path (str): Путь к выходным данным
    """
    logger.info("Генерация сводного отчета о качестве")
    
    try:
        # Создание сводного отчета
        summary_data = []
        for report in qc_reports:
            summary_data.append({
                'file': report['file'],
                'modality': report['modality'],
                'overall_status': report['overall_status'],
                'timestamp': report['timestamp']
            })
        
        df = pd.DataFrame(summary_data)
        summary_file = os.path.join(output_path, "qc_summary_report.tsv")
        df.to_csv(summary_file, sep='\t', index=False)
        logger.info(f"Сохранен сводный отчет о качестве: {summary_file}")
        
    except Exception as e:
        logger.error(f"Ошибка генерации сводного отчета: {e}")

if __name__ == "__main__":
    process()