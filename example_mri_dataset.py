"""
Example usage of MRIDataset with PyTorch DataLoader for MRI stroke classification (JPG only).
"""

import torch
from torch.utils.data import DataLoader
from preprocessing.dataset import MRIDataset
from preprocessing.mri_transforms import MRITransforms
from config import Config

def main():
    # Example dataset structure (JPG only):
    # dataset/
    #   ├── stroke/
    #   │   ├── img1.jpg
    #   │   ├── img2.jpeg
    #   │   └── ...
    #   └── normal/
    #       ├── img3.jpg
    #       ├── img4.jpeg
    #       └── ...
    
    # Set your dataset path here
    dataset_path = "path/to/your/dataset"  # <-- Change this to your actual dataset path
    
    # Get transforms
    train_transform = MRITransforms.get_train_transforms()
    val_transform = MRITransforms.get_val_transforms()
    
    # Create datasets
    print("Loading training dataset...")
    train_dataset = MRIDataset(
        images_dir=dataset_path,
        transform=train_transform,
        split='train'
    )
    
    print("\nLoading validation dataset...")
    val_dataset = MRIDataset(
        images_dir=dataset_path,
        transform=val_transform,
        split='val'
    )
    
    # Create DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=True,
        num_workers=Config.NUM_WORKERS,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=False,
        num_workers=Config.NUM_WORKERS,
        pin_memory=True
    )
    
    # Print dataset information
    print(f"Number of classes: {train_dataset.get_num_classes()}")
    print(f"Class names: {train_dataset.get_class_names()}")
    print(f"JPG Class counts (train): {train_dataset.get_class_counts()}")
    print(f"JPG Class counts (val): {val_dataset.get_class_counts()}")
    
    # Example: Iterate through one batch
    print("\n" + "="*50)
    print("Sample batch from training data:")
    print("="*50)
    
    for batch_idx, (images, labels) in enumerate(train_loader):
        print(f"Batch {batch_idx}:")
        print(f"  Images shape: {images.shape}")  # Should be [batch_size, 3, 224, 224]
        print(f"  Labels shape: {labels.shape}")  # Should be [batch_size]
        print(f"  Label values: {labels.tolist()}")
        print(f"  Unique labels in batch: {torch.unique(labels).tolist()}")
        break  # Just show first batch
    
    print("\nDataset is ready for training!")

if __name__ == "__main__":
    main()