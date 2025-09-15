# Справочник API

## Введение

Этот документ описывает программный интерфейс приложения (API) платформы диагональной интеграции мультимодальных биологических данных. API предоставляет доступ к функциональности всех модулей платформы через RESTful интерфейс и Python библиотеку.

## Общая информация

### Базовый URL

Для локального развертывания:
```
http://localhost:8000/api/v1
```

### Форматы данных

Все запросы и ответы используют формат JSON, если не указано иное.

### Аутентификация

API использует токеновую аутентификацию. Для получения токена отправьте POST запрос на `/auth/token` с учетными данными.

```bash
curl -X POST \
  http://localhost:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username": "user", "password": "password"}'
```

### Ошибки

API возвращает стандартные HTTP коды состояния:

- 200 OK - Запрос успешно выполнен
- 201 Created - Ресурс успешно создан
- 400 Bad Request - Некорректный запрос
- 401 Unauthorized - Требуется аутентификация
- 403 Forbidden - Доступ запрещен
- 404 Not Found - Ресурс не найден
- 500 Internal Server Error - Внутренняя ошибка сервера

## Модули API

### 1. Геномные данные

#### Загрузка данных

##### POST /genomics/upload

Загрузка файлов геномных данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `platform` (string): Платформа секвенирования (Illumina, PacBio, Oxford Nanopore)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/genomics/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@sample_R1.fastq' \
  -F 'files=@sample_R2.fastq' \
  -F 'sample_id=SAMPLE001' \
  -F 'platform=Illumina'
```

**Ответ:**
```json
{
  "job_id": "job_12345",
  "status": "uploaded",
  "files": [
    {
      "name": "sample_R1.fastq",
      "size": 123456789,
      "checksum": "abc123..."
    },
    {
      "name": "sample_R2.fastq",
      "size": 123456789,
      "checksum": "def456..."
    }
  ]
}
```

#### Запуск обработки

##### POST /genomics/process/{job_id}

Запуск обработки загруженных геномных данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `reference_genome` (string): Референсный геном (hg38, hg19, mm10)
- `aligner` (string): Выравниватель (bwa-mem2, minimap2)
- `caller` (string): Вызыватель вариантов (gatk, bcftools)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/genomics/process/job_12345 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "reference_genome": "hg38",
    "aligner": "bwa-mem2",
    "caller": "gatk"
  }'
```

**Ответ:**
```json
{
  "job_id": "job_12345",
  "status": "processing",
  "started_at": "2025-01-01T12:00:00Z"
}
```

#### Получение статуса

##### GET /genomics/status/{job_id}

Получение статуса обработки геномных данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Пример запроса:**
```bash
curl -X GET \
  http://localhost:8000/api/v1/genomics/status/job_12345 \
  -H 'Authorization: Bearer <token>'
```

**Ответ:**
```json
{
  "job_id": "job_12345",
  "status": "completed",
  "started_at": "2025-01-01T12:00:00Z",
  "completed_at": "2025-01-01T14:30:00Z",
  "results": {
    "bam_file": "/results/SAMPLE001.bam",
    "vcf_file": "/results/SAMPLE001.vcf",
    "qc_report": "/results/SAMPLE001_qc.html"
  }
}
```

### 2. Транскриптомные данные

#### Загрузка данных bulk RNA-seq

##### POST /transcriptomics/bulk/upload

Загрузка файлов bulk RNA-seq данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `platform` (string): Платформа секвенирования

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/transcriptomics/bulk/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@sample_R1.fastq' \
  -F 'files=@sample_R2.fastq' \
  -F 'sample_id=SAMPLE002' \
  -F 'platform=Illumina'
```

#### Запуск обработки bulk RNA-seq

##### POST /transcriptomics/bulk/process/{job_id}

Запуск обработки bulk RNA-seq данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `aligner` (string): Выравниватель (star, hisat2)
- `quantifier` (string): Квантификатор (featurecounts, htseq)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/transcriptomics/bulk/process/job_67890 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "aligner": "star",
    "quantifier": "featurecounts"
  }'
```

#### Загрузка данных scRNA-seq

##### POST /transcriptomics/singlecell/upload

Загрузка файлов scRNA-seq данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `format` (string): Формат данных (10x, loom, seurat)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/transcriptomics/singlecell/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@matrix.mtx' \
  -F 'files=@barcodes.tsv' \
  -F 'files=@features.tsv' \
  -F 'sample_id=SAMPLE003' \
  -F 'format=10x'
```

#### Запуск обработки scRNA-seq

##### POST /transcriptomics/singlecell/process/{job_id}

Запуск обработки scRNA-seq данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `normalization` (string): Метод нормализации (log, sctransform)
- `clustering` (string): Алгоритм кластеризации (louvain, leiden)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/transcriptomics/singlecell/process/job_11111 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "normalization": "log",
    "clustering": "leiden"
  }'
```

### 3. Данные микроРНК

#### Загрузка данных miRNA-seq

##### POST /mirna/upload

