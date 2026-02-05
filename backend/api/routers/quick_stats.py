"""
Quick Stats API Router
Proporciona estadísticas descriptivas rápidas para análisis exploratorio
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from ...dataset_manager import dataset_manager

router = APIRouter(prefix="/quick-stats", tags=["quick-stats"])


class SingleVariableRequest(BaseModel):
    dataset_id: str
    variable: str


class DualVariableRequest(BaseModel):
    dataset_id: str
    variable_x: str
    variable_y: str


@router.post("/single")
async def analyze_single_variable(request: SingleVariableRequest):
    """
    Calcula estadísticas descriptivas para una variable
    
    Args:
        request: Dataset ID y nombre de la variable
        
    Returns:
        Estadísticas descriptivas completas y histograma
    """
    # Obtener dataset
    df = dataset_manager.get_dataset(request.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    # Validar que la variable existe
    if request.variable not in df.columns:
        raise HTTPException(status_code=400, detail=f"Variable '{request.variable}' no encontrada")
    
    # Obtener la serie
    series = df[request.variable].dropna()
    
    if len(series) == 0:
        raise HTTPException(status_code=400, detail="La variable no tiene datos válidos")
    
    # Detectar tipo de variable
    is_numeric = pd.api.types.is_numeric_dtype(series)
    
    if not is_numeric:
        # Para variables categóricas
        value_counts = series.value_counts()
        mode_value = value_counts.index[0] if len(value_counts) > 0 else None
        
        # Crear gráfico de barras
        fig = px.bar(
            x=value_counts.index.astype(str)[:20],  # Top 20 categorías
            y=value_counts.values[:20],
            labels={'x': request.variable, 'y': 'Frecuencia'},
            title=f'Distribución de {request.variable}'
        )
        fig.update_layout(
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='transparent',
            font=dict(color='#f8fafc')
        )
        
        return {
            "success": True,
            "variable": request.variable,
            "type": "categorical",
            "n_observations": int(len(series)),
            "n_unique": int(series.nunique()),
            "mode": str(mode_value),
            "top_categories": value_counts.head(10).to_dict(),
            "plot": fig.to_json()
        }
    
    # Para variables numéricas
    try:
        # Estadísticas básicas
        mean_val = float(series.mean())
        median_val = float(series.median())
        std_val = float(series.std())
        var_val = float(series.var())
        
        # Moda (puede haber múltiples)
        mode_result = stats.mode(series, keepdims=True)
        mode_val = float(mode_result.mode[0]) if len(mode_result.mode) > 0 else mean_val
        
        # Error estándar de la media
        sem_val = float(stats.sem(series))
        
        # Rango
        min_val = float(series.min())
        max_val = float(series.max())
        range_val = max_val - min_val
        
        # Cuartiles
        q1 = float(series.quantile(0.25))
        q2 = float(series.quantile(0.50))  # mediana
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        
        # Asimetría y curtosis
        skewness = float(series.skew())
        kurtosis = float(series.kurtosis())
        
        # Coeficiente de variación
        cv = (std_val / mean_val * 100) if mean_val != 0 else 0
        
        # Crear histograma con Plotly
        fig = go.Figure()
        
        # Histograma
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
            title=f'Distribución de {request.variable}',
            xaxis_title=request.variable,
            yaxis_title='Frecuencia',
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='transparent',
            font=dict(color='#f8fafc'),
            showlegend=True
        )
        
        return {
            "success": True,
            "variable": request.variable,
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular estadísticas: {str(e)}")


@router.post("/dual")
async def analyze_dual_variables(request: DualVariableRequest):
    """
    Analiza la relación entre dos variables
    
    Args:
        request: Dataset ID y nombres de las dos variables
        
    Returns:
        Correlación y scatter plot
    """
    # Obtener dataset
    df = dataset_manager.get_dataset(request.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    # Validar variables
    if request.variable_x not in df.columns:
        raise HTTPException(status_code=400, detail=f"Variable X '{request.variable_x}' no encontrada")
    if request.variable_y not in df.columns:
        raise HTTPException(status_code=400, detail=f"Variable Y '{request.variable_y}' no encontrada")
    
    # Obtener datos limpios
    data = df[[request.variable_x, request.variable_y]].dropna()
    
    if len(data) < 2:
        raise HTTPException(status_code=400, detail="No hay suficientes datos válidos")
    
    x = data[request.variable_x]
    y = data[request.variable_y]
    
    # Verificar si ambas son numéricas
    x_numeric = pd.api.types.is_numeric_dtype(x)
    y_numeric = pd.api.types.is_numeric_dtype(y)
    
    if not (x_numeric and y_numeric):
        raise HTTPException(
            status_code=400,
            detail="Ambas variables deben ser numéricas para análisis dual"
        )
    
    try:
        # Calcular correlación de Pearson
        correlation, p_value = stats.pearsonr(x, y)
        
        # Calcular regresión lineal
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
        
        # Crear scatter plot
        fig = go.Figure()
        
        # Puntos
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            name='Datos',
            marker=dict(
                size=8,
                color='rgba(99, 102, 241, 0.6)',
                line=dict(width=1, color='white')
            )
        ))
        
        # Línea de tendencia
        x_range = np.linspace(x.min(), x.max(), 100)
        y_trend = slope * x_range + intercept
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_trend,
            mode='lines',
            name=f'Tendencia (R²={r_value**2:.3f})',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f'{request.variable_y} vs {request.variable_x}',
            xaxis_title=request.variable_x,
            yaxis_title=request.variable_y,
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='transparent',
            font=dict(color='#f8fafc'),
            showlegend=True,
            hovermode='closest'
        )
        
        # Interpretación de la correlación
        if abs(correlation) >= 0.7:
            strength = "fuerte"
        elif abs(correlation) >= 0.4:
            strength = "moderada"
        elif abs(correlation) >= 0.2:
            strength = "débil"
        else:
            strength = "muy débil o nula"
        
        direction = "positiva" if correlation > 0 else "negativa"
        
        interpretation = f"Existe una correlación {strength} {direction} entre las variables."
        
        return {
            "success": True,
            "variable_x": request.variable_x,
            "variable_y": request.variable_y,
            "n_observations": int(len(data)),
            "correlation": {
                "pearson_r": round(float(correlation), 4),
                "p_value": round(float(p_value), 6),
                "r_squared": round(float(r_value ** 2), 4),
                "is_significant": p_value < 0.05
            },
            "regression": {
                "slope": round(float(slope), 4),
                "intercept": round(float(intercept), 4),
                "std_error": round(float(std_err), 4),
                "equation": f"y = {slope:.4f}x + {intercept:.4f}"
            },
            "interpretation": interpretation,
            "plot": fig.to_json()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar variables: {str(e)}")
