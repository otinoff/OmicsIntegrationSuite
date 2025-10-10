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
Генератор тестовых данных для проверки модуля транскриптомики
Создает realistic данные для bulk RNA-seq и scRNA-seq
"""

import numpy as np
import pandas as pd
from pathlib import Path
import random

def generate_bulk_rnaseq_data():
    """Генерация тестовых данных bulk RNA-seq"""
    
    # Параметры
    n_genes = 20000  # Количество генов
    n_samples = 12   # Количество образцов
    
    # Создаем имена генов (realistic)
    gene_prefixes = ['ENSG', 'ACTB', 'GAPDH', 'TP53', 'BRCA1', 'EGFR', 'MYC', 'KRAS']
    genes = []
    
    # Добавляем известные гены
    known_genes = [
        'ACTB', 'GAPDH', 'TP53', 'BRCA1', 'EGFR', 'MYC', 'KRAS', 'PTEN',
        'AKT1', 'PIK3CA', 'NRAS', 'BRAF', 'RB1', 'CDKN2A', 'MDM2', 'VEGFA'
    ]
    genes.extend(known_genes)
    
    # Добавляем ENSEMBL-style гены
    for i in range(n_genes - len(known_genes)):
        genes.append(f"ENSG{i+1:08d}")
    
    # Имена образцов
    samples = [f"Sample_{i+1}" for i in range(n_samples)]
    
    # Генерируем матрицу экспрессии
    # Используем логнормальное распределение для реалистичности
    expression_matrix = np.zeros((n_genes, n_samples))
    
    for i in range(n_genes):
        # Базовый уровень экспрессии
        base_expression = np.random.lognormal(mean=5, sigma=2, size=n_samples)
        
        # Добавляем вариабельность между образцами
        sample_effects = np.random.normal(1, 0.3, n_samples)
        sample_effects = np.maximum(sample_effects, 0.1)  # Избегаем отрицательных значений
        
        # Финальная экспрессия
        expression_matrix[i] = base_expression * sample_effects
        
        # Добавляем нули для низко экспрессируемых генов
        if np.random.random() < 0.1:  # 10% генов с очень низкой экспрессией
            mask = np.random.random(n_samples) < 0.7
            expression_matrix[i][mask] = 0
    
    # Создаем DataFrame
    df = pd.DataFrame(expression_matrix, index=genes, columns=samples)
    
    return df

def generate_scrna_seq_data():
    """Генерация тестовых данных scRNA-seq"""
    
    # Параметры
    n_genes = 2000   # Количество генов (меньше для scRNA-seq)
    n_cells = 500    # Количество клеток
    
    # Создаем имена генов
    known_genes = [
        'ACTB', 'GAPDH', 'TP53', 'BRCA1', 'CD3D', 'CD4', 'CD8A', 'IL2',
        'IFNG', 'TNF', 'IL10', 'FOXP3', 'GZMB', 'PRF1', 'CD19', 'MS4A1'
    ]
    
    genes = known_genes.copy()
    
    # Добавляем митохондриальные гены (важно для QC)
    mito_genes = [f'MT-{gene}' for gene in ['CO1', 'CO2', 'CO3', 'CYB', 'ND1', 'ND2', 'ND3', 'ND4', 'ND5', 'ND6']]
    genes.extend(mito_genes)
    
    # Добавляем рибосомальные гены
    ribo_genes = [f'RP{s}{i}' for s in ['S', 'L'] for i in range(1, 20)]
    genes.extend(ribo_genes[:20])
    
    # Остальные гены
    for i in range(n_genes - len(genes)):
        genes.append(f"Gene_{i+1:04d}")
    
    # Имена клеток
    cells = [f"Cell_{i+1}" for i in range(n_cells)]
    
    # Генерируем UMI матрицу (sparse, integers)
    umi_matrix = np.zeros((n_genes, n_cells), dtype=int)
    
    for i, gene in enumerate(genes):
        for j in range(n_cells):
            # Вероятность экспрессии зависит от типа гена
            if gene.startswith('MT-'):
                # Митохондриальные гены - высокая экспрессия
                prob_expression = 0.8
                mean_count = 15
            elif gene.startswith('RP'):
                # Рибосомальные гены - высокая экспрессия
                prob_expression = 0.9
                mean_count = 20
            elif gene in known_genes:
                # Известные гены - средняя экспрессия
                prob_expression = 0.4
                mean_count = 8
            else:
                # Обычные гены - низкая экспрессия
                prob_expression = 0.15
                mean_count = 3
            
            # Генерируем UMI counts
            if np.random.random() < prob_expression:
                # Используем негативное биномиальное распределение (realistic для UMI)
                count = np.random.negative_binomial(n=5, p=5/(5+mean_count))
                umi_matrix[i, j] = max(0, count)
    
    # Создаем DataFrame
    df = pd.DataFrame(umi_matrix, index=genes, columns=cells)
    
    return df

def create_test_files():
    """Создание тестовых файлов"""
    
    # Создаем директорию для тестовых данных
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True, parents=True)
    
    print("Генерирую тестовые данные...")
    
    # 1. Bulk RNA-seq данные
    print("[BULK] Создаю bulk RNA-seq данные...")
    bulk_data = generate_bulk_rnaseq_data()
    
    # Сохраняем в разных форматах
    bulk_data.to_csv(test_dir / "bulk_rnaseq_test.csv")
    bulk_data.to_csv(test_dir / "bulk_rnaseq_test.tsv", sep='\t')
    
    print(f"[OK] Bulk RNA-seq: {bulk_data.shape[0]} генов, {bulk_data.shape[1]} образцов")
    
    # 2. scRNA-seq данные
    print("[scRNA] Создаю scRNA-seq данные...")
    scrna_data = generate_scrna_seq_data()
    
    # Сохраняем в CSV формате (гены в строках, клетки в столбцах)
    scrna_data.to_csv(test_dir / "scrna_seq_test.csv")
    scrna_data.to_csv(test_dir / "scrna_seq_test.tsv", sep='\t')
    
    print(f"[OK] scRNA-seq: {scrna_data.shape[0]} генов, {scrna_data.shape[1]} клеток")
    
    # 3. Создаем README с инструкциями
    readme_content = f"""# Тестовые данные для модуля транскриптомики

