try:
    import torch
    _TORCH_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment specific
    torch = None
    _TORCH_IMPORT_ERROR = exc
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    # Get the project root directory (where config.py is located)
    PROJECT_ROOT = Path(__file__).parent.absolute()
    
    # Dataset paths
    DATASET_ROOT = PROJECT_ROOT / "dataset"
    IMAGES_DIR = DATASET_ROOT / "images"
    IMAGE_DATASET_DIR = DATASET_ROOT / "Dataset_MRI_Folder"
    SYMPTOMS_CSV = DATASET_ROOT / "rag" / "healthcare-dataset-stroke-data.csv"
    EXPECTED_IMAGE_CLASSES = ("Haemorrhagic", "Ischemic", "Normal")
    ENFORCE_EXPECTED_IMAGE_CLASSES = True
    
    # Model paths
    MODELS_DIR = PROJECT_ROOT / "models"
    IMAGE_MODEL_PATH = MODELS_DIR / "stroke_image_resnet18.pth"
    SYMPTOM_MODEL_PATH = MODELS_DIR / "stroke_symptoms_rf.pkl"
    FUSION_MODEL_PATH = MODELS_DIR / "risk_fusion_lr.pkl"
    
    # Training
    SEED = 42
    BATCH_SIZE = 8
    NUM_WORKERS = 0
    EPOCHS = 150
    LR = 0.01
    WEIGHT_DECAY = 1e-4
    PATIENCE = 30
    BACKBONE_LR_RATIO = 0.1
    
    # Model Architecture Configuration
    BACKBONE = "resnet18"  # 'resnet18' or 'resnet50'
    FREEZE_STRATEGY = "gradual"  # 'full', 'partial', 'gradual'
    USE_PRETRAINED = True  # Use ImageNet pretrained weights
    LABEL_SMOOTHING = 0.15
    GRADIENT_CLIP_NORM = 0.5
    
    # Data Augmentation Configuration
    AUGMENTATION_STRENGTH = "strong"  # 'light', 'medical', 'strong'
    Z_SCORE_NORMALIZE = True
    
    # Domain Separation Configuration
    DOMAIN_AWARE_TRAINING = True
    MIN_DOMAIN_SAMPLES = 10
    TEST_SPLIT_RATIO = 0.2
    
    # Evaluation Metrics
    CONFIDENCE_THRESHOLD = 0.7
    RISK_THRESHOLDS = {"LOW": 0.3, "MEDIUM": 0.5, "HIGH": 0.7}
    SAVE_CONFUSION_MATRIX = True
    SAVE_PER_CLASS_METRICS = True
    
    # Device and Performance
    if torch is not None:
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        DEVICE = "cpu"
    USE_AMP = False  # Automatic Mixed Precision
    PIN_MEMORY = True
    
    # Logging and Monitoring
    SAVE_CHECKPOINTS = True
    SAVE_TRAINING_HISTORY = True
    LOG_INTERVAL = 10
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories if they don't exist."""
        dirs_to_create = [cls.MODELS_DIR, cls.DATASET_ROOT]
        for path in dirs_to_create:
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def torch_available(cls):
        """Whether torch imported successfully in this environment."""
        return torch is not None
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of key configuration parameters"""
        return {
            'device': str(cls.DEVICE),
            'batch_size': cls.BATCH_SIZE,
            'learning_rate': cls.LR,
            'epochs': cls.EPOCHS,
            'backbone': cls.BACKBONE,
            'freeze_strategy': cls.FREEZE_STRATEGY,
            'domain_aware': cls.DOMAIN_AWARE_TRAINING,
            'augmentation_strength': cls.AUGMENTATION_STRENGTH
        }
