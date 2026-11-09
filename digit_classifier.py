
from pathlib import Path

import cv2
import numpy as np

from project_paths import TEMPLATE_DIR


# HOG configuration
HOG = cv2.HOGDescriptor(
    (64, 64),  # Window size
    (16, 16),  # Block size
    (8, 8),    # Block stride
    (8, 8),    # Cell size
    9          # Number of bins
)


def extract_features(image):
    """Extract HOG features from a normalized digit."""

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = cv2.resize(image, (64, 64))

    descriptor = HOG.compute(image)

    return descriptor.flatten().astype(np.float32)


def train_classifier():
    """Train KNN using the existing digit templates."""

    features = []
    labels = []

    for digit in "1234":

        folder = TEMPLATE_DIR / digit
        paths = sorted(folder.glob("*.png"))

        if not paths:
            raise FileNotFoundError(
                f"No training images found for digit {digit}"
            )

        for path in paths:

            image = cv2.imread(
                str(path),
                cv2.IMREAD_GRAYSCALE
            )

            if image is None:
                continue

            features.append(extract_features(image))
            labels.append(int(digit))

    if len(features) < 3:
        raise ValueError("Not enough training samples.")

    training_data = np.asarray(features, dtype=np.float32)
    training_labels = np.asarray(labels, dtype=np.float32)

    knn = cv2.ml.KNearest_create()

    knn.train(
        training_data,
        cv2.ml.ROW_SAMPLE,
        training_labels
    )

    print(f"KNN trained with {len(features)} samples.")

    return knn


def predict_digit(image, knn):
    """Predict a digit using HOG + KNN."""

    features = extract_features(image)
    sample = features.reshape(1, -1)

    k = min(3, knn.getDefaultK())

    # Use three nearest neighbours
    _, result, neighbours, distances = knn.findNearest(
        sample,
        k=3
    )

    prediction = str(int(result[0, 0]))

    return prediction, distances
