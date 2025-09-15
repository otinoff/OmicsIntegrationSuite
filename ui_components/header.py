"""
Header Component for OmicsIntegrationSuite
Компонент заголовка для OmicsIntegrationSuite
"""

import streamlit as st

def render_header():
    """Отображение заголовка приложения"""
    
    # Заголовок с анимацией
    st.markdown("""
    <div class="main-header animate-on-load">
        <h1>🧬 OmicsIntegrationSuite</h1>
        <p>Платформа диагональной интеграции мультимодальных биологических данных</p>
        <p style="font-size: 0.9em; opacity: 0.8;">Доступно по адресу: <a href="http://omicsintegrationsuite.onff.ru/" style="color: white; text-decoration: underline;">http://omicsintegrationsuite.onff.ru/</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_header()