#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль генерации отчетов
Генерирует унифицированные отчеты по результатам обработки данных
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process(input_path=None, output_path=None):
    """
    Основная функция генерации отчетов
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Запуск модуля генерации отчетов")
    
    if input_path is None:
        input_path = "data/input/reporting"
        
    if output_path is None:
        output_path = "data/output/reporting"
    
    # Создание директорий если они не существуют
    Path(input_path).mkdir(parents=True, exist_ok=True)
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Входная директория: {input_path}")
    logger.info(f"Выходная директория: {output_path}")
    
    # Проверка наличия входных файлов
    if not os.path.exists(input_path):
        logger.error(f"Входная директория {input_path} не существует")
        return
    
    # Генерация отчетов
    generate_reports(input_path, output_path)
    
    logger.info("Генерация отчетов завершена")

def generate_reports(input_path, output_path):
    """
    Генерация отчетов по результатам обработки данных
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Начало генерации отчетов")
    
    # Поиск файлов результатов обработки данных
    result_files = {}
    modalities = ['genomics', 'transcriptomics', 'mirna', 'proteomics', 'metabolomics', 'integration', 'quality_control']
    
    for modality in modalities:
        modality_path = os.path.join(input_path, modality)
        if os.path.exists(modality_path):
            result_files[modality] = []
            for root, dirs, files in os.walk(modality_path):
                for file in files:
                    if file.endswith((".tsv", ".csv", ".txt", ".vcf", ".bam", ".h5ad")):
                        result_files[modality].append(os.path.join(root, file))
    
    # Вывод информации о найденных файлах
    for modality, files in result_files.items():
        logger.info(f"Найдено файлов результатов {modality}: {len(files)}")
    
    # Генерация отчетов для каждой модальности
    for modality, files in result_files.items():
        if files:
            generate_modality_report(modality, files, output_path)
    
    # Генерация сводного отчета
    generate_summary_report(result_files, output_path)

def generate_modality_report(modality, files, output_path):
    """
    Генерация отчета для конкретной модальности
    
    Args:
        modality (str): Модальность данных
        files (list): Список файлов результатов
        output_path (str): Путь к выходным данным
    """
    logger.info(f"Генерация отчета для модальности: {modality}")
    
    # Создание директории для отчетов модальности
    modality_report_path = os.path.join(output_path, modality)
    Path(modality_report_path).mkdir(parents=True, exist_ok=True)
    
    # Создание отчета в формате Markdown
    report_content = f"# Отчет по модальности {modality}\n\n"
    report_content += f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Добавление информации о файлах
    report_content += "## Обработанные файлы\n\n"
    for i, file in enumerate(files, 1):
        report_content += f"{i}. {os.path.basename(file)}\n"
    
    report_content += f"\nВсего файлов: {len(files)}\n\n"
    
    # Добавление статистики (если доступна)
    stats = collect_statistics(modality, files)
    if stats:
        report_content += "## Статистика обработки\n\n"
        for key, value in stats.items():
            report_content += f"- {key}: {value}\n"
        report_content += "\n"
    
    # Сохранение отчета
    report_file = os.path.join(modality_report_path, f"{modality}_report.md")
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Сохранен отчет по модальности {modality}: {report_file}")
    except Exception as e:
        logger.error(f"Ошибка сохранения отчета по модальности {modality}: {e}")
    
    # Генерация графиков (если возможно)
    generate_charts(modality, files, modality_report_path)

def collect_statistics(modality, files):
    """
    Сбор статистики по обработанным файлам
    
    Args:
        modality (str): Модальность данных
        files (list): Список файлов результатов
        
    Returns:
        dict: Словарь со статистикой
    """
    stats = {}
    
    try:
        # Базовая статистика по файлам
        stats['Общее количество файлов'] = len(files)
        
        # Статистика по размерам файлов
        total_size = 0
        for file in files:
            if os.path.exists(file):
                total_size += os.path.getsize(file)
        
        stats['Общий размер файлов (МБ)'] = round(total_size / (1024 * 1024), 2)
        
        # Дополнительная статистика в зависимости от модальности
        if modality == 'quality_control':
            # Статистика по отчетам контроля качества
            passed_checks = 0
            warning_checks = 0
            failed_checks = 0
            
            for file in files:
                if file.endswith('.tsv'):
                    try:
                        df = pd.read_csv(file, sep='\t')
                        if 'status' in df.columns:
                            passed_checks += len(df[df['status'] == 'passed'])
                            warning_checks += len(df[df['status'] == 'warning'])
                            failed_checks += len(df[df['status'] == 'failed'])
                    except Exception as e:
                        logger.warning(f"Ошибка чтения файла QC {file}: {e}")
            
            stats['Пройденные проверки'] = passed_checks
            stats['Предупреждения'] = warning_checks
            stats['Проваленные проверки'] = failed_checks
            
    except Exception as e:
        logger.error(f"Ошибка сбора статистики для модальности {modality}: {e}")
    
    return stats

