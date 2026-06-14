from pathlib import Path

import cv2
# Prevent OpenCV from competing with PyTorch workers leading to deadlocks/crashes
cv2.setNumThreads(0)

import numpy as np
import torch
from loguru import logger
from torch.utils.data import Dataset

from .mri_transforms import MRITransforms


class MRIDataset(Dataset):
    """MRI dataset with deterministic sample ordering and optional subsetting."""

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")

    def __init__(
        self,
        images_dir,
        transform=None,
        split="train",
        samples=None,
        class_names=None,
        class_to_idx=None,
        verbose=False,
    ):
        self.images_dir = Path(images_dir)
        self.transform = transform
        self.split = split

        if not self.images_dir.exists():
            raise FileNotFoundError(f"Dataset directory does not exist: {self.images_dir}")
        if not self.images_dir.is_dir():
            raise ValueError(f"Expected a directory for dataset root: {self.images_dir}")

        self.classes = class_names or self._discover_classes()
        if not self.classes:
            raise ValueError(f"No class folders found in {self.images_dir}")

        self.class_to_idx = class_to_idx or {
            class_name: idx for idx, class_name in enumerate(self.classes)
        }
        self.samples = list(samples) if samples is not None else self._load_samples()

        if not self.samples:
            raise ValueError(f"No valid images found in {self.images_dir}")

        if verbose:
            self._log_dataset_info()

    def _discover_classes(self):
        return sorted(
            d.name for d in self.images_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        )

    def _load_samples(self):
        """Load all image paths and labels in a deterministic, recursive way."""
        samples = []

        for class_name in self.classes:
            class_idx = self.class_to_idx[class_name]
            class_path = self.images_dir / class_name
            if not class_path.exists() or not class_path.is_dir():
                logger.warning(f"Skipping missing class directory: {class_path}")
                continue

            class_images = []
            for ext in self.IMAGE_EXTENSIONS:
                class_images.extend(class_path.rglob(f"*{ext}"))

            for img_path in sorted(class_images, key=lambda p: p.name.lower()):
                if img_path.is_file():
                    samples.append((str(img_path), class_idx))

            if not class_images:
                logger.warning(f"No valid images found in class directory: {class_path}")

        return samples

    def _log_dataset_info(self):
        class_counts = self.get_class_counts()
        logger.info(
            "Loaded {} split: {} samples, classes={}",
            self.split,
            len(self.samples),
            self.classes,
        )
        logger.info("Class distribution: {}", class_counts)

    def subset(self, indices, split=None, transform=None):
        """Return a dataset view containing only the selected sample indices."""
        filtered_samples = [self.samples[i] for i in indices]
        return MRIDataset(
            images_dir=self.images_dir,
            transform=self.transform if transform is None else transform,
            split=self.split if split is None else split,
            samples=filtered_samples,
            class_names=self.classes,
            class_to_idx=self.class_to_idx,
            verbose=False,
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"Could not load image: {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if self.transform is not None:
            transformed = self.transform(image=image)
            if isinstance(transformed, dict) and "image" in transformed:
                image = transformed["image"]
            else:
                image = transformed
        else:
            image = self._basic_transform(image)

        return image, torch.tensor(label, dtype=torch.long)

    def _basic_transform(self, image):
        transform = MRITransforms.get_val_transforms()
        augmented = transform(image=np.asarray(image))
        return augmented["image"]

    def get_class_counts(self):
        counts = {cls: 0 for cls in self.classes}
        for _, label in self.samples:
            counts[self.classes[label]] += 1
        return counts

    def get_class_names(self):
        return self.classes

    def get_num_classes(self):
        return len(self.classes)
