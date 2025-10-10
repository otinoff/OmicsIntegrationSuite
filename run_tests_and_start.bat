@echo off
chcp 65001 >nul
echo =======================================
echo    OMICS INTEGRATION SUITE - ТЕСТЫ
echo =======================================
echo.

echo [1/5] Проверка Python и зависимостей...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/5] Установка зависимостей...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Некоторые зависимости не установлены
)

echo.
echo [3/5] Запуск базовых тестов компонентов...
python test_all_components.py
if %errorlevel% neq 0 (
    echo [ERROR] Базовые тесты не прошли!
    echo Продолжить? (y/n)
    set /p continue=
    if /i not "%continue%"=="y" exit /b 1
)

echo.
echo [4/5] Генерация демо-отчетов...
echo Создание профессионального отчета...
python create_professional_report.py
if %errorlevel% neq 0 (
    echo [WARNING] Ошибка создания профессионального отчета
)

echo Создание стандартного научного отчета...
python create_standard_report.py
if %errorlevel% neq 0 (
    echo [WARNING] Ошибка создания стандартного отчета
)

echo Создание современного отчета...
python create_modern_report.py
if %errorlevel% neq 0 (
    echo [WARNING] Ошибка создания современного отчета
)

echo.
echo [5/5] Запуск веб-интерфейса...
echo =======================================
echo   ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!
echo   Запуск Streamlit веб-интерфейса...
echo =======================================
echo.
echo Веб-интерфейс будет доступен по адресу:
echo   http://localhost:8502
echo.
echo Для остановки нажмите Ctrl+C
echo.

python -m streamlit run web_interface.py --server.port 8502