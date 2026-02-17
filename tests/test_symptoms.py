#!/usr/bin/env python3
"""
Test script for symptom-model training and inference using a small synthetic CSV.
"""

import sys
import random
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.metrics import confusion_matrix, roc_curve
from sklearn.model_selection import train_test_split

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.symptom_classifier import SymptomClassifier
from preprocessing.symptom_processor import SymptomProcessor


def _feature_names_from_processor(processor: SymptomProcessor):
    pre = processor.preprocessor
    names = []
    if "num" in pre.named_transformers_:
        names.extend(processor.selected_numerical_features)
    if "cat" in pre.named_transformers_:
        cat_pipe = pre.named_transformers_["cat"]
        onehot = cat_pipe.named_steps["onehot"]
        cat_names = list(onehot.get_feature_names_out(processor.selected_categorical_features))
        names.extend(cat_names)
    return names


def _bar(value: float, max_value: float, width: int = 30) -> str:
    if max_value <= 0:
        return ""
    n = int(round((value / max_value) * width))
    return "#" * max(0, n)


def _print_terminal_visuals(y_test, y_pred, y_prob, model, processor) -> None:
    print("\n=== Confusion Matrix (Terminal) ===")
    cm = confusion_matrix(y_test, y_pred)
    print("               Pred 0   Pred 1")
    print(f"True 0      {cm[0, 0]:8d} {cm[0, 1]:8d}")
    print(f"True 1      {cm[1, 0]:8d} {cm[1, 1]:8d}")

    print("\n=== ROC Summary (Terminal) ===")
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    print(f"AUC: {auc:.4f}")
    print("Top ROC points (threshold, FPR, TPR):")
    limit = min(8, len(thresholds))
    for i in range(limit):
        print(f"  {thresholds[i]:7.4f} | {fpr[i]:7.4f} | {tpr[i]:7.4f}")

    print("\n=== Probability Histogram (Terminal) ===")
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    c0 = [0] * (len(bins) - 1)
    c1 = [0] * (len(bins) - 1)
    for prob, label in zip(y_prob, y_test):
        idx = len(bins) - 2
        for j in range(len(bins) - 1):
            if bins[j] <= prob < bins[j + 1]:
                idx = j
                break
        if label == 0:
            c0[idx] += 1
        else:
            c1[idx] += 1
    max_count = max(c0 + c1) if (c0 + c1) else 1
    for j in range(len(bins) - 1):
        label = f"[{bins[j]:.1f}, {bins[j + 1]:.1f})"
        print(
            f"{label}  y=0 {c0[j]:2d} {_bar(c0[j], max_count)}   "
            f"y=1 {c1[j]:2d} {_bar(c1[j], max_count)}"
        )

    if hasattr(model.model, "feature_importances_"):
        print("\n=== Top Feature Importances (Terminal) ===")
        feature_names = _feature_names_from_processor(processor)
        importances = model.model.feature_importances_
        pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:12]
        max_imp = pairs[0][1] if pairs else 1.0
        for name, imp in pairs:
            print(f"{name:35s} {imp:8.4f} {_bar(imp, max_imp)}")


def run_symptom_test(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "stroke" not in df.columns:
        raise ValueError("Expected 'stroke' target column in test CSV.")

    processor = SymptomProcessor()
    X = processor.fit(df)
    y = df["stroke"].astype(int).values

    split_seed = random.randint(0, 10_000_000)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=split_seed, stratify=y
    )

    model = SymptomClassifier()
    model.model.set_params(class_weight="balanced")
    model.fit(X_train, y_train)
    model.processor = processor

    y_pred = model.model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    print("=== Symptom Model Test ===")
    print(f"CSV: {csv_path}")
    print(f"Rows: {len(df)}")
    report_text = classification_report(y_test, y_pred, digits=4)
    auc_value = roc_auc_score(y_test, y_prob)
    print(report_text)
    print(f"ROC-AUC: {auc_value:.4f}")

    sample_idx = random.randint(0, len(df) - 1)
    feature_cols = [c for c in df.columns if c != "stroke"]
    sample_df = df.loc[[sample_idx], feature_cols].copy()
    sample_prob = model.predict_proba(model.processor.transform(sample_df))[0]
    true_label = int(df.loc[sample_idx, "stroke"])
    print(f"Random split seed: {split_seed}")
    print(f"Random sample index: {sample_idx} (true stroke={true_label})")
    print(f"Sample stroke probability: {sample_prob:.4f}")

    _print_terminal_visuals(
        y_test=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
        model=model,
        processor=processor,
    )


if __name__ == "__main__":
    default_csv = Path(__file__).parent / "data" / "symptoms_test_data.csv"
    run_symptom_test(default_csv)
