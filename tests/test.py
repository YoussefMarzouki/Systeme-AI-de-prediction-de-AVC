#!/usr/bin/env python3
import sys
import random
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_model import load_and_predict
from config import Config

def main():
    dataset_root = Config.IMAGE_DATASET_DIR
    sample_images = sorted(dataset_root.rglob("*"))
    sample_images = [p for p in sample_images if p.is_file()]
    if not sample_images:
        raise FileNotFoundError(f"No images found under {dataset_root}")

    image_path = random.choice(sample_images)
    result = load_and_predict(image_path)
    print("Prediction Result:")
    print(f"Image: {image_path}")
    print(f"Predicted Class: {result['predicted_class']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print("All Probabilities:")
    for cls, prob in result['probabilities'].items():
        print(f"  {cls}: {prob:.4f}")


if __name__ == "__main__":
    main()
