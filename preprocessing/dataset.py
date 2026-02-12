import torch
from torch.utils.data import Dataset
from PIL import Image
import pandas as pd
import cv2
import numpy as np
from pathlib import Path
from .mri_transforms import MRITransforms

class MRIDataset(Dataset):
    def __init__(self, images_dir, transform=None, split='train'):
        self.images_dir = Path(images_dir)
        self.transform = transform
        
        self.samples = []
        for label, folder in enumerate(['normal', 'stroke']):
            folder_path = self.images_dir / folder
            if folder_path.exists():
                for img_path in folder_path.glob('*.jpg'):
                    self.samples.append((str(img_path), label))
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        # Load with OpenCV for albumentations
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if self.transform:
            augmented = self.transform(image=image)
            image = augmented['image']
        
        return image, torch.tensor(label, dtype=torch.long)
