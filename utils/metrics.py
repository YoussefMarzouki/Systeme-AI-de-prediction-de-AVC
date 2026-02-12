import numpy as np
from sklearn.metrics import accuracy_score, f1_score, classification_report
import torch

def compute_metrics(y_true, y_pred, y_proba=None):
    """Compute medical classification metrics"""
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='binary')
    
    metrics = {
        'accuracy': float(acc),
        'f1': float(f1),
        'sensitivity': float(recall_score(y_true, y_pred)),
        'specificity': float(specificity_score(y_true, y_pred))
    }
    return metrics

def specificity_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0

def confidence_from_proba(y_proba):
    """Extract confidence from probabilities"""
    return float(np.max(y_proba))