Загрузка файлов miRNA-seq данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `platform` (string): Платформа секвенирования

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/mirna/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@sample.fastq' \
  -F 'sample_id=SAMPLE004' \
  -F 'platform=Illumina'
```

#### Запуск обработки miRNA-seq

##### POST /mirna/process/{job_id}

Запуск обработки miRNA-seq данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `adapter_trimming` (boolean): Обрезка адаптеров
- `alignment_reference` (string): Референс для выравнивания (mirbase)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/mirna/process/job_22222 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "adapter_trimming": true,
    "alignment_reference": "mirbase_v22"
  }'
```

### 4. Протеомные данные

#### Загрузка протеомных данных

##### POST /proteomics/upload

Загрузка файлов протеомных данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `instrument` (string): Масс-спектрометр (thermo, bruker)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/proteomics/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@sample.raw' \
  -F 'sample_id=SAMPLE005' \
  -F 'instrument=thermo'
```

#### Запуск обработки протеомных данных

##### POST /proteomics/process/{job_id}

Запуск обработки протеомных данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `search_engine` (string): Поисковый движок (maxquant, diann, fragpipe)
- `database` (string): База данных (uniprot_human, uniprot_mouse)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/proteomics/process/job_33333 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "search_engine": "maxquant",
    "database": "uniprot_human"
  }'
```

### 5. Метаболомные данные

#### Загрузка метаболомных данных

##### POST /metabolomics/upload

Загрузка файлов метаболомных данных.

**Параметры запроса:**
- `files` (array): Массив файлов для загрузки
- `sample_id` (string): Идентификатор образца
- `instrument` (string): Масс-спектрометр

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/metabolomics/upload \
  -H 'Authorization: Bearer <token>' \
  -F 'files=@sample.raw' \
  -F 'sample_id=SAMPLE006' \
  -F 'instrument=qtof'
```

#### Запуск обработки метаболомных данных

##### POST /metabolomics/process/{job_id}

Запуск обработки метаболомных данных.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Параметры запроса:**
- `peak_picking` (object): Параметры пик-пиккинга
- `alignment` (object): Параметры выравнивания
- `annotation_db` (string): База данных для аннотации (hmdb, lipidmaps)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/metabolomics/process/job_44444 \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "peak_picking": {
      "method": "centwave",
      "ppm": 25
    },
    "alignment": {
      "method": "obiwarp",
      "rt_tol": 30
    },
    "annotation_db": "hmdb"
  }'
```

### 6. Диагональная интеграция

#### Создание задачи интеграции

##### POST /integration/create

Создание задачи диагональной интеграции.

**Параметры запроса:**
- `samples` (array): Массив идентификаторов образцов
- `modalities` (array): Массив модальностей для интеграции
- `integration_method` (string): Метод интеграции (cca, mnn, harmony)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/integration/create \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "samples": ["SAMPLE001", "SAMPLE002", "SAMPLE003"],
    "modalities": ["genomics", "transcriptomics", "proteomics"],
    "integration_method": "cca"
  }'
```

#### Запуск интеграции

##### POST /integration/process/{job_id}

Запуск процесса диагональной интеграции.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/integration/process/job_55555 \
  -H 'Authorization: Bearer <token>'
```

### 7. Контроль качества

#### Запуск контроля качества

##### POST /qc/run

Запуск контроля качества для указанных данных.

**Параметры запроса:**
- `sample_ids` (array): Массив идентификаторов образцов
- `modalities` (array): Массив модальностей для проверки качества

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/qc/run \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "sample_ids": ["SAMPLE001", "SAMPLE002"],
    "modalities": ["genomics", "transcriptomics"]
  }'
```

### 8. Отчетность

#### Генерация отчета

##### POST /reporting/generate

Генерация отчета по результатам обработки.

**Параметры запроса:**
- `job_ids` (array): Массив идентификаторов задач
- `report_type` (string): Тип отчета (summary, detailed, publication)
- `format` (string): Формат отчета (pdf, html, docx)

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/reporting/generate \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_ids": ["job_12345", "job_67890"],
    "report_type": "summary",
    "format": "pdf"
  }'
```

## Python API

Помимо REST API, платформа предоставляет Python API для программного доступа к функциональности.

### Установка

```python
pip install multimodal-bio-data-integration
```

### Использование

```python
from multimodal_bio_integration import GenomicsModule, TranscriptomicsModule

# Создание экземпляров модулей
genomics = GenomicsModule()
transcriptomics = TranscriptomicsModule()

# Обработка геномных данных
genomics_job = genomics.upload_files(
    file_paths=['sample_R1.fastq', 'sample_R2.fastq'],
    sample_id='SAMPLE001',
    platform='Illumina'
)

genomics_result = genomics.process(
    job_id=genomics_job.job_id,
    reference_genome='hg38',
    aligner='bwa-mem2'
)

# Обработка транскриптомных данных
transcriptomics_job = transcriptomics.upload_bulk_files(
    file_paths=['sample_R1.fastq', 'sample_R2.fastq'],
    sample_id='SAMPLE002',
    platform='Illumina'
)

transcriptomics_result = transcriptomics.process_bulk(
    job_id=transcriptomics_job.job_id,
    aligner='star',
    quantifier='featurecounts'
)
```

