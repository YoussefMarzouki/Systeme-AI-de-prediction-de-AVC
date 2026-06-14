"""
predictor.py
============
Unified stroke risk predictor combining:
  - MRI image classification (ResNet-based)
  - Symptom evaluation via Groq RAG (GroqSymptomClassifier)
"""

import torch
import torch.nn.functional as F
import cv2
import numpy as np
from loguru import logger
from pathlib import Path

try:
    from ..models.image_classifier import StrokeImageClassifier
    from ..models.symptom_classifier import GroqSymptomClassifier
    from ..preprocessing.mri_transforms import MRITransforms
    from ..config import Config
except ImportError:
    # Fallback for direct module loading from project root (e.g. `uvicorn api:app`).
    from models.image_classifier import StrokeImageClassifier
    from models.symptom_classifier import GroqSymptomClassifier
    from preprocessing.mri_transforms import MRITransforms
    from config import Config


class StrokeRiskPredictor:
    """
    High-level predictor that fuses MRI image analysis and Groq-powered
    symptom evaluation into a single stroke risk score.
    """

    def __init__(self, groq_api_key: str | None = None):
        Config.ensure_dirs()

        # ---- Image model ---------------------------------------------------
        num_image_classes = len(getattr(Config, "EXPECTED_IMAGE_CLASSES", ())) or 2
        self.image_model = StrokeImageClassifier(num_classes=num_image_classes).to(Config.DEVICE)
        if Config.IMAGE_MODEL_PATH.exists():
            checkpoint = torch.load(Config.IMAGE_MODEL_PATH, map_location=Config.DEVICE, weights_only=True)
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                checkpoint = checkpoint["model_state_dict"]
            self._load_image_checkpoint(checkpoint)
            logger.info(f"Loaded image model from: {Config.IMAGE_MODEL_PATH}")
        else:
            logger.warning(f"Image model not found at: {Config.IMAGE_MODEL_PATH}. Using untrained weights.")
        self.image_model.eval()

        # ---- Groq symptom classifier ----------------------------------------
        self.symptom_model = GroqSymptomClassifier(api_key=groq_api_key)
        logger.info("GroqSymptomClassifier initialised.")

        # Fusion weights
        self.image_weight   = 0.7
        self.symptom_weight = 0.3

        logger.info("StrokeRiskPredictor initialised.")

    def _load_image_checkpoint(self, state_dict: dict) -> None:
        """Load checkpoint with a safe fallback when classifier head sizes differ."""
        try:
            self.image_model.load_state_dict(state_dict, strict=False)
            return
        except RuntimeError as exc:
            logger.warning(
                "Image checkpoint has incompatible tensors; loading compatible layers only: {}",
                str(exc),
            )

        model_state = self.image_model.state_dict()
        compatible_state = {
            key: value
            for key, value in state_dict.items()
            if key in model_state and model_state[key].shape == value.shape
        }
        self.image_model.load_state_dict(compatible_state, strict=False)
        logger.info("Loaded {} compatible tensors from image checkpoint.", len(compatible_state))

    # ------------------------------------------------------------------
    def predict_image(self, image_path: str) -> dict:
        """
        Predict stroke type from an MRI image file.

        Returns
        -------
        dict with ``probability``, ``confidence``, and ``predicted_class`` keys.
        """
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        transform = MRITransforms.get_val_transforms()
        augmented  = transform(image=image)
        image_tensor = augmented["image"].unsqueeze(0).to(Config.DEVICE)

        with torch.no_grad():
            outputs = self.image_model(image_tensor)
            probs   = F.softmax(outputs, dim=1)
            
            # The classes expected are typically ("Hemorrhagic", "Ischemic", "Normal")
            # If the index is 0 or 1, the patient has a stroke. If 2, they are normal.
            # Thus, the combined probability of having a stroke is P(Hemorrhagic) + P(Ischemic)
            stroke_prob = float(probs[0, 0].item() + probs[0, 1].item())
            
            confidence  = float(max(probs[0].cpu().numpy()))
            predicted_class_idx = int(probs.argmax(dim=1).item())

        expected_classes = tuple(getattr(Config, "EXPECTED_IMAGE_CLASSES", ()))
        if 0 <= predicted_class_idx < len(expected_classes):
            predicted_class = expected_classes[predicted_class_idx]
        else:
            predicted_class = f"class_{predicted_class_idx}"

        return {
            "probability": stroke_prob,
            "confidence": confidence,
            "predicted_class": predicted_class,
        }

    # ------------------------------------------------------------------
    def predict_symptoms(self, symptoms: "dict | str") -> dict:
        """
        Evaluate stroke risk from symptoms using the Groq RAG engine.

        Parameters
        ----------
        symptoms : dict | str
            Structured symptom dict or free-text French/English description.

        Returns
        -------
        dict with keys:
            ``probability``  – numeric risk in [0, 1]
            ``confidence``   – fixed confidence score (e.g. 0.85)
            ``urgency``      – urgency level string
            ``response``     – full structured French evaluation
            ``usage``        – Groq token usage
        """
        result = self.symptom_model.evaluate(symptoms)
        prob   = result["probability"]
        return {
            "probability": prob,
            "confidence":  0.85,
            "urgency":     result["urgency"],
            "response":    result["response"],
            "usage":       result["usage"],
        }

    # ------------------------------------------------------------------
    def fuse_risk(self, image_result: dict, symptom_result: dict) -> dict:
        """Fuse image and symptom predictions into a single risk score."""
        fused_prob = (
            self.image_weight   * image_result["probability"] +
            self.symptom_weight * symptom_result["probability"]
        )
        confidence = min(image_result["confidence"], symptom_result["confidence"])

        if confidence < Config.CONFIDENCE_THRESHOLD:
            risk_level = "UNCERTAIN"
        else:
            if fused_prob < Config.RISK_THRESHOLDS["LOW"]:
                risk_level = "LOW"
            elif fused_prob < Config.RISK_THRESHOLDS["MEDIUM"]:
                risk_level = "MEDIUM"
            elif fused_prob < Config.RISK_THRESHOLDS["HIGH"]:
                risk_level = "HIGH"
            else:
                risk_level = "VERY_HIGH"

        logger.info({
            "image_prob":   image_result["probability"],
            "symptom_prob": symptom_result["probability"],
            "fused_prob":   fused_prob,
            "confidence":   confidence,
            "risk_level":   risk_level,
        })

        return {
            "risk_level":  risk_level,
            "probability": float(fused_prob),
            "confidence":  float(confidence),
        }
