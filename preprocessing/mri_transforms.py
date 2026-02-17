import albumentations as A
from albumentations.pytorch import ToTensorV2
import numpy as np
import inspect


class ZScoreNormalize(A.ImageOnlyTransform):
    """Per-image Z-score normalization for MRI intensity standardization"""
    def __init__(self, always_apply=False, p=1.0):
        super(ZScoreNormalize, self).__init__(always_apply, p)
    
    def apply(self, img, **params):
        # Convert to float for numerical stability
        img_float = img.astype(np.float32)
        # Calculate per-channel statistics
        mean = np.mean(img_float, axis=(0, 1), keepdims=True)
        std = np.std(img_float, axis=(0, 1), keepdims=True)
        # Avoid division by zero
        std = np.maximum(std, 1e-8)
        # Z-score normalization
        normalized = (img_float - mean) / std
        # Clip to reasonable range to handle outliers
        normalized = np.clip(normalized, -3, 3)
        # Scale to [0, 1] for albumentations compatibility
        normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min() + 1e-8)
        return normalized.astype(np.float32)


class MRITransforms:
    @staticmethod
    def _gauss_noise_transform(p=0.3):
        """Create GaussNoise transform compatible with multiple albumentations versions."""
        gauss_noise_params = inspect.signature(A.GaussNoise).parameters
        if "std_range" in gauss_noise_params:
            return A.GaussNoise(
                std_range=(0.04, 0.2),
                mean_range=(0.0, 0.0),
                per_channel=True,
                p=p,
            )
        return A.GaussNoise(
            var_limit=(0.0016, 0.04),
            mean=0,
            per_channel=True,
            p=p,
        )

    @staticmethod
    def get_train_transforms():
        return A.Compose([
            # MRI-specific preprocessing
            ZScoreNormalize(p=1.0),
            A.Resize(224, 224),
            
            # Strong MRI-appropriate augmentations
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.RandomRotate90(p=0.5),
            
            # Intensity augmentations (crucial for MRI generalization)
            A.RandomBrightnessContrast(
                brightness_limit=0.2,  # Reduced for medical realism
                contrast_limit=0.2,
                brightness_by_max=True,
                p=0.4
            ),
            A.RandomGamma(
                gamma_limit=(80, 120),  # Subtle gamma correction
                p=0.3
            ),
            
            # Noise and blur for robustness
            MRITransforms._gauss_noise_transform(p=0.3),
            A.GaussianBlur(
                blur_limit=(3, 5),  # Slight blur
                sigma_limit=(0.1, 1.0),
                p=0.2
            ),
            
            # Final normalization (ImageNet stats for pretrained models)
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
    
    @staticmethod
    def get_val_transforms():
        return A.Compose([
            # Same preprocessing as training (crucial for consistency)
            ZScoreNormalize(p=1.0),
            A.Resize(224, 224),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
    
    @staticmethod
    def get_test_transforms():
        """Identical to validation transforms for consistent inference"""
        return MRITransforms.get_val_transforms()
