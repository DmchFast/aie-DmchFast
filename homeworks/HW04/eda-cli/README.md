# S04 – eda_cli: HTTP-сервис качества датасетов (FastAPI)

Расширенная версия проекта `eda-cli` из Семинара 03.

К существующему CLI-приложению для EDA добавлен **HTTP-сервис на FastAPI** с эндпоинтами `/health`, `/quality`, `/quality-from-csv` и `/quality-flags-from-csv`.  
Используется в рамках Семинара 04 курса «Инженерия ИИ».

## Требования

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) установлен в систему

## Инициализация проекта

В корне проекта (в папке `eda-cli`):

```bash
uv sync
```

Эта команда:

- создаст виртуальное окружение `.venv`;
- установит зависимости из `pyproject.toml`;
- установит сам проект `eda-cli` в окружение.

## Запуск CLI

### Краткий обзор

```bash
uv run eda-cli overview data/example.csv
```

Параметры:

- `--sep` – разделитель (по умолчанию `,`);
- `--encoding` – кодировка (по умолчанию `utf-8`).

### Полный EDA-отчёт

```bash
uv run eda-cli report data/example.csv --out-dir reports_example
```

Параметры:

- `--sep` – разделитель (по умолчанию ,);
- `--encoding` – кодировка (по умолчанию utf-8);
- `--out-dir` – каталог для сохранения отчёта (по умолчанию reports);
- `--max-hist-columns` – сколько числовых колонок включать в гистограммы (по умолчанию 6);
- `--top-k-categories` – сколько top-значений выводить для категориальных признаков (по умолчанию 5);

В результате в каталоге `reports_example/` появятся:

- `report.md` – основной отчёт в Markdown;
- `summary.csv` – таблица по колонкам;
- `missing.csv` – пропуски по колонкам;
- `correlation.csv` – корреляционная матрица (если есть числовые признаки);
- `top_categories/*.csv` – top-k категорий по строковым признакам;
- `hist_*.png` – гистограммы числовых колонок;
- `missing_matrix.png` – визуализация пропусков;
- `correlation_heatmap.png` – тепловая карта корреляций.

## Запуск HTTP-сервиса

HTTP-сервис реализован в модуле `eda_cli.api` на FastAPI.

Запуск Uvicorn
```bash
uv run uvicorn eda_cli.api:app --reload --port 8000
```
- `eda_cli.api:app` - путь до объекта FastAPI app в модуле eda_cli.api;

- `--reload` - автоматический перезапуск сервера при изменении кода (удобно для разработки);

- `--port 8000` - порт сервиса (можно поменять при необходимости).\

Доступ по адресу:
http://127.0.0.1:8000

## Эндпоинты сервиса

### 1. GET /health
Health-check

Запрос:
```bash
GET /health
```

Ожидаемый ответ 200 OK
```json
{
  "status": "ok",
  "timestamp": 1766392591.391653,
  "service": "eda-quality-service",
  "version": "1.0.0"
}
```
Или проверка через curl:

```bash
curl http://127.0.0.1:8000/health
```

---

### 2. Swagger UI: GET /docs
Интерфейс документации и тестирования API:

http://127.0.0.1:8000/docs


Через /docs можно:

- вызывать `GET /health`;
- вызывать `POST /quality` (форма для JSON);
- вызывать `POST /quality-from-csv` и `POST /quality-flags-from-csv` (форма для загрузки файла).

---

### POST /quality – оценка качества по агрегированным признакам

Эндпоинт принимает агрегированные признаки датасета и возвращает эвристическую оценку качества.

```bash
POST /quality
Content-Type: application/json
```
Внутри:

```json
{
  "n_rows": 1000,
  "n_cols": 10,
  "max_missing_share": 0.1,
  "has_constant_columns": false,
  "has_high_cardinality_categoricals": false
}
```

Пример ответа 200 OK:

```json
{
  "ok_for_model": true,
  "quality_score": 0.9,
  "latency_ms": 1.5,
  "flags": {
    "too_few_rows": false,
    "too_many_columns": false,
    "too_many_missing": false,
    "has_constant_columns": false,
    "has_high_cardinality_categoricals": false
  },
  "n_rows": 1000,
  "n_cols": 10
}
```

Через curl:

```bash
curl -X POST "http://127.0.0.1:8000/quality" -H "Content-Type: application/json" -d "{\"n_rows\": 1000, \"n_cols\": 10, \"max_missing_share\": 0.1, \"has_constant_columns\": false, \"has_high_cardinality_categoricals\": false}"
```

---

### POST /quality-from-csv – оценка качества по CSV-файлу

Эндпоинт принимает CSV-файл, читает его и оценивает качество данных.

Запрос:

```bash
POST /quality-from-csv
Content-Type: multipart/form-data
file: <CSV-файл>
```

Через Swagger:

- в `/docs` открыть `POST /quality-from-csv`,
- нажать `Try it out`,
- выбрать файл (`data/example.csv`),
 -нажать `Execute`.

 Через curl:

```bash
curl -X POST "http://127.0.0.1:8000/quality-from-csv" -F "file=@data/example.csv"
```

Ответ будет содержать:

- `ok_for_model` - результат по эвристикам;
- `quality_score` - интегральный скор качества;
- `flags` - булевы флаги из compute_quality_flags;
- `n_rows`, `n_cols` - размеры датасета;
- `latency_ms` - время обработки запроса.


---

### POST /quality-flags-from-csv – полные флаги качества из CSV-файла

Эндпоинт принимает CSV-файл и возвращает все флаги качества данных.

Запрос:

```bash
POST /quality-flags-from-csv
Content-Type: multipart/form-data
file: <CSV-файл>
```

Через Swagger:

- в `/docs` открыть `POST /quality-from-csv`,
- нажать `Try it out`,
- выбрать файл (`data/example.csv`),
 -нажать `Execute`.

 Через curl:

```bash
curl -X POST "http://127.0.0.1:8000/quality-flags-from-csv" -F "file=@data/example.csv"
```

Ответ будет содержать:

- `too_few_rows` - содержит ли датасет недостаточное количество строк;
- `too_many_missing` - количество пропущенных значений превышает порог;
- `has_constant_columns` - есть ли колонки, где все значения одинаковые;
- `has_high_cardinality_categoricals` - есть ли категориальные признаки с очень большим числом уникальных значений;
- `max_missing_share` - максимальная доля пропусков по колонкам;
- `quality_score` - интегральная оценка качества.

---

## Тесты

```bash
uv run pytest -q
```

## По ДЗ выполнено:

### 1. Добавлен HTTP-сервис на FastAPI с эндпоинтами:

- `/health` - проверка работоспособности
- `/quality` - оценка качества по метрикам
- `/quality-from-csv` - оценка качества из CSV-файла
- `/quality-flags-from-csv` - полные флаги качества из CSV

### 2. Интеграция с EDA-ядром из HW03:

- Использование функций `summarize_dataset`, `missing_table`, `compute_quality_flags`
- Включены эвристики

### 3. Обработка ошибок:

- Корректная обработка пустых файлов (HTTP 400)
- Проверка на пустой DataFrame
- Обработка ошибок чтения CSV

### 4. Описания:

- Запуск через uvicorn
- Запросы через curl
- Коротко об эндпоинтов