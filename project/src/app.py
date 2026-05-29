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

@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier
    classifier = ImageClassifier()
    logger.info("Application started")
    yield


app = FastAPI(title="Image Classifier", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

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