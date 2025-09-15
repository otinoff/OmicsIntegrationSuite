#!/bin/bash

# Скрипт для настройки автоматического развертывания
# OmicsIntegrationSuite через GitHub Actions

echo "========================================="
echo "Настройка развертывания OmicsIntegrationSuite"
echo "========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия SSH ключа
KEY_PATH="$HOME/.ssh/omics_deploy_key"

if [ -f "$KEY_PATH" ]; then
    echo -e "${YELLOW}SSH ключ уже существует: $KEY_PATH${NC}"
    read -p "Создать новый ключ? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Используем существующий ключ"
    else
        ssh-keygen -t rsa -b 4096 -C "github-actions@omics-integration" -f "$KEY_PATH" -N ""
        echo -e "${GREEN}Новый SSH ключ создан${NC}"
    fi
else
    echo "Создаем новый SSH ключ..."
    ssh-keygen -t rsa -b 4096 -C "github-actions@omics-integration" -f "$KEY_PATH" -N ""
    echo -e "${GREEN}SSH ключ создан: $KEY_PATH${NC}"
fi

echo ""
echo "========================================="
echo "Шаг 1: Добавьте публичный ключ на сервер"
echo "========================================="
echo ""
echo "Скопируйте следующий публичный ключ:"
echo ""
echo -e "${YELLOW}"
cat "${KEY_PATH}.pub"
echo -e "${NC}"
echo ""
echo "Затем выполните на сервере (root@5.35.88.251):"
echo -e "${GREEN}echo 'ВСТАВЬТЕ_КЛЮЧ_ЗДЕСЬ' >> ~/.ssh/authorized_keys${NC}"
echo ""
read -p "Нажмите Enter после добавления ключа на сервер..."

echo ""
echo "========================================="
echo "Шаг 2: Добавьте приватный ключ в GitHub Secrets"
echo "========================================="
echo ""
echo "1. Откройте: https://github.com/otinoff/OmicsIntegrationSuite/settings/secrets/actions"
echo "2. Нажмите 'New repository secret'"
echo "3. Name: SERVER_SSH_KEY"
echo "4. Value: Скопируйте содержимое приватного ключа ниже:"
echo ""
echo -e "${YELLOW}--- НАЧАЛО ПРИВАТНОГО КЛЮЧА ---${NC}"
cat "$KEY_PATH"
echo -e "${YELLOW}--- КОНЕЦ ПРИВАТНОГО КЛЮЧА ---${NC}"
echo ""
read -p "Нажмите Enter после добавления секрета в GitHub..."

echo ""
echo "========================================="
echo "Шаг 3: Проверка подключения"
echo "========================================="
echo ""
echo "Проверяем подключение к серверу..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$KEY_PATH" root@5.35.88.251 "echo 'Подключение успешно!'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Подключение к серверу успешно!${NC}"
else
    echo -e "${RED}✗ Не удалось подключиться к серверу${NC}"
    echo "Проверьте, что публичный ключ добавлен на сервер"
fi

echo ""
echo "========================================="
echo "Готово!"
echo "========================================="
echo ""
echo "Теперь вы можете:"
echo "1. Сделать push в main ветку для автоматического развертывания"
echo "2. Или запустить вручную: https://github.com/otinoff/OmicsIntegrationSuite/actions"
echo ""
echo -e "${GREEN}Настройка завершена!${NC}"