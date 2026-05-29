import os
import json
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "artifacts/best_model.pth")
CLASSES_JSON = os.getenv("CLASSES_JSON", "configs/classes.json")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def load_classes():
    with open(CLASSES_JSON, "r") as f:
        return json.load(f)