#!/usr/bin/env python3
"""
Training script for the structured symptom-based stroke risk model.

- Uses ONLY classical ML (RandomForest by default).
- Provides basic evaluation (accuracy, F1, sensitivity, specificity).
- Saves both the preprocessor and model for production inference.
- Deterministic: fixed seeds.
"""

import os
import argparse
import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    recall_score,
    confusion_matrix,
    classification_report
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from config import Config
from preprocessing.symptom_processor import SymptomProcessor
from utils.logger import logger


def set_seeds(seed: int = 42) -> None:
    """Ensure deterministic behavior."""
    np.random.seed(seed)


def compute_binary_metrics(y_true, y_pred) -> dict:
    """Compute medically relevant binary classification metrics."""
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="binary")
    sensitivity = recall_score(y_true, y_pred, pos_label=1)

    # Specificity = TN / (TN + FP)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "accuracy": float(acc),
        "f1": float(f1),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
    }


def build_model(
    model_type: str = "rf",
    random_state: int = 42
):
    """
    Build a simple, interpretable model.

    Allowed:
      - 'rf': RandomForestClassifier
      - 'lr': LogisticRegression
    """
    if model_type == "rf":
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=4,
            min_samples_leaf=2,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        )
    elif model_type == "lr":
        model = LogisticRegression(
            solver="liblinear",
            penalty="l2",
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=random_state,
        )
    else:
        raise ValueError("model_type must be 'rf' or 'lr'.")

    return model


def main(
    model_type: str = "rf",
    test_size: float = 0.2
) -> None:
    set_seeds(Config.SEED)
    Config.ensure_dirs()

    symptoms_path: Path = Config.SYMPTOMS_CSV
    if not symptoms_path.exists():
        raise FileNotFoundError(f"Symptoms CSV not found at: {symptoms_path}")

    logger.info(f"Loading symptoms dataset from {symptoms_path}")
    df = pd.read_csv(symptoms_path)

    if "stroke" not in df.columns:
        raise ValueError("Expected binary target column 'stroke' in symptoms.csv")

    # Fit preprocessor on full dataset features
    processor = SymptomProcessor()
    X_all = processor.fit(df)
    y_all = df["stroke"].values.astype(int)

    X_train, X_val, y_train, y_val = train_test_split(
        X_all,
        y_all,
        test_size=test_size,
        random_state=Config.SEED,
        stratify=y_all,
    )

    logger.info(f"Training symptom model [{model_type}] on {X_train.shape[0]} samples")
    model = build_model(model_type=model_type, random_state=Config.SEED)
    model.fit(X_train, y_train)

    # Evaluation
    y_val_pred = model.predict(X_val)
    y_val_proba = model.predict_proba(X_val)[:, 1]

    metrics = compute_binary_metrics(y_val, y_val_pred)
    logger.info("Validation metrics:")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")

    logger.info("Full classification report:")
    logger.info("\n" + classification_report(y_val, y_val_pred, digits=4))

    # Feature importance / explainability
    try:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            logger.info("Top feature importances:")
            for idx, importance in enumerate(importances):
                logger.info(f"  Feature {idx}: {importance:.4f}")
        elif hasattr(model, "coef_"):
            coefs = model.coef_[0]
            logger.info("Top feature coefficients (LR):")
            for idx, coef in enumerate(coefs):
                logger.info(f"  Feature {idx}: {coef:.4f}")
    except Exception as exc:
        logger.warning(f"Unable to log feature importance: {exc}")

    # Persist model and processor
    logger.info(f"Saving symptom model to {Config.SYMPTOM_MODEL_PATH}")
    joblib.dump(model, Config.SYMPTOM_MODEL_PATH)

    processor_path = Config.MODELS_DIR / "symptom_processor.pkl"
    logger.info(f"Saving symptom preprocessor to {processor_path}")
    joblib.dump(processor, processor_path)

    logger.info("Symptom model training completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train stroke symptom-based risk model"
    )
    parser.add_argument(
        "--model_type",
        choices=["rf", "lr"],
        default="rf",
        help="Model type: 'rf' (RandomForest) or 'lr' (LogisticRegression).",
    )
    parser.add_argument(
        "--test_size",
        type=float,
        default=0.2,
        help="Proportion of validation data.",
    )

    args = parser.parse_args()
    main(model_type=args.model_type, test_size=args.test_size)