## Файлы:

### Bulk RNA-seq:
- `bulk_rnaseq_test.csv` - Матрица экспрессии (CSV формат)
- `bulk_rnaseq_test.tsv` - Матрица экспрессии (TSV формат)
- Размер: {bulk_data.shape[0]} генов × {bulk_data.shape[1]} образцов
- Формат: гены в строках, образцы в столбцах

### Single-cell RNA-seq:
- `scrna_seq_test.csv` - UMI матрица (CSV формат)  
- `scrna_seq_test.tsv` - UMI матрица (TSV формат)
- Размер: {scrna_data.shape[0]} генов × {scrna_data.shape[1]} клеток
- Формат: гены в строках, клетки в столбцах
- Включает митохондриальные гены (MT-*) для QC

## Инструкции по использованию:

1. Запустите приложение: `streamlit run web_interface.py --server.port 8502`
2. Выберите модуль "📊 Транскриптомика"
3. Перейдите в таб "📤 Загрузка и настройка"
4. Инициализируйте процессор
5. Для Bulk RNA-seq: загрузите `bulk_rnaseq_test.csv`
6. Для scRNA-seq: загрузите `scrna_seq_test.csv`

## Характеристики данных:

### Bulk RNA-seq:
- Realistic логнормальное распределение экспрессии
- Включает известные гены (TP53, BRCA1, GAPDH и др.)
- Вариабельность между образцами
- Некоторые гены с нулевой экспрессией

### scRNA-seq:
- UMI counts (целые числа)
- Митохондриальные гены для QC анализа
- Рибосомальные гены
- Sparse матрица (много нулей)
- Негативное биномиальное распределение

Данные созданы для демонстрации и тестирования функциональности QC модуля.
"""
    
    with open(test_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n[SUCCESS] Тестовые данные созданы в: {test_dir}")
    print("\n[FILES] Созданные файлы:")
    for file in test_dir.iterdir():
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({size_mb:.2f} MB)")
    
    print(f"\n[README] Инструкции сохранены в: {test_dir}/README.md")
    
    return test_dir

if __name__ == "__main__":
    create_test_files()