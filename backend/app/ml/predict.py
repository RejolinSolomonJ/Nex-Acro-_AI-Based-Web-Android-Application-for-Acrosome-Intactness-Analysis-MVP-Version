"""
Prediction service – runs inference on preprocessed images.

Supports:
  - Single image prediction
  - Batch prediction (multiple images)
  - Mock prediction mode (when no trained model is available)
"""

import os
import time
import random
from typing import Optional

import numpy as np

from app.config import settings
from app.ml.preprocessing import preprocess_from_bytes, preprocess_from_path

# Global model reference (loaded once, reused)
_model = None
_model_loaded = False


def _load_model_lazy():
    """Lazy-load the model on first prediction call."""
    global _model, _model_loaded

    if _model_loaded:
        return

    model_path = settings.MODEL_PATH

    if os.path.exists(model_path):
        import tensorflow as tf
        _model = tf.keras.models.load_model(model_path)
        _model_loaded = True
        print(f"[OK] ML Model loaded: {model_path}")
    else:
        print(f"[WARN] No trained model found at {model_path}. Using mock predictions.")
        _model = None
        _model_loaded = True


def predict_single(image_bytes: bytes) -> dict:
    """
    Predict acrosome intactness for a single image.

    Returns:
        {
            "classification": "intact" | "damaged",
            "confidence": float (0.0 – 1.0),
            "intact_probability": float,
            "damaged_probability": float,
            "processing_time_ms": float,
        }
    """
    _load_model_lazy()

    start = time.perf_counter()

    # Preprocess
    processed = preprocess_from_bytes(image_bytes)
    input_tensor = np.expand_dims(processed, axis=0)  # (1, 224, 224, 3)

    if _model is not None:
        # Real model prediction
        prediction = _model.predict(input_tensor, verbose=0)
        intact_prob = float(prediction[0][0])
    else:
        # Mock prediction for development / demo
        intact_prob = _mock_predict()

    damaged_prob = 1.0 - intact_prob
    classification = "intact" if intact_prob >= settings.CONFIDENCE_THRESHOLD else "damaged"
    confidence = max(intact_prob, damaged_prob)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "classification": classification,
        "confidence": round(confidence, 4),
        "intact_probability": round(intact_prob, 4),
        "damaged_probability": round(damaged_prob, 4),
        "processing_time_ms": round(elapsed_ms, 2),
    }


def predict_batch(images_bytes: list[bytes]) -> list[dict]:
    """
    Predict on a batch of images for better throughput.

    Returns a list of prediction dicts (same format as predict_single).
    """
    _load_model_lazy()

    start = time.perf_counter()

    # Preprocess all images
    processed_list = []
    for img_bytes in images_bytes:
        processed = preprocess_from_bytes(img_bytes)
        processed_list.append(processed)

    batch_input = np.array(processed_list, dtype=np.float32)  # (N, 224, 224, 3)

    if _model is not None:
        # Batch prediction (much faster than individual)
        predictions = _model.predict(batch_input, verbose=0)
        intact_probs = [float(p[0]) for p in predictions]
    else:
        intact_probs = [_mock_predict() for _ in images_bytes]

    total_ms = (time.perf_counter() - start) * 1000
    per_image_ms = total_ms / len(images_bytes) if images_bytes else 0

    results = []
    for intact_prob in intact_probs:
        damaged_prob = 1.0 - intact_prob
        classification = "intact" if intact_prob >= settings.CONFIDENCE_THRESHOLD else "damaged"
        confidence = max(intact_prob, damaged_prob)

        results.append({
            "classification": classification,
            "confidence": round(confidence, 4),
            "intact_probability": round(intact_prob, 4),
            "damaged_probability": round(damaged_prob, 4),
            "processing_time_ms": round(per_image_ms, 2),
        })

    return results


def _mock_predict() -> float:
    """
    Generate a realistic mock prediction for demo/development.
    Simulates a model with ~75% accuracy – biased towards intact.
    """
    if random.random() < 0.65:
        # Intact – high confidence
        return random.uniform(0.70, 0.98)
    else:
        # Damaged – high confidence
        return random.uniform(0.05, 0.35)


def get_model_info() -> dict:
    """Return information about the loaded model."""
    _load_model_lazy()

    if _model is not None:
        return {
            "status": "loaded",
            "model_path": settings.MODEL_PATH,
            "input_shape": str(_model.input_shape),
            "total_params": int(_model.count_params()),
            "model_name": _model.name,
        }
    else:
        return {
            "status": "mock_mode",
            "model_path": settings.MODEL_PATH,
            "message": "No trained model found. Using mock predictions for development.",
        }
