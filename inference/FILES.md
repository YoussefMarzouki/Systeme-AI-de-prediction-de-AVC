# Inference Files

This folder contains the high-level prediction logic used by `api.py`.

## `predictor.py`

Defines `StrokeRiskPredictor`, the central runtime object for the AI service.

## `StrokeRiskPredictor`

Combines:

- MRI image classifier: `StrokeImageClassifier`
- symptom classifier: `GroqSymptomClassifier`
- fusion rule: weighted probability average

### `__init__(groq_api_key=None)`

Initializes runtime prediction.

What it does:

- Calls `Config.ensure_dirs()`.
- Creates a `StrokeImageClassifier` with class count from `Config.EXPECTED_IMAGE_CLASSES`.
- Loads `Config.IMAGE_MODEL_PATH` if it exists.
- Falls back to untrained weights if no image checkpoint is found.
- Creates `GroqSymptomClassifier`.
- Sets fusion weights:
  - image: `0.7`
  - symptoms: `0.3`

Interesting detail:

- It supports both checkpoint dictionaries containing `model_state_dict` and plain PyTorch state dicts.

### `_load_image_checkpoint(state_dict)`

Loads a model checkpoint safely.

First attempt:

- load with `strict=False`

Fallback:

- if tensor sizes do not match, load only compatible tensors.

Why useful:

- Prevents the whole API from failing when the classifier head shape changed between old and new checkpoints.

### `predict_image(image_path)`

Predicts from a single MRI file path.

Steps:

- reads image with OpenCV
- converts BGR to RGB
- applies validation transforms
- runs the image model
- applies softmax
- computes stroke probability as:

```text
P(Hemorrhagic) + P(Ischemic)
```

- sets `predicted_class` from `Config.EXPECTED_IMAGE_CLASSES`

Returns:

```python
{
    "probability": stroke_prob,
    "confidence": max_class_probability,
    "predicted_class": predicted_class,
}
```

Important assumption:

- The class order must match `Config.EXPECTED_IMAGE_CLASSES`. If this order changes, the stroke probability calculation must be reviewed.

### `predict_symptoms(symptoms)`

Predicts from structured symptoms or free text.

Steps:

- calls `self.symptom_model.evaluate(symptoms)`
- receives urgency, full French response, token usage, and risk probability
- returns a compact dictionary with fixed confidence `0.85`

Returns:

```python
{
    "probability": prob,
    "confidence": 0.85,
    "urgency": "...",
    "response": "...",
    "usage": {...},
}
```

### `fuse_risk(image_result, symptom_result)`

Combines image and symptom scores.

Formula:

```text
fused = 0.7 * image_probability + 0.3 * symptom_probability
confidence = min(image_confidence, symptom_confidence)
```

Then maps `fused` to:

- `UNCERTAIN` if confidence is below `Config.CONFIDENCE_THRESHOLD`
- `LOW`
- `MEDIUM`
- `HIGH`
- `VERY_HIGH`

Returns:

```python
{
    "risk_level": risk_level,
    "probability": fused_probability,
    "confidence": confidence,
}
```
