# Настройка автоматического развертывания через GitHub Actions

## Шаги для настройки

### 1. Генерация SSH ключа (если еще нет)

На локальной машине выполните:
```bash
ssh-keygen -t rsa -b 4096 -C "github-actions@omics-integration"
```

Сохраните ключ в безопасное место, например: `~/.ssh/omics_deploy_key`

### 2. Добавление публичного ключа на сервер

Скопируйте содержимое публичного ключа:
```bash
cat ~/.ssh/omics_deploy_key.pub
```

Подключитесь к серверу и добавьте ключ:
```bash
ssh root@5.35.88.251
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
```

### 3. Настройка GitHub Secrets

1. Перейдите в репозиторий на GitHub: https://github.com/otinoff/OmicsIntegrationSuite
2. Зайдите в Settings → Secrets and variables → Actions
3. Создайте новый секрет:
   - Name: `SERVER_SSH_KEY`
   - Value: Содержимое приватного ключа (cat ~/.ssh/omics_deploy_key)

### 4. Структура GitHub Actions

Файл `.github/workflows/deploy.yml` уже настроен и будет:
- Запускаться при push в ветку main или master
- Подключаться к серверу 5.35.88.251 по SSH
- Клонировать/обновлять код в `/var/OmicsIntegrationSuite`
- Устанавливать Python зависимости
- Выполнять health check

### 5. Первое развертывание

После настройки секретов, развертывание произойдет автоматически при следующем push в main ветку.

Также можно запустить вручную:
1. Перейдите в Actions на GitHub
2. Выберите "Deploy to Server"
3. Нажмите "Run workflow"

### 6. Проверка развертывания

Подключитесь к серверу и проверьте:
```bash
ssh root@5.35.88.251
cd /var/OmicsIntegrationSuite
ls -la
python3 main.py --help
```

### 7. Мониторинг

Следите за статусом развертываний:
- GitHub Actions: https://github.com/otinoff/OmicsIntegrationSuite/actions
- Логи на сервере: `/var/OmicsIntegrationSuite/logs/`

## Troubleshooting

### Проблема: Permission denied (publickey)
**Решение**: Убедитесь, что приватный ключ правильно добавлен в GitHub Secrets

### Проблема: Host key verification failed
**Решение**: Добавьте сервер в known_hosts или используйте StrictHostKeyChecking=no в SSH конфигурации

### Проблема: Python dependencies installation failed
**Решение**: Убедитесь, что на сервере установлен Python 3.8+ и pip3

## Контакты поддержки

При возникновении проблем обращайтесь к администратору проекта.