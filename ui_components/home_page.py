"""
Home Page Component for OmicsIntegrationSuite
Компонент главной страницы для OmicsIntegrationSuite
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import random
import datetime

def render_home_page():
    """Отображение главной страницы"""
    
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
    dates = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(days=7),
        end=datetime.datetime.now(),
        freq='h'
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
    
    st.plotly_chart(fig)

if __name__ == "__main__":
    render_home_page()