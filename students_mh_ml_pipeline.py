"""
Students Mental Health ML Pipeline
===================================

Machine learning pipeline for predicting mental health risk in students
based on demographic, academic, lifestyle, and social factors.

Dataset: Real student mental health survey (7,022 students, 20 features)
Target: Composite mental health score (derived from stress, depression, anxiety)

Author: Mental Health Analytics Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import joblib
from datetime import datetime
from typing import Dict, Tuple, List
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.metrics import (mean_absolute_error, r2_score, mean_squared_error,
                            classification_report, confusion_matrix)
import warnings
warnings.filterwarnings('ignore')

# Optional: SHAP for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("ℹ️  SHAP not installed. Install with: pip install shap")


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration for Students Mental Health ML Pipeline"""
    
    MODEL_VERSION = "StudentMH_v1.0.0"
    RANDOM_STATE = 42
    
    # Data split
    VAL_SIZE = 0.15
    TEST_SIZE = 0.15
    CV_FOLDS = 5
    
    # Model parameters
    RF_N_ESTIMATORS = 150
    RF_MAX_DEPTH = 15
    RF_MIN_SAMPLES_SPLIT = 10
    
    # Ordinal encodings (explicitly defined for interpretability)
    ORDINAL_MAPPINGS = {
        'Sleep_Quality': ['Poor', 'Average', 'Good'],
        'Physical_Activity': ['Low', 'Moderate', 'High'],
        'Diet_Quality': ['Poor', 'Average', 'Good'],
        'Social_Support': ['Low', 'Moderate', 'High'],
        'Substance_Use': ['Never', 'Occasionally', 'Frequently'],
        'Counseling_Service_Use': ['Never', 'Occasionally', 'Frequently'],
        'Extracurricular_Involvement': ['Low', 'Moderate', 'High']
    }
    
    # Nominal encodings (no inherent order)
    NOMINAL_FEATURES = ['Course', 'Gender', 'Relationship_Status', 'Residence_Type']
    
    # Binary encodings
    BINARY_MAPPINGS = {
        'Family_History': {'No': 0, 'Yes': 1},
        'Chronic_Illness': {'No': 0, 'Yes': 1}
    }
    
    # Risk thresholds for classification
    RISK_THRESHOLDS = {
        'Low': (0.0, 0.3),
        'Moderate': (0.3, 0.6),
        'High': (0.6, 0.8),
        'Critical': (0.8, 1.0)
    }
    
    # File paths
    MODEL_SAVE_PATH = "student_mh_model.pkl"
    DATABASE_PATH = "students_mental_health.db"


# =============================================================================
# DATA LOADING & PREPROCESSING
# =============================================================================

