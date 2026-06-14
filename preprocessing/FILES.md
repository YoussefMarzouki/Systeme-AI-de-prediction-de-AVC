# Preprocessing Files

This folder prepares MRI images and symptom data before model inference/training.

## `dataset.py`

Defines `MRIDataset`, a PyTorch `Dataset` for class-folder MRI image data.

Expected layout:

```text
image trainning/
  train/
    Hemorrhagic/
    Ischemic/
    Normal/
  valid/
    Hemorrhagic/
    Ischemic/
    Normal/
  test/
    Hemorrhagic/
    Ischemic/
    Normal/
```

### `MRIDataset.__init__(...)`

Creates a dataset from an image directory.

Important behavior:

- Validates that the dataset root exists.
- Discovers class folders or uses the passed `class_names`.
- Builds `class_to_idx`.
- Loads image samples recursively.
- Can use preselected `samples` for subset views.

### `_discover_classes()`

Returns sorted class-folder names. Hidden folders are ignored.

### `_load_samples()`

Finds `.jpg`, `.jpeg`, and `.png` images recursively under each class folder.

Interesting detail:

- Image paths are sorted by lowercase filename, which makes runs deterministic.

### `subset(indices, split=None, transform=None)`

Returns a new `MRIDataset` with only selected samples.

Useful for:

- K-fold training
- manual train/validation subsets
- experiments without copying files

### `__getitem__(idx)`

Loads one image:

- reads image with OpenCV
- converts BGR to RGB
- applies Albumentations transforms if present
- returns `(image_tensor, label_tensor)`

### `_basic_transform(image)`

Fallback validation transform used when no transform is passed.

### `get_class_counts()`, `get_class_names()`, `get_num_classes()`

Small helpers used by training and validation logs.

## `mri_transforms.py`

Defines image preprocessing and augmentation.

### `ZScoreNormalize`

Custom Albumentations image-only transform.

What it does:

- Converts image to `float32`.
- Computes per-image mean and standard deviation.
- Applies z-score normalization.
- Clips values to reduce outlier impact.
- Rescales to `[0, 1]`.

Why it matters:

- MRI intensity values can vary a lot between scans, so per-image standardization makes training more stable.

### `MRITransforms._gauss_noise_transform(p=0.3)`

Creates an Albumentations Gaussian-noise transform while supporting multiple Albumentations versions.

This exists because newer versions use `std_range`, while older versions use `var_limit`.

### `MRITransforms.get_train_transforms()`

Training pipeline:

- resize to `224x224`
- z-score normalization
- flips and rotations
- grid/elastic/perspective distortions
- brightness/contrast and gamma changes
- Gaussian noise and blur
- ImageNet normalization
- tensor conversion

This is intentionally stronger than validation augmentation to improve generalization.

### `MRITransforms.get_val_transforms()`

Validation/inference pipeline:

- resize to `224x224`
- z-score normalization
- ImageNet normalization
- tensor conversion

No random augmentation is used here.

### `MRITransforms.get_test_transforms()`

Returns the validation transform so test and inference preprocessing stay consistent.

## `symptom_processor.py`

Converts symptom input into model-ready text.

### `RAGSymptomProcessor`

Modern processor used by `GroqSymptomClassifier`.

### `RAGSymptomProcessor.to_text(symptoms)`

Accepts either:

- a plain string
- a dictionary with structured symptom fields

If a string is passed:

- returns the stripped string unchanged

If a dictionary is passed:

- creates a French clinical description
- maps keys like `face`, `arm`, `speech`, `hypertension`, `diabetes` into French labels
- appends `free_text` as extra information

Example input:

```python
{
    "age": 68,
    "gender": "homme",
    "face": "bouche deviee",
    "arm": "bras gauche faible",
    "free_text": "Debut il y a 20 minutes"
}
```

Example output shape:

```text
Description des symptomes du patient :
  - Age : 68
  - Sexe : homme
  - Visage (deviation/asymetrie) : bouche deviee
  - Bras/jambe (faiblesse) : bras gauche faible

Information complementaire : Debut il y a 20 minutes
```

### `SymptomProcessor`

Legacy sklearn preprocessing pipeline imported in this file. It is kept for compatibility but is not the main RAG path.
