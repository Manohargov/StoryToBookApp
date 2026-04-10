import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
COVERS_DIR = OUTPUT_DIR / "covers"

# Create directories if they don't exist
for dir_path in [OUTPUT_DIR, TEMP_DIR, COVERS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

MODEL_CONFIG = {
    "default_model_path": str(BASE_DIR / "fine_tuned_model"),
    "use_float16_cuda": True,
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "image_height": 1600,
    "image_width": 1200
}

PROCESSING_CONFIG = {
    "whisper_model_size": "base",
    "chapter_word_count": 1000
}