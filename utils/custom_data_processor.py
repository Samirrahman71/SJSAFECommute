"""
Custom data processor for handling crashdata2011-2021.csv format
and for handling custom uploaded data formats
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

def process_custom_data(df, column_mapping):
    """
    Process custom uploaded data based on user-defined column mapping
    
    Args:
        df: Uploaded pandas dataframe
        column_mapping: Dictionary mapping standard field names to dataset column names
            Expected keys: date, location, severity, weather, factor, time
    
    Returns:
        Processed dataframe and stats dictionary
    """
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Apply column mapping while maintaining original data
    # Create standardized columns based on the mapping
    
    # Process date/time information
    if column_mapping.get('date'):
        # Try to convert to datetime
        try:
            processed_df['date'] = pd.to_datetime(processed_df[column_mapping['date']], errors='coerce')
            
            # If we successfully converted to datetime, extract components
            if not processed_df['date'].isna().all():
                processed_df['year'] = processed_df['date'].dt.year
                processed_df['month'] = processed_df['date'].dt.month
                processed_df['day_of_week'] = processed_df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
                
                # Try to get hour from date or separate time column
                if column_mapping.get('time'):
                    # If time is in a separate column
                    try:
                        time_series = pd.to_datetime(processed_df[column_mapping['time']], format='%H:%M:%S', errors='coerce')
                        processed_df['hour'] = time_series.dt.hour
                    except:
                        # If time is not in a standard format, try to extract from strings
                        processed_df['hour'] = processed_df[column_mapping['time']].str.extract('(\d+)').astype(float)
                else:
                    # Try to extract hour from datetime
                    processed_df['hour'] = processed_df['date'].dt.hour
        except:
            # If date conversion fails, create a placeholder
            processed_df['date'] = None
            processed_df['year'] = None
            processed_df['month'] = None
            processed_df['day_of_week'] = None
            processed_df['hour'] = None
    
    # Process location information
    if column_mapping.get('location'):
        processed_df['location'] = processed_df[column_mapping['location']]
    else:
        processed_df['location'] = 'Unknown'
    
    # Process severity information
    if column_mapping.get('severity'):
        # Try to map severity to numerical values if they're not already
        try:
            # First try to convert directly to numbers
            processed_df['severity'] = pd.to_numeric(processed_df[column_mapping['severity']], errors='coerce')
            
            # If conversion failed or produced NaNs, try text mapping
            if processed_df['severity'].isna().all():
                # Map common text descriptions to numerical scale (1-5)
                severity_mapping = {
                    'fatal': 5, 'death': 5, 'killed': 5,
                    'critical': 4, 'severe': 4, 'serious': 4, 'major': 4,
                    'moderate': 3, 'significant': 3,
                    'minor': 2, 'slight': 2, 'light': 2,
                    'property': 1, 'pdo': 1, 'damage': 1, 'none': 1, 'no injury': 1
                }
                
                # Create a lowercase version of the column for mapping
                col_lower = processed_df[column_mapping['severity']].astype(str).str.lower()
                
                # Apply mapping based on substring matching
                def map_severity(text):
                    for key, value in severity_mapping.items():
                        if key in text:
                            return value
                    return 3  # Default to moderate if no match
                
                processed_df['severity'] = col_lower.apply(map_severity)
        except:
            # If all else fails, create a default severity
            processed_df['severity'] = 3  # Default to moderate
    else:
        processed_df['severity'] = 3  # Default severity 
    
    # Process weather information
    if column_mapping.get('weather'):
        # Standard weather mapping
        weather_mapping = {
            'clear': 'clear', 'sunny': 'clear', 'fair': 'clear',
            'rain': 'rain', 'rainy': 'rain', 'shower': 'rain', 
            'snow': 'snow', 'snowy': 'snow', 'sleet': 'snow', 'hail': 'snow',
            'fog': 'fog', 'foggy': 'fog', 'mist': 'fog',
            'cloud': 'cloudy', 'overcast': 'cloudy',
            'wind': 'windy', 'gust': 'windy', 'storm': 'stormy'
        }
        
        # Create lowercase version for mapping
        col_lower = processed_df[column_mapping['weather']].astype(str).str.lower()
        
        # Apply mapping
        def map_weather(text):
            for key, value in weather_mapping.items():
                if key in text:
                    return value
            return 'other'
        
        processed_df['weather'] = col_lower.apply(map_weather)
    else:
        processed_df['weather'] = 'unknown'
    
    # Process factor information
    if column_mapping.get('factor'):
        processed_df['factor'] = processed_df[column_mapping['factor']]
    else:
        processed_df['factor'] = 'unknown'
    
    # Generate statistics for the dataset
    stats = {
        'total_incidents': len(processed_df),
    }
    
    # Add date range if available
    if 'date' in processed_df.columns and not processed_df['date'].isna().all():
        min_date = processed_df['date'].min()
        max_date = processed_df['date'].max()
        if pd.notna(min_date) and pd.notna(max_date):
            stats['date_range'] = f"{min_date.strftime('%b %d, %Y')} to {max_date.strftime('%b %d, %Y')}"
            
            # Calculate months between dates for average
            months_diff = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
            stats['avg_monthly'] = len(processed_df) / max(1, months_diff)
    
    # Add other stats based on available data
    if 'location' in processed_df.columns:
        stats['locations'] = processed_df['location'].value_counts().head(10).to_dict()
    
    if 'severity' in processed_df.columns:
        stats['severity_distribution'] = processed_df['severity'].value_counts().sort_index().to_dict()
    
    if 'weather' in processed_df.columns:
        stats['weather_distribution'] = processed_df['weather'].value_counts().to_dict()
    
    if 'factor' in processed_df.columns:
        stats['factors'] = processed_df['factor'].value_counts().head(5).to_dict()
    
    if 'hour' in processed_df.columns and not processed_df['hour'].isna().all():
        hour_counts = processed_df['hour'].value_counts().sort_index()
        stats['incidents_by_hour'] = hour_counts.to_dict()
    
    if 'day_of_week' in processed_df.columns and not processed_df['day_of_week'].isna().all():
        day_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
                      3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        day_counts = processed_df['day_of_week'].value_counts().sort_index()
        day_counts.index = day_counts.index.map(lambda x: day_mapping.get(x, x))
        stats['incidents_by_day'] = day_counts.to_dict()
    
    return processed_df, stats
