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
    """Infer class names from the configured test dataset directory."""
    dataset_dir = Config.TEST_IMAGE_DATASET_DIR
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
    try:
        loaded = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        # Older torch versions do not support `weights_only`.
        loaded = torch.load(path, map_location=device)
    if isinstance(loaded, dict) and "model_state_dict" in loaded:
        return loaded["model_state_dict"]
    return loaded


def _infer_num_classes_from_state_dict(state_dict):
    """Infer output dimension from known or discovered classifier-weight keys."""
    preferred_keys = (
        "backbone.fc.4.weight",  # current ResNet head in this project
        "backbone.fc.weight",    # plain ResNet fc layer
        "classifier.11.weight",  # legacy head used in older checkpoints
    )
    for key in preferred_keys:
        tensor = state_dict.get(key)
        if isinstance(tensor, torch.Tensor) and tensor.ndim == 2:
            return int(tensor.shape[0])

    candidates = []
    for key, tensor in state_dict.items():
        if not isinstance(tensor, torch.Tensor):
            continue
        if tensor.ndim != 2 or not key.endswith(".weight"):
            continue
        if "classifier" not in key and ".fc" not in key and "head" not in key:
            continue
        candidates.append((int(tensor.shape[0]), key))

    if not candidates:
        sample_keys = list(state_dict.keys())[:10]
        raise KeyError(
            "Could not infer classifier output layer from checkpoint state_dict. "
            f"Sample keys: {sample_keys}"
        )

    # In this codebase the final layer has the smallest output dimension (num_classes).
    inferred_num_classes, _ = min(candidates, key=lambda item: item[0])
    return inferred_num_classes


def load_and_predict(image_path):
    """Load trained model and predict on single image"""
    # Ensure model file exists
    if not Config.IMAGE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {Config.IMAGE_MODEL_PATH}")
    
    # Load model
    device = Config.DEVICE
    class_names = _resolve_class_names()
    state_dict = _load_state_dict(Config.IMAGE_MODEL_PATH, device)
    checkpoint_num_classes = _infer_num_classes_from_state_dict(state_dict)
    if checkpoint_num_classes != len(class_names):
        raise ValueError(
            "Model/output-class mismatch. "
            f"Checkpoint has {checkpoint_num_classes} classes, dataset expects {len(class_names)} "
            f"({class_names}). Ensure test dataset classes match the model classes: {Config.TEST_IMAGE_DATASET_DIR}"
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
    dataset_root = Config.TEST_IMAGE_DATASET_DIR
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
