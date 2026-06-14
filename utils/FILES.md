# Utility Files

Small reusable helpers for metrics and logging.

## `metrics.py`

Classification metrics used by training and evaluation.

### `compute_metrics(y_true, y_pred, y_proba=None)`

Computes core metrics:

- accuracy
- F1
- precision
- sensitivity/recall
- specificity
- AUC
- number of classes

Behavior:

- uses binary metrics when there are two classes
- uses weighted/macro multiclass metrics when there are more than two classes
- supports one-vs-rest AUC for multiclass probabilities

### `compute_medical_metrics(y_true, y_pred, y_proba=None, class_names=None)`

Adds more clinically useful detail:

- confusion matrix
- balanced accuracy
- Matthews correlation coefficient
- per-class precision
- per-class recall/sensitivity
- per-class specificity
- per-class F1
- class support

### `specificity_score(y_true, y_pred)`

Computes specificity.

For binary classification:

```text
TN / (TN + FP)
```

For multiclass, delegates to `specificity_multiclass()`.

### `mcc_score(y_true, y_pred)`

Computes Matthews Correlation Coefficient.

Why useful:

- MCC is more balanced than accuracy when classes are imbalanced.

### `specificity_multiclass(y_true, y_pred)`

Computes specificity for each class using one-vs-rest logic, then returns the macro average.

### `safe_precision_recall_fscore_support(y_true, y_pred, average=None)`

Wrapper around sklearn's precision/recall/F-score with `zero_division=0`.

Prevents warnings/errors when a class has no predicted samples.

### `confidence_from_proba(y_proba)`

Returns the average maximum probability as a simple confidence score.

### `calculate_prediction_entropy(y_proba)`

Computes entropy of predicted probabilities.

Interpretation:

- lower entropy = model is more certain
- higher entropy = model is less certain

### `get_clinical_interpretation(metrics)`

Turns numeric metrics into plain-language interpretation.

It returns:

- overall performance label
- clinical relevance label
- recommendations, for example collect more data or reduce false negatives

## `logger.py`

Configures Loguru logging.

### `setup_logger()`

Sets up:

- console logging
- rotating file logging at `logs/ai_module.log`

Returns the configured `logger`.

### `logger`

Module-level configured logger reused by other AI scripts.
