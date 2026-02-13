
import pandas as pd
import numpy as np
import sys
import os

def test_data_processing():
    print("Loading sample data...")
    df = pd.read_csv('sample_data/customer_segmentation_mixed.csv')
    
    time_column = 'Age'
    value_column = 'Spending_Score'
    
    # Simulate first part of analyze_arima
    ts_data = df[[time_column, value_column]].copy()
    
    print(f"Original shape: {ts_data.shape}")
    
    ts_data[time_column] = pd.to_datetime(ts_data[time_column])
    ts_data = ts_data.sort_values(time_column)
    ts_data = ts_data.dropna(subset=[value_column])
    
    print(f"Index after pd.to_datetime and sort:")
    print(ts_data[time_column].head(10))
    
    # Check for duplicates
    duplicates = ts_data[time_column].duplicated().sum()
    print(f"Total duplicates in 'time' column: {duplicates}")
    
    # If we set index
    ts_data.set_index(time_column, inplace=True)
    print(f"Is index unique? {ts_data.index.is_unique}")
    
    # Freq inference
    import pandas as pd
    inferred_freq = pd.infer_freq(ts_data.index)
    print(f"Inferred frequency: {inferred_freq}")
    
    # If freq is None, the code does:
    diffs = pd.Series(ts_data.index).diff().dropna()
    if len(diffs) > 0:
        median_diff = diffs.median()
        print(f"Median difference: {median_diff}")
        # With duplicates, median_diff is likely 0 days 00:00:00!
        days = median_diff.days if hasattr(median_diff, 'days') else 1
        print(f"Days from median_diff: {days}")

if __name__ == "__main__":
    test_data_processing()
