import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from loguru import logger
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import Config
from models.image_classifier import StrokeImageClassifier
from preprocessing.dataset import MRIDataset
from preprocessing.mri_transforms import MRITransforms
from utils.metrics import compute_metrics

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:  # pragma: no cover
    StratifiedGroupKFold = None


class ImageTrainer:
    """Clean image training pipeline with optional domain-aware K-fold training."""

    def __init__(self, images_dir, domain_info=None):
        self.images_dir = Path(images_dir)
        self.domain_info = domain_info or {}
        self.device = Config.DEVICE
        self.training_history = []

        self._set_seeds()
        Config.ensure_dirs()

    def _set_seeds(self):
        random.seed(Config.SEED)
        np.random.seed(Config.SEED)
        torch.manual_seed(Config.SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(Config.SEED)
            torch.cuda.manual_seed_all(Config.SEED)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def train(self):
        """Train using explicit train/valid/test split directories."""
        logger.info("Starting image training with explicit train/valid/test splits")
        
        train_dir = self.images_dir / "train"
        valid_dir = self.images_dir / "valid"
        test_dir = self.images_dir / "test"
        
        if not train_dir.exists() or not valid_dir.exists() or not test_dir.exists():
            raise FileNotFoundError(f"Dataset directory {self.images_dir} must contain 'train', 'valid', and 'test' subdirectories.")
            
        train_dataset = MRIDataset(
            train_dir,
            transform=MRITransforms.get_train_transforms(),
            split="train",
            class_names=list(Config.EXPECTED_IMAGE_CLASSES),
            verbose=True,
        )
        self._validate_expected_classes(train_dataset.classes)
        
        val_dataset = MRIDataset(
            valid_dir,
            transform=MRITransforms.get_val_transforms(),
            split="val",
            class_names=list(Config.EXPECTED_IMAGE_CLASSES),
            verbose=True,
        )
        
        test_dataset = MRIDataset(
            test_dir,
            transform=MRITransforms.get_val_transforms(),
            split="test",
            class_names=list(Config.EXPECTED_IMAGE_CLASSES),
            verbose=True,
        )
        
        logger.info(
            "Split sizes | train={} valid={} test={}",
            len(train_dataset),
            len(val_dataset),
            len(test_dataset),
        )

        train_loader = self._create_dataloader(
            train_dataset,
            shuffle=True,
            seed=Config.SEED,
        )
        val_loader = self._create_dataloader(
            val_dataset,
            shuffle=False,
            seed=Config.SEED + 1000,
        )
        test_loader = self._create_dataloader(
            test_dataset,
            shuffle=False,
            seed=Config.SEED + 2000,
        )

        model = self._build_model(num_classes=train_dataset.get_num_classes())
        fold_result, best_state = self._train_fold(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            fold_name="training",
        )
        
        # Load the best model state to evaluate on the test set
        model.load_state_dict(best_state)
        torch.save(best_state, Config.IMAGE_MODEL_PATH)
        logger.info("Saved best model at {}", Config.IMAGE_MODEL_PATH)
        
        # Evaluate on test set
        criterion = nn.CrossEntropyLoss()
        test_loss, test_metrics = self._evaluate(model, test_loader, criterion)
        logger.info("Test set evaluation: loss={:.4f} f1={:.4f} acc={:.4f}", test_loss, test_metrics["f1"], test_metrics["accuracy"])
        
        fold_result["test_f1"] = float(test_metrics["f1"])
        fold_result["test_accuracy"] = float(test_metrics["accuracy"])
        fold_result["test_metrics"] = dict(test_metrics)
        
        cv_results = [fold_result]
        self._save_training_results(cv_results=cv_results, mean_f1=fold_result["f1"], std_f1=0.0)
        
        return fold_result["test_f1"]

    def _validate_expected_classes(self, discovered_classes):
        if not Config.ENFORCE_EXPECTED_IMAGE_CLASSES:
            return

        expected = set(Config.EXPECTED_IMAGE_CLASSES)
        found = set(discovered_classes)
        missing = sorted(expected - found)
        if missing:
            raise ValueError(
                "Missing expected image classes in training dataset "
                f"{self.images_dir}: {missing}. "
                f"Found classes: {sorted(discovered_classes)}"
            )

    def _resolve_n_splits(self, labels, requested_splits):
        class_counts = np.bincount(labels)
        nonzero_counts = class_counts[class_counts > 0]
        if len(nonzero_counts) < 2:
            raise ValueError("At least two classes with samples are required for training.")

        max_stratified_splits = int(nonzero_counts.min())
        effective_splits = min(requested_splits, max_stratified_splits)
        if effective_splits < 2:
            raise ValueError(
                f"Not enough samples per class for K-fold. "
                f"Minimum class count is {max_stratified_splits}."
            )
        if effective_splits != requested_splits:
            logger.warning(
                "Reducing n_splits from {} to {} due to class counts",
                requested_splits,
                effective_splits,
            )
        return effective_splits

    def _build_split_iterator(self, indices, labels, samples, n_splits):
        labels_array = np.asarray(labels, dtype=np.int64)
        num_classes = int(len(np.unique(labels_array)))

        if Config.DOMAIN_AWARE_TRAINING and StratifiedGroupKFold is not None:
            groups = np.array(
                [self._extract_scanner_name(Path(path).name) for path, _ in samples],
                dtype=object,
            )
            unique_groups, group_counts = np.unique(groups, return_counts=True)
            fragmented_groups = np.max(group_counts) <= 1
            if len(unique_groups) >= n_splits and not fragmented_groups:
                logger.info(
                    "Using StratifiedGroupKFold with {} scanner groups",
                    len(unique_groups),
                )
                splitter = StratifiedGroupKFold(
                    n_splits=n_splits,
                    shuffle=True,
                    random_state=Config.SEED,
                )
                grouped_splits = list(splitter.split(indices, labels_array, groups=groups))
                problematic_folds = self._find_folds_missing_classes(
                    grouped_splits,
                    labels_array,
                    num_classes,
                )
                if not problematic_folds:
                    return grouped_splits

                logger.warning(
                    "Domain-aware split produced folds with missing classes ({} problematic folds, examples={}). "
                    "Falling back to StratifiedKFold for stable validation metrics.",
                    len(problematic_folds),
                    problematic_folds[:3],
                )
            else:
                logger.warning(
                    "Domain-aware split disabled: groups are not usable (need >= {} groups, got {}, max group size={})",
                    n_splits,
                    len(unique_groups),
                    int(np.max(group_counts)) if len(group_counts) else 0,
                )

        logger.info("Using StratifiedKFold split")
        splitter = StratifiedKFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=Config.SEED,
        )
        return list(splitter.split(indices, labels_array))

    def _find_folds_missing_classes(self, split_iterator, labels, num_classes):
        problematic_folds = []
        for fold_idx, (_, val_idx) in enumerate(split_iterator, start=1):
            fold_counts = np.bincount(labels[val_idx], minlength=num_classes)
            missing_classes = [int(class_idx) for class_idx in np.where(fold_counts == 0)[0].tolist()]
            if missing_classes:
                problematic_folds.append(
                    {
                        "fold": int(fold_idx),
                        "val_size": int(len(val_idx)),
                        "missing_class_indices": missing_classes,
                    }
                )
        return problematic_folds

    def _extract_scanner_name(self, filename):
        stem = Path(filename).stem
        if "_" in stem:
            return stem.split("_", 1)[0].strip().lower()
        if "-" in stem:
            return stem.split("-", 1)[0].strip().lower()
        return "unknown_scanner"

    def _create_dataloader(self, dataset, shuffle, seed):
        generator = torch.Generator()
        generator.manual_seed(seed)
        return DataLoader(
            dataset,
            batch_size=Config.BATCH_SIZE,
            shuffle=shuffle,
            num_workers=Config.NUM_WORKERS,
            pin_memory=bool(Config.PIN_MEMORY and self.device.type == "cuda"),
            generator=generator,
            drop_last=shuffle,
        )

    def _build_model(self, num_classes):
        return StrokeImageClassifier(
            num_classes=num_classes,
            pretrained=Config.USE_PRETRAINED,
            backbone=Config.BACKBONE,
            freeze_strategy=Config.FREEZE_STRATEGY,
        ).to(self.device)

    def _train_fold(self, model, train_loader, val_loader, fold_name):
        train_labels = np.array(
            [int(label) for _, label in train_loader.dataset.samples],
            dtype=np.int64,
        )
        class_weights = self._compute_class_weights(train_labels, model.num_classes).to(self.device)
        criterion = nn.CrossEntropyLoss(
            weight=class_weights,
            label_smoothing=Config.LABEL_SMOOTHING,
        )

        backbone_params, classifier_params = model.get_backbone_parameters()
        optimizer_groups = []
        if backbone_params:
            optimizer_groups.append(
                {"params": backbone_params, "lr": Config.LR * Config.BACKBONE_LR_RATIO}
            )
        optimizer_groups.append({"params": classifier_params, "lr": Config.LR})

        optimizer = optim.SGD(
            optimizer_groups,
            momentum=0.9,
            weight_decay=Config.WEIGHT_DECAY,
            nesterov=True,
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=0.5,
            patience=max(3, Config.PATIENCE // 4),
        )

        scaler = torch.amp.GradScaler(
            device="cuda",
            enabled=bool(Config.USE_AMP and self.device.type == "cuda"),
        )

        best_metrics = None
        best_state = None
        best_epoch = -1
        patience_counter = 0
        fold_history = []

        for epoch in range(1, Config.EPOCHS + 1):
            model.gradual_unfreeze(epoch - 1, Config.EPOCHS)

            train_loss, train_metrics = self._train_one_epoch(
                model=model,
                loader=train_loader,
                criterion=criterion,
                optimizer=optimizer,
                scaler=scaler,
            )
            val_loss, val_metrics = self._evaluate(model, val_loader, criterion)
            scheduler.step(val_metrics["f1"])

            current_lr = float(max(group["lr"] for group in optimizer.param_groups))
            epoch_record = {
                "fold": fold_name,
                "epoch": epoch,
                "lr": current_lr,
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
                "train_metrics": train_metrics,
                "val_metrics": val_metrics,
            }
            fold_history.append(epoch_record)

            logger.info(
                "{} Epoch {}/{} | train_loss={:.4f} val_loss={:.4f} val_f1={:.4f} lr={:.6f}",
                fold_name,
                epoch,
                Config.EPOCHS,
                train_loss,
                val_loss,
                val_metrics["f1"],
                current_lr,
            )

            if best_metrics is None or val_metrics["f1"] > best_metrics["f1"]:
                best_metrics = val_metrics
                best_epoch = epoch
                patience_counter = 0
                best_state = {
                    key: value.detach().cpu().clone() for key, value in model.state_dict().items()
                }
                self._save_checkpoint(
                    model=model,
                    optimizer=optimizer,
                    epoch=epoch,
                    metrics=val_metrics,
                    fold_name=fold_name,
                )
            else:
                patience_counter += 1

            if patience_counter >= Config.PATIENCE:
                logger.info("Early stopping for {} at epoch {}", fold_name, epoch)
                break

        self.training_history.extend(fold_history)
        fold_result = {
            "fold_name": fold_name,
            "best_epoch": int(best_epoch),
            "f1": float(best_metrics["f1"]),
            "accuracy": float(best_metrics["accuracy"]),
            "precision": float(best_metrics["precision"]),
            "sensitivity": float(best_metrics["sensitivity"]),
            "specificity": float(best_metrics["specificity"]),
            "auc": float(best_metrics["auc"]),
            "confusion_matrix": best_metrics.get("confusion_matrix", []),
            "per_class_precision": best_metrics.get("per_class_precision", []),
            "per_class_recall": best_metrics.get("per_class_recall", []),
            "per_class_f1": best_metrics.get("per_class_f1", []),
            "per_class_specificity": best_metrics.get("per_class_specificity", []),
        }
        return fold_result, best_state

    def _train_one_epoch(self, model, loader, criterion, optimizer, scaler):
        model.train()
        all_preds = []
        all_labels = []
        total_loss = 0.0

        progress = tqdm(loader, desc="Training", leave=False)
        for images, labels in progress:
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(
                device_type=self.device.type,
                enabled=scaler.is_enabled(),
            ):
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=Config.GRADIENT_CLIP_NORM,
            )
            scaler.step(optimizer)
            scaler.update()

            total_loss += float(loss.item())
            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.detach().cpu().numpy().tolist())
            all_labels.extend(labels.detach().cpu().numpy().tolist())

            progress.set_postfix({"loss": f"{loss.item():.4f}"})

        if len(loader) == 0:
            raise RuntimeError("Training loader is empty.")

        avg_loss = total_loss / len(loader)
        metrics = compute_metrics(all_labels, all_preds)
        return avg_loss, metrics

    def _evaluate(self, model, loader, criterion):
        model.eval()
        all_preds = []
        all_labels = []
        all_probs = []
        total_loss = 0.0

        with torch.no_grad():
            for images, labels in loader:
                images = images.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                outputs = model(images)
                loss = criterion(outputs, labels)
                probs = torch.softmax(outputs, dim=1)
                preds = torch.argmax(probs, dim=1)

                total_loss += float(loss.item())
                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels.cpu().numpy().tolist())
                all_probs.extend(probs.cpu().numpy().tolist())

        if len(loader) == 0:
            raise RuntimeError("Validation loader is empty.")

        avg_loss = total_loss / len(loader)
        probs_array = np.asarray(all_probs, dtype=np.float32)
        metrics = compute_metrics(all_labels, all_preds, probs_array)

        num_classes = probs_array.shape[1] if probs_array.ndim == 2 else 0
        cm = confusion_matrix(all_labels, all_preds, labels=list(range(num_classes)))
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels,
            all_preds,
            labels=list(range(num_classes)),
            average=None,
            zero_division=0,
        )

        per_class_specificity = []
        for i in range(num_classes):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            tn = cm.sum() - (tp + fp + fn)
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            per_class_specificity.append(float(specificity))

        metrics["confusion_matrix"] = cm.tolist()
        metrics["per_class_precision"] = [float(v) for v in precision.tolist()]
        metrics["per_class_recall"] = [float(v) for v in recall.tolist()]
        metrics["per_class_f1"] = [float(v) for v in f1.tolist()]
        metrics["per_class_specificity"] = per_class_specificity
        return avg_loss, metrics

    def _compute_class_weights(self, labels, num_classes):
        classes = np.unique(labels)
        raw_weights = compute_class_weight(
            class_weight="balanced",
            classes=classes,
            y=labels,
        )
        class_weights = np.ones(num_classes, dtype=np.float32)
        for class_idx, weight in zip(classes, raw_weights):
            class_weights[int(class_idx)] = float(weight)
        return torch.tensor(class_weights, dtype=torch.float32)

    def _save_checkpoint(self, model, optimizer, epoch, metrics, fold_name):
        if not Config.SAVE_CHECKPOINTS:
            return

        checkpoint = {
            "epoch": int(epoch),
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "metrics": metrics,
            "fold_name": fold_name,
        }
        checkpoint_path = Config.MODELS_DIR / f"checkpoint_{fold_name}.pth"
        torch.save(checkpoint, checkpoint_path)
        logger.info("Saved checkpoint: {}", checkpoint_path)

    def _save_training_results(self, cv_results, mean_f1, std_f1):
        results = {
            "mean_f1": float(mean_f1),
            "std_f1": float(std_f1),
            "cv_results": cv_results,
            "config": {
                "batch_size": Config.BATCH_SIZE,
                "learning_rate": Config.LR,
                "epochs": Config.EPOCHS,
                "seed": Config.SEED,
                "backbone": Config.BACKBONE,
                "freeze_strategy": Config.FREEZE_STRATEGY,
                "use_pretrained": Config.USE_PRETRAINED,
            },
        }

        results_path = Config.MODELS_DIR / "training_results.json"
        with open(results_path, "w", encoding="utf-8") as handle:
            json.dump(self._to_builtin(results), handle, indent=2)
        logger.info("Saved training results: {}", results_path)

        if Config.SAVE_TRAINING_HISTORY:
            history_path = Config.MODELS_DIR / "training_history.json"
            with open(history_path, "w", encoding="utf-8") as handle:
                json.dump(self._to_builtin(self.training_history), handle, indent=2)
            logger.info("Saved training history: {}", history_path)

    def _to_builtin(self, value):
        if isinstance(value, dict):
            return {str(key): self._to_builtin(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._to_builtin(item) for item in value]
        if isinstance(value, tuple):
            return [self._to_builtin(item) for item in value]
        if isinstance(value, np.generic):
            return value.item()
        return value
