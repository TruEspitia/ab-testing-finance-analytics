"""
Single Variable Analyzer
Analiza estadísticas descriptivas para una sola variable
"""
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px


class SingleVariableAnalyzer:
    """Analizador de variables individuales (numéricas y categóricas)"""
    
    def analyze(self, df: pd.DataFrame, variable: str) -> dict:
        """
        Analiza una variable individual
        
        Args:
            df: DataFrame con los datos
            variable: Nombre de la variable a analizar
            
        Returns:
            dict con estadísticas y plot
        """
        # Validar que la variable existe
        if variable not in df.columns:
            raise ValueError(f"Variable '{variable}' no encontrada")
        
        # Obtener la serie sin valores nulos
        series = df[variable].dropna()
        
        if len(series) == 0:
            raise ValueError("La variable no tiene datos válidos")
        
        # Detectar tipo de variable
        is_numeric = pd.api.types.is_numeric_dtype(series)
        
        if is_numeric:
            return self._analyze_numeric(series, variable)
        else:
            return self._analyze_categorical(series, variable)
    
    def _analyze_categorical(self, series: pd.Series, variable: str) -> dict:
        """Analiza variable categórica"""
        value_counts = series.value_counts()
        mode_value = value_counts.index[0] if len(value_counts) > 0 else None
        
        # Crear gráfico de barras
        fig = px.bar(
            x=value_counts.index.astype(str)[:20],  # Top 20 categorías
            y=value_counts.values[:20],
            labels={'x': variable, 'y': 'Frecuencia'},
            title=f'Distribución de {variable}'
        )
        fig.update_layout(
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc')
        )
        
        return {
            "success": True,
            "variable": variable,
            "type": "categorical",
            "n_observations": int(len(series)),
            "n_unique": int(series.nunique()),
            "mode": str(mode_value),
            "top_categories": value_counts.head(10).to_dict(),
            "plot": fig.to_json()
        }
    
    def _analyze_numeric(self, series: pd.Series, variable: str) -> dict:
        """Analiza variable numérica"""
        # Estadísticas básicas
        mean_val = float(series.mean())
        median_val = float(series.median())
        std_val = float(series.std())
        var_val = float(series.var())
        
        # Moda
        mode_result = stats.mode(series)
        try:
            mode_val = float(mode_result.mode[0]) if hasattr(mode_result.mode, '__getitem__') else float(mode_result.mode)
        except (IndexError, TypeError):
            mode_val = mean_val
        
        # Error estándar de la media
        sem_val = float(stats.sem(series))
        
        # Rango
        min_val = float(series.min())
        max_val = float(series.max())
        range_val = max_val - min_val
        
        # Cuartiles
        q1 = float(series.quantile(0.25))
        q2 = float(series.quantile(0.50))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        
        # Asimetría y curtosis
        skewness = float(series.skew())
        kurtosis = float(series.kurtosis())
        
        # Coeficiente de variación
        cv = (std_val / mean_val * 100) if mean_val != 0 else 0
        
        # Crear histograma
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=series,
            name='Distribución',
            marker_color='rgba(99, 102, 241, 0.7)',
            nbinsx=30
        ))
        
        # Línea de media
        fig.add_vline(
            x=mean_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Media: {mean_val:.2f}",
            annotation_position="top"
        )
        
        # Línea de mediana
        fig.add_vline(
            x=median_val,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Mediana: {median_val:.2f}",
            annotation_position="bottom"
        )
        
        fig.update_layout(
            title=f'Distribución de {variable}',
            xaxis_title=variable,
            yaxis_title='Frecuencia',
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc'),
            showlegend=True
        )
        
        return {
            "success": True,
            "variable": variable,
            "type": "numeric",
            "n_observations": int(len(series)),
            "statistics": {
                "central_tendency": {
                    "mean": round(mean_val, 4),
                    "median": round(median_val, 4),
                    "mode": round(mode_val, 4)
                },
                "dispersion": {
                    "std": round(std_val, 4),
                    "variance": round(var_val, 4),
                    "sem": round(sem_val, 4),
                    "cv": round(cv, 2)
                },
                "range": {
                    "min": round(min_val, 4),
                    "max": round(max_val, 4),
                    "range": round(range_val, 4)
                },
                "quartiles": {
                    "q1": round(q1, 4),
                    "q2": round(q2, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4)
                },
                "shape": {
                    "skewness": round(skewness, 4),
                    "kurtosis": round(kurtosis, 4)
                }
            },
            "plot": fig.to_json()
        }
