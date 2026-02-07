import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from pmdarima import auto_arima
import warnings
warnings.filterwarnings('ignore')

class TimeSeriesAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def analyze_arima(self, time_column: str, value_column: str, 
                      periods_ahead: int = 10, auto_select: bool = True):
        """
        Realiza análisis ARIMA con detección automática de parámetros
        """
        # Preparar datos
        ts_data = self.df[[time_column, value_column]].copy()
        ts_data[time_column] = pd.to_datetime(ts_data[time_column])
        ts_data = ts_data.sort_values(time_column)
        ts_data.set_index(time_column, inplace=True)
        
        # Test de estacionariedad
        # Manejo básico de errores si la serie es muy corta o constante
        try:
            adf_result = adfuller(ts_data[value_column].dropna())
            is_stationary = bool(adf_result[1] < 0.05)
            adf_stat = float(adf_result[0])
            p_value = float(adf_result[1])
        except Exception:
            is_stationary = False
            adf_stat = 0.0
            p_value = 1.0
        
        if auto_select:
            # Auto ARIMA para encontrar mejores parámetros
            try:
                model = auto_arima(
                    ts_data[value_column],
                    seasonal=True,
                    m=12,  # Frecuencia mensual por defecto, ajustable si se detecta otra
                    stepwise=True,
                    suppress_warnings=True,
                    error_action='ignore'
                )
                order = tuple(int(x) for x in model.order)
                seasonal_order = tuple(int(x) for x in model.seasonal_order)
            except Exception:
                # Fallback si auto_arima falla
                order = (1, 1, 1)
                seasonal_order = (0, 0, 0, 0)
        else:
            # Parámetros por defecto
            order = (1, 1, 1)
            seasonal_order = (0, 0, 0, 0)
        
        # Ajustar modelo
        try:
            arima_model = ARIMA(
                ts_data[value_column], 
                order=order,
                seasonal_order=seasonal_order
            )
            fitted_model = arima_model.fit()
        except Exception:
            # Si falla el ajuste con los parámetros dados, intentar un modelo simple
            arima_model = ARIMA(ts_data[value_column], order=(1,0,0))
            fitted_model = arima_model.fit()
            order = (1,0,0)
            seasonal_order = (0,0,0,0)
        
        # Pronóstico
        forecast = fitted_model.forecast(steps=periods_ahead)
        
        # Generar fechas futuras
        last_date = ts_data.index[-1]
        # Inferir frecuencia si es posible
        freq = pd.infer_freq(ts_data.index)
        if not freq:
            freq = 'D' # Default a diario si no se puede inferir
            
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1), # Esto es aproximado, idealmente usar freq
            periods=periods_ahead,
            freq=freq
        )
        # Si pd.date_range con freq falla o genera algo raro, fallback manual simple (dias)
        if len(future_dates) != periods_ahead:
             future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods_ahead,
                freq='D'
            )

        forecast_df = pd.DataFrame({
            'forecast': forecast,
            'date': future_dates
        })
        
        # Intervalos de confianza
        forecast_summary = fitted_model.get_forecast(steps=periods_ahead)
        conf_int = forecast_summary.conf_int()
        
        # Convertir a listas serializables
        dates_iso = [d.isoformat() for d in ts_data.index]
        forecast_dates_iso = [d.isoformat() for d in forecast_df['date']]
        
        return {
            'success': True,
            'model_params': {
                'order': order,
                'seasonal_order': seasonal_order,
                'aic': getattr(fitted_model, 'aic', 0),
                'bic': getattr(fitted_model, 'bic', 0)
            },
            'stationarity': {
                'is_stationary': is_stationary,
                'adf_statistic': adf_stat,
                'p_value': p_value
            },
            'historical_data': {
                'dates': dates_iso,
                'values': ts_data[value_column].fillna(0).tolist(),
                'fitted_values': fitted_model.fittedvalues.fillna(0).tolist()
            },
            'forecast': {
                'dates': forecast_dates_iso,
                'values': forecast_df['forecast'].fillna(0).tolist(),
                'lower_bound': conf_int.iloc[:, 0].fillna(0).tolist(),
                'upper_bound': conf_int.iloc[:, 1].fillna(0).tolist()
            },
            'metrics': {
                'rmse': float(np.sqrt(fitted_model.mse)),
                'mae': float(fitted_model.mae)
            },
            'model_summary': fitted_model.summary().as_text()
        }