### Классы API

#### BaseModule

Базовый класс для всех модулей.

```python
class BaseModule:
    def __init__(self, config: dict = None):
        """Инициализация модуля"""
        pass
    
    def upload_files(self, file_paths: list, sample_id: str, **kwargs) -> Job:
        """Загрузка файлов"""
        pass
    
    def process(self, job_id: str, **kwargs) -> JobResult:
        """Обработка данных"""
        pass
    
    def get_status(self, job_id: str) -> JobStatus:
        """Получение статуса задачи"""
        pass
```

#### GenomicsModule

Модуль обработки геномных данных.

```python
class GenomicsModule(BaseModule):
    def upload_files(self, file_paths: list, sample_id: str, platform: str) -> Job:
        """Загрузка файлов геномных данных"""
        pass
    
    def process(self, job_id: str, reference_genome: str, 
                aligner: str, caller: str) -> JobResult:
        """Обработка геномных данных"""
        pass
    
    def validate_vcf(self, vcf_file: str) -> ValidationResult:
        """Валидация VCF файла"""
        pass
```

#### TranscriptomicsModule

Модуль обработки транскриптомных данных.

```python
class TranscriptomicsModule(BaseModule):
    def upload_bulk_files(self, file_paths: list, sample_id: str, 
                          platform: str) -> Job:
        """Загрузка файлов bulk RNA-seq"""
        pass
    
    def process_bulk(self, job_id: str, aligner: str, 
                     quantifier: str) -> JobResult:
        """Обработка bulk RNA-seq данных"""
        pass
    
    def upload_single_cell_files(self, file_paths: list, sample_id: str, 
                                format: str) -> Job:
        """Загрузка файлов scRNA-seq"""
        pass
    
    def process_single_cell(self, job_id: str, normalization: str, 
                           clustering: str) -> JobResult:
        """Обработка scRNA-seq данных"""
        pass
```

## События и вебхуки

API поддерживает вебхуки для уведомления о событиях.

### Подписка на события

##### POST /webhooks/subscribe

Подписка на уведомления о событиях.

**Параметры запроса:**
- `url` (string): URL для получения уведомлений
- `events` (array): Массив событий для подписки
- `secret` (string): Секретный ключ для подписи уведомлений

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/webhooks/subscribe \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://your-service.com/webhook",
    "events": ["job_completed", "job_failed"],
    "secret": "your_secret_key"
  }'
```

### Поддерживаемые события

- `job_started` - Задача начата
- `job_completed` - Задача завершена успешно
- `job_failed` - Задача завершена с ошибкой
- `file_uploaded` - Файл загружен
- `qc_passed` - Контроль качества пройден
- `qc_failed` - Контроль качества не пройден

## Ограничения и квоты

API имеет следующие ограничения:

- Максимальный размер загружаемого файла: 10 ГБ
- Максимальное количество одновременных задач: 100
- Максимальное количество запросов в минуту: 1000
- Время хранения результатов: 30 дней

## Логирование и мониторинг

### Получение логов

##### GET /logs/{job_id}

Получение логов выполнения задачи.

**Параметры пути:**
- `job_id` (string): Идентификатор задачи

**Пример запроса:**
```bash
curl -X GET \
  http://localhost:8000/api/v1/logs/job_12345 \
  -H 'Authorization: Bearer <token>'
```

### Метрики производительности

##### GET /metrics

Получение метрик производительности системы.

**Пример запроса:**
```bash
curl -X GET \
  http://localhost:8000/api/v1/metrics \
  -H 'Authorization: Bearer <token>'
```

## Безопасность

### Шифрование данных

Все данные передаются по HTTPS и шифруются при хранении.

### Управление доступом

API использует ролевую модель доступа:
- `user` - Пользователь
- `admin` - Администратор
- `developer` - Разработчик

### Аудит действий

Все действия пользователей логируются для аудита.

## Поддержка

Для получения помощи по API:

1. Обратитесь к документации
2. Проверьте примеры использования
3. Свяжитесь с поддержкой: support@example.com

## Изменения API

### Версия 1.0.0

Первоначальный выпуск API.

### Версия 1.1.0

Добавлены:
- Поддержка вебхуков
- Расширенные метрики производительности
- Улучшенная обработка ошибок

### Версия 1.2.0

Добавлены:
- Поддержка новых форматов данных
- Расширенные параметры конфигурации
- Улучшенная документация

## Заключение

Этот справочник API предоставляет полное описание всех доступных функций платформы диагональной интеграции мультимодальных биологических данных. Следуя этому руководству, вы сможете эффективно интегрировать платформу в свои приложения и рабочие процессы.

Для получения дополнительной информации о конкретных модулях и методах обработки данных обратитесь к технической документации в папке `docs/`.