#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль диагональной интеграции данных
Объединяет данные различных модальностей
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
    Основная функция диагональной интеграции данных
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Запуск модуля диагональной интеграции данных")
    
    if input_path is None:
        input_path = "data/input/integration"
        
    if output_path is None:
        output_path = "data/output/integration"
    
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
    integrate_data(input_path, output_path)
    
    logger.info("Диагональная интеграция данных завершена")

def integrate_data(input_path, output_path):
    """
    Интеграция данных различных модальностей
    
    Args:
        input_path (str): Путь к входным данным
        output_path (str): Путь к выходным данным
    """
    logger.info("Начало диагональной интеграции данных")
    
    # Поиск файлов данных различных модальностей
    data_files = {}
    modalities = ['genomics', 'transcriptomics', 'mirna', 'proteomics', 'metabolomics']
    
    for modality in modalities:
        modality_path = os.path.join(input_path, modality)
        if os.path.exists(modality_path):
            data_files[modality] = []
            for root, dirs, files in os.walk(modality_path):
                for file in files:
                    if file.endswith(".tsv") or file.endswith(".csv") or file.endswith(".txt"):
                        data_files[modality].append(os.path.join(root, file))
    
    # Вывод информации о найденных файлах
    for modality, files in data_files.items():
        logger.info(f"Найдено файлов {modality}: {len(files)}")
    
    # Интеграция данных
    integrated_data = perform_integration(data_files, output_path)
    
    # Сохранение интегрированных данных
    save_integrated_data(integrated_data, output_path)

def perform_integration(data_files, output_path):
    """
    Выполнение интеграции данных
    
    Args:
        data_files (dict): Словарь с файлами данных по модальностям
        output_path (str): Путь к выходным данным
        
    Returns:
        dict: Интегрированные данные
    """
    logger.info("Выполнение интеграции данных")
    
    integrated_data = {}
    
    # Загрузка данных каждой модальности
    loaded_data = {}
    for modality, files in data_files.items():
        loaded_data[modality] = []
        for file in files:
            try:
                # Попытка загрузки данных
                if file.endswith(".tsv"):
                    df = pd.read_csv(file, sep='\t')
                elif file.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_csv(file, sep='\t')
                
                loaded_data[modality].append((file, df))
                logger.info(f"Загружен файл {file} для модальности {modality}")
            except Exception as e:
                logger.error(f"Ошибка загрузки файла {file}: {e}")
    
    # Создание матрицы интеграции
    integration_matrix = create_integration_matrix(loaded_data)
    
    # Выполнение диагональной интеграции
    integrated_data = diagonal_integration(loaded_data, integration_matrix)
    
    return integrated_data

def create_integration_matrix(loaded_data):
    """
    Создание матрицы интеграции
    
    Args:
        loaded_data (dict): Загруженные данные по модальностям
        
    Returns:
        dict: Матрица интеграции
    """
    logger.info("Создание матрицы интеграции")
    
    # Для демонстрации создаем простую матрицу интеграции
    modalities = list(loaded_data.keys())
    integration_matrix = {}
    
    for i, modality1 in enumerate(modalities):
        integration_matrix[modality1] = {}
        for j, modality2 in enumerate(modalities):
            if i != j:
                # Определяем возможность интеграции между модальностями
                integration_matrix[modality1][modality2] = can_integrate(modality1, modality2)
    
    return integration_matrix

def can_integrate(modality1, modality2):
    """
    Определение возможности интеграции между модальностями
    
    Args:
        modality1 (str): Первая модальность
        modality2 (str): Вторая модальность
        
    Returns:
        bool: Возможность интеграции
    """
    # Простая логика определения возможности интеграции
    # В реальной системе здесь будет более сложная логика
    integration_pairs = [
        ('genomics', 'transcriptomics'),
        ('transcriptomics', 'proteomics'),
        ('proteomics', 'metabolomics'),
        ('mirna', 'transcriptomics')
    ]
    
    return (modality1, modality2) in integration_pairs or (modality2, modality1) in integration_pairs

def diagonal_integration(loaded_data, integration_matrix):
    """
    Выполнение диагональной интеграции
    
    Args:
        loaded_data (dict): Загруженные данные по модальностям
        integration_matrix (dict): Матрица интеграции
        
    Returns:
        dict: Интегрированные данные
    """
    logger.info("Выполнение диагональной интеграции")
    
    integrated_data = {}
    
    # Для демонстрации просто объединяем все данные в один датафрейм
    all_dataframes = []
    modality_labels = []
    
    for modality, files in loaded_data.items():
        for file, df in files:
            all_dataframes.append(df)
            modality_labels.extend([modality] * len(df))
    
    if all_dataframes:
        # Объединение всех датафреймов
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_df['modality'] = modality_labels
        
        integrated_data['combined'] = combined_df
    
    return integrated_data

def save_integrated_data(integrated_data, output_path):
    """
    Сохранение интегрированных данных
    
    Args:
        integrated_data (dict): Интегрированные данные
        output_path (str): Путь к выходным данным
    """
    logger.info("Сохранение интегрированных данных")
    
    for key, data in integrated_data.items():
        output_file = os.path.join(output_path, f"integrated_{key}.tsv")
        try:
            data.to_csv(output_file, sep='\t', index=False)
            logger.info(f"Сохранен файл интегрированных данных: {output_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения файла {output_file}: {e}")

if __name__ == "__main__":
    process()