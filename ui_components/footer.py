"""
Footer Component for OmicsIntegrationSuite
Компонент футера для OmicsIntegrationSuite
"""

import streamlit as st

def render_footer():
    """Отображение футера приложения"""
    
    # Футер
    st.markdown("---")
    st.markdown("""
    <div class="main-footer">
        <p>© 2025 OmicsIntegrationSuite | Разработано для РНИМУ им. Н.И. Пирогова</p>
        <p>🌐 Доступно онлайн: <a href="http://omicsintegrationsuite.onff.ru/">http://omicsintegrationsuite.onff.ru/</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_footer()