# Training Files

This folder contains the MRI image training pipeline.

## `image_trainer.py`

Defines `ImageTrainer`, the class used by `train_image.py`.

## `ImageTrainer`

Trains the ResNet-based MRI classifier using explicit `train/valid/test` folders.

### `__init__(images_dir, domain_info=None)`

Stores dataset path, optional domain/scanner info, device, and training history.

Also:

- sets random seeds
- ensures required directories exist

### `_set_seeds()`

Sets seeds for:

- Python `random`
- NumPy
- PyTorch CPU
- PyTorch CUDA

Also configures deterministic CuDNN behavior when CUDA is available.

Why it matters:

- Reproducible medical-model experiments are easier to compare and debug.

### `train()`

Main training flow.

Steps:

- expects `train`, `valid`, and `test` subfolders
- creates `MRIDataset` objects
- validates expected classes
- creates deterministic dataloaders
- builds the model
- trains with `_train_fold()`
- loads the best validation checkpoint
- saves best model to `Config.IMAGE_MODEL_PATH`
- evaluates on the test set
- saves training results and history
- returns final test F1 score

### `_validate_expected_classes(discovered_classes)`

Checks that dataset folders match `Config.EXPECTED_IMAGE_CLASSES`.

This protects against silently training with wrong class order.

### `_resolve_n_splits(labels, requested_splits)`

Determines how many stratified folds are possible from class counts.

Currently useful for K-fold/domain-aware extensions.

### `_build_split_iterator(indices, labels, samples, n_splits)`

Builds stratified train/validation splits.

Interesting behavior:

- uses `StratifiedGroupKFold` when domain-aware training is enabled and scanner groups are usable
- falls back to `StratifiedKFold` when groups are fragmented or produce missing classes

### `_find_folds_missing_classes(split_iterator, labels, num_classes)`

Detects folds where validation data is missing one or more classes.

This is important because medical model metrics are misleading if a validation fold has no samples for a class.

### `_extract_scanner_name(filename)`

Extracts a scanner/domain group from the filename.

Rules:

- split on `_`
- else split on `-`
- else `unknown_scanner`

### `_create_dataloader(dataset, shuffle, seed)`

Creates a deterministic PyTorch `DataLoader`.

Uses:

- configured batch size
- configured worker count
- pinned memory on CUDA
- `drop_last=True` for shuffled training

### `_build_model(num_classes)`

Creates `StrokeImageClassifier` using config values:

- pretrained setting
- backbone
- freeze strategy

### `_train_fold(model, train_loader, val_loader, fold_name)`

Runs full training for one split.

Important steps:

- computes class weights for imbalance
- uses cross-entropy with label smoothing
- separates backbone/head optimizer groups
- uses SGD with momentum and Nesterov
- uses `ReduceLROnPlateau` scheduler on validation F1
- uses AMP on CUDA when enabled
- saves best checkpoint by validation F1
- supports early stopping by patience

Returns:

- fold metrics summary
- best model state dict

### `_train_one_epoch(model, loader, criterion, optimizer, scaler)`

Training loop for one epoch.

Steps:

- forward pass under AMP if enabled
- compute loss
- backpropagate with gradient scaling
- clip gradients
- optimizer step
- collect predictions and labels
- compute metrics with `compute_metrics()`

### `_evaluate(model, loader, criterion)`

Validation/test loop.

Collects:

- loss
- predictions
- probabilities
- confusion matrix
- per-class precision/recall/F1/specificity

### `_compute_class_weights(labels, num_classes)`

Creates balanced class weights using sklearn.

Useful when class folders have different numbers of images.

### `_save_checkpoint(model, optimizer, epoch, metrics, fold_name)`

Saves checkpoint files like:

```text
models/checkpoint_training.pth
```

Checkpoint contains:

- epoch
- model state
- optimizer state
- metrics
- fold name

### `_save_training_results(cv_results, mean_f1, std_f1)`

Writes:

- `models/training_results.json`
- `models/training_history.json`

### `_to_builtin(value)`

Converts NumPy values, tuples, lists, and dictionaries into JSON-safe Python types.
