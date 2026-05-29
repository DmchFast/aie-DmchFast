from PIL import Image
import io
import numpy as np

def read_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")