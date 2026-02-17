#!/usr/bin/env python3
"""
Script to test the trained stroke classification model
"""

import sys
from pathlib import Path

# Add parent directory to Python path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import cv2
from preprocessing.mri_transforms import MRITransforms
from models.image_classifier import StrokeImageClassifier
from config import Config

def _resolve_class_names():
    """Infer class names from the training dataset directory."""
    dataset_dir = Config.IMAGE_DATASET_DIR
    if dataset_dir.exists():
        classes = sorted([p.name for p in dataset_dir.iterdir() if p.is_dir()])
        if classes:
            if Config.ENFORCE_EXPECTED_IMAGE_CLASSES:
                missing = sorted(set(Config.EXPECTED_IMAGE_CLASSES) - set(classes))
                if missing:
                    raise ValueError(
                        f"Missing expected classes in {dataset_dir}: {missing}. "
                        f"Found classes: {classes}"
                    )
            return classes
    return list(Config.EXPECTED_IMAGE_CLASSES)


def _load_state_dict(path, device):
    """Load either a pure state_dict or a checkpoint dictionary."""
    loaded = torch.load(path, map_location=device)
    if isinstance(loaded, dict) and "model_state_dict" in loaded:
        return loaded["model_state_dict"]
    return loaded


def load_and_predict(image_path):
    """Load trained model and predict on single image"""
    # Ensure model file exists
    if not Config.IMAGE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {Config.IMAGE_MODEL_PATH}")
    
    # Load model
    device = Config.DEVICE
    class_names = _resolve_class_names()
    state_dict = _load_state_dict(Config.IMAGE_MODEL_PATH, device)
    checkpoint_num_classes = int(state_dict["classifier.11.weight"].shape[0])
    if checkpoint_num_classes != len(class_names):
        raise ValueError(
            "Model/output-class mismatch. "
            f"Checkpoint has {checkpoint_num_classes} classes, dataset expects {len(class_names)} "
            f"({class_names}). Retrain image model with dataset: {Config.IMAGE_DATASET_DIR}"
        )

    model = StrokeImageClassifier(num_classes=len(class_names), pretrained=False)
    model.load_state_dict(state_dict, strict=True)
    model = model.to(device)
    model.eval()
    
    # Load and preprocess image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    transform = MRITransforms.get_val_transforms()
    augmented = transform(image=image)
    image_tensor = augmented['image'].unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        predicted_class = torch.argmax(probabilities, dim=1)

    if probabilities.shape[1] != len(class_names):
        class_names = [f"class_{i}" for i in range(probabilities.shape[1])]
    
    return {
        'predicted_class': class_names[predicted_class.item()],
        'confidence': float(torch.max(probabilities).item()),
        'probabilities': {class_names[i]: float(prob) for i, prob in enumerate(probabilities[0])}
    }

if __name__ == "__main__":
    dataset_root = Config.IMAGE_DATASET_DIR
    sample_images = sorted(dataset_root.glob("*/*"))
    if sample_images:
        image_path = sample_images[0]
        result = load_and_predict(image_path)
        print("=== Model Test Results ===")
        print(f"Image: {image_path}")
        print(f"Predicted Class: {result['predicted_class']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print("Probabilities:")
        for cls, prob in result['probabilities'].items():
            print(f"  {cls}: {prob:.4f}")
    else:
        print(f"No test images found under: {dataset_root}")
