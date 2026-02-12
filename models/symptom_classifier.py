from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import joblib

class SymptomClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.feature_importance_ = None
    
    def fit(self, X, y):
        self.model.fit(X, y)
        self.feature_importance_ = self.model.feature_importances_
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]
    
    def save(self, path):
        joblib.dump(self, path)
    
    @classmethod
    def load(cls, path):
        return joblib.load(path)
