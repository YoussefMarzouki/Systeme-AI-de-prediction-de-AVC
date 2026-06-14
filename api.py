#!/usr/bin/env python3
"""
FastAPI microservice for stroke prediction using image and symptom-based models.
Provides REST endpoints for inference on MRI images and patient symptoms.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import torch
import cv2
import numpy as np
import tempfile
from pathlib import Path
import logging
from datetime import datetime
import uvicorn

from inference.predictor import StrokeRiskPredictor
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class SymptomInput(BaseModel):
    """Input model for symptom-based predictions"""
    description: str = Field(..., description="Free-form text describing patient symptoms")
    language: Optional[str] = Field(default="fr", description="User language preference: ar, en, fr")


class PredictionResult(BaseModel):
    """Output model for predictions"""
    probability: float = Field(..., ge=0, le=1, description="Predicted stroke probability")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence score")
    risk_level: Optional[str] = Field(None, description="Risk classification: LOW, MEDIUM, HIGH, VERY_HIGH, UNCERTAIN")
    timestamp: str = Field(..., description="Prediction timestamp")

class ImagePredictionResult(PredictionResult):
    """Output model for image predictions"""
    predicted_class: Optional[str] = Field(default=None, description="Predicted image class")


class SymptomPredictionResult(PredictionResult):
    """Output model for symptom predictions"""
    urgency: Optional[str] = Field(default=None, description="RAG urgency evaluation")
    response: Optional[str] = Field(default=None, description="RAG structured response")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage statistics")


class FusedPredictionResult(BaseModel):
    """Output model for fused image + symptom predictions"""
    predicted_class: Optional[str] = Field(default=None, description="Predicted image class")
    fused_probability: float = Field(..., ge=0, le=1, description="Fused stroke probability")
    image_probability: Optional[float] = Field(None, ge=0, le=1, description="Image-based probability")
    symptom_probability: Optional[float] = Field(None, ge=0, le=1, description="Symptom-based probability")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence score")
    risk_level: str = Field(..., description="Risk classification")
    timestamp: str = Field(..., description="Prediction timestamp")
    symptom_urgency: Optional[str] = Field(default=None, description="RAG urgency evaluation")
    symptom_response: Optional[str] = Field(default=None, description="RAG structured response")
    symptom_usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage statistics")


class HealthStatus(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    models_loaded: Dict[str, bool]
    device: str


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Stroke Risk Prediction Microservice",
    description="API for predicting stroke risk using MRI images and patient symptoms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance (loaded once at startup)
predictor: Optional[StrokeRiskPredictor] = None


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the predictor on startup"""
    global predictor
    try:
        logger.info("Initializing StrokeRiskPredictor...")
        predictor = StrokeRiskPredictor()
        logger.info("Predictor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global predictor
    if predictor:
        logger.info("Shutting down predictor")
        try:
            if hasattr(predictor, 'image_model'):
                del predictor.image_model
            if hasattr(predictor, 'symptom_model'):
                del predictor.symptom_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Check the health status of the microservice"""
    try:
        models_status = {
            "image_model": predictor.image_model is not None,
            "symptom_model": predictor.symptom_model is not None,
        }
        
        return HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            models_loaded=models_status,
            device=str(Config.DEVICE)
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            models_loaded={"image_model": False, "symptom_model": False},
            device=str(Config.DEVICE)
        )


# ============================================================================
# Image Prediction Endpoint
# ============================================================================

@app.post("/predict/image", response_model=ImagePredictionResult)
async def predict_image(file: UploadFile = File(...)):
    """
    Predict stroke risk from MRI image
    
    - **file**: MRI image file (JPEG, PNG)
    - Returns: Stroke probability, confidence, and risk level
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Perform prediction
        result = predictor.predict_image(tmp_path)
        
        # Determine risk level
        prob = result["probability"]
        if result["confidence"] < Config.CONFIDENCE_THRESHOLD:
            risk_level = "UNCERTAIN"
        elif prob < Config.RISK_THRESHOLDS["LOW"]:
            risk_level = "LOW"
        elif prob < Config.RISK_THRESHOLDS["MEDIUM"]:
            risk_level = "MEDIUM"
        elif prob < Config.RISK_THRESHOLDS["HIGH"]:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"
        
        # Clean up temporary file
        Path(tmp_path).unlink()
        
        return ImagePredictionResult(
            probability=result["probability"],
            confidence=result["confidence"],
            risk_level=risk_level,
            timestamp=datetime.utcnow().isoformat(),
            predicted_class=result.get("predicted_class"),
        )
    
    except Exception as e:
        logger.error(f"Image prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")


# ============================================================================
# Symptom Prediction Endpoint
# ============================================================================

@app.post("/predict/symptoms", response_model=SymptomPredictionResult)
async def predict_symptoms(symptoms: SymptomInput):
    """
    Predict stroke risk from patient symptoms
    
    - **symptoms**: Free-text patient symptom description
    - Returns: Stroke probability, confidence, and risk level
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Convert Pydantic model to dict
        symptoms_dict = {"free_text": symptoms.description, "language": symptoms.language}
        
        # Perform prediction
        result = predictor.predict_symptoms(symptoms_dict)
        
        # Handle error cases
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        # Determine risk level
        prob = result["probability"]
        if result["confidence"] < Config.CONFIDENCE_THRESHOLD:
            risk_level = "UNCERTAIN"
        elif prob < Config.RISK_THRESHOLDS["LOW"]:
            risk_level = "LOW"
        elif prob < Config.RISK_THRESHOLDS["MEDIUM"]:
            risk_level = "MEDIUM"
        elif prob < Config.RISK_THRESHOLDS["HIGH"]:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"
        
        return SymptomPredictionResult(
            probability=result["probability"],
            confidence=result["confidence"],
            risk_level=risk_level,
            timestamp=datetime.utcnow().isoformat(),
            urgency=result.get("urgency"),
            response=result.get("response"),
            usage=result.get("usage"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Symptom prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")


# ============================================================================
# Fused Prediction Endpoint (Image + Symptoms)
# ============================================================================
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Symptom prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")


# ============================================================================
# Fused Prediction Endpoint (Image + Symptoms)
# ============================================================================

@app.post("/predict/fused", response_model=FusedPredictionResult)
async def predict_fused(
    file: UploadFile = File(...),
    description: str = Form(...),
    language: Optional[str] = Form("fr"),
):
    """
    Predict stroke risk from both MRI image and patient symptoms
    
    Combines image-based and symptom-based predictions using weighted fusion
    
    - **file**: MRI image file
    - **description**: Free-text patient symptom description
    - **language**: Optional language preference for RAG (ar, en, fr)
    - Returns: Fused probability, individual probabilities, confidence, and risk level
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Get image prediction
        image_result = predictor.predict_image(tmp_path)
        
        # Get symptom prediction
        symptoms_dict = {"free_text": description, "language": language}
        symptom_result = predictor.predict_symptoms(symptoms_dict)
        # Fuse predictions
        fused_result = predictor.fuse_risk(image_result, symptom_result)
        
        # Clean up temporary file
        Path(tmp_path).unlink()
        
        return FusedPredictionResult(
            predicted_class=image_result.get("predicted_class"),
            fused_probability=fused_result["probability"],
            image_probability=image_result["probability"],
            symptom_probability=symptom_result["probability"],
            confidence=fused_result["confidence"],
            risk_level=fused_result["risk_level"],
            timestamp=datetime.utcnow().isoformat(),
            symptom_urgency=symptom_result.get("urgency"),
            symptom_response=symptom_result.get("response"),
            symptom_usage=symptom_result.get("usage"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fused prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")


# ============================================================================
# API Metadata Endpoint
# ============================================================================

@app.get("/info")
async def api_info():
    """Get API information and capabilities"""
    return {
        "title": "Stroke Risk Prediction Microservice",
        "version": "1.0.0",
        "description": "Predicts stroke risk using MRI images and patient symptoms",
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Health check and model status"
            },
            "predict_image": {
                "method": "POST",
                "path": "/predict/image",
                "description": "Predict from MRI image"
            },
            "predict_symptoms": {
                "method": "POST",
                "path": "/predict/symptoms",
                "description": "Predict from patient symptoms"
            },
            "predict_fused": {
                "method": "POST",
                "path": "/predict/fused",
                "description": "Predict from image and symptoms combined"
            }
        },
        "device": str(Config.DEVICE),
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Documentation
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "message": "Stroke Risk Prediction Microservice",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run with: python api.py
    # Access at: http://localhost:8000/docs
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for GPU memory efficiency
        log_level="info"
    )
