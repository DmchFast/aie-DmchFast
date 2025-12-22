import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel

# Импортируем функции из вашего core.py
from eda_cli.core import (
    summarize_dataset,
    missing_table,
    compute_quality_flags,
    DatasetSummary
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EDA Quality Service",
    description="HTTP сервис для оценки качества данных",
    version="1.0.0"
)


# Модели Pydantic
#Модель запроса для оценки качества по метрикам
class QualityRequest(BaseModel):
    n_rows: int
    n_cols: int
    max_missing_share: float
    has_constant_columns: bool = False
    has_high_cardinality_categoricals: bool = False


# Модель ответа для оценки качества
class QualityResponse(BaseModel):
    ok_for_model: bool
    quality_score: float
    latency_ms: float
    flags: Dict[str, Any]
    n_rows: int
    n_cols: int


# Вспомогательные функции
def read_csv_file(file: UploadFile) -> pd.DataFrame:
    """Безопасное чтение CSV файла"""
    try:
        # Читаем содержимое файла
        contents = file.file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Файл пустой")
        
        # Пробуем прочитать CSV
        try:
            df = pd.read_csv(pd.io.common.BytesIO(contents))
        except UnicodeDecodeError:
            # Пробуем альтернативную кодировку
            df = pd.read_csv(pd.io.common.BytesIO(contents), encoding='latin1')
        except Exception as read_error:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения CSV: {str(read_error)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Файл не содержит данных (пустой DataFrame)")
        
        return df
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")


# Эндпоинты
@app.get("/health", tags=["Здоровье"])
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "service": "eda-quality-service",
        "version": "1.0.0"
    }


@app.post("/quality", response_model=QualityResponse, tags=["Качество"])
async def assess_quality(request: QualityRequest):
    """
    Оценка качества данных на основе переданных метрик
    """
    start_time = time.time()
    
    # Логику для оценки по метрикам
    flags = {
        "too_few_rows": request.n_rows < 100,
        "too_many_columns": request.n_cols > 100,
        "too_many_missing": request.max_missing_share > 0.5,
        "has_constant_columns": request.has_constant_columns,
        "has_high_cardinality_categoricals": request.has_high_cardinality_categoricals,
    }
    
    # Расчет качества
    score = 1.0
    score -= request.max_missing_share
    
    if request.n_rows < 100:
        score -= 0.2
    if request.n_cols > 100:
        score -= 0.1
    if request.has_constant_columns:
        score -= 0.1
    if request.has_high_cardinality_categoricals:
        score -= 0.1
    
    score = max(0.0, min(1.0, score))
    ok_for_model = score >= 0.5
    
    latency_ms = (time.time() - start_time) * 1000
    
    return QualityResponse(
        ok_for_model=ok_for_model,
        quality_score=score,
        latency_ms=latency_ms,
        flags=flags,
        n_rows=request.n_rows,
        n_cols=request.n_cols
    )


@app.post("/quality-from-csv", tags=["Качество"])
async def assess_quality_from_csv(file: UploadFile = File(...)):
    """
    Оценка качества данных из загруженного CSV файла
    """
    start_time = time.time()
    
    try:
        df = read_csv_file(file)
        
        # EDA-ЯДРО
        summary = summarize_dataset(df)
        missing_df = missing_table(df)
        flags = compute_quality_flags(summary, missing_df)
        
        quality_score = flags.get("quality_score", 0.0)
        response = {
            "ok_for_model": quality_score >= 0.5,
            "quality_score": quality_score,
            "latency_ms": (time.time() - start_time) * 1000,
            "flags": {
                "too_few_rows": flags.get("too_few_rows", False),
                "too_many_columns": flags.get("too_many_columns", False),
                "too_many_missing": flags.get("too_many_missing", False),
                "has_constant_columns": flags.get("has_constant_columns", False),
                "has_high_cardinality_categoricals": flags.get("has_high_cardinality_categoricals", False),
                "constant_columns": flags.get("constant_columns", []),
                "high_cardinality_columns": flags.get("high_cardinality_columns", []),
                "max_missing_share": flags.get("max_missing_share", 0.0),
            },
            "n_rows": df.shape[0],
            "n_cols": df.shape[1],
            "filename": file.filename
        }
        
        return response
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Ошибка при оценке качества: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.post("/quality-flags-from-csv", tags=["Качество"])
async def get_quality_flags_from_csv(file: UploadFile = File(...)):
    """
    Получение полного набора флагов качества из CSV файла
    Включает эвристики из HW03:
    1. Константные колонки
    2. Категориальные колонки с высокой кардинальностью
    """
    start_time = time.time()
    
    try:

        df = read_csv_file(file)
        
        # EDA-ЯДРО
        summary = summarize_dataset(df)
        missing_df = missing_table(df)
        flags = compute_quality_flags(summary, missing_df)
        
        # Ответ с флагами
        response = {
            "flags": {
                "too_few_rows": flags.get("too_few_rows", False),
                "too_many_columns": flags.get("too_many_columns", False),
                "too_many_missing": flags.get("too_many_missing", False),
                "has_constant_columns": flags.get("has_constant_columns", False),
                "has_high_cardinality_categoricals": flags.get("has_high_cardinality_categoricals", False),
                "constant_columns": flags.get("constant_columns", []),
                "high_cardinality_columns": flags.get("high_cardinality_columns", []),
                "high_cardinality_threshold": flags.get("high_cardinality_threshold", 100),
                "max_missing_share": flags.get("max_missing_share", 0.0),
                "quality_score": flags.get("quality_score", 0.0),
            },
            "latency_ms": (time.time() - start_time) * 1000,
            "dataset_info": {
                "n_rows": df.shape[0],
                "n_cols": df.shape[1],
                "filename": file.filename
            }
        }
        
        return response
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Ошибка при получении флагов качества: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)