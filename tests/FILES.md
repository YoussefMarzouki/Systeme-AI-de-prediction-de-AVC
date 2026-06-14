# Test Files

Scripts for checking the AI model and symptom system.

## `test.py`

Small random-image smoke test.

### `main()`

Steps:

- finds all images under `Config.TEST_IMAGE_DATASET_DIR`
- picks one random image
- calls `load_and_predict()` from `test_model.py`
- prints predicted class, confidence, and class probabilities

Use this when you want a quick "does the trained model run?" check.

## `test_model.py`

Single-image model loading and prediction.

### `_resolve_class_names()`

Reads class folders from the test dataset.

If `Config.ENFORCE_EXPECTED_IMAGE_CLASSES` is enabled, it verifies expected classes exist.

### `_load_state_dict(path, device)`

Loads either:

- a checkpoint dict containing `model_state_dict`
- a plain PyTorch state dict

Supports older PyTorch versions that do not support `weights_only`.

### `_infer_num_classes_from_state_dict(state_dict)`

Infers the output class count from classifier-layer weights.

It checks known keys first, then searches for classifier/fc/head weight tensors.

Why useful:

- catches mismatch between checkpoint output classes and dataset class folders.

### `load_and_predict(image_path)`

Main helper.

Steps:

- checks that model file exists
- resolves class names
- loads checkpoint
- verifies class count matches
- creates `StrokeImageClassifier`
- loads model weights strictly
- preprocesses one image
- runs softmax prediction
- returns predicted class, confidence, and probability per class

## `test_symptoms.py`

Tests the RAG symptom pipeline.

### Unit tests without network

- `test_processor_dict()` - Verifies structured symptom dict is converted into French clinical text.
- `test_processor_free_text()` - Verifies plain free text passes through unchanged.
- `test_processor_free_text_key()` - Verifies `free_text` is appended correctly.

### Integration tests with provider/API access

- `test_evaluate_dict()` - Runs RAG evaluation on structured FAST symptoms.
- `test_evaluate_free_text()` - Runs RAG on one free-text symptom case.
- `test_multi_turn_chat()` - Verifies follow-up conversation works.
- `test_reset_conversation()` - Verifies conversation history can be cleared.

Note:

- These integration tests require a usable Groq/OpenRouter/LM Studio configuration.

## `evaluate_model.py`

Evaluates the image model on a random labeled subset.

### `collect_labeled_images()`

Returns all test images and class names from `Config.TEST_IMAGE_DATASET_DIR`.

### `build_confusion_matrix(class_names, y_true, y_pred)`

Builds a class-ordered confusion matrix.

### `format_confusion_matrix(class_names, matrix)`

Turns the confusion matrix into readable text for terminal output.

### `evaluate_model(sample_count, seed)`

Runs evaluation.

Steps:

- collects labeled images
- selects deterministic random sample
- predicts each image with `load_and_predict()`
- computes accuracy
- computes average confidence
- counts per-class correct predictions
- stores mistakes for inspection

Returns a summary dictionary.

### `parse_args()`

CLI options:

- `--samples`
- `--seed`
- `--show-errors`

### `main()`

Prints:

- dataset path
- sample count
- accuracy
- correct/total
- average confidence
- per-class accuracy
- confusion matrix
- sample mistakes
