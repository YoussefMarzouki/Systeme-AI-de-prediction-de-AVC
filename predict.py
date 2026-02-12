#!/usr/bin/env python3
import json
import sys
from inference.predictor import StrokeRiskPredictor
from config import Config

def main():
    predictor = StrokeRiskPredictor()
    
    # Example usage
    image_result = predictor.predict_image("path/to/mri.jpg")
    symptom_result = predictor.predict_symptoms({
        "age": 65,
        "gender": "male", 
        "hypertension": "yes",
        "heart_disease": "yes",
        "blood_pressure": 150,
        "cholesterol": 220
    })
    
    final_result = predictor.fuse_risk(image_result, symptom_result)
    print(json.dumps(final_result, indent=2))

if __name__ == "__main__":
    main()
