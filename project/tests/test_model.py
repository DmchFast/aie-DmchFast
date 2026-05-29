import pytest
from PIL import Image
import numpy as np
from src.model import ImageClassifier

@pytest.fixture
def classifier():
    return ImageClassifier()

def test_predict_shape(classifier):
    # Создаём случайное изображение
    img = Image.new('RGB', (224, 224), color='red')
    result = classifier.predict(img)
    assert "class" in result
    assert "probabilities" in result
    assert len(result["probabilities"]) == 6
    assert isinstance(result["class"], str)

def test_probabilities_sum(classifier):
    img = Image.new('RGB', (224, 224), color='red')
    result = classifier.predict(img)
    total = sum(result["probabilities"].values())
    assert abs(total - 1.0) < 1e-5