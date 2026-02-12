#!/usr/bin/env python3
import pandas as pd
from loguru import logger
from models.symptom_classifier import SymptomClassifier
from preprocessing.symptom_processor import SymptomProcessor
from sklearn.model_selection import train_test_split
from config import Config

if __name__ == "__main__":
    df = pd.read_csv(Config.SYMPTOMS_CSV)
    processor = SymptomProcessor()
    
    X = processor.fit(df)
    y = df['stroke'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=Config.SEED, stratify=y
    )
    
    model = SymptomClassifier()
    model.fit(X_train, y_train)
    
    # Evaluate
    from sklearn.metrics import classification_report
    preds = model.model.predict(X_test)
    logger.info(classification_report(y_test, preds))
    
    model.save(Config.SYMPTOM_MODEL_PATH)
    logger.info("Symptom model trained and saved")
