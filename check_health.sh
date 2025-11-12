#!/bin/bash

echo "=========================================="
echo "🔍 OmicsIntegrationSuite Health Check"
echo "=========================================="
echo ""

# 1. Check Python
echo "1️⃣ Python version:"
python3 --version || echo "❌ Python not found"
echo ""

# 2. Check Streamlit
echo "2️⃣ Streamlit installed:"
python3 -c "import streamlit; print(f'✅ Streamlit {streamlit.__version__}')" 2>&1 || echo "❌ Streamlit not installed"
echo ""

# 3. Check if process is running
echo "3️⃣ Streamlit process:"
if ps aux | grep -v grep | grep "streamlit run" > /dev/null; then
    echo "✅ Streamlit is running"
    ps aux | grep -v grep | grep "streamlit run"
else
    echo "❌ Streamlit is NOT running"
fi
echo ""

# 4. Check port 8520
echo "4️⃣ Port 8520 status:"
if netstat -tuln 2>/dev/null | grep ":8520" > /dev/null || ss -tuln 2>/dev/null | grep ":8520" > /dev/null; then
    echo "✅ Port 8520 is listening"
    netstat -tuln 2>/dev/null | grep ":8520" || ss -tuln 2>/dev/null | grep ":8520"
else
    echo "❌ Port 8520 is NOT listening"
fi
echo ""

# 5. Test local connection
echo "5️⃣ Local connection test:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8520 | grep -q "200\|302"; then
    echo "✅ Streamlit responds on localhost:8520"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8520)
    echo "❌ Streamlit NOT responding (HTTP $HTTP_CODE)"
fi
echo ""

# 6. Check last 20 lines of log
echo "6️⃣ Last 20 lines of streamlit.log:"
if [ -f "streamlit.log" ]; then
    tail -20 streamlit.log
else
    echo "❌ streamlit.log not found"
fi
echo ""

# 7. Check web_interface.py imports
echo "7️⃣ Test web_interface.py imports:"
python3 -c "
import sys
import os
sys.path.append('.')
try:
    import streamlit as st
    print('✅ streamlit: OK')
except Exception as e:
    print(f'❌ streamlit: {e}')

try:
    from ui_components.mirna_module import render_mirna_module
    print('✅ ui_components.mirna_module: OK')
except Exception as e:
    print(f'❌ ui_components.mirna_module: {e}')

try:
    from ui_components.genomics_module import render_genomics_module
    print('✅ ui_components.genomics_module: OK')
except Exception as e:
    print(f'❌ ui_components.genomics_module: {e}')
" 2>&1
echo ""

echo "=========================================="
echo "Health check complete!"
echo "=========================================="
