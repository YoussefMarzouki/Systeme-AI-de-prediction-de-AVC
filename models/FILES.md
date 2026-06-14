# AI Model Definition Files

This folder contains the model-level classes. The image classifier is a PyTorch model. The symptom classifiers wrap either the modern RAG flow or an older sklearn model.

## `image_classifier.py`

Defines `StrokeImageClassifier`, the MRI image classifier.

### `StrokeImageClassifier.__init__(num_classes=2, pretrained=True, backbone="resnet18", freeze_strategy="partial")`

Builds a ResNet image classifier.

What it does:

- Selects `resnet18` or `resnet50`.
- Loads ImageNet weights when `pretrained=True`.
- Applies a transfer-learning freeze strategy.
- Replaces the original ResNet `fc` layer with a custom head:
  - dropout
  - linear layer to 128 features
  - ReLU
  - dropout
  - final linear layer to `num_classes`

Why it matters:

- This lets the project reuse a general image backbone while learning MRI-specific stroke classes.

### `_apply_freeze_strategy(strategy)`

Controls which backbone layers are trainable.

Supported strategies:

- `full` - Freeze the entire backbone and train only the classifier head.
- `partial` - Freeze everything except `layer4`.
- `gradual` - Initially train `layer3` and `layer4`, then unfreeze earlier layers later.
- `none` - Train the full network.

### `get_backbone_parameters()`

Splits parameters into two groups:

- backbone parameters
- classifier head parameters

Used by the trainer to assign different learning rates:

- smaller learning rate for pretrained backbone
- larger learning rate for the classifier head

### `gradual_unfreeze(current_epoch, total_epochs)`

Only active when `freeze_strategy == "gradual"`.

What it does:

- After about 66 percent of training, unfreezes `layer2`.
- After about 85 percent of training, unfreezes `layer1`.

This gives stable early training, then allows deeper fine-tuning later.

### `forward(x)`

Runs the input tensor through the ResNet backbone and custom head.

## `symptom_classifier.py`

Contains both the current RAG symptom classifier and a legacy sklearn classifier.

### `_normalize_urgency_label(value)`

Normalizes messy or accented urgency output into stable labels:

- `URGENCE IMMEDIATE`
- `URGENCE A EVALUER RAPIDEMENT`
- `FAIBLE PROBABILITE MAIS SURVEILLANCE`
- `UNKNOWN`

### `_urgency_probability(value)`

Maps urgency labels into numeric probabilities:

- immediate urgency -> about `0.92`
- rapid evaluation -> about `0.65`
- low probability but monitoring -> about `0.20`
- unknown -> `0.50`

This is how text-based RAG output becomes usable in the fusion model.

### `GroqSymptomClassifier`

Modern symptom classifier used by `StrokeRiskPredictor`.

Important methods:

- `__init__(api_key=None, model="gemini-2.0-flash")` - Creates `SymptomRAG`, creates `RAGSymptomProcessor`, and starts an empty conversation history.
- `evaluate(symptoms)` - Converts structured/free-text symptoms to text, calls RAG, normalizes urgency, adds numeric probability, and stores the turn in history.
- `predict_proba(symptoms)` - Compatibility helper returning only the numeric probability.
- `reset_conversation()` - Clears multi-turn history.
- `chat(message)` - Sends a follow-up message using current conversation history.

### `SymptomClassifier`

Legacy sklearn `RandomForestClassifier`.

Important methods:

- `fit(X, y)` - Trains the random forest and stores feature importance.
- `predict_proba(X)` - Returns positive-class probability.
- `save(path)` - Saves the classifier with `joblib`.
- `load(path)` - Loads a saved classifier.

Use this only for older experiments or compatibility. The active path uses `GroqSymptomClassifier`.
