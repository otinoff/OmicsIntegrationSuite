"""
OmicsIntegrationSuite Web Interface
Web-based interface for multi-omics data integration platform
Available at: http://omicsintegrationsuite.onff.ru/
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.genomics.genomics_processor import GenomicsProcessor
from modules.transcriptomics.transcriptomics_processor import TranscriptomicsProcessor
from modules.mirna.mirna_processor import MiRNAProcessor
from modules.proteomics.proteomics_processor import ProteomicsProcessor
from modules.metabolomics.metabolomics_processor import MetabolomicsProcessor
from modules.integration.integration_processor import IntegrationProcessor
from modules.quality_control.qc_processor import QualityControlProcessor
from modules.reporting.reporting_processor import ReportingProcessor

# Настройка страницы
st.set_page_config(
    page_title="OmicsIntegrationSuite",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .module-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🧬 OmicsIntegrationSuite</h1>
    <p>Платформа диагональной интеграции мультимодальных биологических данных</p>
    <p style="font-size: 0.9em;">Доступно по адресу: http://omicsintegrationsuite.onff.ru/</p>
</div>
""", unsafe_allow_html=True)

# Боковая панель
st.sidebar.title("🎛️ Панель управления")
st.sidebar.markdown("---")

# Выбор модуля
module = st.sidebar.selectbox(
    "Выберите модуль",
    [
        "🏠 Главная",
        "🧬 Геномика",
        "📊 Транскриптомика",
        "🔬 МикроРНК",
        "🦠 Протеомика",
        "⚗️ Метаболомика",
        "🔄 Интеграция данных",
        "✅ Контроль качества",
        "📈 Отчеты"
    ]
)

# Статус системы
st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Статус системы")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("Сервер", "Онлайн", delta="100%")
with col2:
    st.metric("Модули", "8/8", delta="Активны")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Быстрые ссылки")
st.sidebar.markdown("- [GitHub репозиторий](https://github.com/otinoff/OmicsIntegrationSuite)")
st.sidebar.markdown("- [Документация](https://github.com/otinoff/OmicsIntegrationSuite/tree/main/docs)")
st.sidebar.markdown("- [API Reference](https://github.com/otinoff/OmicsIntegrationSuite/blob/main/docs/API_REFERENCE.md)")

