import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from .model import ImageClassifier
from .preprocess import read_image_from_bytes
from .config import LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

classifier = None
app_started_at = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier, app_started_at
    app_started_at = time.time()
    classifier = ImageClassifier()
    logger.info(
        "Application started: model_path=%s, classes=%s",
        classifier.model_path,
        classifier.num_classes,
    )
    yield


app = FastAPI(title="Image Classifier", lifespan=lifespan)

@app.get("/health")
async def health():
    uptime_seconds = None if app_started_at is None else round(time.time() - app_started_at, 3)
    return {
        "status": "ok",
        "model_loaded": classifier is not None,
        "model_path": None if classifier is None else classifier.model_path,
        "classes": None if classifier is None else classifier.num_classes,
        "uptime_seconds": uptime_seconds,
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start_time = time.time()
    try:
        contents = await file.read()
        image = read_image_from_bytes(contents)
        result = classifier.predict(image)
        elapsed = time.time() - start_time
        logger.info(f"Prediction for {file.filename} took {elapsed:.3f}s, class={result['class']}")
        return result
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=400, detail=str(e))