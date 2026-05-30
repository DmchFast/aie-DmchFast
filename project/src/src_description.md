# Исходный код проекта

В этой папке размещается **основной код проекта**:

**Файлы:**
- `app.py` — точка входа FastAPI-сервиса с эндпоинтами `/health` и `/predict`.
- `model.py` — класс `ImageClassifier` для загрузки модели и выполнения инференса.
- `preprocess.py` — функция `read_image_from_bytes()` для предобработки изображений.
- `config.py` — загрузка конфигурации из `.env` и файлов конфига (MODEL_PATH, LOG_LEVEL, CLASSES_JSON).
- `__init__.py` — пакетная инициализация.

**Запуск:**

Основная команда для запуска сервиса:
```bash
uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Подробнее см. `project/README.md`.