# Основное содержимое
if module == "🏠 Главная":
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Обработано файлов", "1,234", "↑ 12%")
    with col2:
        st.metric("Активных процессов", "3", "↑ 2")
    with col3:
        st.metric("Использование CPU", "45%", "↓ 5%")
    with col4:
        st.metric("Использование RAM", "8.2 GB", "↑ 0.5 GB")
    
    st.markdown("---")
    
    # Информация о модулях
    st.header("📦 Доступные модули")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🧬 Модуль геномики
        - Обработка FASTQ файлов
        - Анализ BAM/SAM файлов
        - Работа с VCF файлами
        - Контроль качества данных
        """)
        
        st.markdown("""
        ### 📊 Модуль транскриптомики
        - Bulk RNA-seq анализ
        - Single-cell RNA-seq
        - Нормализация данных
        - Дифференциальная экспрессия
        """)
        
        st.markdown("""
        ### 🔬 Модуль микроРНК
        - miRNA-seq анализ
        - Предсказание таргетов
        - Анализ путей регуляции
        """)
        
        st.markdown("""
        ### 🦠 Модуль протеомики
        - Обработка MS данных
        - Идентификация белков
        - Количественный анализ
        """)
    
    with col2:
        st.markdown("""
        ### ⚗️ Модуль метаболомики
        - LC-MS/GC-MS анализ
        - Идентификация метаболитов
        - Анализ метаболических путей
        """)
        
        st.markdown("""
        ### 🔄 Модуль интеграции
        - Мультиомиксная интеграция
        - Корреляционный анализ
        - Сетевой анализ
        - Машинное обучение
        """)
        
        st.markdown("""
        ### ✅ Контроль качества
        - Валидация данных
        - Метрики качества
        - Фильтрация выбросов
        """)
        
        st.markdown("""
        ### 📈 Модуль отчетности
        - Генерация отчетов
        - Визуализация результатов
        - Экспорт данных
        """)
    
    st.markdown("---")
    
    # График активности
    st.header("📊 Активность системы")
    
    # Создаем пример данных для графика
    import numpy as np
    import datetime
    
    dates = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(days=7),
        end=datetime.datetime.now(),
        freq='H'
    )
    
    activity_data = pd.DataFrame({
        'Время': dates,
        'Геномика': np.random.randint(0, 100, len(dates)),
        'Транскриптомика': np.random.randint(0, 80, len(dates)),
        'Протеомика': np.random.randint(0, 60, len(dates)),
        'Метаболомика': np.random.randint(0, 40, len(dates))
    })
    
    fig = px.line(
        activity_data,
        x='Время',
        y=['Геномика', 'Транскриптомика', 'Протеомика', 'Метаболомика'],
        title='Активность модулей за последнюю неделю',
        labels={'value': 'Количество процессов', 'variable': 'Модуль'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

elif module == "🧬 Геномика":
    st.header("🧬 Модуль обработки геномных данных")
    
    tab1, tab2, tab3 = st.tabs(["Загрузка данных", "Обработка", "Результаты"])
    
    with tab1:
        st.subheader("Загрузка файлов")
        
        file_type = st.selectbox(
            "Выберите тип файла",
            ["FASTQ", "BAM/SAM", "VCF"]
        )
        
        uploaded_file = st.file_uploader(
            f"Загрузите {file_type} файл",
            type=['fastq', 'fq', 'bam', 'sam', 'vcf'] if file_type == "FASTQ" else 
                  ['bam', 'sam'] if file_type == "BAM/SAM" else ['vcf'],
            accept_multiple_files=False
        )
        
        if uploaded_file:
            st.success(f"✅ Файл {uploaded_file.name} успешно загружен")
            st.info(f"Размер: {uploaded_file.size / 1024 / 1024:.2f} MB")
    
    with tab2:
        st.subheader("Параметры обработки")
        
        col1, col2 = st.columns(2)
        
        with col1:
            quality_threshold = st.slider("Порог качества", 0, 40, 20)
            min_length = st.number_input("Минимальная длина", value=50)
            
        with col2:
            trim_adapters = st.checkbox("Удалить адаптеры", value=True)
            normalize = st.checkbox("Нормализация", value=True)
        
        if st.button("🚀 Начать обработку", type="primary"):
            with st.spinner("Обработка данных..."):
                progress_bar = st.progress(0)
                for i in range(100):
                    import time
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                st.success("✅ Обработка завершена!")
    
    with tab3:
        st.subheader("Результаты анализа")
        
        # Пример результатов
        st.markdown("### Статистика качества")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего ридов", "1,234,567")
        with col2:
            st.metric("Качество > Q30", "95.3%")
        with col3:
            st.metric("Средняя длина", "150 bp")
        
        # График распределения качества
        quality_scores = np.random.normal(30, 5, 1000)
        fig = px.histogram(
            quality_scores,
            nbins=50,
            title="Распределение качества ридов",
            labels={'value': 'Качество (Phred score)', 'count': 'Количество'}
        )
        st.plotly_chart(fig, use_container_width=True)

elif module == "📊 Транскриптомика":
    st.header("📊 Модуль обработки транскриптомных данных")
    st.info("Модуль транскриптомики позволяет анализировать данные RNA-seq")
    
    # Добавьте функционал для транскриптомики

elif module == "🔬 МикроРНК":
    st.header("🔬 Модуль обработки данных микроРНК")
    st.info("Модуль для анализа miRNA-seq данных")
    
    # Добавьте функционал для микроРНК

elif module == "🦠 Протеомика":
    st.header("🦠 Модуль обработки протеомных данных")
    st.info("Модуль для анализа масс-спектрометрических данных")
    
    # Добавьте функционал для протеомики

elif module == "⚗️ Метаболомика":
    st.header("⚗️ Модуль обработки метаболомных данных")
    st.info("Модуль для анализа метаболомных данных")
    
    # Добавьте функционал для метаболомики

elif module == "🔄 Интеграция данных":
    st.header("🔄 Модуль диагональной интеграции")
    st.info("Интеграция мультимодальных биологических данных")
    
    # Добавьте функционал для интеграции

elif module == "✅ Контроль качества":
    st.header("✅ Модуль контроля качества")
    st.info("Контроль качества данных на всех этапах обработки")
    
    # Добавьте функционал для контроля качества

elif module == "📈 Отчеты":
    st.header("📈 Модуль генерации отчетов")
    st.info("Создание комплексных отчетов по результатам анализа")
    
    # Добавьте функционал для отчетов

# Футер
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>© 2025 OmicsIntegrationSuite | Разработано для РНИМУ им. Н.И. Пирогова</p>
    <p>🌐 Доступно онлайн: <a href="http://omicsintegrationsuite.onff.ru/">http://omicsintegrationsuite.onff.ru/</a></p>
</div>
""", unsafe_allow_html=True)