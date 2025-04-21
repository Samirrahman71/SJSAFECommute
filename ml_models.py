"""
Machine Learning Models for San Jose Safe Commute
Provides predictive models for route safety analysis and risk prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, classification_report
import joblib
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafetyScorePredictor:
    """
    ML model for predicting safety scores based on route and condition features
    """
    def __init__(self, model_path=None):
        self.model = None
        self.preprocessor = None
        self.model_path = model_path or "models/safety_score_model.pkl"
        self.feature_importance = {}
        self.load_model()

    def load_model(self):
        """Load the trained model if it exists, otherwise return None"""
        try:
            if os.path.exists(self.model_path):
                loaded_model = joblib.load(self.model_path)
                self.model = loaded_model.get('model')
                self.preprocessor = loaded_model.get('preprocessor')
                self.feature_importance = loaded_model.get('feature_importance', {})
                logger.info(f"Model loaded from {self.model_path}")
                return True
            else:
                logger.warning(f"Model file not found at {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False

    def train(self, X, y, test_size=0.2, random_state=42):
        """
        Train a new safety score prediction model
        
        Args:
            X: Features dataframe
            y: Target variable (safety scores)
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Model performance metrics
        """
        try:
            # Define feature types
            categorical_features = [col for col in X.columns if X[col].dtype == 'object']
            numerical_features = [col for col in X.columns if X[col].dtype != 'object']
            
            # Create preprocessor
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', StandardScaler(), numerical_features),
                    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
                ])
            
            # Create and train pipeline
            model = Pipeline([
                ('preprocessor', preprocessor),
                ('regressor', RandomForestRegressor(n_estimators=100, random_state=random_state))
            ])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Extract feature importance
            if hasattr(model['regressor'], 'feature_importances_'):
                # Get feature names from preprocessor
                cat_features = model['preprocessor'].transformers_[1][1].get_feature_names_out(categorical_features)
                all_features = numerical_features + list(cat_features)
                
                # Map importances to features
                importances = model['regressor'].feature_importances_
                feature_importance = {feature: importance for feature, importance in zip(all_features, importances)}
                # Sort by importance descending
                self.feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            # Save the model
            self.model = model['regressor']
            self.preprocessor = model['preprocessor']
            
            if not os.path.exists(os.path.dirname(self.model_path)):
                os.makedirs(os.path.dirname(self.model_path))
                
            # Save model artifacts
            joblib.dump({
                'model': self.model,
                'preprocessor': self.preprocessor,
                'feature_importance': self.feature_importance
            }, self.model_path)
            
            logger.info(f"Model trained and saved to {self.model_path}")
            
            return {
                'rmse': rmse,
                'mse': mse,
                'feature_importance': self.feature_importance
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict(self, features):
        """
        Predict safety score for given route and condition features
        
        Args:
            features: Dict or DataFrame with feature values
            
        Returns:
            Predicted safety score (float)
        """
        try:
            if self.model is None or self.preprocessor is None:
                logger.warning("Model not loaded. Using fallback prediction logic.")
                return self._fallback_prediction(features)
            
            # Convert dict to DataFrame if needed
            if isinstance(features, dict):
                features_df = pd.DataFrame([features])
            else:
                features_df = features
            
            # Preprocess features
            X_processed = self.preprocessor.transform(features_df)
            
            # Make prediction
            prediction = self.model.predict(X_processed)
            
            return float(prediction[0]) if len(prediction) == 1 else prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return self._fallback_prediction(features)

    def _fallback_prediction(self, features):
        """
        Generate a safety score when model fails
        
        Args:
            features: Dict with feature values
            
        Returns:
            Estimated safety score (float)
        """
        # Base score
        score = 7.0
        
        # Extract features from dict
        if isinstance(features, dict):
            # Time of day adjustments
            time_of_day = features.get('time_of_day', '').lower()
            if 'morning' in time_of_day and 'rush' in time_of_day:
                score -= 1.5
            elif 'evening' in time_of_day and 'rush' in time_of_day:
                score -= 1.8
            elif 'night' in time_of_day or 'late' in time_of_day:
                score -= 1.0
            
            # Weather adjustments
            weather = features.get('weather', '').lower()
            if 'rain' in weather:
                score -= 1.0
            elif 'fog' in weather:
                score -= 1.2
            elif 'snow' in weather:
                score -= 1.5
            
            # Traffic density adjustments
            traffic = features.get('traffic_density', 0)
            if isinstance(traffic, (int, float)):
                score -= (traffic / 10) * 2
        
        # Ensure score is within 1-10 range
        return max(1.0, min(10.0, score))

class IncidentRiskClassifier:
    """
    ML model for classifying incident risk levels at specific locations and times
    """
    def __init__(self, model_path=None):
        self.model = None
        self.preprocessor = None
        self.model_path = model_path or "models/incident_risk_model.pkl"
        self.classes = ['low', 'medium', 'high']
        self.load_model()

    def load_model(self):
        """Load the trained model if it exists, otherwise return None"""
        try:
            if os.path.exists(self.model_path):
                loaded_model = joblib.load(self.model_path)
                self.model = loaded_model.get('model')
                self.preprocessor = loaded_model.get('preprocessor')
                self.classes = loaded_model.get('classes', ['low', 'medium', 'high'])
                logger.info(f"Risk classifier loaded from {self.model_path}")
                return True
            else:
                logger.warning(f"Risk classifier not found at {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading risk classifier: {str(e)}")
            return False

    def train(self, X, y, test_size=0.2, random_state=42):
        """
        Train a new incident risk classifier
        
        Args:
            X: Features dataframe
            y: Target variable (risk levels)
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Model performance metrics
        """
        try:
            # Define feature types
            categorical_features = [col for col in X.columns if X[col].dtype == 'object']
            numerical_features = [col for col in X.columns if X[col].dtype != 'object']
            
            # Create preprocessor
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', StandardScaler(), numerical_features),
                    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
                ])
            
            # Create and train pipeline
            model = Pipeline([
                ('preprocessor', preprocessor),
                ('classifier', GradientBoostingClassifier(n_estimators=100, random_state=random_state))
            ])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Save the model
            self.model = model['classifier']
            self.preprocessor = model['preprocessor']
            self.classes = list(model['classifier'].classes_)
            
            if not os.path.exists(os.path.dirname(self.model_path)):
                os.makedirs(os.path.dirname(self.model_path))
                
            # Save model artifacts
            joblib.dump({
                'model': self.model,
                'preprocessor': self.preprocessor,
                'classes': self.classes
            }, self.model_path)
            
            logger.info(f"Risk classifier trained and saved to {self.model_path}")
            
            return {
                'classification_report': report,
                'accuracy': report['accuracy']
            }
            
        except Exception as e:
            logger.error(f"Error training risk classifier: {str(e)}")
            raise

    def predict_risk(self, features):
        """
        Predict incident risk level for given location and condition features
        
        Args:
            features: Dict or DataFrame with feature values
            
        Returns:
            Dict with risk level and probability
        """
        try:
            if self.model is None or self.preprocessor is None:
                logger.warning("Risk classifier not loaded. Using fallback prediction logic.")
                return self._fallback_risk_prediction(features)
            
            # Convert dict to DataFrame if needed
            if isinstance(features, dict):
                features_df = pd.DataFrame([features])
            else:
                features_df = features
            
            # Preprocess features
            X_processed = self.preprocessor.transform(features_df)
            
            # Make prediction
            prediction = self.model.predict(X_processed)
            probabilities = self.model.predict_proba(X_processed)
            
            # Get highest probability class
            risk_level = prediction[0]
            risk_proba = max(probabilities[0])
            
            return {
                'risk_level': risk_level,
                'probability': float(risk_proba),
                'class_probabilities': {cls: float(prob) for cls, prob in zip(self.classes, probabilities[0])}
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk: {str(e)}")
            return self._fallback_risk_prediction(features)

    def _fallback_risk_prediction(self, features):
        """
        Generate a risk prediction when model fails
        
        Args:
            features: Dict with feature values
            
        Returns:
            Dict with estimated risk level and probability
        """
        # Default medium risk
        risk_level = 'medium'
        risk_proba = 0.6
        
        # Extract features from dict
        if isinstance(features, dict):
            # Time factors
            time_of_day = features.get('time_of_day', '').lower()
            if 'rush' in time_of_day:
                risk_level = 'high'
                risk_proba = 0.8
            elif 'night' in time_of_day:
                risk_level = 'high'
                risk_proba = 0.75
                
            # Weather factors
            weather = features.get('weather', '').lower()
            if any(w in weather for w in ['rain', 'fog', 'snow', 'storm']):
                risk_level = 'high'
                risk_proba = 0.82
                
            # Day of week
            day = features.get('day_of_week', '').lower()
            if day in ['friday', 'saturday']:
                if risk_level == 'high':
                    risk_proba += 0.05
                else:
                    risk_level = 'medium'
                    risk_proba = 0.65
        
        # Generate probabilities for all classes
        if risk_level == 'high':
            class_probabilities = {'low': 0.05, 'medium': 1 - risk_proba - 0.05, 'high': risk_proba}
        elif risk_level == 'medium':
            class_probabilities = {'low': 0.2, 'medium': risk_proba, 'high': 1 - risk_proba - 0.2}
        else:
            class_probabilities = {'low': risk_proba, 'medium': 0.3, 'high': 1 - risk_proba - 0.3}
            
        return {
            'risk_level': risk_level,
            'probability': risk_proba,
            'class_probabilities': class_probabilities
        }

def generate_time_predictions(model, base_features, safety_score):
    """
    Generate safety predictions for different times of day
    
    Args:
        model: Instance of SafetyScorePredictor
        base_features: Base feature values
        safety_score: Current safety score
        
    Returns:
        Dict mapping time periods to predicted safety scores
    """
    time_periods = [
        "Early Morning (5-7 AM)",
        "Morning Rush (7-9 AM)",
        "Mid-Day (9 AM-4 PM)",
        "Evening Rush (4-7 PM)",
        "Evening (7-10 PM)",
        "Late Night (10 PM-5 AM)"
    ]
    
    predictions = {}
    
    try:
        for period in time_periods:
            # Copy base features and update time
            features = base_features.copy()
            features['time_of_day'] = period
            
            # Predict safety score for this time
            prediction = model.predict(features)
            predictions[period] = prediction
            
    except Exception as e:
        logger.error(f"Error generating time predictions: {str(e)}")
        # Fallback to heuristic predictions
        predictions = {
            "Early Morning (5-7 AM)": min(safety_score + 1.0, 10.0),
            "Morning Rush (7-9 AM)": max(safety_score - 1.0, 1.0),
            "Mid-Day (9 AM-4 PM)": min(safety_score + 0.5, 10.0),
            "Evening Rush (4-7 PM)": max(safety_score - 1.2, 1.0),
            "Evening (7-10 PM)": safety_score,
            "Late Night (10 PM-5 AM)": max(safety_score - 0.8, 1.0)
        }
    
    return predictions

# Initialize models
safety_model = SafetyScorePredictor()
risk_classifier = IncidentRiskClassifier()
