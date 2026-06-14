#!/usr/bin/env python3
r"""
Evaluate the trained image model on a random sample of labeled MRI images.

Examples
--------
    .venv\Scripts\python.exe tests\evaluate_model.py
    .venv\Scripts\python.exe tests\evaluate_model.py --samples 100 --seed 42
"""

import argparse
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from config import Config
from tests.test_model import load_and_predict


def collect_labeled_images():
    """Return all labeled image paths and the ordered class names."""
    dataset_root = Config.TEST_IMAGE_DATASET_DIR
    class_names = sorted([path.name for path in dataset_root.iterdir() if path.is_dir()])
    samples = []
    valid_suffixes = {".jpg", ".jpeg", ".png"}

    for class_name in class_names:
        class_dir = dataset_root / class_name
        for image_path in sorted(class_dir.rglob("*")):
            if image_path.is_file() and image_path.suffix.lower() in valid_suffixes:
                samples.append((image_path, class_name))

    if not samples:
        raise FileNotFoundError(f"No images found under {dataset_root}")

    return samples, class_names


def build_confusion_matrix(class_names, y_true, y_pred):
    """Build a confusion matrix using the provided class ordering."""
    index_by_class = {class_name: idx for idx, class_name in enumerate(class_names)}
    matrix = [[0 for _ in class_names] for _ in class_names]

    for true_label, pred_label in zip(y_true, y_pred):
        matrix[index_by_class[true_label]][index_by_class[pred_label]] += 1

    return matrix


def format_confusion_matrix(class_names, matrix):
    """Render a compact text confusion matrix."""
    label_width = max(len(name) for name in class_names)
    cell_width = max(7, label_width + 2)
    header = "true\\pred".ljust(label_width + 2) + "".join(
        name.rjust(cell_width) for name in class_names
    )
    rows = [header]

    for class_name, row in zip(class_names, matrix):
        rows.append(class_name.ljust(label_width + 2) + "".join(str(value).rjust(cell_width) for value in row))

    return "\n".join(rows)


def evaluate_model(sample_count, seed):
    """Run evaluation on a deterministic subset and return a summary dict."""
    if sample_count <= 0:
        raise ValueError("sample_count must be greater than 0")

    all_samples, class_names = collect_labeled_images()
    evaluated_count = min(sample_count, len(all_samples))

    rng = random.Random(seed)
    selected_samples = rng.sample(all_samples, evaluated_count)

    y_true = []
    y_pred = []
    confidences = []
    per_class_counts = defaultdict(int)
    per_class_correct = defaultdict(int)
    mistakes = []

    for image_path, true_label in selected_samples:
        result = load_and_predict(image_path)
        predicted_label = result["predicted_class"]
        confidence = float(result["confidence"])

        y_true.append(true_label)
        y_pred.append(predicted_label)
        confidences.append(confidence)
        per_class_counts[true_label] += 1

        if predicted_label == true_label:
            per_class_correct[true_label] += 1
        else:
            mistakes.append(
                {
                    "image": str(image_path),
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "confidence": confidence,
                }
            )

    correct = sum(1 for true_label, pred_label in zip(y_true, y_pred) if true_label == pred_label)
    accuracy = correct / evaluated_count if evaluated_count else 0.0
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    confusion_matrix = build_confusion_matrix(class_names, y_true, y_pred)

    return {
        "evaluated_count": evaluated_count,
        "seed": seed,
        "accuracy": accuracy,
        "correct": correct,
        "average_confidence": average_confidence,
        "class_names": class_names,
        "per_class_counts": dict(per_class_counts),
        "per_class_correct": dict(per_class_correct),
        "confusion_matrix": confusion_matrix,
        "mistakes": mistakes,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate the image model on labeled MRI samples.")
    parser.add_argument("--samples", type=int, default=100, help="Number of random samples to evaluate.")
    parser.add_argument("--seed", type=int, default=Config.SEED, help="Random seed used for sampling.")
    parser.add_argument(
        "--show-errors",
        type=int,
        default=10,
        help="How many incorrect predictions to print.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    summary = evaluate_model(sample_count=args.samples, seed=args.seed)

    print("=== Model Evaluation ===")
    print(f"Dataset: {Config.TEST_IMAGE_DATASET_DIR}")
    print(f"Samples evaluated: {summary['evaluated_count']}")
    print(f"Sampling seed: {summary['seed']}")
    print(f"Final score (accuracy): {summary['accuracy'] * 100:.2f}%")
    print(f"Correct predictions: {summary['correct']}/{summary['evaluated_count']}")
    print(f"Average confidence: {summary['average_confidence']:.4f}")

    print("\nPer-class accuracy:")
    for class_name in summary["class_names"]:
        total = summary["per_class_counts"].get(class_name, 0)
        correct = summary["per_class_correct"].get(class_name, 0)
        class_accuracy = (correct / total) if total else 0.0
        print(f"  {class_name}: {correct}/{total} ({class_accuracy * 100:.2f}%)")

    print("\nConfusion matrix:")
    print(format_confusion_matrix(summary["class_names"], summary["confusion_matrix"]))

    if args.show_errors > 0 and summary["mistakes"]:
        print(f"\nSample mistakes (showing up to {args.show_errors}):")
        for mistake in summary["mistakes"][: args.show_errors]:
            print(
                f"  true={mistake['true_label']}, predicted={mistake['predicted_label']}, "
                f"confidence={mistake['confidence']:.4f}, image={mistake['image']}"
            )


if __name__ == "__main__":
    main()
