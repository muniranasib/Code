
"""Centralized paths for project data and images."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


# INPUT DATA
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = BASE_DIR / "images"


# GENERATED OUTPUT
GENERATED_DATA_DIR = DATA_DIR / "generated_data"
GENERATED_IMAGE_DIR = IMAGE_DIR / "generated_images"


# TRAINING DATA
TRAINING_DATA_DIR = BASE_DIR / "training_data"
TRAINING_IMAGE_DIR = TRAINING_DATA_DIR / "images"
TRAINING_GENERATED_IMAGE_DIR = (
    TRAINING_IMAGE_DIR / "generated_images"
)

TEMPLATE_DIR = TRAINING_DATA_DIR / "digit_templates"


# Create output folders automatically
for folder in (
    GENERATED_DATA_DIR,
    GENERATED_IMAGE_DIR,
    TRAINING_GENERATED_IMAGE_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)
