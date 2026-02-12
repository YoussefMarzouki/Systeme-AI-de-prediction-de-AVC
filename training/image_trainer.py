import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from sklearn.model_selection import KFold
from tqdm import tqdm
import numpy as np
from loguru import logger
from ..preprocessing.dataset import MRIDataset
from ..preprocessing.mri_transforms import MRITransforms
from ..models.image_classifier import StrokeImageClassifier
from ..utils.metrics import compute_metrics
from ..config import Config

class ImageTrainer:
    def __init__(self, images_dir):
        self.images_dir = images_dir
        torch.manual_seed(Config.SEED)
        np.random.seed(Config.SEED)
    
    def train_kfold(self, n_splits=5):
        """K-fold cross-validation training"""
        dataset = MRIDataset(self.images_dir)
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=Config.SEED)
        
        best_val_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(dataset)):
            logger.info(f"Training Fold {fold + 1}/{n_splits}")
            
            train_dataset = torch.utils.data.Subset(dataset, train_idx)
            val_dataset = torch.utils.data.Subset(dataset, val_idx)
            
            train_loader = DataLoader(
                train_dataset, batch_size=Config.BATCH_SIZE,
                shuffle=True, num_workers=Config.NUM_WORKERS,
                pin_memory=True
            )
            val_loader = DataLoader(
                val_dataset, batch_size=Config.BATCH_SIZE,
                shuffle=False, num_workers=Config.NUM_WORKERS
            )
            
            model = StrokeImageClassifier().to(Config.DEVICE)
            self._train_fold(model, train_loader, val_loader, fold)
            val_score = self._evaluate(model, val_loader)
            best_val_scores.append(val_score)
        
        logger.info(f"Mean CV F1: {np.mean(best_val_scores):.4f} ± {np.std(best_val_scores):.4f}")
        return np.mean(best_val_scores)
    
    def _train_fold(self, model, train_loader, val_loader, fold):
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=Config.LR, weight_decay=Config.WEIGHT_DECAY
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
        
        best_f1 = 0
        patience_counter = 0
        
        for epoch in range(Config.EPOCHS):
            model.train()
            train_loss = 0
            for images, labels in tqdm(train_loader, desc=f"Fold {fold} Epoch {epoch}"):
                images, labels = images.to(Config.DEVICE), labels.to(Config.DEVICE)
                
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += loss.item()
            
            val_f1 = self._evaluate(model, val_loader, return_f1=True)
            scheduler.step(val_f1)
            
            if val_f1 > best_f1:
                best_f1 = val_f1
                patience_counter = 0
                torch.save(model.state_dict(), Config.IMAGE_MODEL_PATH)
            else:
                patience_counter += 1
                
            if patience_counter >= Config.PATIENCE:
                logger.info(f"Early stopping at epoch {epoch}")
                break
    
    def _evaluate(self, model, loader, return_f1=False):
        model.eval()
        all_preds, all_labels, all_probs = [], [], []
        
        with torch.no_grad():
            for images, labels in loader:
                images, labels = images.to(Config.DEVICE), labels.to(Config.DEVICE)
                outputs = model(images)
                probs = torch.softmax(outputs, dim=1)
                preds = torch.argmax(probs, dim=1)
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probs.extend(probs.cpu().numpy())
        
        metrics = compute_metrics(all_labels, all_preds)
        if return_f1:
            return metrics['f1']
        return metrics
