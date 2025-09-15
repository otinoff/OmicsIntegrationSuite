"""
Sidebar Component for OmicsIntegrationSuite
Компонент боковой панели для OmicsIntegrationSuite
"""

import streamlit as st

def render_sidebar():
    """Отображение боковой панели с навигацией"""
    
    # Инициализация состояния сессии
    if 'selected_module' not in st.session_state:
        st.session_state.selected_module = "🏠 Главная"
    
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
            # Формируем полное название модуля с иконкой
            full_label = f"{icon} {label}"
            btn_key = f"menu_{label.replace(' ', '_')}"
            
            # Проверяем, является ли эта кнопка активной
            is_active = st.session_state.selected_module == full_label
            
            # Создаем кнопку с соответствующим стилем
            button_class = "menu-btn active" if is_active else "menu-btn"
            
            if st.button(
                full_label,
                key=btn_key,
                type="secondary" if not is_active else "primary"
            ):
                st.session_state.selected_module = full_label
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

if __name__ == "__main__":
    render_sidebar()