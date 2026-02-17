import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score, confusion_matrix, roc_auc_score, precision_score


def compute_metrics(y_true, y_pred, y_proba=None):
    """Compute comprehensive medical classification metrics"""
    acc = accuracy_score(y_true, y_pred)
    
    # Determine if binary or multiclass
    if y_proba is not None and hasattr(y_proba, "ndim") and y_proba.ndim == 2:
        n_classes = int(y_proba.shape[1])
    else:
        n_classes = int(len(np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))))
    n_classes = max(n_classes, 2)
    
    if n_classes <= 2:
        # Binary classification
        f1 = f1_score(y_true, y_pred, average='binary', zero_division=0)
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        sensitivity = float(recall_score(y_true, y_pred, zero_division=0))
        specificity = float(specificity_score(y_true, y_pred))
        
        # ROC-AUC for binary case
        if y_proba is not None and y_proba.ndim == 2:
            auc = float(roc_auc_score(y_true, y_proba[:, 1]))
        else:
            auc = 0.0
    else:
        # Multiclass classification
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        precision = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
        # For multiclass, calculate macro averages
        sensitivity = float(recall_score(y_true, y_pred, average='macro', zero_division=0))
        specificity = float(specificity_multiclass(y_true, y_pred))
        
        # Multi-class AUC (one-vs-rest)
        if y_proba is not None:
            try:
                auc = float(roc_auc_score(y_true, y_proba, multi_class='ovr'))
            except:
                auc = 0.0
        else:
            auc = 0.0
    
    metrics = {
        'accuracy': float(acc),
        'f1': float(f1),
        'precision': precision,
        'sensitivity': sensitivity,  # Recall
        'specificity': specificity,
        'auc': auc,
        'num_classes': n_classes
    }
    return metrics

def compute_medical_metrics(y_true, y_pred, y_proba=None, class_names=None):
    """Compute detailed medical imaging metrics with clinical relevance"""
    # Basic metrics
    basic_metrics = compute_metrics(y_true, y_pred, y_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, _ = \
        safe_precision_recall_fscore_support(y_true, y_pred, average=None)
    
    # Specificity per class
    specificity_per_class = []
    n_classes = len(np.unique(y_true))
    
    for i in range(n_classes):
        # TN = sum of all elements - (row i + column i - diagonal element)
        tn = cm.sum() - (cm[i, :].sum() + cm[:, i].sum() - cm[i, i])
        fp = cm[:, i].sum() - cm[i, i]
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        specificity_per_class.append(specificity)
    
    # Clinical metrics
    clinical_metrics = {
        'balanced_accuracy': (basic_metrics['sensitivity'] + basic_metrics['specificity']) / 2,
        'matthews_correlation_coefficient': mcc_score(y_true, y_pred),
        'per_class_metrics': {}
    }
    
    # Add per-class metrics
    class_names = class_names or [f'Class_{i}' for i in range(n_classes)]
    for i, class_name in enumerate(class_names):
        clinical_metrics['per_class_metrics'][class_name] = {
            'precision': float(precision_per_class[i]),
            'recall': float(recall_per_class[i]),  # sensitivity
            'specificity': float(specificity_per_class[i]),
            'f1_score': float(f1_per_class[i]),
            'support': int(cm[i, :].sum())
        }
    
    # Combine all metrics
    comprehensive_metrics = {
        **basic_metrics,
        **clinical_metrics,
        'confusion_matrix': cm.tolist()
    }
    
    return comprehensive_metrics

def specificity_score(y_true, y_pred):
    """Calculate specificity for binary classification"""
    cm = confusion_matrix(y_true, y_pred)
    if cm.size == 1:
        # Only one class present
        return 1.0 if y_true[0] == y_pred[0] else 0.0
    elif cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        return tn / (tn + fp) if (tn + fp) > 0 else 0.0
    else:
        # Multiclass case - return macro average specificity
        return specificity_multiclass(y_true, y_pred)

def mcc_score(y_true, y_pred):
    """Matthews Correlation Coefficient - balanced metric for imbalanced datasets"""
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        denominator = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        if denominator == 0:
            return 0.0
        return (tp * tn - fp * fn) / denominator
    else:
        # For multiclass, use sklearn's implementation
        from sklearn.metrics import matthews_corrcoef
        return matthews_corrcoef(y_true, y_pred)

def specificity_multiclass(y_true, y_pred):
    """Calculate specificity for multiclass classification (macro average)"""
    from sklearn.metrics import precision_recall_fscore_support
    cm = confusion_matrix(y_true, y_pred)
    # Specificity for each class (true negatives / (true negatives + false positives))
    specificities = []
    n_classes = cm.shape[0]
    
    for i in range(n_classes):
        # For class i:
        # TN = all elements - (row i + column i - diagonal element)
        tn = cm.sum() - (cm[i, :].sum() + cm[:, i].sum() - cm[i, i])
        fp = cm[:, i].sum() - cm[i, i]
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        specificities.append(spec)
    
    # Return macro average specificity
    return sum(specificities) / len(specificities) if specificities else 0.0

def safe_precision_recall_fscore_support(y_true, y_pred, average=None):
    """Safe wrapper for precision_recall_fscore_support with zero_division handling"""
    from sklearn.metrics import precision_recall_fscore_support as prfs
    return prfs(y_true, y_pred, average=average, zero_division=0)

def confidence_from_proba(y_proba):
    """Extract confidence from probabilities"""
    if y_proba.ndim == 1:
        return float(np.max(y_proba))
    else:
        return float(np.max(y_proba, axis=1).mean())

def calculate_prediction_entropy(y_proba):
    """Calculate entropy of predictions as uncertainty measure"""
    if y_proba.ndim == 1:
        # Binary case
        y_proba = np.column_stack([1-y_proba, y_proba])
    
    # Add small epsilon to avoid log(0)
    epsilon = 1e-15
    y_proba = np.clip(y_proba, epsilon, 1 - epsilon)
    entropy = -np.sum(y_proba * np.log(y_proba), axis=1)
    return float(np.mean(entropy))

def get_clinical_interpretation(metrics):
    """Provide clinical interpretation of metrics"""
    interpretation = {
        'overall_performance': '',
        'clinical_relevance': '',
        'recommendations': []
    }
    
    # Overall performance assessment
    f1 = metrics.get('f1', 0)
    if f1 >= 0.85:
        interpretation['overall_performance'] = 'Excellent performance'
    elif f1 >= 0.75:
        interpretation['overall_performance'] = 'Good performance'
    elif f1 >= 0.60:
        interpretation['overall_performance'] = 'Moderate performance'
    else:
        interpretation['overall_performance'] = 'Poor performance'
    
    # Clinical relevance
    sensitivity = metrics.get('sensitivity', 0)
    specificity = metrics.get('specificity', 0)
    
    if sensitivity >= 0.9 and specificity >= 0.9:
        interpretation['clinical_relevance'] = 'High clinical utility - good for screening'
    elif sensitivity >= 0.8 or specificity >= 0.8:
        interpretation['clinical_relevance'] = 'Moderate clinical utility'
    else:
        interpretation['clinical_relevance'] = 'Limited clinical utility - needs improvement'
    
    # Recommendations
    if f1 < 0.7:
        interpretation['recommendations'].append('Consider collecting more training data')
        interpretation['recommendations'].append('Try different augmentation strategies')
    
    if sensitivity < 0.8:
        interpretation['recommendations'].append('Focus on reducing false negatives')
    
    if specificity < 0.8:
        interpretation['recommendations'].append('Focus on reducing false positives')
    
    return interpretation
