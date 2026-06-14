# AI Model Service Files

This folder is the AI microservice used by the Flask backend. It has two prediction channels:

- MRI image classification through a ResNet-based PyTorch model.
- Symptom analysis through a RAG/LLM pipeline that returns an urgency label and a numeric probability.

The main runtime path is:

`api.py` -> `inference/predictor.py` -> `models/`, `preprocessing/`, and `rag/`

## Main Files

### `api.py`

FastAPI application exposed on port `8000`.

Important classes:

- `SymptomInput` - Request body for `/predict/symptoms`; contains one free-text `description`.
- `PredictionResult` - Base response shape with `probability`, `confidence`, `risk_level`, and `timestamp`.
- `ImagePredictionResult` - Adds `predicted_class` for MRI image predictions.
- `SymptomPredictionResult` - Adds RAG fields: `urgency`, `response`, and `usage`.
- `FusedPredictionResult` - Combines image probability, symptom probability, fused probability, confidence, risk level, and symptom explanation.
- `HealthStatus` - Response for model/service health.

Important functions/endpoints:

- `startup_event()` - Creates one global `StrokeRiskPredictor` when the API starts. This avoids loading models on every request.
- `shutdown_event()` - Deletes model objects and clears CUDA cache if available.
- `health_check()` - Returns whether image and symptom models are loaded and which device is used.
- `predict_image(file)` - Saves an uploaded MRI image temporarily, calls `predictor.predict_image()`, converts probability/confidence into a risk label, deletes the temp file, and returns an image prediction.
- `predict_symptoms(symptoms)` - Converts free text into `{"free_text": ...}`, calls `predictor.predict_symptoms()`, maps probability to a risk label, and returns the RAG response.
- `predict_fused(file, description)` - Runs both image and symptom prediction, then calls `predictor.fuse_risk()` for a single fused result.
- `api_info()` - Lists supported endpoints and device info.
- `root()` - Simple landing response pointing to `/docs` and `/redoc`.

Things to know:

- `predict_image()` and `predict_fused()` both create temporary files because the predictor expects an image path.
- Risk labels come from `Config.RISK_THRESHOLDS`.
- If symptom prediction fails inside `predict_fused()`, it falls back to neutral symptom probability `0.5` and confidence `0.0`.

### `config.py`

Central configuration for dataset paths, model paths, training hyperparameters, device selection, thresholds, and RAG provider settings.

Important fields:

- `PROJECT_ROOT` - Root of the AI service.
- `IMAGE_DATASET_DIR` - Expected MRI dataset root.
- `EXPECTED_IMAGE_CLASSES` - Class order, normally `Hemorrhagic`, `Ischemic`, `Normal`.
- `IMAGE_MODEL_PATH` - Saved trained model path: `models/stroke_image_resnet18.pth`.
- `BATCH_SIZE`, `EPOCHS`, `LR`, `PATIENCE` - Main training settings.
- `BACKBONE`, `FREEZE_STRATEGY`, `USE_PRETRAINED` - ResNet/model transfer-learning settings.
- `CONFIDENCE_THRESHOLD` and `RISK_THRESHOLDS` - Used to convert probabilities into clinical risk labels.
- `RAG_TEMPLATE_FILE`, `RAG_CASES_FILE`, `RAG_KNOWLEDGE_BASE_FILE` - Text sources loaded by the RAG engine.

Important functions:

- `ensure_dirs()` - Creates required folders such as `models/`, `dataset/`, and the expected test class folders.
- `torch_available()` - Returns whether PyTorch imported successfully.
- `get_config_summary()` - Returns a compact training config dictionary printed by `train_image.py`.

### `train_image.py`

Command-line entry point for image model training.

Important functions:

- `parse_args()` - Reads optional `--images-dir`, defaulting to `Config.IMAGE_DATASET_DIR`.
- `main()` - Ensures folders exist, logs config values, creates `ImageTrainer`, runs training, saves `final_training_config.json`, and prints the final F1 score.

Typical use:

```powershell
python train_image.py --images-dir "dataset/image trainning"
```

### `symptom_chat.py`

Interactive command-line tool for testing symptom RAG without the full backend/frontend.

Important functions:

- `_normalize_urgency_label(value)` - Normalizes variant urgency text into one expected label.
- `_print_banner()` - Prints the CLI heading and medical disclaimer.
- `_print_urgency_badge(urgency)` - Color-codes urgency output in the terminal.
- `run_interactive(rag)` - Multi-turn chat loop. Maintains conversation history until `reset`, `quit`, or `exit`.
- `run_single_query(rag, query)` - One-shot symptom evaluation for CLI automation.
- `main()` - Parses `--api-key`, `--model`, and `--query`, creates `SymptomRAG`, and chooses interactive or one-shot mode.

Typical use:

```powershell
python symptom_chat.py --query "Homme 65 ans, bouche deviee et bras faible depuis 20 minutes"
```

## Folders

- `models/` - PyTorch image classifier and symptom classifier wrappers.
- `preprocessing/` - MRI transforms, dataset loader, and symptom text formatter.
- `training/` - Full image-training pipeline.
- `inference/` - High-level prediction/fusion logic used by the API.
- `rag/` - Provider failover, prompt construction, urgency extraction, and local fallback for symptom RAG.
- `utils/` - Metrics and logging helpers.
- `tests/` - Scripts for model and symptom checks.
- `dataset/` - Image dataset and RAG knowledge files.
