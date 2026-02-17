#!/usr/bin/env python3
import pandas as pd
from loguru import logger
from models.symptom_classifier import SymptomClassifier
from preprocessing.symptom_processor import SymptomProcessor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from config import Config

if __name__ == "__main__":
    Config.ensure_dirs()

    if not Config.SYMPTOMS_CSV.exists():
        raise FileNotFoundError(f"Symptoms CSV not found at: {Config.SYMPTOMS_CSV}")

    df = pd.read_csv(Config.SYMPTOMS_CSV)
    if "stroke" not in df.columns:
        raise ValueError("Expected target column 'stroke' in symptom CSV.")

    logger.info(f"Loaded symptom dataset from {Config.SYMPTOMS_CSV} with shape={df.shape}")

    processor = SymptomProcessor()
    X = processor.fit(df)
    y = df['stroke'].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=Config.SEED, stratify=y
    )

    model = SymptomClassifier()
    model.model.set_params(class_weight="balanced")
    model.fit(X_train, y_train)

    # Keep fitted processor with the saved model for inference.
    model.processor = processor

    preds = model.model.predict(X_test)
    probs = model.predict_proba(X_test)
    report_text = classification_report(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    cm = confusion_matrix(y_test, preds)
    logger.info(report_text)
    logger.info(f"ROC-AUC: {auc:.4f}")
    logger.info(f"Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    
    model.save(Config.SYMPTOM_MODEL_PATH)
    logger.info(f"Symptom model trained and saved to {Config.SYMPTOM_MODEL_PATH}")
