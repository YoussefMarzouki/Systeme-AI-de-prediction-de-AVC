import torch
import torch.nn.functional as F
import cv2
import numpy as np
import json
import pandas as pd
from loguru import logger
from pathlib import Path
from captum.attr import IntegratedGradients
from ..models.image_classifier import StrokeImageClassifier
from ..models.symptom_classifier import SymptomClassifier
from ..preprocessing.symptom_processor import SymptomProcessor
from ..preprocessing.mri_transforms import MRITransforms
from ..config import Config
import joblib

class StrokeRiskPredictor:
    def __init__(self):
        # Ensure model directory exists
        Config.ensure_dirs()
        
        # Load image model
        self.image_model = StrokeImageClassifier().to(Config.DEVICE)
        if Config.IMAGE_MODEL_PATH.exists():
            self.image_model.load_state_dict(torch.load(Config.IMAGE_MODEL_PATH, map_location=Config.DEVICE), strict=False)
            logger.info(f"Loaded image model from: {Config.IMAGE_MODEL_PATH}")
        else:
            logger.warning(f"Image model not found at: {Config.IMAGE_MODEL_PATH}")
            logger.info("Using untrained model for predictions")
        self.image_model.eval()
        
        # Load symptom model
        if Config.SYMPTOM_MODEL_PATH.exists():
            self.symptom_model = SymptomClassifier.load(Config.SYMPTOM_MODEL_PATH)
            logger.info(f"Loaded symptom model from: {Config.SYMPTOM_MODEL_PATH}")
        else:
            logger.warning(f"Symptom model not found at: {Config.SYMPTOM_MODEL_PATH}")
            logger.info("Symptom predictions may not work")
            self.symptom_model = None
        
        self.symptom_model = SymptomClassifier.load(Config.SYMPTOM_MODEL_PATH)
        self.symptom_processor = getattr(self.symptom_model, "processor", SymptomProcessor())
        
        # Fusion model (simple weighted average for production stability)
        self.image_weight = 0.7
        self.symptom_weight = 0.3
        
        logger.info("StrokeRiskPredictor initialized")
    
    def predict_image(self, image_path):
        """Predict stroke risk from MRI image"""
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        transform = MRITransforms.get_val_transforms()
        augmented = transform(image=image)
        image_tensor = augmented['image'].unsqueeze(0).to(Config.DEVICE)
        
        with torch.no_grad():
            outputs = self.image_model(image_tensor)
            probs = F.softmax(outputs, dim=1)
            stroke_prob = probs[0, 1].item()
            confidence = max(probs[0].cpu().numpy())
        
        return {
            "probability": stroke_prob,
            "confidence": confidence
        }
    
    def predict_symptoms(self, symptoms_json):
        """Predict stroke risk from symptoms"""
        if self.symptom_model is None:
            logger.error("Symptom model not loaded")
            return {"probability": 0.0, "confidence": 0.0, "error": "Model not available"}
            
        symptoms_df = pd.DataFrame([symptoms_json])
        X_processed = self.symptom_processor.transform(symptoms_df)
        
        stroke_prob = self.symptom_model.predict_proba(X_processed)[0]
        confidence = stroke_prob if stroke_prob > 0.5 else 1 - stroke_prob
        
        return {
            "probability": float(stroke_prob),
            "confidence": float(confidence)
        }
    
    def fuse_risk(self, image_result, symptom_result):
        """Fuse image and symptom predictions"""
        fused_prob = (
            self.image_weight * image_result["probability"] +
            self.symptom_weight * symptom_result["probability"]
        )
        
        # Confidence as minimum of individual confidences
        confidence = min(image_result["confidence"], symptom_result["confidence"])
        
        if confidence < Config.CONFIDENCE_THRESHOLD:
            risk_level = "UNCERTAIN"
        else:
            if fused_prob < Config.RISK_THRESHOLDS["LOW"]:
                risk_level = "LOW"
            elif fused_prob < Config.RISK_THRESHOLDS["MEDIUM"]:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
        
        # Log prediction
        logger.info({
            "image_prob": image_result["probability"],
            "symptom_prob": symptom_result["probability"],
            "fused_prob": fused_prob,
            "confidence": confidence,
            "risk_level": risk_level
        })
        
        return {
            "risk_level": risk_level,
            "probability": float(fused_prob),
            "confidence": float(confidence)
        }