def generate_charts(modality, files, output_path):
    """
    Генерация графиков для отчета
    
    Args:
        modality (str): Модальность данных
        files (list): Список файлов результатов
        output_path (str): Путь к выходным данным
    """
    logger.info(f"Генерация графиков для модальности: {modality}")
    
    try:
        # Создание графика распределения размеров файлов
        file_sizes = []
        file_names = []
        
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file) / (1024 * 1024)  # Размер в МБ
                file_sizes.append(size)
                file_names.append(os.path.basename(file)[:20])  # Укороченное имя файла
        
        if file_sizes:
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(file_sizes)), file_sizes)
            plt.xlabel('Файлы')
            plt.ylabel('Размер (МБ)')
            plt.title(f'Распределение размеров файлов ({modality})')
            plt.xticks(range(len(file_names)), file_names, rotation=45, ha='right')
            plt.tight_layout()
            
            chart_file = os.path.join(output_path, f"{modality}_file_sizes.png")
            plt.savefig(chart_file, dpi=300)
            plt.close()
            logger.info(f"Сохранен график размеров файлов: {chart_file}")
            
    except Exception as e:
        logger.error(f"Ошибка генерации графиков для модальности {modality}: {e}")

def generate_summary_report(result_files, output_path):
    """
    Генерация сводного отчета
    
    Args:
        result_files (dict): Словарь с файлами результатов по модальностям
        output_path (str): Путь к выходным данным
    """
    logger.info("Генерация сводного отчета")
    
    # Создание отчета в формате Markdown
    report_content = "# Сводный отчет по обработке данных\n\n"
    report_content += f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Добавление информации по модальностям
    report_content += "## Сводная информация по модальностям\n\n"
    report_content += "| Модальность | Количество файлов | Общий размер (МБ) |\n"
    report_content += "|-------------|-------------------|------------------|\n"
    
    total_files = 0
    total_size = 0
    
    for modality, files in result_files.items():
        file_count = len(files)
        modality_size = 0
        
        for file in files:
            if os.path.exists(file):
                modality_size += os.path.getsize(file) / (1024 * 1024)
        
        total_files += file_count
        total_size += modality_size
        
        report_content += f"| {modality} | {file_count} | {modality_size:.2f} |\n"
    
    report_content += f"\n**Итого:** | **{total_files}** | **{total_size:.2f}** |\n\n"
    
    # Добавление информации о контрольных проверках (если доступны)
    qc_files = result_files.get('quality_control', [])
    if qc_files:
        passed_checks = 0
        warning_checks = 0
        failed_checks = 0
        
        for qc_file in qc_files:
            if qc_file.endswith('.tsv'):
                try:
                    df = pd.read_csv(qc_file, sep='\t')
                    if 'status' in df.columns:
                        passed_checks += len(df[df['status'] == 'passed'])
                        warning_checks += len(df[df['status'] == 'warning'])
                        failed_checks += len(df[df['status'] == 'failed'])
                except Exception as e:
                    logger.warning(f"Ошибка чтения файла QC {qc_file}: {e}")
        
        report_content += "## Сводная статистика контроля качества\n\n"
        report_content += f"- Пройденные проверки: {passed_checks}\n"
        report_content += f"- Предупреждения: {warning_checks}\n"
        report_content += f"- Проваленные проверки: {failed_checks}\n\n"
    
    # Сохранение сводного отчета
    summary_report_file = os.path.join(output_path, "summary_report.md")
    try:
        with open(summary_report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Сохранен сводный отчет: {summary_report_file}")
    except Exception as e:
        logger.error(f"Ошибка сохранения сводного отчета: {e}")

if __name__ == "__main__":
    process()