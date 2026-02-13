
import pandas as pd
import numpy as np
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from backend.time_series_analyzer import TimeSeriesAnalyzer

def reproduce_issue():
    print("Loading sample data...")
    df = pd.read_csv('sample_data/customer_segmentation_mixed.csv')
    
    # Use 'Age' as time column and 'Spending_Score' as value
    time_col = 'Age'
    value_col = 'Spending_Score'
    
    print(f"Analyzing {value_col} over {time_col}...")
    analyzer = TimeSeriesAnalyzer(df)
    
    try:
        result = analyzer.analyze_arima(
            time_column=time_col,
            value_column=value_col,
            periods_ahead=10,
            auto_select=True
        )
        
        print("\nAnalysis Result Summary:")
        print(f"Success: {result['success']}")
        print(f"Model Order: {result['model_params']['order']}")
        print(f"Number of historical dates: {len(result['historical_data']['dates'])}")
        print(f"First 5 historical dates: {result['historical_data']['dates'][:5]}")
        
        # Check for duplicates in historical dates
        unique_dates = len(set(result['historical_data']['dates']))
        print(f"Number of unique historical dates: {unique_dates}")
        
        if unique_dates < len(result['historical_data']['dates']):
            print("WARNING: Found duplicate dates in historical data!")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce_issue()