class DataProcessor:
    """Handle all data loading and preprocessing"""
    
    def __init__(self):
        self.ordinal_encoders = {}
        self.nominal_encoder = None
        self.is_fitted = False
    
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """Load student mental health survey CSV"""
        df = pd.read_csv(filepath)
        print(f"✓ Loaded {len(df)} records from CSV")
        return df
    
    def create_target_variable(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create composite mental health score from stress, depression, anxiety
        
        Formula: Normalized weighted average
        - Stress: 30%
        - Depression: 40% (more weight as it's more severe)
        - Anxiety: 30%
        
        Output: 0 (good mental health) to 1 (severe issues)
        """
        df = df.copy()
        
        # Normalize to 0-1 scale (all are 0-5 range)
        stress_norm = df['Stress_Level'] / 5.0
        depression_norm = df['Depression_Score'] / 5.0
        anxiety_norm = df['Anxiety_Score'] / 5.0
        
        # Weighted composite score
        df['Mental_Health_Risk'] = (
            0.30 * stress_norm +
            0.40 * depression_norm +
            0.30 * anxiety_norm
        )
        
        # Clip to ensure 0-1 range
        df['Mental_Health_Risk'] = df['Mental_Health_Risk'].clip(0, 1)
        
        return df
    
    def preprocess_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """
        Preprocess all features
        
        Steps:
        1. Handle missing values
        2. Encode ordinal variables
        3. Encode nominal variables (one-hot)
        4. Encode binary variables
        """
        df = df.copy()
        
        # 1. Handle missing values
        df = self._handle_missing_values(df)
        
        # 2. Encode ordinal variables
        for feature, categories in Config.ORDINAL_MAPPINGS.items():
            if feature in df.columns:
                if fit:
                    encoder = OrdinalEncoder(
                        categories=[categories],
                        handle_unknown='use_encoded_value',
                        unknown_value=-1
                    )
                    df[[f'{feature}_encoded']] = encoder.fit_transform(df[[feature]])
                    self.ordinal_encoders[feature] = encoder
                else:
                    encoder = self.ordinal_encoders[feature]
                    df[[f'{feature}_encoded']] = encoder.transform(df[[feature]])
        
        # 3. Encode nominal variables (one-hot encoding)
        if fit:
            # Create dummy variables
            df_encoded = pd.get_dummies(df, columns=Config.NOMINAL_FEATURES, 
                                       prefix=Config.NOMINAL_FEATURES,
                                       drop_first=True)  # Avoid multicollinearity
            self.nominal_columns = [col for col in df_encoded.columns 
                                   if any(col.startswith(f"{feat}_") 
                                         for feat in Config.NOMINAL_FEATURES)]
            df = df_encoded
        else:
            # Use saved column structure
            df_encoded = pd.get_dummies(df, columns=Config.NOMINAL_FEATURES,
                                       prefix=Config.NOMINAL_FEATURES,
                                       drop_first=True)
            # Ensure same columns as training
            for col in self.nominal_columns:
                if col not in df_encoded.columns:
                    df_encoded[col] = 0
            df = df_encoded[df_encoded.columns.intersection(
                [c for c in df_encoded.columns if c not in Config.NOMINAL_FEATURES]
            )]
        
        # 4. Encode binary variables
        for feature, mapping in Config.BINARY_MAPPINGS.items():
            if feature in df.columns:
                df[f'{feature}_encoded'] = df[feature].map(mapping)
        
        if fit:
            self.is_fitted = True
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately"""
        df = df.copy()
        
        # CGPA: fill with median
        if 'CGPA' in df.columns:
            df['CGPA'].fillna(df['CGPA'].median(), inplace=True)
        
        # Substance_Use: fill with most common (Never)
        if 'Substance_Use' in df.columns:
            df['Substance_Use'].fillna('Never', inplace=True)
        
        # Relationship_Status: fill with most common
        if 'Relationship_Status' in df.columns:
            df['Relationship_Status'].fillna(df['Relationship_Status'].mode()[0], 
                                            inplace=True)
        
        return df
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for modeling"""
        feature_cols = [
            'Age', 'CGPA', 'Semester_Credit_Load', 'Financial_Stress',
            # Ordinal encoded
            'Sleep_Quality_encoded', 'Physical_Activity_encoded',
            'Diet_Quality_encoded', 'Social_Support_encoded',
            'Substance_Use_encoded', 'Counseling_Service_Use_encoded',
            'Extracurricular_Involvement_encoded',
            # Binary encoded
            'Family_History_encoded', 'Chronic_Illness_encoded'
        ]
        
        # Add one-hot encoded nominal features
        if hasattr(self, 'nominal_columns'):
            feature_cols.extend(self.nominal_columns)
        
        return feature_cols


# =============================================================================
# ML MODEL
# =============================================================================

class MentalHealthPredictor:
    """Predict student mental health risk"""
    
    def __init__(self):
        self.regressor = RandomForestRegressor(
            n_estimators=Config.RF_N_ESTIMATORS,
            max_depth=Config.RF_MAX_DEPTH,
            min_samples_split=Config.RF_MIN_SAMPLES_SPLIT,
            random_state=Config.RANDOM_STATE,
            n_jobs=-1
        )
        
        self.processor = DataProcessor()
        self.feature_columns = None
        self.is_trained = False
        self.shap_explainer = None
    
    def train(self, 
              df: pd.DataFrame,
              use_cross_validation: bool = True) -> Dict:
        """
        Train mental health risk predictor
        
        Args:
            df: Raw dataframe with all features
            use_cross_validation: Whether to perform k-fold CV
        
        Returns:
            Dictionary with training metrics
        """
        print("\n" + "="*70)
        print("TRAINING MENTAL HEALTH RISK PREDICTOR")
        print("="*70)
        
        # Create target variable
        df = self.processor.create_target_variable(df)
        print(f"✓ Created composite mental health risk score")
        
        # Preprocess features
        df_processed = self.processor.preprocess_features(df, fit=True)
        print(f"✓ Preprocessed features")
        
        # Get feature columns
        self.feature_columns = self.processor.get_feature_columns()
        available_cols = [col for col in self.feature_columns if col in df_processed.columns]
        print(f"✓ Using {len(available_cols)} features")
        
        X = df_processed[available_cols].values
        y = df['Mental_Health_Risk'].values
        
        # Train/val/test split
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=Config.TEST_SIZE, random_state=Config.RANDOM_STATE
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val,
            test_size=Config.VAL_SIZE / (1 - Config.TEST_SIZE),
            random_state=Config.RANDOM_STATE
        )
        
        print(f"\nData Split:")
        print(f"  Training:   {len(X_train)} samples")
        print(f"  Validation: {len(X_val)} samples")
        print(f"  Test:       {len(X_test)} samples")
        
        # Train model
        print(f"\nTraining RandomForest with {Config.RF_N_ESTIMATORS} trees...")
        self.regressor.fit(X_train, y_train)
        self.is_trained = True
        print("✓ Training complete")
        
        # Cross-validation
        cv_scores = None
        if use_cross_validation:
            print(f"\nRunning {Config.CV_FOLDS}-fold cross-validation...")
            kfold = KFold(n_splits=Config.CV_FOLDS, shuffle=True, 
                         random_state=Config.RANDOM_STATE)
            cv_scores = cross_val_score(
                self.regressor, X_train, y_train,
                cv=kfold,
                scoring='neg_mean_absolute_error'
            )
            print(f"  CV MAE: {-cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        # Evaluate
        y_train_pred = self.regressor.predict(X_train)
        y_val_pred = self.regressor.predict(X_val)
        y_test_pred = self.regressor.predict(X_test)
        
        metrics = {
            # Training
            'train_mae': mean_absolute_error(y_train, y_train_pred),
            'train_r2': r2_score(y_train, y_train_pred),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            
            # Validation
            'val_mae': mean_absolute_error(y_val, y_val_pred),
            'val_r2': r2_score(y_val, y_val_pred),
            'val_rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
            
            # Test
            'test_mae': mean_absolute_error(y_test, y_test_pred),
            'test_r2': r2_score(y_test, y_test_pred),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
            
            # CV
            'cv_mae_mean': -cv_scores.mean() if cv_scores is not None else None,
            'cv_mae_std': cv_scores.std() if cv_scores is not None else None,
            
            # For later use
            'X_test': X_test,
            'y_test': y_test,
            'available_columns': available_cols
        }
        
        # Initialize SHAP
        if SHAP_AVAILABLE:
            print("\nInitializing SHAP explainer...")
            self.shap_explainer = shap.TreeExplainer(self.regressor)
            print("✓ SHAP explainer ready")
        
        return metrics
    
    def predict(self, df: pd.DataFrame, return_shap: bool = False) -> List[Dict]:
        """
        Predict mental health risk for students
        
        Args:
            df: DataFrame with student features
            return_shap: Whether to include SHAP values
        
        Returns:
            List of prediction dictionaries
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Preprocess
        df_processed = self.processor.preprocess_features(df, fit=False)
        
        # Get features
        available_cols = [col for col in self.feature_columns 
                         if col in df_processed.columns]
        X = df_processed[available_cols].values
        
        # Predict
        risk_scores = self.regressor.predict(X)
        risk_scores = np.clip(risk_scores, 0, 1)
        
        # Get feature importance
        feature_importance = self.get_feature_importance(available_cols)
        
        # Get SHAP if requested
        shap_values = None
        if return_shap and SHAP_AVAILABLE and self.shap_explainer:
            shap_values = self.shap_explainer.shap_values(X)
        
        # Build results
        results = []
        for i in range(len(X)):
            risk_level = self._categorize_risk(risk_scores[i])
            top_factor = self._identify_top_factor(
                df.iloc[i] if i < len(df) else None,
                feature_importance
            )
            
            result = {
                'mental_health_risk_score': float(risk_scores[i]),
                'risk_level': risk_level,
                'top_risk_factor': top_factor,
                'feature_importance': feature_importance,
                'model_version': Config.MODEL_VERSION,
                'prediction_timestamp': datetime.now().isoformat()
            }
            
            if shap_values is not None:
                result['shap_values'] = {
                    available_cols[j]: float(shap_values[i, j])
                    for j in range(len(available_cols))
                }
            
            results.append(result)
        
        return results
    
    def _categorize_risk(self, score: float) -> str:
        """Categorize risk score into Low/Moderate/High/Critical"""
        for level, (low, high) in Config.RISK_THRESHOLDS.items():
            if low <= score < high:
                return level
        return 'Critical'  # Default for scores >= 0.8
    
    def _identify_top_factor(self, 
                            student_row: pd.Series,
                            importance: Dict[str, float]) -> str:
        """Identify primary risk factor for a student"""
        if student_row is None:
            return list(importance.keys())[0]
        
        factors = []
        
        # Check various risk factors
        if 'Sleep_Quality' in student_row and student_row['Sleep_Quality'] == 'Poor':
            factors.append(('poor_sleep', 0.85))
        
        if 'Financial_Stress' in student_row and student_row['Financial_Stress'] >= 4:
            factors.append(('financial_stress', 0.80))
        
        if 'Social_Support' in student_row and student_row['Social_Support'] == 'Low':
            factors.append(('low_social_support', 0.75))
        
        if 'Counseling_Service_Use' in student_row and student_row['Counseling_Service_Use'] == 'Never':
            if 'Stress_Level' in student_row and student_row['Stress_Level'] >= 3:
                factors.append(('no_counseling_high_stress', 0.70))
        
        if 'Physical_Activity' in student_row and student_row['Physical_Activity'] == 'Low':
            factors.append(('low_physical_activity', 0.65))
        
        if 'Semester_Credit_Load' in student_row and student_row['Semester_Credit_Load'] >= 25:
            factors.append(('academic_overload', 0.70))
        
        # Return highest priority factor or most important feature
        if factors:
            return max(factors, key=lambda x: x[1])[0]
        else:
            return list(importance.keys())[0]
    
    def get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance dictionary"""
        importances = self.regressor.feature_importances_
        importance_dict = dict(zip(feature_names, importances))
        return dict(sorted(importance_dict.items(), 
                          key=lambda x: x[1], 
                          reverse=True))
    
    def save(self, filepath: str = None):
        """Save model to disk"""
        if filepath is None:
            filepath = Config.MODEL_SAVE_PATH
        
        model_data = {
            'regressor': self.regressor,
            'processor': self.processor,
            'feature_columns': self.feature_columns,
            'config': {
                'version': Config.MODEL_VERSION,
                'random_state': Config.RANDOM_STATE
            }
        }
        
        joblib.dump(model_data, filepath)
        print(f"\n✓ Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str = None):
        """Load model from disk"""
        if filepath is None:
            filepath = Config.MODEL_SAVE_PATH
        
        model_data = joblib.load(filepath)
        
        predictor = cls()
        predictor.regressor = model_data['regressor']
        predictor.processor = model_data['processor']
        predictor.feature_columns = model_data['feature_columns']
        predictor.is_trained = True
        
        if SHAP_AVAILABLE:
            predictor.shap_explainer = shap.TreeExplainer(predictor.regressor)
        
        print(f"✓ Model loaded from {filepath}")
        print(f"  Version: {model_data['config']['version']}")
        
        return predictor


# =============================================================================
# DATABASE INTEGRATION
# =============================================================================

def load_data_to_database(df: pd.DataFrame, db_path: str = Config.DATABASE_PATH):
    """Load CSV data into SQLite database"""
    conn = sqlite3.connect(db_path)
    
    print(f"\nLoading data to database: {db_path}")
    
    # Create composite score
    processor = DataProcessor()
    df = processor.create_target_variable(df)
    
    # Insert students
    for idx, row in df.iterrows():
        cursor = conn.cursor()
        
        # Insert student
        cursor.execute("""
            INSERT OR IGNORE INTO students (
                age, course, gender, cgpa, semester_credit_load, residence_type
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            int(row['Age']),
            row['Course'],
            row['Gender'],
            float(row['CGPA']) if pd.notna(row['CGPA']) else None,
            int(row['Semester_Credit_Load']),
            row['Residence_Type']
        ))
        
        student_id = cursor.lastrowid
        
        # Insert mental health assessment
        cursor.execute("""
            INSERT INTO mental_health_assessments (
                student_id, stress_level, depression_score, anxiety_score, 
                mental_health_score
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            student_id,
            int(row['Stress_Level']),
            int(row['Depression_Score']),
            int(row['Anxiety_Score']),
            float(row['Mental_Health_Risk'])
        ))
        
        # Insert lifestyle factors
        cursor.execute("""
            INSERT INTO lifestyle_factors (
                student_id, sleep_quality, physical_activity, diet_quality
            ) VALUES (?, ?, ?, ?)
        """, (
            student_id,
            row['Sleep_Quality'],
            row['Physical_Activity'],
            row['Diet_Quality']
        ))
        
        # Insert social factors
        cursor.execute("""
            INSERT INTO social_factors (
                student_id, social_support, relationship_status, 
                substance_use, extracurricular_involvement
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            student_id,
            row['Social_Support'],
            row['Relationship_Status'],
            row['Substance_Use'] if pd.notna(row['Substance_Use']) else 'Never',
            row['Extracurricular_Involvement']
        ))
        
        # Insert support services
        cursor.execute("""
            INSERT INTO support_services (
                student_id, counseling_service_use
            ) VALUES (?, ?)
        """, (
            student_id,
            row['Counseling_Service_Use']
        ))
        
        # Insert medical history
        cursor.execute("""
            INSERT OR IGNORE INTO medical_history (
                student_id, family_history_mental_health, chronic_illness
            ) VALUES (?, ?, ?)
        """, (
            student_id,
            1 if row['Family_History'] == 'Yes' else 0,
            1 if row['Chronic_Illness'] == 'Yes' else 0
        ))
        
        # Insert stress factors
        cursor.execute("""
            INSERT INTO stress_factors (
                student_id, financial_stress
            ) VALUES (?, ?)
        """, (
            student_id,
            int(row['Financial_Stress'])
        ))
        
        if idx % 1000 == 0:
            print(f"  Processed {idx} records...")
    
    conn.commit()
    conn.close()
    print(f"✓ Loaded {len(df)} records to database")


def store_predictions(predictions: List[Dict], 
                     student_ids: List[int],
                     db_path: str = Config.DATABASE_PATH):
    """Store model predictions to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for student_id, pred in zip(student_ids, predictions):
        cursor.execute("""
            INSERT INTO ml_predictions (
                student_id, predicted_stress_level, composite_mental_health_score,
                risk_level, top_risk_factor, feature_importance_json,
                model_version, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            pred['mental_health_risk_score'] * 5,  # Convert back to 0-5 scale
            pred['mental_health_risk_score'],
            pred['risk_level'],
            pred['top_risk_factor'],
            json.dumps(pred['feature_importance']),
            pred['model_version'],
            0.85  # Placeholder confidence
        ))
    
    conn.commit()
    conn.close()
    print(f"✓ Stored {len(predictions)} predictions to database")


