"""
Enhanced OmicsIntegrationSuite Web Interface
Улучшенный веб-интерфейс с современным дизайном и улучшенной навигацией
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

# Безопасный импорт модулей с обработкой ошибок
try:
    from modules.genomics.genomics_processor import GenomicsProcessor
except ImportError:
    GenomicsProcessor = None
    
try:
    from modules.transcriptomics.transcriptomics_processor import TranscriptomicsProcessor
except ImportError:
    TranscriptomicsProcessor = None
    
try:
    from modules.mirna.mirna_processor import MiRNAProcessor
except ImportError:
    MiRNAProcessor = None
    
try:
    from modules.proteomics.proteomics_processor import ProteomicsProcessor
except ImportError:
    ProteomicsProcessor = None
    
try:
    from modules.metabolomics.metabolomics_processor import MetabolomicsProcessor
except ImportError:
    MetabolomicsProcessor = None
    
try:
    from modules.integration.integration_processor import IntegrationProcessor
except ImportError:
    IntegrationProcessor = None
    
try:
    from modules.quality_control.qc_processor import QualityControlProcessor
except ImportError:
    QualityControlProcessor = None
    
try:
    from modules.reporting.reporting_processor import ReportingProcessor
except ImportError:
    ReportingProcessor = None

# Настройка страницы
st.set_page_config(
    page_title="OmicsIntegrationSuite",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Современные CSS стили
st.markdown("""
<style>
    /* Основные переменные */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --danger-color: #dc3545;
        --info-color: #17a2b8;
        --light-bg: #f8f9fa;
        --dark-text: #343a40;
        --light-text: #f8f9fa;
        --border-radius: 12px;
        --shadow: 0 4px 6px rgba(0,0,0,0.1);
        --transition: all 0.3s ease;
    }
    
    /* Градиентный заголовок */
    .main-header {
        text-align: center;
        padding: 2.5rem 1rem;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,0.1) 0%, rgba(255,255,0) 70%);
        transform: rotate(30deg);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Боковая панель */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border-right: 1px solid rgba(0,0,0,0.1);
    }
    
    /* Кнопки меню */
    .menu-btn {
        width: 100%;
        text-align: left;
        padding: 1rem 1.2rem;
        margin: 0.25rem 0;
        border: none;
        border-radius: var(--border-radius);
        background: white;
        color: var(--dark-text);
        font-weight: 500;
        cursor: pointer;
        transition: var(--transition);
        box-shadow: var(--shadow);
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .menu-btn:hover {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .menu-btn.active {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Карточки модулей */
    .module-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
        transition: var(--transition);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    .module-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Метрики */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.2rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        transition: var(--transition);
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Кнопки */
    .stButton>button {
        border-radius: var(--border-radius);
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Вкладки */
    [data-baseweb="tab-list"] {
        background: white;
        border-radius: var(--border-radius);
        padding: 0.5rem;
        box-shadow: var(--shadow);
    }
    
    [data-baseweb="tab"] {
        padding: 1rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
    }
    
    /* Прогрессбары */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--accent-color) 100%);
    }
    
    /* Алерты */
    [data-baseweb="notification"] {
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
    }
    
    /* Селектбоксы */
    [data-baseweb="select"] {
        border-radius: var(--border-radius);
    }
    
    /* Слайдеры */
    [data-baseweb="slider"] {
        padding: 1rem 0;
    }
    
    /* Футер */
    .main-footer {
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: var(--border-radius);
        color: var(--dark-text);
    }
    
    /* Адаптивность */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .menu-btn {
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        [data-testid="stMetric"] {
            padding: 0.8rem;
        }
    }
    
    /* Анимации */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-on-load {
        animation: fadeInUp 0.6s ease-out forwards;
    }
    
    /* Цветовые индикаторы */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background: var(--success-color);
        box-shadow: 0 0 8px var(--success-color);
    }
    
    .status-processing {
        background: var(--warning-color);
        box-shadow: 0 0 8px var(--warning-color);
    }
    
    .status-offline {
        background: var(--danger-color);
        box-shadow: 0 0 8px var(--danger-color);
    }
    
    /* Быстрые ссылки */
    .quick-link {
        display: block;
        padding: 0.5rem;
        color: var(--primary-color);
        text-decoration: none;
        border-radius: 5px;
        margin: 0.25rem 0;
        transition: var(--transition);
    }
    
    .quick-link:hover {
        background: #e9ecef;
        text-decoration: underline;
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# Заголовок с анимацией
st.markdown("""
<div class="main-header animate-on-load">
    <h1>🧬 OmicsIntegrationSuite</h1>
    <p>Платформа диагональной интеграции мультимодальных биологических данных</p>
    <p style="font-size: 0.9em; opacity: 0.8;">Доступно по адресу: <a href="http://omicsintegrationsuite.onff.ru/" style="color: white; text-decoration: underline;">http://omicsintegrationsuite.onff.ru/</a></p>
</div>
""", unsafe_allow_html=True)

# Инициализация состояния сессии
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = "🏠 Главная"

# Боковая панель с улучшенной навигацией
with st.sidebar:
    st.markdown("### 🧬 Модули обработки")
    
    # Кнопки меню с иконками
    menu_items = [
        ("🏠", "Главная"),
        ("🧬", "Геномика"),
        ("📊", "Транскриптомика"),
        ("🔬", "МикроРНК"),
        ("🦠", "Протеомика"),
        ("⚗️", "Метаболомика"),
        ("🔄", "Интеграция данных"),
        ("✅", "Контроль качества"),
        ("📈", "Отчеты")
    ]
    
    # Отображение кнопок меню
    for icon, label in menu_items:
        btn_key = f"menu_{label.replace(' ', '_')}"
        
        # Проверяем, является ли эта кнопка активной
        is_active = st.session_state.selected_module == label
        
        # Создаем кнопку с соответствующим стилем
        button_class = "menu-btn active" if is_active else "menu-btn"
        
        if st.button(
            f"{icon} {label}",
            key=btn_key,
            type="secondary" if not is_active else "primary"
        ):
            st.session_state.selected_module = label
            st.rerun()
    
    st.markdown("---")
    
    # Статус системы
    st.markdown("### 📡 Статус системы")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="status-indicator status-online"></span> Сервер', unsafe_allow_html=True)
        st.markdown("**Онлайн**")
    with col2:
        st.markdown('<span class="status-indicator status-online"></span> Модули', unsafe_allow_html=True)
        st.markdown("**8/8 активны**")
    
    # Метрики системы
    st.markdown("---")
    st.markdown("### 📊 Метрики")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Обработано файлов", "1,234", "↑ 12%")
        st.metric("Активных процессов", "3", "↑ 2")
    with col2:
        st.metric("CPU загрузка", "45%", "↓ 5%")
        st.metric("RAM использование", "8.2 GB", "↑ 0.5 GB")
    
    st.markdown("---")
    
    # Быстрые ссылки
    st.markdown("### 🔗 Быстрые ссылки")
    st.markdown("""
    <div style="padding: 0.5rem 0;">
        <a href="https://github.com/otinoff/OmicsIntegrationSuite" target="_blank" class="quick-link">📁 GitHub репозиторий</a>
        <a href="https://github.com/otinoff/OmicsIntegrationSuite/tree/main/docs" target="_blank" class="quick-link">📚 Документация</a>
        <a href="https://github.com/otinoff/OmicsIntegrationSuite/blob/main/docs/API_REFERENCE.md" target="_blank" class="quick-link">🔧 API Reference</a>
    </div>
    """, unsafe_allow_html=True)

# Основное содержимое
selected_module = st.session_state.selected_module

if selected_module == "🏠 Главная":
    # Анимированные метрики
    st.markdown('<div class="animate-on-load">', unsafe_allow_html=True)
    
    # Метрики с анимацией
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📥 Обработано файлов", "1,234", "↑ 12%")
    with col2:
        st.metric("⚡ Активных процессов", "3", "↑ 2")
    with col3:
        st.metric("🖥️ CPU загрузка", "45%", "↓ 5%")
    with col4:
        st.metric("🧠 RAM использование", "8.2 GB", "↑ 0.5 GB")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Информация о модулях
    st.header("📦 Доступные модули")
    
    # Создаем сетку модулей
    modules_grid = [
        [
            {
                "icon": "🧬",
                "title": "Модуль геномики",
                "description": "Обработка FASTQ, BAM/SAM, VCF файлов",
                "features": [
                    "Контроль качества данных",
                    "Выравнивание ридов",
                    "Вызов вариантов"
                ]
            },
            {
                "icon": "📊",
                "title": "Модуль транскриптомики",
                "description": "Bulk RNA-seq и scRNA-seq анализ",
                "features": [
                    "Нормализация данных",
                    "Дифференциальная экспрессия",
                    "Кластеризация клеток"
                ]
            }
        ],
        [
            {
                "icon": "🔬",
                "title": "Модуль микроРНК",
                "description": "Анализ miRNA-seq данных",
                "features": [
                    "Предсказание таргетов",
                    "Анализ путей регуляции",
                    "Количественный анализ"
                ]
            },
            {
                "icon": "🦠",
                "title": "Модуль протеомики",
                "description": "MS данные и идентификация белков",
                "features": [
                    "Идентификация пептидов",
                    "Количественный анализ",
                    "Анализ посттрансляционных модификаций"
                ]
            }
        ],
        [
            {
                "icon": "⚗️",
                "title": "Модуль метаболомики",
                "description": "LC-MS/GC-MS анализ метаболитов",
                "features": [
                    "Идентификация метаболитов",
                    "Анализ метаболических путей",
                    "Статистический анализ"
                ]
            },
            {
                "icon": "🔄",
                "title": "Модуль интеграции",
                "description": "Мультиомиксная интеграция данных",
                "features": [
                    "Корреляционный анализ",
                    "Сетевой анализ",
                    "Машинное обучение"
                ]
            }
        ]
    ]
    
    # Отображение модулей в сетке
    for row in modules_grid:
        cols = st.columns(2)
        for idx, module in enumerate(row):
            with cols[idx]:
                st.markdown(f"""
                <div class="module-card animate-on-load">
                    <div class="module-icon">{module['icon']}</div>
                    <h3>{module['title']}</h3>
                    <p><strong>{module['description']}</strong></p>
                    <ul>
                        {''.join([f'<li>{feature}</li>' for feature in module['features']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    # Дополнительные модули
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="module-card animate-on-load">
            <div class="module-icon">✅</div>
            <h3>Модуль контроля качества</h3>
            <p><strong>Валидация данных на всех этапах</strong></p>
            <ul>
                <li>Метрики качества</li>
                <li>Фильтрация выбросов</li>
                <li>Валидация результатов</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="module-card animate-on-load">
            <div class="module-icon">📈</div>
            <h3>Модуль отчетности</h3>
            <p><strong>Генерация комплексных отчетов</strong></p>
            <ul>
                <li>Визуализация результатов</li>
                <li>Экспорт данных</li>
                <li>Автоматические отчеты</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # График активности с анимацией
    st.markdown("---")
    st.header("📊 Активность системы")
    
    # Создаем пример данных для графика
    import datetime
    import random
    
    dates = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(days=7),
        end=datetime.datetime.now(),
        freq='H'
    )
    
    activity_data = pd.DataFrame({
        'Время': dates,
        'Геномика': [random.randint(0, 100) for _ in range(len(dates))],
        'Транскриптомика': [random.randint(0, 80) for _ in range(len(dates))],
        'Протеомика': [random.randint(0, 60) for _ in range(len(dates))],
        'Метаболомика': [random.randint(0, 40) for _ in range(len(dates))]
    })
    
    fig = px.line(
        activity_data,
        x='Время',
        y=['Геномика', 'Транскриптомика', 'Протеомика', 'Метаболомика'],
        title='Активность модулей за последнюю неделю',
        labels={'value': 'Количество процессов', 'variable': 'Модуль'},
        line_shape='spline'
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

elif selected_module == "🧬 Геномика":
    st.header("🧬 Модуль обработки геномных данных")
    
    # Создаем табы с иконками
    tab1, tab2, tab3 = st.tabs(["📤 Загрузка данных", "⚙️ Обработка", "📊 Результаты"])
    
    with tab1:
        st.subheader("Загрузка файлов")
        
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        with col2:
            st.markdown("### 📋 Поддерживаемые форматы")
            st.markdown("""
            - **FASTQ**: `.fastq`, `.fq`, `.fastq.gz`, `.fq.gz`
            - **BAM/SAM**: `.bam`, `.sam`
            - **VCF**: `.vcf`, `.vcf.gz`
            """)
            
            st.markdown("### ⚡ Рекомендации")
            st.markdown("""
            - Максимальный размер файла: 5 GB
            - Поддерживаемые платформы: Illumina, PacBio, Oxford Nanopore
            - Автоматическое определение формата
            """)
    
    with tab2:
        st.subheader("Параметры обработки")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔧 Качество данных")
            quality_threshold = st.slider("Порог качества", 0, 40, 20)
            min_length = st.number_input("Минимальная длина", value=50)
            
            trim_adapters = st.checkbox("Удалить адаптеры", value=True)
            normalize = st.checkbox("Нормализация", value=True)
            
        with col2:
            st.markdown("#### 🧬 Обработка")
            max_length = st.number_input("Максимальная длина", value=150)
            deduplicate = st.checkbox("Удаление дубликатов", value=True)
            recalibrate = st.checkbox("Рекалибрация качества", value=False)
            
            st.markdown("#### 📊 Фильтрация")
            filter_low_complexity = st.checkbox("Фильтр низкой сложности", value=True)
            filter_contamination = st.checkbox("Фильтр контаминации", value=True)
        
        st.markdown("---")
        if st.button("🚀 Начать обработку", type="primary", use_container_width=True):
            with st.spinner("Обработка данных..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(100):
                    import time
                    time.sleep(0.05)  # Имитация обработки
                    progress_bar.progress(i + 1)
                    status_text.info(f"Обработано: {i+1}%")
                
                st.success("✅ Обработка завершена!")
                st.balloons()
    
    with tab3:
        st.subheader("Результаты анализа")
        
        # Пример результатов
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего ридов", "1,234,567", "↑ 5.2%")
        with col2:
            st.metric("Качество > Q30", "95.3%", "↑ 1.1%")
        with col3:
            st.metric("Средняя длина", "150 bp", "0 bp")
            
        st.markdown("---")
        
        # График распределения качества
        st.markdown("### 📈 Распределение качества ридов")
        
        import random
        quality_scores = [random.gauss(30, 5) for _ in range(1000)]
        fig = px.histogram(
            quality_scores,
            nbins=50,
            title="Распределение качества ридов",
            labels={'value': 'Качество (Phred score)', 'count': 'Количество'},
            color_discrete_sequence=['#667eea']
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Таблица результатов
        st.markdown("### 📋 Детальная статистика")
        
        results_df = pd.DataFrame({
            'Метрика': ['Общее количество ридов', 'Среднее качество', 'Процент Q30', 'Средняя длина', 'GC-содержание'],
            'Значение': ['1,234,567', '32.1', '95.3%', '150 bp', '42.3%'],
            'Статус': ['✅', '✅', '✅', '✅', '✅']
        })
        
        st.dataframe(results_df, use_container_width=True, hide_index=True)

elif selected_module == "📊 Транскриптомика":
    st.header("📊 Модуль обработки транскриптомных данных")
    st.info("Модуль транскриптомики позволяет анализировать данные RNA-seq")
    
    # Добавьте функционал для транскриптомики

elif selected_module == "🔬 МикроРНК":
    st.header("🔬 Модуль обработки данных микроРНК")
    st.info("Модуль для анализа miRNA-seq данных")
    
    # Добавьте функционал для микроРНК

elif selected_module == "🦠 Протеомика":
    st.header("🦠 Модуль обработки протеомных данных")
    st.info("Модуль для анализа масс-спектрометрических данных")
    
    # Добавьте функционал для протеомики

elif selected_module == "⚗️ Метаболомика":
    st.header("⚗️ Модуль обработки метаболомных данных")
    st.info("Модуль для анализа метаболомных данных")
    
    # Добавьте функционал для метаболомики

elif selected_module == "🔄 Интеграция данных":
    st.header("🔄 Модуль диагональной интеграции")
    st.info("Интеграция мультимодальных биологических данных")
    
    # Добавьте функционал для интеграции

elif selected_module == "✅ Контроль качества":
    st.header("✅ Модуль контроля качества")
    st.info("Контроль качества данных на всех этапах обработки")
    
    # Добавьте функционал для контроля качества

elif selected_module == "📈 Отчеты":
    st.header("📈 Модуль генерации отчетов")
    st.info("Создание комплексных отчетов по результатам анализа")
    
    # Добавьте функционал для отчетов

# Футер
st.markdown("---")
st.markdown("""
<div class="main-footer">
    <p>© 2025 OmicsIntegrationSuite | Разработано для РНИМУ им. Н.И. Пирогова</p>
    <p>🌐 Доступно онлайн: <a href="http://omicsintegrationsuite.onff.ru/">http://omicsintegrationsuite.onff.ru/</a></p>
</div>
""", unsafe_allow_html=True)