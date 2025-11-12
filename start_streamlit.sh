#!/bin/bash

# Скрипт для запуска Streamlit веб-интерфейса
# Доступен по адресу: http://omicsintegrationsuite.onff.ru/

echo "Starting OmicsIntegrationSuite Web Interface..."

# Установка переменных окружения
export STREAMLIT_SERVER_PORT=8520
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Проверка установки Streamlit
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit не найден. Устанавливаем..."
    pip3 install streamlit plotly altair
fi

# Остановка предыдущего процесса Streamlit если он запущен
pkill -f "streamlit run" 2>/dev/null

# Запуск Streamlit в фоновом режиме
nohup streamlit run web_interface.py \
    --server.port $STREAMLIT_SERVER_PORT \
    --server.address $STREAMLIT_SERVER_ADDRESS \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base "light" \
    > streamlit.log 2>&1 &

echo "Streamlit запущен на порту $STREAMLIT_SERVER_PORT"
echo "Логи доступны в файле streamlit.log"
echo "Веб-интерфейс доступен по адресу: http://omicsintegrationsuite.onff.ru/"