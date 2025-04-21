"""
Custom data processor for handling crashdata2011-2021.csv format
"""

import pandas as pd
import numpy as np
from datetime import datetime

def process_crash_data(df):
    """
    Process the crashdata2011-2021.csv format data
    
    Args:
        df: Loaded pandas dataframe
    
    Returns:
        Processed dataframe and stats dictionary
    """
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Convert crash datetime to proper format
    processed_df['datetime'] = pd.to_datetime(processed_df['CrashDateTime'], errors='coerce')
    processed_df['date'] = processed_df['datetime'].dt.date
    processed_df['time'] = processed_df['datetime'].dt.time
    
    # Map fields to our standard format
    processed_df['incident_type'] = 'crash'  # Default incident type
    
    # Calculate severity based on injury columns
    def calculate_severity(row):
        if row['FatalInjuries'] > 0:
            return 5  # Fatal
        elif row['SevereInjuries'] > 0:
            return 4  # Severe
        elif row['ModerateInjuries'] > 0:
            return 3  # Moderate
        elif row['MinorInjuries'] > 0:
            return 2  # Minor
        else:
            return 1  # Property damage only
    
    processed_df['severity'] = processed_df.apply(calculate_severity, axis=1)
    
    # Create a more descriptive location field
    processed_df['location'] = processed_df.apply(
        lambda row: f"{row['AStreetName']} & {row['BStreetName']}" 
        if pd.notna(row['AStreetName']) and pd.notna(row['BStreetName']) 
        else row['AStreetName'] if pd.notna(row['AStreetName']) 
        else row['BStreetName'] if pd.notna(row['BStreetName'])
        else "Unknown", axis=1
    )
    
    # Map weather condition to our standard format
    weather_mapping = {
        'Clear': 'clear',
        'Rain': 'rain',
        'Fog': 'fog',
        'Snow': 'snow',
        'Cloudy': 'cloudy',
        'Other': 'other'
    }
    processed_df['weather'] = processed_df['Weather'].map(
        lambda x: next((v for k, v in weather_mapping.items() if k in str(x)), 'other')
    )
    
    # Extract traffic density from other features
    def estimate_traffic_density(row):
        time = row['datetime'].hour if not pd.isna(row['datetime']) else 12
        
        # Rush hours typically have high traffic
        if (7 <= time <= 9) or (16 <= time <= 18):
            return 'high'
        # Late night typically has low traffic
        elif 22 <= time or time <= 5:
            return 'low'
        # Other times have medium traffic
        else:
            return 'medium'
    
    processed_df['traffic_density'] = processed_df.apply(estimate_traffic_density, axis=1)
    
    # Add day of week
    processed_df['day_of_week'] = processed_df['datetime'].dt.day_name()
    processed_df['hour'] = processed_df['datetime'].dt.hour
    
    # Generate statistics
    stats = {
        'total_incidents': len(processed_df),
        'incident_types': {'crash': len(processed_df)},
        'locations': processed_df['location'].value_counts().head(10).to_dict(),
        'severity_distribution': processed_df['severity'].value_counts().to_dict(),
        'weather_distribution': processed_df['weather'].value_counts().to_dict(),
        'collisions_by_type': processed_df['CollisionType'].value_counts().to_dict(),
        'factors': processed_df['PrimaryCollisionFactor'].value_counts().head(5).to_dict()
    }
    
    # Time-based stats
    hour_counts = processed_df['hour'].value_counts().sort_index()
    stats['incidents_by_hour'] = hour_counts.to_dict()
    stats['incidents_by_day'] = processed_df['day_of_week'].value_counts().to_dict()
    
    # Year stats
    if 'datetime' in processed_df.columns:
        processed_df['year'] = processed_df['datetime'].dt.year
        stats['incidents_by_year'] = processed_df['year'].value_counts().sort_index().to_dict()
    
    return processed_df, stats
