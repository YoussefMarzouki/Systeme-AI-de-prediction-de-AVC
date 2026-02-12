import torch
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    # Dataset paths
    DATASET_ROOT = Path("dataset")
    IMAGES_DIR = DATASET_ROOT / "images"
    SYMPTOMS_CSV = DATASET_ROOT / "symptoms.csv"
    
    # Model paths
    MODELS_DIR = Path("models")
    IMAGE_MODEL_PATH = MODELS_DIR / "stroke_image_resnet18.pth"
    SYMPTOM_MODEL_PATH = MODELS_DIR / "stroke_symptoms_rf.pkl"
    FUSION_MODEL_PATH = MODELS_DIR / "risk_fusion_lr.pkl"
    
    # Training
    SEED = 42
    BATCH_SIZE = 16
    NUM_WORKERS = 4
    EPOCHS = 50
    LR = 1e-4
    WEIGHT_DECAY = 1e-4
    PATIENCE = 10
    
    # Thresholds
    CONFIDENCE_THRESHOLD = 0.7
    RISK_THRESHOLDS = {"LOW": 0.3, "MEDIUM": 0.7, "HIGH": 0.7}
    
    # Device
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    @classmethod
    def ensure_dirs(cls):
        for path in [cls.MODELS_DIR]:
            path.mkdir(exist_ok=True)
