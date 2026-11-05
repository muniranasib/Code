from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TRAINING_DATA_DIR = BASE_DIR / "training_data"
IMAGE_DIR = TRAINING_DATA_DIR / "images"
TEMPLATE_DIR = TRAINING_DATA_DIR / "digit_templates"