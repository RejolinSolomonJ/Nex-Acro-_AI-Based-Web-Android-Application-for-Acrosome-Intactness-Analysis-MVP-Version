"""
CNN Model architecture for Acrosome Intactness Classification.

Two model options:
  1. Transfer Learning with MobileNetV2 (recommended – lightweight, mobile-ready)
  2. Custom CNN from scratch (backup option)

Both output binary classification: Intact (1) vs Damaged (0)
"""

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.applications import MobileNetV2, ResNet50V2

from app.config import settings

INPUT_SHAPE = (settings.IMAGE_SIZE, settings.IMAGE_SIZE, 3)


def build_mobilenet_model(
    input_shape: tuple = INPUT_SHAPE,
    learning_rate: float = 1e-4,
    fine_tune_layers: int = 30,
) -> tf.keras.Model:
    """
    Transfer-learning model using MobileNetV2 backbone.

    MobileNetV2 is ideal because it's:
      - Lightweight (3.4M params) → good for deployment on Android
      - Pre-trained on ImageNet → strong feature extraction
      - Efficient architecture with depthwise separable convolutions

    Fine-tunes the last `fine_tune_layers` layers of the backbone.
    """
    # Load MobileNetV2 without top classification layers
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )

    # Freeze all layers first
    base_model.trainable = True
    for layer in base_model.layers[:-fine_tune_layers]:
        layer.trainable = False

    # Build classification head
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(128, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(1, activation="sigmoid"),  # Binary: intact prob
    ], name="AcrosomeMobileNet")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )

    return model


def build_custom_cnn(
    input_shape: tuple = INPUT_SHAPE,
    learning_rate: float = 1e-3,
) -> tf.keras.Model:
    """
    Custom CNN built from scratch for acrosome classification.
    Useful when transfer learning isn't available or for experimentation.

    Architecture:
      Conv2D(32) → Conv2D(64) → Conv2D(128) → Conv2D(256)
      Each block: Conv → BN → ReLU → MaxPool → Dropout
      FC head: Dense(256) → Dense(128) → Dense(1, sigmoid)
    """
    model = models.Sequential([
        # ── Block 1 ──────────────────────────────────────────
        layers.Conv2D(32, (3, 3), padding="same", input_shape=input_shape),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # ── Block 2 ──────────────────────────────────────────
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # ── Block 3 ──────────────────────────────────────────
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # ── Block 4 ──────────────────────────────────────────
        layers.Conv2D(256, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # ── Classification Head ──────────────────────────────
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(128, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(1, activation="sigmoid"),
    ], name="AcrosomeCustomCNN")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )

    return model


def build_resnet50_model(
    input_shape: tuple = INPUT_SHAPE,
    learning_rate: float = 1e-4,
    fine_tune_layers: int = 30,
) -> tf.keras.Model:
    """
    Transfer-learning model using ResNet50V2 backbone.
    More powerful feature extractor than MobileNetV2, ideal for the expanded diverse dataset.
    """
    base_model = ResNet50V2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )

    base_model.trainable = True
    for layer in base_model.layers[:-fine_tune_layers]:
        layer.trainable = False

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(1, activation="sigmoid"),
    ], name="AcrosomeResNet50")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )

    return model


def load_trained_model(model_path: str = None) -> tf.keras.Model:
    """Load a saved trained model from disk."""
    path = model_path or settings.MODEL_PATH
    model = tf.keras.models.load_model(path)
    print(f"[OK] Model loaded from: {path}")
    return model


def get_model_summary(model: tf.keras.Model) -> str:
    """Get a string summary of the model architecture."""
    summary_lines = []
    model.summary(print_fn=lambda x: summary_lines.append(x))
    return "\n".join(summary_lines)
