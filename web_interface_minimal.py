"""
OmicsIntegrationSuite Web Interface - MINIMAL VERSION
Минимальная версия для диагностики 502 ошибки
"""

import streamlit as st

# Настройка страницы
st.set_page_config(
    page_title="OmicsIntegrationSuite - Minimal",
    page_icon="🧬",
    layout="wide"
)

# Заголовок
st.title("🧬 OmicsIntegrationSuite")
st.success("✅ Streamlit работает! Это минимальная версия для диагностики.")

# Информация
st.info("""
**Статус:** Минимальная версия запущена успешно

**Что это значит:**
- ✅ Streamlit установлен и работает
- ✅ Python работает
- ✅ Порт 8520 доступен
- ⚠️ Полные UI компоненты отключены

**Следующие шаги:**
1. Проверьте логи на сервере: `tail -100 /var/OmicsIntegrationSuite/streamlit.log`
2. Проверьте что все зависимости установлены: `pip3 list | grep streamlit`
3. Восстановите полную версию
""")

# Проверка импортов
st.subheader("🔍 Диагностика импортов")

imports_status = {}

# Test basic imports
try:
    import pandas as pd
    imports_status['pandas'] = f"✅ {pd.__version__}"
except Exception as e:
    imports_status['pandas'] = f"❌ {str(e)}"

try:
    import plotly
    imports_status['plotly'] = f"✅ {plotly.__version__}"
except Exception as e:
    imports_status['plotly'] = f"❌ {str(e)}"

try:
    from pathlib import Path
    imports_status['pathlib'] = "✅ OK"
except Exception as e:
    imports_status['pathlib'] = f"❌ {str(e)}"

# Show results
for lib, status in imports_status.items():
    st.write(f"**{lib}:** {status}")

st.markdown("---")
st.markdown("🔄 **Для возврата к полной версии:** переименуйте `web_interface_minimal.py` → `web_interface.py`")
