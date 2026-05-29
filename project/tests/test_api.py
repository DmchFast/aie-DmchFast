import io
import os
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MODEL_PATH", str(PROJECT_ROOT / "artifacts" / "best_model.pth"))
os.environ.setdefault("CLASSES_JSON", str(PROJECT_ROOT / "configs" / "classes.json"))
os.environ.setdefault("LOG_LEVEL", "INFO")

from src.app import app


def _make_image_bytes() -> bytes:
	img = Image.new("RGB", (224, 224), color=(255, 0, 0))
	buf = io.BytesIO()
	img.save(buf, format="JPEG")
	return buf.getvalue()


def test_health():
	with TestClient(app) as client:
		response = client.get("/health")
	assert response.status_code == 200
	assert response.json().get("status") == "ok"


def test_predict():
	image_bytes = _make_image_bytes()
	with TestClient(app) as client:
		response = client.post(
			"/predict",
			files={"file": ("test.jpg", image_bytes, "image/jpeg")},
		)
	assert response.status_code == 200
	payload = response.json()
	assert "class" in payload
	assert "probabilities" in payload
	assert isinstance(payload["probabilities"], dict)
	total = sum(payload["probabilities"].values())
	assert abs(total - 1.0) < 1e-3
