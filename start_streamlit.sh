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
echo "Launching Streamlit on port $STREAMLIT_SERVER_PORT..."
nohup streamlit run web_interface.py \
    --server.port $STREAMLIT_SERVER_PORT \
    --server.address $STREAMLIT_SERVER_ADDRESS \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base "light" \
    > streamlit.log 2>&1 &

STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

# Подождем 3 секунды и проверим что процесс запустился
sleep 3

if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
    echo "✅ Streamlit successfully started on port $STREAMLIT_SERVER_PORT"
    echo "📋 Logs: tail -f streamlit.log"
    echo "🌐 Web interface: http://omicsintegrationsuite.onff.ru/"
else
    echo "❌ ERROR: Streamlit failed to start!"
    echo "📋 Check logs: tail -50 streamlit.log"
    exit 1
fi