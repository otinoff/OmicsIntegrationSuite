"""
OmicsIntegrationSuite Web Interface in RGNKC Style
Веб-интерфейс OmicsIntegrationSuite в стиле РГНКЦ
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

# Импорт компонентов UI
from ui_components import (
    render_header,
    render_sidebar,
    render_home_page,
    render_genomics_module,
    render_transcriptomics_module,
    render_mirna_module,
    render_proteomics_module,
    render_metabolomics_module,
    render_integration_module,
    render_quality_control_module,
    render_reporting_module,
    render_footer
)

# Настройка страницы
st.set_page_config(
    page_title="OmicsIntegrationSuite",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Современные CSS стили в соответствии с дизайнерским руководством РГНКЦ
st.markdown("""
<style>
    /* Основные переменные из дизайнерского руководства РГНКЦ */
    :root {
        --primary-blue: #2B5AA0; /* Основной синий */
        --teal-dark: #1B5E5E; /* Темно-бирюзовый из логотипа РНИМУ */
        --accent-red: #D73527; /* Красный акцент из логотипа РНИМУ */
        --background: #FFFFFF; /* Белый фон */
        --light-bg: #F8F9FA; /* Светло-серый */
        --text-primary: #333333; /* Темно-серый текст */
        --text-secondary: #666666; /* Средний серый */
        --border-color: #E5E5E5; /* Светло-серый границы */
        --success-color: #28A745; /* Зеленый успех */
        --warning-color: #FD7E14; /* Оранжевый предупреждение */
        --danger-color: #DC3545; /* Ошибка */
        --info-color: #17A2B8; /* Информация */
        --border-radius: 8px; /* Радиус скругления */
        --border-radius-btn: 6px; /* Радиус скругления для кнопок */
        --shadow: 0 2px 4px rgba(0,0,0,0.1); /* Тень для карточек */
        --transition: all 0.3s ease;
    }
    
    /* Заголовок в стиле РГНКЦ */
    .main-header {
        text-align: center;
        padding: 2.5rem 1rem;
        background-color: var(--primary-blue);
        color: white;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: white;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto;
        color: white;
    }
    
    /* Боковая панель в стиле РГНКЦ */
    [data-testid="stSidebar"] {
        background-color: var(--background);
        border-right: 1px solid var(--border-color);
    }
    
    /* Кнопки меню в стиле РГНКЦ */
    .menu-btn {
        width: 100%;
        text-align: left;
        padding: 1rem 1.2rem;
        margin: 0.25rem 0;
        border: none;
        border-radius: var(--border-radius);
        background: var(--background);
        color: var(--text-primary);
        font-weight: 500;
        cursor: pointer;
        transition: var(--transition);
        box-shadow: var(--shadow);
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .menu-btn:hover {
        background-color: var(--primary-blue);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .menu-btn.active {
        background-color: var(--primary-blue);
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Карточки модулей в стиле РГНКЦ */
    .module-card {
        background: var(--background);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
        transition: var(--transition);
        border: 1px solid var(--border-color);
    }
    
    .module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .module-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        color: var(--primary-blue);
    }
    
    /* Метрики в стиле РГНКЦ */
    [data-testid="stMetric"] {
        background: var(--background);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        transition: var(--transition);
        border: 1px solid var(--border-color);
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Кнопки в стиле РГНКЦ */
    .stButton>button {
        border-radius: var(--border-radius-btn);
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: var(--transition);
        box-shadow: var(--shadow);
    }
    
    /* Основная кнопка */
    .stButton>button.primary {
        background-color: var(--primary-blue);
        color: white;
    }
    
    .stButton>button.primary:hover {
        background-color: #1a4a8a;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Вторичная кнопка */
    .stButton>button.secondary {
        background-color: transparent;
        color: var(--primary-blue);
        border: 1px solid var(--primary-blue);
    }
    
    .stButton>button.secondary:hover {
        background-color: rgba(43, 90, 160, 0.1);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Вкладки в стиле РГНКЦ */
    [data-baseweb="tab-list"] {
        background: var(--background);
        border-radius: var(--border-radius);
        padding: 0.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    }
    
    [data-baseweb="tab"] {
        padding: 1rem 1.5rem;
        font-weight: 500;
        transition: var(--transition);
        color: var(--text-primary);
    }
    
    /* Прогрессбары в стиле РГНКЦ */
    .stProgress > div > div {
        background-color: var(--primary-blue);
    }
    
    /* Алерты в стиле РГНКЦ */
    [data-baseweb="notification"] {
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
    }
    
    /* Селектбоксы в стиле РГНКЦ */
    [data-baseweb="select"] {
        border-radius: 4px;
        border: 1px solid var(--border-color);
    }
    
    /* Слайдеры в стиле РГНКЦ */
    [data-baseweb="slider"] {
        padding: 1rem 0;
    }
    
    /* Футер в стиле РГНКЦ */
    .main-footer {
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        background-color: var(--light-bg);
        border-radius: var(--border-radius);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
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
    
    /* Цветовые индикаторы в стиле РГНКЦ */
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
    
    /* Быстрые ссылки в стиле РГНКЦ */
    .quick-link {
        display: block;
        padding: 0.5rem;
        color: var(--primary-blue);
        text-decoration: none;
        border-radius: 5px;
        margin: 0.25rem 0;
        transition: var(--transition);
    }
    
    .quick-link:hover {
        background-color: var(--light-bg);
        text-decoration: underline;
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# Основная логика приложения
def main():
    # Отображение заголовка
    render_header()
    
    # Отображение боковой панели
    render_sidebar()
    
    # Получение выбранного модуля из состояния сессии
    selected_module = st.session_state.get('selected_module', '🏠 Главная')
    
    # Отображение контента в зависимости от выбранного модуля
    if selected_module == "🏠 Главная":
        render_home_page()
    elif selected_module == "🧬 Геномика":
        render_genomics_module()
    elif selected_module == "📊 Транскриптомика":
        render_transcriptomics_module()
    elif selected_module == "🔬 МикроРНК":
        render_mirna_module()
    elif selected_module == "🦠 Протеомика":
        render_proteomics_module()
    elif selected_module == "⚗️ Метаболомика":
        render_metabolomics_module()
    elif selected_module == "🔄 Интеграция данных":
        render_integration_module()
    elif selected_module == "✅ Контроль качества":
        render_quality_control_module()
    elif selected_module == "📈 Отчеты":
        render_reporting_module()
    
    # Отображение футера
    render_footer()

if __name__ == "__main__":
    main()