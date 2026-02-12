import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

class SymptomProcessor:
    def __init__(self):
        self.numerical_features = ['age', 'blood_pressure', 'cholesterol']
        self.categorical_features = ['gender', 'hypertension', 'heart_disease']
        self.preprocessor = None
        self.scaler = StandardScaler()
    
    def fit(self, df):
        """Fit preprocessor on training data"""
        numerical_transformer = Pipeline([
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline([
            ('onehot', OneHotEncoder(drop='first', sparse_output=False))
        ])
        
        self.preprocessor = ColumnTransformer([
            ('num', numerical_transformer, self.numerical_features),
            ('cat', categorical_transformer, self.categorical_features)
        ])
        
        X_processed = self.preprocessor.fit_transform(df[self.numerical_features + self.categorical_features])
        return X_processed
    
    def transform(self, df):
        """Transform data"""
        if self.preprocessor is None:
            raise ValueError("Processor not fitted. Call fit() first.")
        return self.preprocessor.transform(df[self.numerical_features + self.categorical_features])
