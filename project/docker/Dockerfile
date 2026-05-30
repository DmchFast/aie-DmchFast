FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ src/
COPY configs/ configs/
COPY artifacts/ artifacts/

EXPOSE 8000

ENV MODEL_PATH=artifacts/best_model.pth
ENV CLASSES_JSON=configs/classes.json
ENV LOG_LEVEL=INFO

CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
