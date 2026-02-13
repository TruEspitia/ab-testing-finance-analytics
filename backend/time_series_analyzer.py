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

    def _detect_seasonal_period(self, ts_index):
        """
        Detecta el período estacional basado en la frecuencia del índice temporal.
        """
        freq = pd.infer_freq(ts_index)
        if freq is None:
            # Estimar frecuencia por la mediana de diferencias
            diffs = pd.Series(ts_index).diff().dropna()
            if len(diffs) > 0:
                median_diff = diffs.median()
                days = median_diff.days if hasattr(median_diff, 'days') else 1
                if days <= 1:
                    return 7, 'D'    # Diario → estacionalidad semanal
                elif days <= 7:
                    return 4, 'W'    # Semanal → estacionalidad mensual (~4 semanas)
                elif days <= 31:
                    return 12, 'MS'  # Mensual → estacionalidad anual
                else:
                    return 4, 'QS'   # Trimestral → estacionalidad anual
            return 7, 'D'  # Default

        freq_upper = freq.upper()
        if freq_upper.startswith('D') or freq_upper.startswith('B'):
            return 7, freq     # Diario/Business → semanal
        elif freq_upper.startswith('W'):
            return 52, freq    # Semanal → anual
        elif freq_upper.startswith('M') or freq_upper.startswith('MS'):
            return 12, freq    # Mensual → anual
        elif freq_upper.startswith('Q') or freq_upper.startswith('QS'):
            return 4, freq     # Trimestral → anual
        elif freq_upper.startswith('H'):
            return 24, freq    # Horario → diario
        elif freq_upper.startswith('T') or freq_upper.startswith('MIN'):
            return 60, freq    # Minutal → horario
        else:
            return 12, freq    # Fallback

    def analyze_arima(self, time_column: str, value_column: str,
                      periods_ahead: int = 10, auto_select: bool = True):
        """
        Realiza análisis ARIMA con detección automática de parámetros
        """
        # Preparar datos
        ts_data = self.df[[time_column, value_column]].copy()
        ts_data[time_column] = pd.to_datetime(ts_data[time_column])
        ts_data = ts_data.sort_values(time_column)
        ts_data = ts_data.dropna(subset=[value_column])
        
        # Agregar valores duplicados en la misma fecha (promedio)
        # Esto es crítico para columnas con duplicados como "Age"
        ts_data = ts_data.groupby(time_column)[value_column].mean().to_frame()
        
        # Ya no necesitamos set_index porque groupby ya lo hizo
        # ts_data.set_index(time_column, inplace=True)

        # Detectar período estacional y frecuencia
        seasonal_period, detected_freq = self._detect_seasonal_period(ts_data.index)
        n_obs = len(ts_data)

        # Si la serie es muy corta para estacionalidad, desactivar
        use_seasonal = n_obs >= 2 * seasonal_period

        # Test de estacionariedad
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
            try:
                model = auto_arima(
                    ts_data[value_column],
                    seasonal=use_seasonal,
                    m=seasonal_period if use_seasonal else 1,
                    start_p=1, start_q=1,
                    max_p=5, max_q=5,
                    max_d=2, max_D=1,
                    d=None,        # Auto-detect differencing
                    D=None if use_seasonal else 0,
                    stepwise=True,
                    suppress_warnings=True,
                    error_action='ignore',
                    trace=False,
                    information_criterion='aic',
                    with_intercept=True
                )
                order = tuple(int(x) for x in model.order)
                seasonal_order = tuple(int(x) for x in model.seasonal_order)
            except Exception:
                order = (1, 1, 1)
                seasonal_order = (0, 0, 0, 0)
        else:
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
            # Fallback progresivo
            fallback_orders = [(1, 1, 1), (2, 1, 2), (1, 1, 0), (0, 1, 1)]
            fitted_model = None
            for fb_order in fallback_orders:
                try:
                    arima_model = ARIMA(ts_data[value_column], order=fb_order)
                    fitted_model = arima_model.fit()
                    order = fb_order
                    seasonal_order = (0, 0, 0, 0)
                    break
                except Exception:
                    continue
            if fitted_model is None:
                arima_model = ARIMA(ts_data[value_column], order=(1, 0, 0))
                fitted_model = arima_model.fit()
                order = (1, 0, 0)
                seasonal_order = (0, 0, 0, 0)

        # Pronóstico
        forecast = fitted_model.forecast(steps=periods_ahead)

        # Generar fechas futuras
        last_date = ts_data.index[-1]
        freq = pd.infer_freq(ts_data.index)
        if not freq:
            freq = 'D'

        try:
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods_ahead,
                freq=freq
            )
        except Exception:
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods_ahead,
                freq='D'
            )

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