# =============================================================================
# EVALUATION & REPORTING
# =============================================================================

def print_evaluation_report(metrics: Dict):
    """Print comprehensive evaluation report"""
    print("\n" + "="*70)
    print("MENTAL HEALTH RISK PREDICTOR - EVALUATION REPORT")
    print("="*70)
    print(f"Model Version: {Config.MODEL_VERSION}")
    print(f"Dataset: Students Mental Health Survey")
    print("="*70)
    
    print("\nTRAINING METRICS:")
    print(f"  MAE:  {metrics['train_mae']:.4f}")
    print(f"  R²:   {metrics['train_r2']:.4f}")
    print(f"  RMSE: {metrics['train_rmse']:.4f}")
    
    print("\nVALIDATION METRICS:")
    print(f"  MAE:  {metrics['val_mae']:.4f}")
    print(f"  R²:   {metrics['val_r2']:.4f}")
    print(f"  RMSE: {metrics['val_rmse']:.4f}")
    
    if metrics.get('cv_mae_mean'):
        print(f"\nCROSS-VALIDATION ({Config.CV_FOLDS}-fold):")
        print(f"  MAE: {metrics['cv_mae_mean']:.4f} "
              f"(+/- {metrics['cv_mae_std']:.4f})")
    
    print("\nTEST METRICS (Final Evaluation):")
    print(f"  MAE:  {metrics['test_mae']:.4f}")
    print(f"  R²:   {metrics['test_r2']:.4f}")
    print(f"  RMSE: {metrics['test_rmse']:.4f}")
    
    print("\nINTERPRETATION:")
    print(f"  Average prediction error: {metrics['test_mae']:.1%} of risk scale")
    print(f"  Model explains {metrics['test_r2']:.1%} of variance in mental health risk")
    print("="*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution pipeline"""
    
    print("="*70)
    print("STUDENTS MENTAL HEALTH ML PIPELINE")
    print("="*70)
    
    # Load data
    print("\n1. Loading dataset...")
    df = pd.read_csv('/mnt/user-data/uploads/students_mental_health_survey.csv')
    print(f"   ✓ Loaded {len(df)} students")
    
    # Train model
    print("\n2. Training model...")
    model = MentalHealthPredictor()
    metrics = model.train(df, use_cross_validation=True)
    
    # Print evaluation
    print_evaluation_report(metrics)
    
    # Save model
    print("\n3. Saving model...")
    model.save()
    
    # Example predictions
    print("\n4. Example Predictions:")
    print("-" * 70)
    sample_students = df.head(5)
    predictions = model.predict(sample_students, return_shap=SHAP_AVAILABLE)
    
    for i, pred in enumerate(predictions):
        print(f"\nStudent {i+1}:")
        print(f"  Risk Score: {pred['mental_health_risk_score']:.3f}")
        print(f"  Risk Level: {pred['risk_level']}")
        print(f"  Top Factor: {pred['top_risk_factor']}")
    
    # Feature importance
    print("\n5. Top 10 Risk Factors:")
    print("-" * 70)
    importance = predictions[0]['feature_importance']
    for i, (feat, imp) in enumerate(list(importance.items())[:10], 1):
        print(f"  {i:2}. {feat:40} {imp:.4f}")
    
    print("\n" + "="*70)
    print("Pipeline execution complete!")
    print("="*70)
    
    return model, metrics, predictions


if __name__ == "__main__":
    model, metrics, predictions = main()
