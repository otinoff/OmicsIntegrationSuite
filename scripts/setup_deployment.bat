@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo =========================================
echo Настройка развертывания OmicsIntegrationSuite
echo =========================================
echo.

set KEY_PATH=%USERPROFILE%\.ssh\omics_deploy_key

:: Проверка наличия SSH ключа
if exist "%KEY_PATH%" (
    echo SSH ключ уже существует: %KEY_PATH%
    set /p REPLY="Создать новый ключ? (y/n): "
    if /i "!REPLY!"=="y" (
        ssh-keygen -t rsa -b 4096 -C "github-actions@omics-integration" -f "%KEY_PATH%" -N ""
        echo Новый SSH ключ создан
    ) else (
        echo Используем существующий ключ
    )
) else (
    echo Создаем новый SSH ключ...
    ssh-keygen -t rsa -b 4096 -C "github-actions@omics-integration" -f "%KEY_PATH%" -N ""
    echo SSH ключ создан: %KEY_PATH%
)

echo.
echo =========================================
echo Шаг 1: Добавьте публичный ключ на сервер
echo =========================================
echo.
echo Скопируйте следующий публичный ключ:
echo.
echo ---------- ПУБЛИЧНЫЙ КЛЮЧ ----------
type "%KEY_PATH%.pub"
echo.
echo ------------------------------------
echo.
echo Затем выполните на сервере (root@5.35.88.251):
echo echo 'ВСТАВЬТЕ_КЛЮЧ_ЗДЕСЬ' >> ~/.ssh/authorized_keys
echo.
pause

echo.
echo =========================================
echo Шаг 2: Добавьте приватный ключ в GitHub Secrets
echo =========================================
echo.
echo 1. Откройте: https://github.com/otinoff/OmicsIntegrationSuite/settings/secrets/actions
echo 2. Нажмите 'New repository secret'
echo 3. Name: SERVER_SSH_KEY
echo 4. Value: Скопируйте содержимое приватного ключа ниже:
echo.
echo --- НАЧАЛО ПРИВАТНОГО КЛЮЧА ---
type "%KEY_PATH%"
echo.
echo --- КОНЕЦ ПРИВАТНОГО КЛЮЧА ---
echo.
pause

echo.
echo =========================================
echo Шаг 3: Проверка подключения
echo =========================================
echo.
echo Проверяем подключение к серверу...
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "%KEY_PATH%" root@5.35.88.251 "echo Подключение успешно!" 2>nul

if %ERRORLEVEL% == 0 (
    echo [OK] Подключение к серверу успешно!
) else (
    echo [ERROR] Не удалось подключиться к серверу
    echo Проверьте, что публичный ключ добавлен на сервер
)

echo.
echo =========================================
echo Готово!
echo =========================================
echo.
echo Теперь вы можете:
echo 1. Сделать push в main ветку для автоматического развертывания
echo 2. Или запустить вручную: https://github.com/otinoff/OmicsIntegrationSuite/actions
echo.
echo Настройка завершена!
pause