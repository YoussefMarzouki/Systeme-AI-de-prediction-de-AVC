import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer

class SymptomProcessor:
    def __init__(self):
        self.numerical_features = ['age', 'avg_glucose_level', 'bmi']
        self.categorical_features = [
            'gender',
            'hypertension',
            'heart_disease',
            'ever_married',
            'work_type',
            'Residence_type',
            'smoking_status',
        ]
        self._fallback_numerical_features = ['age', 'blood_pressure', 'cholesterol']
        self._fallback_categorical_features = ['gender', 'hypertension', 'heart_disease']
        self.selected_numerical_features = []
        self.selected_categorical_features = []
        self.preprocessor = None

    def _select_available_features(self, df):
        num = [c for c in self.numerical_features if c in df.columns]
        cat = [c for c in self.categorical_features if c in df.columns]

        if not num and not cat:
            num = [c for c in self._fallback_numerical_features if c in df.columns]
            cat = [c for c in self._fallback_categorical_features if c in df.columns]

        if not num and not cat:
            raise ValueError("No usable symptom features found in dataframe.")

        self.selected_numerical_features = num
        self.selected_categorical_features = cat
        return num, cat
    
    def fit(self, df):
        """Fit preprocessor on training data"""
        df = df.copy()
        if 'bmi' in df.columns:
            df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')

        num_features, cat_features = self._select_available_features(df)

        numerical_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
        ])
        
        transformers = []
        if num_features:
            transformers.append(('num', numerical_transformer, num_features))
        if cat_features:
            transformers.append(('cat', categorical_transformer, cat_features))
        self.preprocessor = ColumnTransformer(transformers)
        
        X_processed = self.preprocessor.fit_transform(df[num_features + cat_features])
        return X_processed
    
    def transform(self, df):
        """Transform data"""
        if self.preprocessor is None:
            raise ValueError("Processor not fitted. Call fit() first.")
        df = df.copy()
        if 'bmi' in df.columns:
            df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')

        for col in self.selected_numerical_features + self.selected_categorical_features:
            if col not in df.columns:
                df[col] = np.nan

        cols = self.selected_numerical_features + self.selected_categorical_features
        return self.preprocessor.transform(df[cols])
