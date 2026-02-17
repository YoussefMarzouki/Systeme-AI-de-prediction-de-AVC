#!/usr/bin/env python3
"""
Test script to verify that all paths are correctly configured
"""

from config import Config
from pathlib import Path
import torch

def test_paths():
    print("=== Testing Path Configuration ===")
    print(f"Project Root: {Config.PROJECT_ROOT}")
    print(f"Models Directory: {Config.MODELS_DIR}")
    print(f"Image Model Path: {Config.IMAGE_MODEL_PATH}")
    print(f"Symptom Model Path: {Config.SYMPTOM_MODEL_PATH}")
    print(f"Dataset Root: {Config.DATASET_ROOT}")
    
    print("\n=== Testing Directory Creation ===")
    Config.ensure_dirs()
    
    print(f"\nModels directory exists: {Config.MODELS_DIR.exists()}")
    print(f"Dataset directory exists: {Config.DATASET_ROOT.exists()}")
    
    print(f"\n=== Testing Model Path Resolution ===")
    print(f"Absolute path: {Config.IMAGE_MODEL_PATH.absolute()}")
    print(f"Path exists: {Config.IMAGE_MODEL_PATH.exists()}")
    
    if Config.IMAGE_MODEL_PATH.exists():
        try:
            # Test loading the model file
            state_dict = torch.load(Config.IMAGE_MODEL_PATH, map_location='cpu')
            print(f"Model file loaded successfully. Keys: {len(state_dict.keys())}")
        except Exception as e:
            print(f"Error loading model: {e}")
    else:
        print("Model file not found (this is expected if not trained yet)")

if __name__ == "__main__":
    test_paths()