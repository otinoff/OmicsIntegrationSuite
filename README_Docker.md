# OmicsIntegrationSuite Docker Setup
## Полное решение для установки биоинформатических инструментов

### 📋 Содержание
- [Быстрый старт](#быстрый-старт)
- [Установка Docker](#установка-docker)
- [Сборка образов](#сборка-образов)
- [Использование](#использование)
- [Решение проблем](#решение-проблем)

---

## 🚀 Быстрый старт

### Windows (PowerShell)
```powershell
# 1. Установите Docker Desktop
# Скачайте с https://www.docker.com/products/docker-desktop/

# 2. Клонируйте репозиторий или перейдите в папку
cd M:\TaskContract2025\OmicsIntegrationSuite

# 3. Соберите минимальный образ для тестирования
docker build -f Dockerfile.minimal -t omics-suite:minimal .

# 4. Проверьте работу
docker run --rm omics-suite:minimal
```

### Linux/Mac
```bash
# 1. Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Перейдите в директорию проекта
cd M/TaskContract2025/OmicsIntegrationSuite

# 3. Сделайте скрипты исполняемыми
chmod +x build.sh run.sh

# 4. Соберите образ
./build.sh minimal

# 5. Проверьте работу
./run.sh check
```

---

## 📦 Сборка образов

### Вариант 1: Минимальный образ (рекомендуется для начала)
**Размер:** ~500MB  
**Время сборки:** 2-3 минуты  
**Содержит:** Только Python библиотеки

```bash
# Linux/Mac
./build.sh minimal

# Windows PowerShell
docker build -f Dockerfile.minimal -t omics-suite:minimal .
```

### Вариант 2: Полный образ
**Размер:** ~2GB  
**Время сборки:** 10-15 минут  
**Содержит:** Все биоинформатические инструменты

```bash
# Linux/Mac
./build.sh full

# Windows PowerShell
docker build -t omics-suite:latest .
```

---

## 💻 Использование

### 1. Интерактивная оболочка
```bash
# Linux/Mac
./run.sh shell

# Windows PowerShell
docker run -it --rm `
  -v ${PWD}/data:/data `
  -v ${PWD}/modules:/app/modules `
  omics-suite:latest bash
```

### 2. Обработка данных
```bash
# Linux/Mac
./run.sh process data/input data/output reference.fa

# Windows PowerShell
docker run --rm `
  -v ${PWD}/data:/data `
  omics-suite:latest `
  --input /data/input/genomics `
  --output /data/output/genomics
```

### 3. Jupyter Notebook
```bash
# Linux/Mac
./run.sh jupyter

# Windows PowerShell
docker run -it --rm `
  -p 8888:8888 `
  -v ${PWD}/notebooks:/notebooks `
  omics-suite:latest `
  bash -c "pip install jupyter && jupyter notebook --ip=0.0.0.0 --allow-root"
```
Откройте браузер: http://localhost:8888

### 4. Проверка инструментов
```bash
# Linux/Mac
./run.sh check

# Windows PowerShell
docker run --rm omics-suite:latest bash -c "samtools --version && bcftools --version"
```

---

## 🐳 Docker Compose

### Запуск всех сервисов
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f
```

### Доступные сервисы:
- **omics-suite**: Основной процессор
- **jupyter**: Notebook сервер (порт 8888)
- **dev**: Контейнер для разработки

---

## 📁 Структура проекта

```
OmicsIntegrationSuite/
├── Dockerfile              # Полный образ с инструментами
├── Dockerfile.minimal      # Минимальный образ
├── docker-compose.yml      # Конфигурация для compose
├── .dockerignore          # Исключения при сборке
├── requirements.txt       # Python зависимости
├── build.sh              # Скрипт сборки (Linux/Mac)
├── run.sh                # Скрипт запуска (Linux/Mac)
├── modules/              # Код модулей
│   └── genomics/        # Модули обработки геномных данных
├── data/                # Данные (не включаются в образ)
│   ├── input/          # Входные файлы
│   ├── output/         # Результаты обработки
│   └── reference/      # Референсные геномы
├── tests/              # Тесты
└── notebooks/          # Jupyter notebooks
```

---

## 🔧 Решение проблем

### Проблема: "Cannot connect to Docker daemon"
```bash
# Windows
Start-Service docker

# Linux
sudo systemctl start docker
sudo usermod -aG docker $USER
# Перелогиньтесь
```

### Проблема: "No space left on device"
```bash
# Очистка Docker
docker system prune -a --volumes

# Проверка места
docker system df
```

### Проблема: Ошибки при сборке
```bash
# Пересборка без кеша
docker build --no-cache -t omics-suite:latest .

# С подробным выводом
DOCKER_BUILDKIT=1 docker build --progress=plain -t omics-suite:latest .
```

### Проблема: Медленная сборка на Windows
Используйте WSL2:
1. Включите WSL2 в Windows Features
2. Установите Ubuntu из Microsoft Store
3. Запускайте Docker из WSL2 терминала

---

## 🧬 Установленные инструменты

| Инструмент | Версия | Назначение |
|------------|--------|------------|
| samtools | 1.17 | Работа с BAM/SAM файлами |
| bcftools | 1.17 | Работа с VCF файлами |
| htslib | 1.17 | tabix, bgzip |
| fastp | 0.23.4 | Предобработка FASTQ |
| BWA-MEM2 | 2.2.1 | Выравнивание ридов |
| Minimap2 | 2.26 | Альтернативный алайнер |
| FastQC | 0.12.1 | Контроль качества |

## 📚 Python библиотеки

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| pysam | 0.21.0 | Работа с BAM/SAM/VCF |
| cyvcf2 | 0.30.22 | Быстрая работа с VCF |
| biopython | 1.81 | Биоинформатика |
| pybedtools | 0.9.0 | Работа с BED файлами |
| pysamstats | 1.1.2 | Статистика по BAM |

---

## 📝 Примеры команд

### Обработка одного FASTQ файла
```bash
docker run --rm \
  -v $(pwd)/data:/data \
  omics-suite:latest \
  python -c "
from modules.genomics.fastq_processor import process_fastq_files
process_fastq_files(
    ['/data/input/sample.fastq'],
    '/data/output',
    '/data/reference/hg38.fa'
)
"
```

### Фильтрация VCF файла
```bash
docker run --rm \
  -v $(pwd)/data:/data \
  omics-suite:latest \
  python -c "
from modules.genomics.filter_validator import filter_vcf_file
filter_vcf_file('/data/input/variants.vcf', '/data/output')
"
```

### Контроль качества
```bash
docker run --rm \
  -v $(pwd)/data:/data \
  omics-suite:latest \
  python -c "
from modules.genomics.quality_control import run_quality_control
run_quality_control(
    ['/data/input/sample.fastq'],
    '/data/output'
)
"
```

---

## 📈 Производительность

### Рекомендуемые системные требования:
- **CPU:** 4+ ядер
- **RAM:** 8GB минимум, 16GB рекомендуется
- **Диск:** 20GB свободного места
- **ОС:** Windows 10+, Ubuntu 20.04+, macOS 10.15+

### Оптимизация:
```bash
# Увеличить память для Docker (Windows/Mac)
# Docker Desktop → Settings → Resources → Memory: 8GB

# Использовать больше потоков
docker run --rm \
  -e THREADS=16 \
  omics-suite:latest
```

---

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте версию Docker: `docker --version` (требуется 20.10+)
2. Убедитесь, что Docker daemon запущен
3. Проверьте наличие свободного места на диске
4. Посмотрите логи: `docker logs <container_id>`

---

## 📄 Лицензия

Проект TaskContract2025 - OmicsIntegrationSuite  
© 2025 SnowWhiteAI

---

*Документация создана для обеспечения воспроизводимости биоинформатических анализов*