import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.time_series_analyzer import TimeSeriesAnalyzer

def test_arima_analysis():
    # Crear datos de prueba
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    # Serie con tendencia y algo de ruido
    values = np.linspace(0, 10, 100) + np.random.normal(0, 0.5, 100)
    df = pd.DataFrame({'date': dates, 'value': values})
    
    analyzer = TimeSeriesAnalyzer(df)
    result = analyzer.analyze_arima(
        time_column='date', 
        value_column='value', 
        periods_ahead=10,
        auto_select=False # Usar parámetros simples para speed
    )
    
    assert result['success'] == True
    assert len(result['forecast']['values']) == 10
    assert 'model_params' in result
    assert 'metrics' in result
    assert 'stationarity' in result
    assert len(result['historical_data']['values']) == 100

def test_arima_auto_select():
    # Test shorter series with auto_select
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    values = np.random.randn(30) + 10
    df = pd.DataFrame({'date': dates, 'value': values})
    
    analyzer = TimeSeriesAnalyzer(df)
    result = analyzer.analyze_arima('date', 'value', periods_ahead=5, auto_select=True)
    
    assert result['success'] == True
    assert len(result['forecast']['values']) == 5
