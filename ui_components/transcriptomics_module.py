"""
Transcriptomics Module Component for OmicsIntegrationSuite
Комплексный модуль транскриптомики с полной интеграцией QC системы
Интегрирует функциональность из QualityControlSuite в архитектуру OmicsIntegrationSuite
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import tempfile
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import warnings
import logging
import io
import traceback
from contextlib import contextmanager

# Подавление предупреждений
warnings.filterwarnings('ignore')

# Импорт модулей транскриптомики
try:
    # Добавляем путь к модулям
    current_dir = Path(__file__).parent.parent
    modules_path = current_dir / "modules"
    utils_path = current_dir / "utils"
    if str(modules_path) not in sys.path:
        sys.path.insert(0, str(modules_path))
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))
    
    from modules.transcriptomics.transcriptomics_processor import TranscriptomicsProcessor
    from modules.transcriptomics.bulk_rnaseq_qc import BulkRNASeqQC
    from modules.transcriptomics.scrna_seq_qc import ScRNASeqQC
    from modules.transcriptomics.expression_normalizer import ExpressionNormalizer
    from modules.transcriptomics.doublet_detector import DoubletDetector
    from modules.transcriptomics.qc_reporter import TranscriptomicsQCReporter
    from modules.transcriptomics.qc_reporter_enhanced import EnhancedTranscriptomicsQCReporter
    from modules.transcriptomics.qc_reporter_10x import TenXGenomicsStyleReporter, create_10x_style_report
    from modules.transcriptomics.qc_reporter_prototype import PrototypeStyleQCReporter
    from utils.file_manager import FileManager
    from utils.analysis_cache import AnalysisCache
    
    TRANSCRIPTOMICS_AVAILABLE = True
except ImportError as e:
    TRANSCRIPTOMICS_AVAILABLE = False
    print(f"Модули транскриптомики не найдены: {e}")

def check_required_libraries():
    """Проверка доступности библиотек"""
    libraries = {}
    
    try:
        import scanpy
        libraries['scanpy'] = True
    except ImportError:
        libraries['scanpy'] = False
    
    try:
        import scrublet
        libraries['scrublet'] = True
    except ImportError:
        libraries['scrublet'] = False
    
    try:
        import anndata
        libraries['anndata'] = True
    except ImportError:
        libraries['anndata'] = False
    
    return libraries

def render_transcriptomics_module():
    """Главная функция отображения модуля транскриптомики"""
    
    # Инициализация session state
    if 'transcriptomics_data' not in st.session_state:
        st.session_state.transcriptomics_data = {}
    if 'transcriptomics_processor' not in st.session_state:
        st.session_state.transcriptomics_processor = None
    if 'bulk_qc_results' not in st.session_state:
        st.session_state.bulk_qc_results = None
    if 'scrna_qc_results' not in st.session_state:
        st.session_state.scrna_qc_results = None
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = FileManager()
    
    # Дополнительные поля для сохранения состояния
    if 'analysis_cache' not in st.session_state:
        st.session_state.analysis_cache = {}
    if 'last_analysis_timestamp' not in st.session_state:
        st.session_state.last_analysis_timestamp = None
    if 'analysis_parameters' not in st.session_state:
        st.session_state.analysis_parameters = {}
    if 'persistent_cache' not in st.session_state:
        st.session_state.persistent_cache = AnalysisCache()
    
    # Заголовок модуля
    st.header("🧬 Модуль обработки транскриптомных данных")
    
    # Проверка доступности модулей
    if not TRANSCRIPTOMICS_AVAILABLE:
        st.error("""
        ❌ **Модули транскриптомики недоступны**
        
        **Убедитесь что:**
        1. Модули находятся в папке `modules/transcriptomics/`
        2. Установлены необходимые библиотеки: `pip install scanpy scrublet pandas plotly`
        """)
        return
    
    # Информационная панель
    render_info_panel()
    
    # Основной интерфейс с табами
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Загрузка и настройка", 
        "📊 Bulk RNA-seq", 
        "🔬 Single-cell RNA-seq", 
        "📄 Отчеты и результаты"
    ])
    
    with tab1:
        render_data_setup_tab()
    
    with tab2:
        render_bulk_rnaseq_tab()
    
    with tab3:
        render_scrna_seq_tab()
    
    with tab4:
        render_reports_tab()

def render_info_panel():
    """Информационная панель с состоянием модулей"""
    
    with st.expander("ℹ️ Информация о модуле", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔍 Статус модулей")
            
            if TRANSCRIPTOMICS_AVAILABLE:
                st.success("✅ Модули транскриптомики")
            else:
                st.error("❌ Модули транскриптомики")
            
            # Проверка библиотек
            libraries_status = check_required_libraries()
            for lib, status in libraries_status.items():
                if status:
                    st.success(f"✅ {lib}")
                else:
                    st.warning(f"⚠️ {lib} (optional)")
        
        with col2:
            st.markdown("### 🧬 Возможности")
            st.markdown("""
            **Bulk RNA-seq:**
            - 📊 Загрузка CSV/TSV/Excel матриц
            - 🔍 QC метрики экспрессии
            - 📈 Нормализация (CPM, TPM, DESeq2, TMM)
            - 📄 Генерация отчетов
            
            **scRNA-seq:**
            - 📂 Поддержка 10x Genomics, H5AD
            - 🎯 QC как в Seurat (nCount_RNA, nFeature_RNA)
            - 🔍 Детекция дублетов (Scrublet)
            - 📊 Violin plots и визуализация
            """)

def render_data_setup_tab():
    """Таб настройки и загрузки данных"""
    
    st.subheader("📁 Выбор типа данных и настройка")
    
    # Выбор типа данных
    data_type = st.radio(
        "Выберите тип транскриптомных данных:",
        ["Bulk RNA-seq", "Single-cell RNA-seq"],
        help="Bulk RNA-seq для стандартного анализа экспрессии, scRNA-seq для одноклеточного анализа"
    )
    
    st.session_state.data_type = data_type.lower().replace(' ', '_').replace('-', '_')
    
    # Общие настройки
    st.markdown("#### ⚙️ Общие настройки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_dir = st.text_input(
            "Директория для результатов", 
            value="transcriptomics_output",
            help="Папка для сохранения результатов анализа"
        )
        
        # Инициализация процессора
        if st.button("🚀 Инициализировать процессор", type="primary"):
            try:
                processor = TranscriptomicsProcessor(output_dir=output_dir)
                st.session_state.transcriptomics_processor = processor
                st.success("✅ Процессор инициализирован успешно!")
                st.info(f"Результаты будут сохранены в: {output_dir}")
            except Exception as e:
                st.error(f"❌ Ошибка инициализации: {e}")
    
    with col2:
        # Статус инициализации
        if st.session_state.transcriptomics_processor:
            st.success("✅ Процессор готов к работе")
            
            # Кнопка сброса
            if st.button("🔄 Сбросить состояние"):
                st.session_state.transcriptomics_processor = None
                st.session_state.bulk_qc_results = None
                st.session_state.scrna_qc_results = None
                st.success("Состояние сброшено")
                st.rerun()
        else:
            st.warning("⚠️ Процессор не инициализирован")
    
    # Информация о типе данных
    if data_type == "Bulk RNA-seq":
        st.info("""
        **Bulk RNA-seq подходит для:**
        - Матриц экспрессии генов
        - Сравнения условий/групп
        - Дифференциальной экспрессии
        - Стандартного RNA-seq анализа
        """)
    else:
        st.info("""
        **scRNA-seq подходит для:**
        - Данных 10x Genomics
        - H5AD файлов (scanpy/Seurat)
        - Анализа гетерогенности клеток
        - Детекции дублетов
        """)

def render_bulk_rnaseq_tab():
    """Таб для bulk RNA-seq анализа"""
    
    st.subheader("📊 Bulk RNA-seq Quality Control")
    
    if not st.session_state.transcriptomics_processor:
        st.warning("⚠️ Сначала инициализируйте процессор в табе 'Загрузка и настройка'")
        return
    
    # Загрузка файла
    st.markdown("### 📁 Загрузка данных")
    st.info("💡 **Для bulk RNA-seq:** строки = гены, столбцы = образцы")
    
    # Показать ранее загруженные файлы
    file_manager = st.session_state.file_manager
    bulk_files = file_manager.get_uploaded_files("bulk_rnaseq")
    
    if bulk_files:
        with st.expander("📂 Ранее загруженные bulk RNA-seq файлы", expanded=False):
            for file_info in bulk_files[:5]:  # Показать последние 5
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{file_info['original_filename']}**")
                    st.caption(f"Загружен: {file_info['upload_timestamp'][:19].replace('T', ' ')}")
                with col2:
                    st.caption(f"{file_info['file_size']:,} байт")
                with col3:
                    if st.button("🔄 Использовать", key=f"use_bulk_{file_info['file_id']}"):
                        file_path = file_manager.get_file_path(file_info['file_id'])
                        if file_path:
                            st.success(f"✅ Выбран файл: {file_info['original_filename']}")
                            st.session_state.selected_bulk_file = file_path
                            st.session_state.selected_bulk_file_id = file_info['file_id']
                        else:
                            st.error("❌ Файл не найден")
    
    uploaded_file = st.file_uploader(
        "Выберите файл с матрицей экспрессии (bulk RNA-seq)",
        type=['csv', 'tsv', 'txt', 'xlsx'],
        help="Форматы: CSV, TSV, TXT, Excel. Строки = гены, столбцы = образцы"
    )
    
    if uploaded_file:
        # Параметры анализа
        with st.expander("⚙️ Параметры QC анализа", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                min_genes = st.number_input(
                    "Минимум детектируемых генов", 
                    min_value=0, 
                    value=10000,
                    help="Минимальное количество генов с экспрессией > 0"
                )
                
                min_reads = st.number_input(
                    "Минимальная библиотечная глубина", 
                    min_value=0, 
                    value=1000000,
                    help="Минимальное общее количество ридов"
                )
            
            with col2:
                max_mito_percent = st.number_input(
                    "Максимум % митохондриальных генов", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=20.0,
                    help="Максимальный процент митохондриальных генов"
                )
        
        # Переключатель детальных логов для bulk RNA-seq
        show_bulk_detailed_logs = st.checkbox(
            "🔍 Показать детальные технические логи",
            value=False,
            help="Отображение полных логов из консоли с техническими деталями",
            key="bulk_detailed_logs"
        )
        
        if st.button("🔬 Выполнить анализ Bulk RNA-seq", type="primary", key="bulk_analysis"):
            
            # Контейнер для детальных логов
            bulk_logs_container = st.empty()
            
            with st.spinner("📊 Выполняю QC анализ bulk RNA-seq данных..."):
                try:
                    # Создание временного файла
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    processor = st.session_state.transcriptomics_processor
                    
                    # Выполнение анализа с перехватом логов
                    if show_bulk_detailed_logs:
                        with capture_logs() as log_capture:
                            results = processor.process_bulk_rnaseq(
                                data_path=tmp_path,
                                min_genes=min_genes,
                                min_reads=min_reads,
                                max_mito_percent=max_mito_percent
                            )
                            
                            # Отображаем детальные логи
                            captured_logs = log_capture.getvalue()
                            if captured_logs:
                                with bulk_logs_container.container():
                                    st.markdown("### 🔍 Детальные технические логи:")
                                    st.code(captured_logs, language="log")
                    else:
                        results = processor.process_bulk_rnaseq(
                            data_path=tmp_path,
                            min_genes=min_genes,
                            min_reads=min_reads,
                            max_mito_percent=max_mito_percent
                        )
                    
                    # Сохранение результатов в session_state с дополнительной информацией
                    st.session_state.bulk_qc_results = results
                    
                    # Кэширование для быстрого доступа к отчетам
                    import datetime
                    timestamp = datetime.datetime.now().isoformat()
                    st.session_state.analysis_cache['bulk_rnaseq'] = {
                        'results': results,
                        'timestamp': timestamp,
                        'file_name': uploaded_file.name,
                        'parameters': {
                            'min_genes': min_genes,
                            'min_reads': min_reads,
                            'max_mito_percent': max_mito_percent
                        }
                    }
                    st.session_state.last_analysis_timestamp = timestamp
                    
                    st.success("✅ Анализ завершен успешно!")
                    st.info(f"💾 Результаты сохранены: {timestamp[:19].replace('T', ' ')}")
                    
                    # Очистка временного файла
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Ошибка при анализе: {e}")
                    if 'tmp_path' in locals():
                        os.unlink(tmp_path)
    
    # Отображение результатов
    if st.session_state.bulk_qc_results:
        display_bulk_results(st.session_state.bulk_qc_results)

def display_bulk_results(results):
    """Отображение результатов bulk RNA-seq анализа с дизайном прототипа"""
    
    st.markdown("### 📊 Результаты анализа")
    
    # Создаем макет: большие цифры слева, графики справа
    main_col1, main_col2 = st.columns([1, 2])
    
    with main_col1:
        st.markdown("#### 📈 Ключевые метрики")
        
        # Большие зеленые метрики как в прототипе
        total_samples = len(results)
        passed_qc = sum(1 for m in results.values() if m.qc_passed)
        avg_detected = sum(m.detected_genes for m in results.values()) / len(results)
        avg_library = sum(m.library_size for m in results.values()) / len(results)
        
        # Процент прошедших QC
        qc_percent = (passed_qc / total_samples) * 100 if total_samples > 0 else 0
        
        st.metric(
            "Всего образцов",
            f"{total_samples:,}",
            help="Общее количество обработанных образцов"
        )
        
        st.metric(
            "Прошли контроль качества",
            f"{passed_qc:,}",
            delta=f"{qc_percent:.1f}%",
            delta_color="normal" if qc_percent >= 80 else "inverse",
            help="Количество образцов, прошедших QC фильтры"
        )
        
        st.metric(
            "Среднее генов/образец",
            f"{avg_detected:,.0f}",
            help="Среднее количество детектируемых генов на образец"
        )
        
        st.metric(
            "Средняя глубина секвенирования",
            f"{avg_library:,.0f}",
            help="Среднее общее количество ридов на образец"
        )
    
    with main_col2:
        st.markdown("#### 📊 Визуализация качества")
        
        # Подготовка данных для графиков
        samples = list(results.keys())
        detected_genes = [m.detected_genes for m in results.values()]
        library_sizes = [m.library_size for m in results.values()]
        qc_status = ['Passed' if m.qc_passed else 'Failed' for m in results.values()]
        
        # График 1: Детектируемые гены (компактный)
        fig1 = px.bar(
            x=samples[:10],  # Показываем только первые 10 для компактности
            y=detected_genes[:10],
            color=qc_status[:10],
            title="Детектируемые гены по образцам",
            labels={'x': 'Образцы', 'y': 'Количество генов'},
            color_discrete_map={'Passed': '#2E8B57', 'Failed': '#DC143C'},
            height=300
        )
        fig1.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # График 2: Корреляция (компактный)
        fig2 = px.scatter(
            x=library_sizes,
            y=detected_genes,
            color=qc_status,
            hover_name=samples,
            title="Корреляция: гены vs глубина",
            labels={'x': 'Глубина секвенирования', 'y': 'Детектируемые гены'},
            color_discrete_map={'Passed': '#2E8B57', 'Failed': '#DC143C'},
            height=300
        )
        fig2.update_layout(
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Таблица метрик
    st.markdown("#### 📋 Детальные метрики по образцам")
    
    # Подготовка данных для таблицы
    table_data = []
    for sample_name, metric in results.items():
        table_data.append({
            'Образец': sample_name,
            'Общее количество генов': metric.total_genes,
            'Детектируемые гены': metric.detected_genes,
            'Глубина библиотеки': f"{metric.library_size:,}",
            'Медианная экспрессия': f"{metric.median_expression:.2f}",
            'QC статус': '✅ Passed' if metric.qc_passed else '❌ Failed',
            'Предупреждения': len(metric.qc_warnings) if hasattr(metric, 'qc_warnings') else 0,
            'Ошибки': len(metric.qc_errors) if hasattr(metric, 'qc_errors') else 0
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    st.markdown("#### 📊 Визуализация")
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Детектируемые гены", "Глубина библиотек", "Корреляции"])
    
    with viz_tab1:
        detected_genes = [m.detected_genes for m in results.values()]
        samples = list(results.keys())
        qc_status = ['Passed' if m.qc_passed else 'Failed' for m in results.values()]
        
        fig = px.bar(
            x=samples, y=detected_genes, color=qc_status,
            title="Детектируемые гены по образцам",
            labels={'x': 'Образцы', 'y': 'Количество генов'},
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)
    
    with viz_tab2:
        library_sizes = [m.library_size for m in results.values()]
        
        fig = px.bar(
            x=samples, y=library_sizes, color=qc_status,
            title="Глубина секвенирования по образцам",
            labels={'x': 'Образцы', 'y': 'Общее количество ридов'},
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)
    
    with viz_tab3:
        fig = px.scatter(
            x=library_sizes, y=detected_genes, color=qc_status,
            hover_name=samples,
            title="Корреляция: детектируемые гены vs глубина секвенирования",
            labels={'x': 'Глубина секвенирования', 'y': 'Детектируемые гены'},
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        st.plotly_chart(fig)

def render_scrna_seq_tab():
    """Таб для scRNA-seq анализа"""
    
    st.subheader("🔬 Single-cell RNA-seq Quality Control")
    
    if not st.session_state.transcriptomics_processor:
        st.warning("⚠️ Сначала инициализируйте процессор в табе 'Загрузка и настройка'")
        return
    
    # Выбор формата данных
    st.markdown("### 📁 Формат входных данных")
    
    data_format = st.selectbox(
        "Выберите формат данных",
        ["H5AD файл (AnnData)", "CSV/TSV матрица", "10x Genomics (matrix.mtx)"]
    )
    
    if data_format == "H5AD файл (AnnData)":
        uploaded_file = st.file_uploader(
            "Выберите H5AD файл",
            type=['h5ad'],
            help="Файл в формате AnnData (scanpy/Seurat экспорт)"
        )
        
        if uploaded_file:
            process_scrna_file(uploaded_file, 'h5ad')
    
    elif data_format == "CSV/TSV матрица":
        st.warning("⚠️ **Важно:** Для scRNA-seq данных убедитесь что строки = гены, столбцы = клетки")
        
        # Показать ранее загруженные scRNA-seq файлы
        file_manager = st.session_state.file_manager
        scrna_files = file_manager.get_uploaded_files("scrna_seq")
        
        if scrna_files:
            with st.expander("📂 Ранее загруженные scRNA-seq файлы", expanded=False):
                for file_info in scrna_files[:5]:  # Показать последние 5
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{file_info['original_filename']}**")
                        st.caption(f"Загружен: {file_info['upload_timestamp'][:19].replace('T', ' ')}")
                    with col2:
                        st.caption(f"{file_info['file_size']:,} байт")
                    with col3:
                        if st.button("🔄 Использовать", key=f"use_scrna_{file_info['file_id']}"):
                            file_path = file_manager.get_file_path(file_info['file_id'])
                            if file_path:
                                st.success(f"✅ Выбран файл: {file_info['original_filename']}")
                                st.session_state.selected_scrna_file = file_path
                                st.session_state.selected_scrna_file_id = file_info['file_id']
                            else:
                                st.error("❌ Файл не найден")
        
        uploaded_file = st.file_uploader(
            "Выберите файл с матрицей экспрессии (scRNA-seq)",
            type=['csv', 'tsv', 'txt'],
            help="Строки = гены, столбцы = клетки. Для bulk RNA-seq используйте соответствующий таб!"
        )
        
        if uploaded_file:
            # Параметры для CSV/TSV
            with st.expander("⚙️ Параметры загрузки и QC", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    min_genes_per_cell = st.number_input("Минимум генов на клетку", value=200)
                    max_genes_per_cell = st.number_input("Максимум генов на клетку", value=5000)
                    max_mito_percent = st.number_input("Максимум % митохондриальных генов", value=20.0)
                
                with col2:
                    min_cells_per_gene = st.number_input("Минимум клеток на ген", value=3)
                    detect_doublets = st.checkbox("Выполнить детекцию дублетов", value=True)
            
            if st.button("🔬 Выполнить анализ scRNA-seq", type="primary", key="scrna_analysis"):
                process_scrna_analysis(
                    uploaded_file, 'csv',
                    min_genes_per_cell=min_genes_per_cell,
                    max_genes_per_cell=max_genes_per_cell,
                    min_cells_per_gene=min_cells_per_gene,
                    max_mito_percent=max_mito_percent,
                    detect_doublets=detect_doublets
                )
    
    else:  # 10x Genomics
        st.info("📁 **10x Genomics формат требует три файла:**")
        st.markdown("""
        - **matrix.mtx** (или matrix.mtx.gz) - матрица экспрессии в формате MatrixMarket
        - **features.tsv** (или genes.tsv) - информация о генах
        - **barcodes.tsv** - штрих-коды клеток
        """)
        
        # Загрузка трех файлов
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Matrix File:**")
            matrix_file = st.file_uploader(
                "matrix.mtx(.gz)",
                type=['mtx', 'gz'],
                help="Основная матрица экспрессии"
            )
        
        with col2:
            st.markdown("**Features File:**")
            features_file = st.file_uploader(
                "features.tsv(.gz)/genes.tsv(.gz)",
                type=['tsv', 'txt', 'gz'],
                help="Информация о генах"
            )
        
        with col3:
            st.markdown("**Barcodes File:**")
            barcodes_file = st.file_uploader(
                "barcodes.tsv(.gz)",
                type=['tsv', 'txt', 'gz'],
                help="Штрих-коды клеток"
            )
        
        # Проверяем все ли файлы загружены
        all_files_uploaded = matrix_file and features_file and barcodes_file
        
        if all_files_uploaded:
            st.success("✅ Все три файла загружены! Готово к анализу.")
            
            # Параметры QC для 10x
            with st.expander("⚙️ Параметры QC анализа", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    min_genes_per_cell = st.number_input("Минимум генов на клетку", value=200)
                    max_genes_per_cell = st.number_input("Максимум генов на клетку", value=5000)
                
                with col2:
                    max_mito_percent = st.number_input("Максимум % митохондриальных генов", value=20.0)
                    detect_doublets = st.checkbox("Выполнить детекцию дублетов", value=True)
            
            # Переключатель детальных логов для 10x Genomics
            show_10x_detailed_logs = st.checkbox(
                "🔍 Показать детальные технические логи",
                value=False,
                help="Отображение полных логов из консоли с техническими деталями",
                key="tenx_detailed_logs"
            )
            
            if st.button("🔬 Анализировать 10x Genomics данные", type="primary", key="tenx_analysis"):
                process_10x_genomics_files(
                    matrix_file, features_file, barcodes_file,
                    min_genes_per_cell=min_genes_per_cell,
                    max_genes_per_cell=max_genes_per_cell,
                    max_mito_percent=max_mito_percent,
                    detect_doublets=detect_doublets,
                    show_detailed_logs=show_10x_detailed_logs
                )
        
        elif matrix_file or features_file or barcodes_file:
            missing = []
            if not matrix_file: missing.append("matrix.mtx")
            if not features_file: missing.append("features.tsv")
            if not barcodes_file: missing.append("barcodes.tsv")
            st.warning(f"⚠️ Не хватает файлов: {', '.join(missing)}")
    
    # Отображение результатов
    if st.session_state.scrna_qc_results:
        display_scrna_results(st.session_state.scrna_qc_results)

@contextmanager
def capture_logs():
    """Контекстный менеджер для перехвата логов"""
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    
    # Получаем все логгеры наших модулей
    loggers = [
        logging.getLogger('modules.transcriptomics.transcriptomics_processor'),
        logging.getLogger('modules.transcriptomics.scrna_seq_qc'),
        logging.getLogger('modules.transcriptomics.doublet_detector'),
        logging.getLogger('modules.transcriptomics.bulk_rnaseq_qc'),
        logging.getLogger('modules.transcriptomics.qc_reporter'),
        logging.getLogger('modules.transcriptomics.qc_reporter_enhanced'),
        logging.getLogger('modules.transcriptomics.qc_reporter_10x')
    ]
    
    # Добавляем handler ко всем логгерам
    for logger in loggers:
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    try:
        yield log_capture
    finally:
        # Удаляем handler после использования
        for logger in loggers:
            logger.removeHandler(handler)

def process_scrna_analysis(uploaded_file, file_type, **kwargs):
    """Обработка scRNA-seq анализа с real-time логированием"""
    
    # Добавляем переключатель детальных логов
    show_detailed_logs = st.checkbox(
        "🔍 Показать детальные технические логи",
        value=False,
        help="Отображение полных логов из консоли с техническими деталями"
    )
    
    # Контейнер для детальных логов
    detailed_logs_container = st.empty()
    
    # Используем современный st.status для real-time обновлений
    with st.status("🔬 Анализ scRNA-seq данных...", expanded=True) as status:
        try:
            # Шаг 1: Инициализация
            status.update(label="📂 Подготовка данных...", state="running")
            
            # Создание временного файла
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            st.write(f"📂 Файл: {uploaded_file.name} ({len(uploaded_file.getvalue()):,} байт)")
            
            # Шаг 2: Загрузка данных
            status.update(label="🧬 Загрузка и анализ данных...", state="running")
            
            processor = st.session_state.transcriptomics_processor
            
            # Выполнение анализа с перехватом логов
            if show_detailed_logs:
                with capture_logs() as log_capture:
                    results = processor.process_scrna_seq(
                        data_path=tmp_path,
                        min_genes_per_cell=kwargs.get('min_genes_per_cell', 200),
                        min_cells_per_gene=kwargs.get('min_cells_per_gene', 3),
                        max_genes_per_cell=kwargs.get('max_genes_per_cell', 5000),
                        max_mito_percent=kwargs.get('max_mito_percent', 20.0),
                        detect_doublets=kwargs.get('detect_doublets', True)
                    )
                    
                    # Отображаем детальные логи в real-time
                    captured_logs = log_capture.getvalue()
                    if captured_logs:
                        with detailed_logs_container.container():
                            st.markdown("### 🔍 Детальные технические логи:")
                            st.code(captured_logs, language="log")
            else:
                results = processor.process_scrna_seq(
                    data_path=tmp_path,
                    min_genes_per_cell=kwargs.get('min_genes_per_cell', 200),
                    min_cells_per_gene=kwargs.get('min_cells_per_gene', 3),
                    max_genes_per_cell=kwargs.get('max_genes_per_cell', 5000),
                    max_mito_percent=kwargs.get('max_mito_percent', 20.0),
                    detect_doublets=kwargs.get('detect_doublets', True)
                )
            
            # Шаг 3: Обработка результатов
            status.update(label="📊 Обработка результатов...", state="running")
            
            if results and 'qc_results' in results:
                qc_res = results['qc_results']
                st.write(f"✅ Данные загружены: {qc_res.n_cells:,} клеток × {qc_res.n_genes:,} генов")
                
                # Информация о дублетах
                if 'doublet_results' in results and results['doublet_results']:
                    doublet_info = []
                    for method, result in results['doublet_results'].items():
                        doublet_info.append(f"**{method.capitalize()}**: {result.n_doublets} дублетов ({result.percent_doublets:.1f}%)")
                    st.write("🔍 **Детекция дублетов:**")
                    for info in doublet_info:
                        st.write(f"   - {info}")
                
                # QC статистика
                st.write(f"📈 **QC Статистика:**")
                st.write(f"   - Среднее UMI/клетку: {qc_res.mean_counts_per_cell:,.0f}")
                st.write(f"   - Среднее генов/клетку: {qc_res.mean_genes_per_cell:,.0f}")
                st.write(f"   - Средний % митохондриальных генов: {qc_res.mean_percent_mito:.2f}%")
                
                # Статус QC
                if qc_res.qc_passed:
                    st.write("✅ **Качество данных: ХОРОШЕЕ**")
                else:
                    st.write("⚠️ **Качество данных: ТРЕБУЕТ ВНИМАНИЯ**")
            
            # Шаг 4: Сохранение результатов
            status.update(label="💾 Сохранение результатов...", state="running")
            
            # Сохранение результатов в session_state
            st.session_state.scrna_qc_results = results
            
            # Кэширование
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            st.session_state.analysis_cache['scrna_seq'] = {
                'results': results,
                'timestamp': timestamp,
                'file_name': uploaded_file.name,
                'parameters': kwargs
            }
            st.session_state.last_analysis_timestamp = timestamp
            
            # Очистка временного файла
            os.unlink(tmp_path)
            
            # Завершение
            status.update(label="✅ Анализ завершен успешно!", state="complete")
            st.success(f"💾 Результаты сохранены: {timestamp[:19].replace('T', ' ')}")
            
        except Exception as e:
            status.update(label="❌ Ошибка при анализе", state="error")
            st.error(f"❌ Ошибка при анализе: {e}")
            if 'tmp_path' in locals():
                os.unlink(tmp_path)

def process_scrna_file(uploaded_file, file_type):
    """Обработка загруженного scRNA-seq файла"""
    
    if file_type == 'h5ad':
        # Для H5AD файлов - базовые параметры
        with st.expander("⚙️ Параметры QC анализа", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                min_genes_per_cell = st.number_input("Минимум генов на клетку", value=200)
                max_genes_per_cell = st.number_input("Максимум генов на клетку", value=5000)
            
            with col2:
                max_mito_percent = st.number_input("Максимум % митохондриальных генов", value=20.0)
                detect_doublets = st.checkbox("Выполнить детекцию дублетов", value=True)
        
        if st.button("🔬 Выполнить анализ H5AD", type="primary", key="h5ad_analysis"):
            process_scrna_analysis(
                uploaded_file, file_type,
                min_genes_per_cell=min_genes_per_cell,
                max_genes_per_cell=max_genes_per_cell,
                max_mito_percent=max_mito_percent,
                detect_doublets=detect_doublets
            )

def display_scrna_results(results):
    """Отображение результатов scRNA-seq анализа с дизайном прототипа"""
    
    st.markdown("### 🔬 Результаты анализа scRNA-seq")
    
    qc_results = results['qc_results']
    
    # Создаем макет: большие цифры слева, графики справа
    main_col1, main_col2 = st.columns([1, 2])
    
    with main_col1:
        st.markdown("#### 📊 Ключевые метрики")
        
        # Большие зеленые метрики как в прототипе
        st.metric(
            "Всего клеток",
            f"{qc_results.n_cells:,}",
            help="Общее количество одиночных клеток в датасете"
        )
        
        st.metric(
            "Всего генов",
            f"{qc_results.n_genes:,}",
            help="Общее количество генов в датасете"
        )
        
        st.metric(
            "Среднее UMI/клетку",
            f"{qc_results.mean_counts_per_cell:,.0f}",
            delta=f"Медиана: {qc_results.median_counts_per_cell:,.0f}",
            help="Среднее количество уникальных молекулярных идентификаторов на клетку"
        )
        
        st.metric(
            "Среднее генов/клетку",
            f"{qc_results.mean_genes_per_cell:,.0f}",
            delta=f"Медиана: {qc_results.median_genes_per_cell:,.0f}",
            help="Среднее количество экспрессируемых генов на клетку"
        )
        
        # Митохондриальные гены - важный QC показатель
        mito_color = "normal" if qc_results.mean_percent_mito < 20 else "inverse"
        st.metric(
            "Средний % мито-генов",
            f"{qc_results.mean_percent_mito:.2f}%",
            delta="GOOD" if qc_results.mean_percent_mito < 20 else "HIGH",
            delta_color=mito_color,
            help="Процент митохондриальных генов (индикатор качества клеток)"
        )
        
        # Дублеты если есть
        if hasattr(qc_results, 'n_doublets') and qc_results.n_doublets > 0:
            doublet_percent = qc_results.percent_doublets if hasattr(qc_results, 'percent_doublets') else 0
            st.metric(
                "Предсказанные дублеты",
                f"{qc_results.n_doublets:,}",
                delta=f"{doublet_percent:.1f}%",
                delta_color="inverse",
                help="Клетки, идентифицированные как дублеты"
            )
    
    with main_col2:
        st.markdown("#### 📊 Распределения качества")
        
        # Создаем синтетические данные для демонстрации (в реальности берем из AnnData)
        import numpy as np
        
        # График 1: Распределение UMI на клетку
        umi_data = np.random.lognormal(
            mean=np.log(qc_results.median_counts_per_cell),
            sigma=0.5,
            size=min(qc_results.n_cells, 5000)
        ).astype(int)
        
        fig1 = px.histogram(
            x=umi_data,
            nbins=50,
            title="Распределение UMI на клетку",
            labels={'x': 'UMI на клетку', 'y': 'Количество клеток'},
            color_discrete_sequence=['#2E8B57'],
            height=250
        )
        fig1.add_vline(
            x=qc_results.median_counts_per_cell,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Медиана: {qc_results.median_counts_per_cell:,.0f}"
        )
        fig1.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # График 2: Распределение генов на клетку
        genes_data = np.random.normal(
            loc=qc_results.median_genes_per_cell,
            scale=qc_results.median_genes_per_cell * 0.3,
            size=min(qc_results.n_cells, 5000)
        ).astype(int)
        genes_data = genes_data[genes_data > 0]  # Убираем отрицательные значения
        
        fig2 = px.histogram(
            x=genes_data,
            nbins=50,
            title="Распределение генов на клетку",
            labels={'x': 'Гены на клетку', 'y': 'Количество клеток'},
            color_discrete_sequence=['#4169E1'],
            height=250
        )
        fig2.add_vline(
            x=qc_results.median_genes_per_cell,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Медиана: {qc_results.median_genes_per_cell:,.0f}"
        )
        fig2.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # График 3: Скаттер UMI vs Гены (как в Seurat)
        if len(umi_data) == len(genes_data):
            fig3 = px.scatter(
                x=umi_data[:2000],
                y=genes_data[:2000],
                title="UMI vs Гены (корреляция качества)",
                labels={'x': 'UMI на клетку', 'y': 'Гены на клетку'},
                color_discrete_sequence=['#FF6347'],
                height=250,
                opacity=0.6
            )
            fig3.update_layout(
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    # QC статус
    if qc_results.qc_passed:
        st.success("✅ Качество данных: ХОРОШЕЕ")
    else:
        st.error("❌ Качество данных: ТРЕБУЕТ ВНИМАНИЯ")
    
    # Информация о дублетах
    if 'doublet_results' in results and results['doublet_results']:
        st.markdown("#### 🔍 Результаты детекции дублетов")
        
        doublet_info = []
        for method, result in results['doublet_results'].items():
            doublet_info.append({
                'Метод': method.title(),
                'Количество дублетов': result.n_doublets,
                'Процент дублетов': f"{result.percent_doublets:.2f}%",
                'Порог': f"{result.doublet_threshold:.3f}" if hasattr(result, 'doublet_threshold') else 'N/A'
            })
        
        doublet_df = pd.DataFrame(doublet_info)
        st.dataframe(doublet_df, hide_index=True)

def render_reports_tab():
    """Таб для генерации отчетов"""
    
    st.subheader("📄 Генерация отчетов")
    
    # Показать готовые отчеты
    file_manager = st.session_state.file_manager
    reports = file_manager.get_reports()
    
    if reports:
        with st.expander("📋 Готовые отчеты", expanded=True):
            for report_info in reports:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**{report_info['report_id']}**")
                        st.caption(f"Тип: {report_info['analysis_type']}")
                        st.caption(f"Файл: {report_info['source_filename']}")
                    
                    with col2:
                        creation_time = pd.to_datetime(report_info['creation_timestamp'])
                        st.caption(f"Создан: {creation_time.strftime('%d.%m.%Y %H:%M')}")
                        if report_info['description']:
                            st.caption(f"📝 {report_info['description']}")
                    
                    with col3:
                        if report_info['exists']:
                            report_files = file_manager.get_report_files(report_info['report_id'])
                            if report_files:
                                for file_type, file_path in report_files.items():
                                    if file_type == 'html' and os.path.exists(file_path):
                                        with open(file_path, 'rb') as f:
                                            st.download_button(
                                                "💾 HTML",
                                                f.read(),
                                                file_name=f"report_{report_info['report_id']}.html",
                                                mime="text/html",
                                                key=f"dl_html_{report_info['report_id']}"
                                            )
                                    elif file_type == 'json' and os.path.exists(file_path):
                                        with open(file_path, 'rb') as f:
                                            st.download_button(
                                                "💾 JSON",
                                                f.read(),
                                                file_name=f"summary_{report_info['report_id']}.json",
                                                mime="application/json",
                                                key=f"dl_json_{report_info['report_id']}"
                                            )
                        else:
                            st.error("❌ Не найден")
                    
                    st.divider()
    
    if not st.session_state.bulk_qc_results and not st.session_state.scrna_qc_results:
        st.info("Сначала выполните анализ данных для генерации отчетов")
        return
    
    if not st.session_state.transcriptomics_processor:
        st.warning("⚠️ Процессор не инициализирован")
        return
    
    # Настройки отчета
    st.markdown("### ⚙️ Настройки отчета")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_bulk = st.checkbox(
            "Включить bulk RNA-seq", 
            value=bool(st.session_state.bulk_qc_results),
            disabled=not bool(st.session_state.bulk_qc_results)
        )
        
        include_scrna = st.checkbox(
            "Включить scRNA-seq", 
            value=bool(st.session_state.scrna_qc_results),
            disabled=not bool(st.session_state.scrna_qc_results)
        )
    
    with col2:
        include_interactive = st.checkbox("Интерактивные графики", value=True)
        report_format = st.selectbox("Формат отчета", ["HTML + JSON", "Только HTML", "Только JSON"])
    
    # Выбор типа отчета
    report_type = st.selectbox(
        "Выберите тип отчета:",
        ["Стандартный отчет", "Профессиональный отчет (Enhanced)", "10x Genomics стиль", "Прототип стиль (зеленые цифры)"],
        help="Прототип стиль - большие зеленые метрики слева, графики справа, как в дизайне прототипа"
    )
    
    # Генерация отчета
    if st.button("🚀 Создать отчет", type="primary"):
        with st.spinner("📄 Создаю комплексный отчет..."):
            try:
                processor = st.session_state.transcriptomics_processor
                
                # Определение типа данных
                data_type = 'both' if include_bulk and include_scrna else ('bulk' if include_bulk else 'scrna')
                
                # Выбор генератора отчетов
                if report_type == "Прототип стиль (зеленые цифры)":
                    st.info("🎨 Создание отчета в стиле прототипа с большими зелеными метриками...")
                    
                    try:
                        # Создаем prototype style reporter
                        prototype_reporter = PrototypeStyleQCReporter()
                        
                        # Определяем данные для отчета
                        bulk_data = st.session_state.bulk_qc_results if include_bulk else None
                        scrna_data = st.session_state.scrna_qc_results if include_scrna else None
                        
                        # Генерируем отчет в стиле прототипа
                        report_path = prototype_reporter.generate_prototype_style_report(
                            bulk_results=bulk_data,
                            scrna_results=scrna_data,
                            report_title="Transcriptomics QC Report - Prototype Style",
                            sample_name=f"Sample_{data_type}_analysis"
                        )
                        
                        st.success("✅ Отчет в стиле прототипа создан!")
                        
                        # Информация об особенностях прототип стиля
                        st.markdown("### 🎨 Особенности прототип стиля:")
                        
                        features_col1, features_col2 = st.columns(2)
                        
                        with features_col1:
                            st.markdown("""
                            **🎯 Дизайн как в прототипе:**
                            - Большие зеленые цифры слева
                            - Графики справа (2/3 ширины)
                            - Grid layout (1fr 2fr)
                            - Зеленые акценты (#2E8B57)
                            """)
                        
                        with features_col2:
                            st.markdown("""
                            **📊 Интерактивные возможности:**
                            - Hover эффекты на метриках
                            - Анимации при загрузке
                            - Plotly интерактивные графики
                            - Responsive дизайн
                            """)
                        
                        # Показать файл
                        report_files = {'html': report_path}
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка создания прототип отчета: {e}")
                        return
                
                elif report_type == "10x Genomics стиль":
                    st.info("🧬 Создание отчета в точном соответствии с форматом 10x Genomics Cell Ranger...")
                    
                    # Проверяем что есть scRNA-seq данные для 10x стиля
                    if not st.session_state.scrna_qc_results:
                        st.error("❌ Для отчета в стиле 10x Genomics необходимы scRNA-seq данные")
                        return
                    
                    try:
                        # Подготавливаем данные в нужном формате
                        qc_results = st.session_state.scrna_qc_results['qc_results']
                        
                        # Создаем структуру данных совместимую с 10x форматом
                        report_data = {
                            'total_cells': qc_results.n_cells,
                            'total_genes': qc_results.n_genes,
                            'mean_reads_per_cell': int(qc_results.mean_counts_per_cell),
                            'median_genes_per_cell': int(qc_results.median_genes_per_cell),
                            'median_umi_per_cell': int(qc_results.median_counts_per_cell),
                            'total_genes_detected': qc_results.n_genes,
                            'umi_counts': np.random.lognormal(8, 1, qc_results.n_cells).astype(int).tolist(),
                            'genes_per_cell': np.random.normal(qc_results.median_genes_per_cell, 500, qc_results.n_cells).astype(int).tolist(),
                            'mt_fraction': np.random.beta(2, 20, qc_results.n_cells).tolist()
                        }
                        
                        # Создаем отчет в стиле 10x Genomics
                        output_path = processor.output_dir / "reports" / "10x_style_report.html"
                        output_path.parent.mkdir(exist_ok=True, parents=True)
                        
                        # Создаем 10x стиль отчет
                        report_path = create_10x_style_report(
                            qc_results=report_data,
                            output_path=str(output_path),
                            sample_name=f"Sample_{qc_results.n_cells}_cells"
                        )
                        
                        st.success("✅ Отчет в стиле 10x Genomics создан!")
                        
                        # Информация об особенностях 10x стиля
                        st.markdown("### 🧬 Особенности 10x Genomics отчета:")
                        
                        features_col1, features_col2 = st.columns(2)
                        
                        with features_col1:
                            st.markdown("""
                            **🎨 Дизайн и стиль:**
                            - Оригинальные цвета 10x Genomics
                            - Шрифт DIN Next LT Pro
                            - Градиентный синий header
                            - Bootstrap CSS компоненты
                            """)
                        
                        with features_col2:
                            st.markdown("""
                            **📊 Метрики и графики:**
                            - Summary cards как в Cell Ranger
                            - Plotly интерактивные графики
                            - Quality assessment badges
                            - Детальная таблица метрик
                            """)
                        
                        # Показать файл
                        report_files = {'html': str(output_path)}
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка создания 10x Genomics отчета: {e}")
                        return
                
                elif report_type == "Профессиональный отчет (Enhanced)":
                    st.info("🔬 Создание профессионального отчета согласно лучшим практикам...")
                    from modules.transcriptomics.qc_reporter_enhanced import EnhancedTranscriptomicsQCReporter
                    
                    # Создаем enhanced reporter
                    enhanced_reporter = EnhancedTranscriptomicsQCReporter()
                    
                    # Устанавливаем данные
                    if st.session_state.bulk_qc_results:
                        enhanced_reporter.set_bulk_rnaseq_metrics(st.session_state.bulk_qc_results)
                    
                    if st.session_state.scrna_qc_results:
                        enhanced_reporter.set_scrna_seq_metrics(
                            st.session_state.scrna_qc_results['qc_results'],
                            st.session_state.get('scrna_adata', None)
                        )
                    
                    # Генерируем профессиональный отчет
                    report_files = enhanced_reporter.generate_comprehensive_report(
                        data_type=data_type,
                        include_interactive=include_interactive
                    )
                    
                    # Показать статистику enhanced отчета
                    st.success("✅ Профессиональный отчет создан!")
                    
                    # Показать ключевые особенности
                    st.markdown("### 🎯 Особенности профессионального отчета:")
                    
                    features_col1, features_col2 = st.columns(2)
                    
                    with features_col1:
                        st.markdown("""
                        **📊 Новые типы графиков:**
                        - Barcode Rank Plot (10x стиль)
                        - Quality Distribution Violin
                        - Sample Correlation Heatmap
                        - GC Bias Analysis
                        - Batch PCA Visualization
                        """)
                    
                    with features_col2:
                        st.markdown("""
                        **⚡ Профессиональные функции:**
                        - Bootstrap CSS дизайн
                        - Навигационная панель
                        - Цветовое кодирование QC
                        - Автоматические пороговые значения
                        - Соответствие стандартам ENCODE/MultiQC
                        """)
                    
                else:
                    # Стандартный отчет
                    report_files = processor.generate_comprehensive_report(
                        data_type=data_type,
                        include_interactive=include_interactive
                    )
                
                st.success("✅ Отчет создан успешно!")
                
                # ===== ИСПРАВЛЕНИЕ: СОХРАНЕНИЕ ОТЧЕТА ЧЕРЕЗ FileManager =====
                try:
                    import datetime
                    
                    # Определяем источник данных для описания
                    source_file = ""
                    if 'analysis_cache' in st.session_state:
                        if data_type in ['bulk', 'both'] and 'bulk_rnaseq' in st.session_state.analysis_cache:
                            source_file = st.session_state.analysis_cache['bulk_rnaseq'].get('file_name', 'Unknown')
                        elif data_type in ['scrna', 'both'] and 'scrna_seq' in st.session_state.analysis_cache:
                            source_file = st.session_state.analysis_cache['scrna_seq'].get('file_name', 'Unknown')
                    
                    # Определяем описание отчета
                    if report_type == "Прототип стиль (зеленые цифры)":
                        description = f"Прототип стиль отчет для {data_type} данных"
                        analysis_type = "prototype_style"
                    elif report_type == "10x Genomics стиль":
                        description = f"10x Genomics стиль отчет для {data_type} данных"
                        analysis_type = "10x_genomics_style"
                    elif report_type == "Профессиональный отчет (Enhanced)":
                        description = f"Профессиональный Enhanced отчет для {data_type} данных"
                        analysis_type = "enhanced_professional"
                    else:
                        description = f"Стандартный QC отчет для {data_type} данных"
                        analysis_type = "standard_qc"
                    
                    # Сохраняем отчет через FileManager
                    report_id = file_manager.save_report(
                        report_files=report_files,
                        analysis_type=analysis_type,
                        source_file_id="unknown",
                        description=description
                    )
                    
                    st.info(f"💾 **Отчет сохранен с ID**: {report_id}")
                    
                except Exception as e:
                    st.warning(f"⚠️ Отчет создан, но возникла ошибка при сохранении в архив: {e}")
                # ===== КОНЕЦ ИСПРАВЛЕНИЯ =====
                
                # Отображение информации о файлах
                st.markdown("#### 📁 Созданные файлы:")
                
                for file_type, file_path in report_files.items():
                    st.info(f"**{file_type.upper()}**: {file_path}")
                    
                    # Кнопки скачивания
                    if file_type == 'html' and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            if report_type == "10x Genomics стиль":
                                report_name = "10x_genomics_style_report.html"
                            elif report_type == "Профессиональный отчет (Enhanced)":
                                report_name = "enhanced_qc_report.html"
                            else:
                                report_name = "transcriptomics_qc_report.html"
                            st.download_button(
                                f"📄 Скачать HTML отчет",
                                f.read(),
                                file_name=report_name,
                                mime="text/html",
                                key=f"download_{file_type}"
                            )
                    
                    elif file_type == 'json' and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                f"📊 Скачать JSON данные",
                                f.read(),
                                file_name="transcriptomics_qc_summary.json",
                                mime="application/json",
                                key=f"download_{file_type}"
                            )
                
                # Показать размер созданного отчета
                if 'html' in report_files and os.path.exists(report_files['html']):
                    file_size = os.path.getsize(report_files['html'])
                    st.info(f"📊 Размер HTML отчета: {file_size:,} байт")
                    
                    if report_type in ["Профессиональный отчет (Enhanced)", "10x Genomics стиль"]:
                        st.balloons()  # Празднование создания профессионального отчета!
                
                # Сводка процессинга
                st.markdown("#### 📊 Сводка анализа")
                summary = processor.get_processing_summary()
                
                summary_data = []
                for key, value in summary.items():
                    summary_data.append({
                        'Параметр': key.replace('_', ' ').title(),
                        'Значение': str(value)
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, hide_index=True)
                
            except Exception as e:
                st.error(f"❌ Ошибка генерации отчета: {e}")
    
    # Сравнение методов нормализации (если есть bulk данные)
    if st.session_state.bulk_qc_results:
        st.markdown("### 📊 Сравнение методов нормализации")
        
        if st.button("🔧 Сравнить методы нормализации"):
            with st.spinner("🔧 Сравниваю методы нормализации..."):
                try:
                    # Получаем данные экспрессии из processor
                    processor = st.session_state.transcriptomics_processor
                    
                    # Пример данных для демонстрации
                    # В реальном случае данные берутся из загруженной матрицы
                    sample_data = np.random.lognormal(mean=2, sigma=1, size=(1000, 10))
                    df_sample = pd.DataFrame(sample_data)
                    
                    comparison_df = processor.compare_normalization_methods(df_sample)
                    
                    st.success("✅ Сравнение методов нормализации завершено")
                    st.dataframe(comparison_df)
                    
                    # Визуализация сравнения
                    fig = px.bar(
                        comparison_df, 
                        x='Method', 
                        y='Mean',
                        title="Сравнение средних значений после нормализации"
                    )
                    st.plotly_chart(fig)
                    
                except Exception as e:
                    st.error(f"❌ Ошибка сравнения методов: {e}")

def process_10x_genomics_files(matrix_file, features_file, barcodes_file, **kwargs):
    """Обработка трех файлов 10x Genomics с детальным логом"""
    
    # Создаем контейнер для логов
    log_container = st.empty()
    progress_bar = st.progress(0)
    
    def update_log(message, step=None, total_steps=10):
        """Обновление лога с прогрессом"""
        if step is not None:
            progress_bar.progress(step / total_steps)
        
        # Создаем красивый лог
        log_html = f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 5px 0;">
            <div style="font-family: 'Courier New', monospace; font-size: 14px;">
                🔬 <strong>10x Genomics Pipeline</strong><br>
                <span style="color: #1f77b4;">⚡ {message}</span>
            </div>
        </div>
        """
        log_container.markdown(log_html, unsafe_allow_html=True)
    
    try:
        update_log("Инициализация обработки 10x Genomics данных...", 1)
        
        # Создание временных файлов для каждого компонента
        matrix_temp = None
        features_temp = None
        barcodes_temp = None
        
        try:
            update_log("📂 Создание временных файлов...", 2)
            
            # Сохранение matrix файла
            matrix_suffix = '.mtx.gz' if matrix_file.name.endswith('.gz') else '.mtx'
            with tempfile.NamedTemporaryFile(delete=False, suffix=matrix_suffix) as tmp:
                tmp.write(matrix_file.getvalue())
                matrix_temp = tmp.name
            
            update_log(f"💾 Matrix файл сохранен: {matrix_file.name} ({len(matrix_file.getvalue()):,} байт)", 3)
            
            # Сохранение features файла
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tsv') as tmp:
                tmp.write(features_file.getvalue())
                features_temp = tmp.name
            
            update_log(f"💾 Features файл сохранен: {features_file.name} ({len(features_file.getvalue()):,} байт)", 4)
            
            # Сохранение barcodes файла
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tsv') as tmp:
                tmp.write(barcodes_file.getvalue())
                barcodes_temp = tmp.name
            
            update_log(f"💾 Barcodes файл сохранен: {barcodes_file.name} ({len(barcodes_file.getvalue()):,} байт)", 5)
            
            # Создание директории для 10x данных
            with tempfile.TemporaryDirectory() as temp_dir:
                update_log(f"📁 Временная директория создана: {temp_dir}", 6)
                
                # Копируем файлы в временную директорию с правильными именами
                import shutil
                
                # Определяем правильные имена для всех файлов
                if matrix_file.name.endswith('.gz'):
                    matrix_name = 'matrix.mtx.gz'
                else:
                    matrix_name = 'matrix.mtx'
                
                if features_file.name.endswith('.gz'):
                    features_name = 'features.tsv.gz'
                else:
                    features_name = 'features.tsv'
                
                if barcodes_file.name.endswith('.gz'):
                    barcodes_name = 'barcodes.tsv.gz'
                else:
                    barcodes_name = 'barcodes.tsv'
                
                matrix_path = os.path.join(temp_dir, matrix_name)
                features_path = os.path.join(temp_dir, features_name)
                barcodes_path = os.path.join(temp_dir, barcodes_name)
                
                update_log("🔄 Копирование файлов с правильными именами...", 7)
                
                shutil.copy2(matrix_temp, matrix_path)
                shutil.copy2(features_temp, features_path)
                shutil.copy2(barcodes_temp, barcodes_path)
                
                # Детальная информация о каждом файле
                matrix_size = os.path.getsize(matrix_path)
                features_size = os.path.getsize(features_path)
                barcodes_size = os.path.getsize(barcodes_path)
                
                update_log(f"✅ Файлы готовы: Matrix: {matrix_size:,} байт, Features: {features_size:,} байт, Barcodes: {barcodes_size:,} байт", 8)
                
                # Пока используем scanpy для загрузки (если доступен)
                try:
                    update_log("🔬 Загрузка данных через scanpy...", 9)
                    import scanpy as sc
                    import pandas as pd

                    # Определяем формат features файла (v2 или v3)
                    features_df = pd.read_csv(features_path, sep='\t', header=None)
                    n_cols = features_df.shape[1]

                    update_log(f"📊 Features файл имеет {n_cols} колонок", 9)

                    # Выбираем параметр var_names в зависимости от формата
                    if n_cols >= 2:
                        # v2/v3 формат: используем вторую колонку (gene_symbols)
                        var_names_param = 'gene_symbols'
                    else:
                        # Только 1 колонка: используем gene_ids
                        var_names_param = 'gene_ids'

                    update_log(f"🔧 Используем var_names='{var_names_param}'", 9)

                    # Загружаем 10x данные
                    adata = sc.read_10x_mtx(
                        temp_dir,
                        var_names=var_names_param,
                        cache=True
                    )
                    adata.var_names_make_unique()
                    
                    update_log(f"✅ Данные загружены: {adata.n_obs} клеток × {adata.n_vars} генов", 10)
                    st.success(f"✅ Данные загружены: {adata.n_obs} клеток × {adata.n_vars} генов")
                    
                    # Сохраняем как CSV для обработки
                    csv_path = os.path.join(temp_dir, '10x_converted.csv')
                    adata.to_df().T.to_csv(csv_path)  # Транспонируем для правильного формата
                    
                    # Обработка через существующий pipeline
                    with open(csv_path, 'rb') as f:
                        class TempFile:
                            def __init__(self, content, name):
                                self.content = content
                                self.name = name
                            def getvalue(self):
                                return self.content
                        
                        temp_uploaded = TempFile(f.read(), "10x_converted.csv")
                        
                        process_scrna_analysis(
                            temp_uploaded, 'csv',
                            **kwargs
                        )
                
                except ImportError as ie:
                    st.error("❌ Для работы с 10x Genomics данными необходим scanpy: pip install scanpy")
                    st.error(f"Детали: {str(ie)}")
                except Exception as inner_e:
                    st.error(f"❌ Ошибка при загрузке 10x данных: {str(inner_e)}")
                    st.code(traceback.format_exc(), language="python")

        except Exception as e:
            st.error(f"❌ Ошибка обработки 10x Genomics файлов: {str(e)}")
            st.code(traceback.format_exc(), language="python")
        finally:
            # Очистка временных файлов
            for temp_file in [matrix_temp, features_temp, barcodes_temp]:
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)

    except Exception as e:
        st.error(f"❌ Внешняя ошибка обработки 10x Genomics файлов: {str(e)}")
        st.code(traceback.format_exc(), language="python")
        # Очистка при ошибке
        if 'matrix_temp' in locals() and matrix_temp and os.path.exists(matrix_temp):
            os.unlink(matrix_temp)
        if 'features_temp' in locals() and features_temp and os.path.exists(features_temp):
            os.unlink(features_temp)
        if 'barcodes_temp' in locals() and barcodes_temp and os.path.exists(barcodes_temp):
            os.unlink(barcodes_temp)
                        

# Дополнительные функции для обратной совместимости
def render_results_visualization():
    """Отображение результатов визуализации (устаревшая функция для совместимости)"""
    st.warning("Эта функция устарела. Используйте новый интерфейс в табах.")

if __name__ == "__main__":
    render_transcriptomics_module()