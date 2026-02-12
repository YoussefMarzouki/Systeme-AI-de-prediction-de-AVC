# Stroke Risk AI Module

Production-ready medical decision support system for stroke risk assessment.

## Features
- MRI image classification (ResNet18 transfer learning)
- Symptom-based risk scoring (Random Forest)  
- Risk fusion with confidence thresholding
- K-fold cross-validation
- Grad-CAM explainability
- Production logging
- Deterministic (fixed seeds)

## Safety Features
- Never outputs diagnosis text
- Confidence thresholding (0.7)
- Rejects uncertain predictions
- Comprehensive logging
- Medical-grade metrics (sensitivity/specificity)

## Quick Start
```bash
pip install -r requirements.txt
python train_image.py
python train_symptoms.py  
python predict.py
