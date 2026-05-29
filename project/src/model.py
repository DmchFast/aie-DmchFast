import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
import logging
from .config import MODEL_PATH, load_classes

logger = logging.getLogger(__name__)

class ImageClassifier:
    def __init__(self, model_path=MODEL_PATH):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = load_classes()
        self.num_classes = len(self.classes)
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.model = self._load_model(model_path)
        self.model.eval()
        logger.info(f"Model loaded on {self.device}")

    def _load_model(self, model_path):
        model = models.resnet18(weights=None)
        num_ftrs = model.fc.in_features
        model.fc = torch.nn.Linear(num_ftrs, self.num_classes)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model = model.to(self.device)
        return model

    def predict(self, image: Image.Image):
        """Принимает PIL Image, возвращает dict с классом и вероятностями"""
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            predicted_class_idx = torch.argmax(probs).item()
            predicted_class = self.classes[predicted_class_idx]
            probabilities = {cls: float(probs[i]) for i, cls in enumerate(self.classes)}
        return {
            "class": predicted_class,
            "probabilities": probabilities
        }