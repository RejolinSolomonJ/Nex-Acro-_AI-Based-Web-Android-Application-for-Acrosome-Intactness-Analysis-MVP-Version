"""
Training pipeline for the Acrosome Intactness CNN model.

Usage:
  python -m app.ml.train --data_dir ./dataset --model_type mobilenet --epochs 50

Dataset structure expected:
  dataset/
  ├── intact/        ← Images of intact acrosomes
  │   ├── img001.jpg
  │   └── ...
  └── damaged/       ← Images of damaged acrosomes
      ├── img001.jpg
      └── ...
"""

import os
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
    TensorBoard,
)
from sklearn.utils.class_weight import compute_class_weight

from app.config import settings
from app.ml.model import build_mobilenet_model, build_custom_cnn, build_resnet50_model, get_model_summary


def create_data_generators(
    data_dir: str,
    image_size: tuple = (224, 224),
    batch_size: int = 32,
    validation_split: float = 0.2,
):
    """
    Create training and validation data generators with augmentation.

    Augmentation strategies for microscopy images:
      - Rotation (cells can appear at any angle)
      - Horizontal/vertical flips
      - Brightness variation (lighting inconsistencies)
      - Zoom (different magnification levels)
      - Width/height shift (position in frame)
    """

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        rotation_range=360,          # Cells can be at any rotation
        horizontal_flip=True,
        vertical_flip=True,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.2,
        brightness_range=[0.8, 1.2],
        shear_range=0.1,
        fill_mode="reflect",
        validation_split=validation_split,
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=validation_split,
    )

    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=image_size,
        batch_size=batch_size,
        class_mode="binary",
        subset="training",
        shuffle=True,
        seed=42,
        classes=["damaged", "intact"],  # 0 = damaged, 1 = intact
    )

    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=image_size,
        batch_size=batch_size,
        class_mode="binary",
        subset="validation",
        shuffle=False,
        seed=42,
        classes=["damaged", "intact"],
    )

    return train_generator, val_generator


def compute_weights(train_generator) -> dict:
    """Compute class weights to handle imbalanced datasets."""
    classes = train_generator.classes
    unique_classes = np.unique(classes)
    weights = compute_class_weight("balanced", classes=unique_classes, y=classes)
    return dict(zip(unique_classes, weights))


def get_callbacks(model_save_path: str) -> list:
    """Configure training callbacks for optimization."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    callbacks = [
        # Save best model based on validation accuracy
        ModelCheckpoint(
            filepath=model_save_path,
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),

        # Stop early if no improvement for 15 epochs
        EarlyStopping(
            monitor="val_loss",
            patience=15,
            restore_best_weights=True,
            verbose=1,
        ),

        # Reduce learning rate on plateau
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1,
        ),

        # TensorBoard logging
        TensorBoard(
            log_dir=f"logs/training_{timestamp}",
            histogram_freq=1,
        ),
    ]

    return callbacks


def train_model(
    data_dir: str,
    model_type: str = "resnet50",
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    output_path: str = None,
):
    """
    Main training function.

    Args:
        data_dir: Path to dataset folder (with intact/ and damaged/ subfolders)
        model_type: "mobilenet", "resnet50", or "custom"
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Initial learning rate
        output_path: Where to save the trained model
    """
    output_path = output_path or settings.MODEL_PATH
    image_size = (settings.IMAGE_SIZE, settings.IMAGE_SIZE)

    print("=" * 60)
    print("ACROSOME INTACTNESS MODEL TRAINING")
    print("=" * 60)
    print(f"  Model type    : {model_type}")
    print(f"  Dataset       : {data_dir}")
    print(f"  Image size    : {image_size}")
    print(f"  Batch size    : {batch_size}")
    print(f"  Epochs        : {epochs}")
    print(f"  Learning rate : {learning_rate}")
    print(f"  Output        : {output_path}")
    print("=" * 60)

    # ── Step 1: Create data generators ───────────────────────
    print("\n[INFO] Loading dataset...")
    train_gen, val_gen = create_data_generators(
        data_dir, image_size, batch_size
    )

    print(f"  Training samples   : {train_gen.samples}")
    print(f"  Validation samples : {val_gen.samples}")
    print(f"  Classes            : {train_gen.class_indices}")

    # ── Step 2: Build model ──────────────────────────────────
    print(f"\n[INFO] Building {model_type} model...")
    if model_type == "mobilenet":
        model = build_mobilenet_model(learning_rate=learning_rate)
    elif model_type == "resnet50":
        model = build_resnet50_model(learning_rate=learning_rate)
    else:
        model = build_custom_cnn(learning_rate=learning_rate)

    print(get_model_summary(model))

    # ── Step 3: Compute class weights ────────────────────────
    class_weights = compute_weights(train_gen)
    print(f"\n[INFO] Class weights: {class_weights}")

    # ── Step 4: Train ────────────────────────────────────────
    print("\n[INFO] Starting training...")
    callbacks = get_callbacks(output_path)

    history = model.fit(
        train_gen,
        steps_per_epoch=train_gen.samples // batch_size,
        validation_data=val_gen,
        validation_steps=val_gen.samples // batch_size,
        epochs=epochs,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )

    # ── Step 5: Evaluate ─────────────────────────────────────
    print("\n[EVAL] Final Evaluation on Validation Set:")
    results = model.evaluate(val_gen, verbose=0)
    metrics = dict(zip(model.metrics_names, results))

    for name, value in metrics.items():
        print(f"  {name:>12s}: {value:.4f}")

    # ── Step 6: Save final model ─────────────────────────────
    model.save(output_path)
    print(f"\n[SAVE] Model saved to: {output_path}")

    # Also save as SavedModel format for serving
    savedmodel_path = output_path.replace(".h5", "_savedmodel")
    model.save(savedmodel_path)
    print(f"[SAVE] SavedModel saved to: {savedmodel_path}")

    print("\n[OK] Training complete!")
    return history, metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Acrosome CNN Model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset folder")
    parser.add_argument("--model_type", type=str, default="resnet50", choices=["mobilenet", "custom", "resnet50"])
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--output", type=str, default=None, help="Output model path")

    args = parser.parse_args()

    train_model(
        data_dir=args.data_dir,
        model_type=args.model_type,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        output_path=args.output,
    )
