"""
Unit tests for machine learning models
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ml_models import SafetyScorePredictor, IncidentRiskClassifier, generate_time_predictions

class TestSafetyScorePredictor(unittest.TestCase):
    def setUp(self):
        # Create predictor with a non-existent model path for testing
        self.predictor = SafetyScorePredictor(model_path="test_models/test_safety_model.pkl")
    
    def test_fallback_prediction(self):
        """Test that fallback prediction returns valid safety scores"""
        # Test with empty features
        score = self.predictor._fallback_prediction({})
        self.assertGreaterEqual(score, 1.0)
        self.assertLessEqual(score, 10.0)
        
        # Test with various feature combinations
        features = {
            'time_of_day': 'Morning Rush Hour',
            'weather': 'Rainy',
            'traffic_density': 8
        }
        score = self.predictor._fallback_prediction(features)
        self.assertGreaterEqual(score, 1.0)
        self.assertLessEqual(score, 10.0)
        
        # Test that rain and rush hour reduce safety score
        baseline = self.predictor._fallback_prediction({})
        rainy_score = self.predictor._fallback_prediction({'weather': 'Rainy'})
        rush_hour_score = self.predictor._fallback_prediction({'time_of_day': 'Morning Rush Hour'})
        
        self.assertLess(rainy_score, baseline)
        self.assertLess(rush_hour_score, baseline)
    
    def test_predict_method(self):
        """Test that predict method works even without a trained model"""
        features = {
            'time_of_day': 'Evening Rush Hour',
            'weather': 'Clear',
            'traffic_density': 5,
            'day_of_week': 'Monday'
        }
        
        score = self.predictor.predict(features)
        self.assertGreaterEqual(score, 1.0)
        self.assertLessEqual(score, 10.0)
        
        # Test with a DataFrame
        df = pd.DataFrame([features])
        score = self.predictor.predict(df)
        self.assertGreaterEqual(score, 1.0)
        self.assertLessEqual(score, 10.0)


class TestRiskClassifier(unittest.TestCase):
    def setUp(self):
        # Create classifier with a non-existent model path for testing
        self.classifier = IncidentRiskClassifier(model_path="test_models/test_risk_model.pkl")
    
    def test_fallback_risk_prediction(self):
        """Test that fallback risk prediction returns valid results"""
        # Test with empty features
        risk = self.classifier._fallback_risk_prediction({})
        
        self.assertIn('risk_level', risk)
        self.assertIn('probability', risk)
        self.assertIn('class_probabilities', risk)
        self.assertIn(risk['risk_level'], ['low', 'medium', 'high'])
        self.assertGreaterEqual(risk['probability'], 0.0)
        self.assertLessEqual(risk['probability'], 1.0)
        
        # Test with high risk features
        high_risk_features = {
            'time_of_day': 'Evening Rush Hour',
            'weather': 'Rainy',
            'day_of_week': 'Friday'
        }
        
        risk = self.classifier._fallback_risk_prediction(high_risk_features)
        self.assertEqual(risk['risk_level'], 'high')
        self.assertGreater(risk['probability'], 0.7)
        
        # Check that probabilities sum to 1
        probabilities = risk['class_probabilities'].values()
        self.assertAlmostEqual(sum(probabilities), 1.0, places=2)
    
    def test_predict_risk_method(self):
        """Test that predict_risk method works even without a trained model"""
        features = {
            'time_of_day': 'Late Night',
            'weather': 'Foggy',
            'day_of_week': 'Saturday'
        }
        
        risk = self.classifier.predict_risk(features)
        
        self.assertIn('risk_level', risk)
        self.assertIn('probability', risk) 
        self.assertIn('class_probabilities', risk)
        self.assertIn(risk['risk_level'], ['low', 'medium', 'high'])
        
        # Check that probabilities sum to 1
        probabilities = risk['class_probabilities'].values()
        self.assertAlmostEqual(sum(probabilities), 1.0, places=2)


class TestTimePredictions(unittest.TestCase):
    def test_generate_time_predictions(self):
        """Test that time predictions work for different times of day"""
        # Create predictor
        predictor = SafetyScorePredictor()
        
        # Test with base features
        base_features = {
            'weather': 'Clear',
            'traffic_density': 5,
            'day_of_week': 'Monday'
        }
        
        safety_score = 7.5
        
        predictions = generate_time_predictions(predictor, base_features, safety_score)
        
        # Check all time periods are present
        expected_periods = [
            "Early Morning (5-7 AM)",
            "Morning Rush (7-9 AM)",
            "Mid-Day (9 AM-4 PM)", 
            "Evening Rush (4-7 PM)",
            "Evening (7-10 PM)",
            "Late Night (10 PM-5 AM)"
        ]
        
        for period in expected_periods:
            self.assertIn(period, predictions)
            self.assertGreaterEqual(predictions[period], 1.0)
            self.assertLessEqual(predictions[period], 10.0)
        
        # Check that rush hours have lower safety scores
        self.assertLess(predictions["Morning Rush (7-9 AM)"], predictions["Early Morning (5-7 AM)"])
        self.assertLess(predictions["Evening Rush (4-7 PM)"], predictions["Mid-Day (9 AM-4 PM)"])


if __name__ == '__main__':
    unittest.main()
