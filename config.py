import os

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
    IMAGE_DATASET_DIR = DATASET_ROOT / "image trainning"
    TEST_IMAGE_DATASET_DIR = IMAGE_DATASET_DIR / "test"
    EXPECTED_IMAGE_CLASSES = ("Hemorrhagic", "Ischemic", "Normal")
    ENFORCE_EXPECTED_IMAGE_CLASSES = True
    
    # Model paths
    MODELS_DIR = PROJECT_ROOT / "models"
    IMAGE_MODEL_PATH = MODELS_DIR / "stroke_image_resnet18.pth"
    
    # Training
    SEED = 42
    BATCH_SIZE = 32  # Increased from 8 to speed up training epochs
    NUM_WORKERS = 2  # Restored! cv2.setNumThreads(0) should fix the silent crashes
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
    CONFIDENCE_THRESHOLD = 0.3
    RISK_THRESHOLDS = {"LOW": 0.3, "MEDIUM": 0.5, "HIGH": 0.7}
    SAVE_CONFUSION_MATRIX = True
    SAVE_PER_CLASS_METRICS = True
    
    # Device and Performance
    if torch is not None:
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        DEVICE = "cpu"
    USE_AMP = True   # Enabled Automatic Mixed Precision for 2x-3x speedup on GPU
    PIN_MEMORY = True

    # Logging and Monitoring
    SAVE_CHECKPOINTS = True
    SAVE_TRAINING_HISTORY = True
    LOG_INTERVAL = 10

    # ---------------------------------------------------------------------------
    # Gemini / Groq AI + RAG Symptom System
    # ---------------------------------------------------------------------------
    LM_STUDIO_BASE_URL: str = os.environ.get("LM_STUDIO_BASE_URL", "")
    LM_STUDIO_MODEL:    str = os.environ.get("LM_STUDIO_MODEL", "microsoft/phi-4-mini-reasoning")
    LM_STUDIO_TIMEOUT:  int = int(os.environ.get("LM_STUDIO_TIMEOUT", "5"))
    OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL:   str = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    GROQ_API_KEY:   str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL:     str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    RAG_KB_DIR         = DATASET_ROOT / "rag"
    RAG_TEMPLATE_FILE  = RAG_KB_DIR / "AVC_RAG_Answer_Template_FR.docx.txt"
    RAG_CASES_FILE     = RAG_KB_DIR / "AVC_Test_Cases_FR.txt"
    RAG_KNOWLEDGE_BASE_FILE = RAG_KB_DIR / "AVC_RAG_Knowledge_Base.txt"
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories if they don't exist."""
        dirs_to_create = [cls.MODELS_DIR, cls.DATASET_ROOT, cls.TEST_IMAGE_DATASET_DIR]
        for path in dirs_to_create:
            path.mkdir(parents=True, exist_ok=True)
        for class_name in cls.EXPECTED_IMAGE_CLASSES:
            (cls.TEST_IMAGE_DATASET_DIR / class_name).mkdir(parents=True, exist_ok=True)

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
