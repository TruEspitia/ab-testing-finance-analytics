
import sys
import os
import pandas as pd
import numpy as np
import traceback

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

try:
    from backend.time_series_analyzer import TimeSeriesAnalyzer
    print("Successfully imported TimeSeriesAnalyzer")
except ImportError as e:
    print(f"Failed to import: {e}")
    sys.exit(1)

def create_dummy_data():
    # Create 100 days of data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    values = np.linspace(10, 50, 100) + np.random.normal(0, 5, 100)
    
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    # Convert to string to simulate reading from CSV/API where types might be loose initially
    # actually dataset_manager probably returns proper types if read via pandas, but let's see.
    # The API request has col names.
    return df

def test_arima():
    print("Creating dummy data...")
    df = create_dummy_data()
    print("Data created. Head:")
    print(df.head())
    
    print("\nInitializing Analyzer...")
    analyzer = TimeSeriesAnalyzer(df)
    
    print("\nRunning analyze_arima...")
    try:
        result = analyzer.analyze_arima(
            time_column='date',
            value_column='value',
            periods_ahead=10,
            auto_select=True
        )
        print("\nSuccess!")
        print("Keys in result:", result.keys())
    except Exception:
        print("\nCaught Exception:")
        traceback.print_exc()

# Copied from backend/api/routers/quick_stats.py to test it
def _generate_arima_interpretation(result):
    """Genera interpretación del modelo ARIMA"""
    order = result['model_params']['order']
    is_stationary = result['stationarity']['is_stationary']
    
    interpretation = f"""
Model ARIMA{order} ...
AIC: {result['model_params']['aic']:.2f}
Stationarity: {is_stationary}
...
"""
    return interpretation.strip()

def test_arima_edge_cases():
    print("\n--- Testing Edge Cases ---")
    
    # Case 1: Short series (less than m=12)
    print("\n1. Short series (n=10)")
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    values = np.random.rand(10)
    df_short = pd.DataFrame({'date': dates, 'value': values})
    analyzer = TimeSeriesAnalyzer(df_short)
    try:
        result = analyzer.analyze_arima('date', 'value', periods_ahead=5)
        print("Short series success")
        _generate_arima_interpretation(result)
        print("Interpretation success")
    except Exception as e:
        print(f"Short series failed: {e}")
        traceback.print_exc()

    # Case 2: Constant series
    print("\n2. Constant series")
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    values = np.ones(50) * 10
    df_const = pd.DataFrame({'date': dates, 'value': values})
    analyzer = TimeSeriesAnalyzer(df_const)
    try:
        result = analyzer.analyze_arima('date', 'value')
        print("Constant series success")
        _generate_arima_interpretation(result)
        print("Interpretation success")
    except Exception as e:
        print(f"Constant series failed: {e}")
        traceback.print_exc()

    # Case 3: Series with NaN
    print("\n3. Series with NaN")
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    values = np.random.rand(50)
    values[10] = np.nan
    df_nan = pd.DataFrame({'date': dates, 'value': values})
    analyzer = TimeSeriesAnalyzer(df_nan)
    try:
        # Note: analyze_arima implementation does dropping of NaNs before analysis?
        # Let's check source code... it does `ts_data[value_column].dropna()` for adfuller
        # but for auto_arima it passes `ts_data[value_column]`. 
        # If auto_arima receives NaNs behavior depends on settings.
        result = analyzer.analyze_arima('date', 'value')
        print("NaN series success")
        _generate_arima_interpretation(result)
        print("Interpretation success")
    except Exception as e:
        print(f"NaN series failed: {e}")
        traceback.print_exc()

    # Case 4: String values in value column
    print("\n4. String values in value column")
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    values = [f"val_{i}" for i in range(10)]
    df_str = pd.DataFrame({'date': dates, 'value': values})
    analyzer = TimeSeriesAnalyzer(df_str)
    try:
        result = analyzer.analyze_arima('date', 'value')
        print("String values success (unexpected)")
    except Exception as e:
        print(f"String values failed as expected: {e}")
        # traceback.print_exc()

    # Case 5: Invalid dates
    print("\n5. Invalid dates")
    dates = ["not-a-date"] * 10
    values = np.random.rand(10)
    df_bad_date = pd.DataFrame({'date': dates, 'value': values})
    analyzer = TimeSeriesAnalyzer(df_bad_date)
    try:
        result = analyzer.analyze_arima('date', 'value')
        print("Invalid dates success (unexpected)")
    except Exception as e:
        print(f"Invalid dates failed as expected: {e}")
        # traceback.print_exc()

if __name__ == "__main__":
    test_arima()
    test_arima_edge_cases()
