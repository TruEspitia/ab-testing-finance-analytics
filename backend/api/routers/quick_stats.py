"""
Quick Stats API Router
Proporciona estadísticas descriptivas rápidas para análisis exploratorio
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
import logging
import traceback
from ...dataset_manager import dataset_manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quick-stats", tags=["quick-stats"])


class SingleVariableRequest(BaseModel):
    dataset_id: str
    variable: str


class DualVariableRequest(BaseModel):
    dataset_id: str
    variable_x: str
    variable_y: str
    correlation_type: Optional[str] = "pearson" # "pearson", "spearman", "kendall", "full"


from fastapi.responses import StreamingResponse
import io
import json

class TimeSeriesRequest(BaseModel):
    dataset_id: str
    time_column: str
    value_column: str
    periods_ahead: int = Field(default=10, ge=1, le=365)
    auto_select_params: bool = True


class QuickStatsExportRequest(BaseModel):
    analysis_type: str  # "single", "dual", "timeseries"
    params: dict



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
            paper_bgcolor='rgba(0,0,0,0)',
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
        # scipy 1.11+ changed stats.mode() API, removed keepdims parameter
        mode_result = stats.mode(series)
        # In scipy 1.11+, mode_result.mode is a scalar, not an array
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
            paper_bgcolor='rgba(0,0,0,0)',
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
        # Calcular correlación según el tipo solicitado
        requested_type = request.correlation_type.lower() if request.correlation_type else "pearson"
        
        results = {}
        
        # Helper function to interpret strength
        def get_interpretation(corr_val, name):
            if abs(corr_val) >= 0.7: strength = "fuerte"
            elif abs(corr_val) >= 0.4: strength = "moderada"
            elif abs(corr_val) >= 0.2: strength = "débil"
            else: strength = "muy débil o nula"
            direction = "positiva" if corr_val > 0 else "negativa"
            return f"Correlación {strength} {direction} ({name})"

        # Generate 3D data (Z-axis is "movement" or normalized rank difference to visualize non-linearity)
        # For visualization purposes, let's create a "Movement" metric
        # This represents how much the rank changes between X and Y
        x_rank = stats.rankdata(x)
        y_rank = stats.rankdata(y)
        z_movement = np.abs(x_rank - y_rank)
        # Normalize Z to be somewhat comparable to data scale for visualization
        z_scale = (float(x.max()) - float(x.min()) + float(y.max()) - float(y.min())) / 2
        if z_scale == 0: z_scale = 1
        z_values = (z_movement / len(x)) * z_scale
        
        # Prepare 3D plot data
        plot_data_3d = {
            "x": x.tolist(),
            "y": y.tolist(),
            "z": z_values.tolist(),
            "mode": "markers",
            "marker": {
                "size": 5,
                "color": z_values.tolist(),
                "colorscale": "Viridis",
                "opacity": 0.8
            },
            "type": "scatter3d"
        }

        if requested_type == "full":
            # Calculate all three
            pearson_r, pearson_p = stats.pearsonr(x, y)
            spearman_r, spearman_p = stats.spearmanr(x, y)
            kendall_r, kendall_p = stats.kendalltau(x, y)
            
            # Linear Regression for trend line (always useful context)
            slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
            
            return {
                "success": True,
                "variable_x": request.variable_x,
                "variable_y": request.variable_y,
                "correlation_type": "full",
                "n_observations": int(len(data)),
                "results": {
                    "pearson": {
                        "name": "Pearson (r)",
                        "coefficient": round(float(pearson_r), 4),
                        "p_value": round(float(pearson_p), 6),
                        "is_significant": bool(pearson_p < 0.05),
                        "interpretation": get_interpretation(pearson_r, "Pearson")
                    },
                    "spearman": {
                        "name": "Spearman (ρ)",
                        "coefficient": round(float(spearman_r), 4),
                        "p_value": round(float(spearman_p), 6),
                        "is_significant": bool(spearman_p < 0.05),
                        "interpretation": get_interpretation(spearman_r, "Spearman")
                    },
                    "kendall": {
                        "name": "Kendall (τ)",
                        "coefficient": round(float(kendall_r), 4),
                        "p_value": round(float(kendall_p), 6),
                        "is_significant": bool(kendall_p < 0.05),
                        "interpretation": get_interpretation(kendall_r, "Kendall")
                    }
                },
                "regression": {
                    "slope": round(float(slope), 4),
                    "intercept": round(float(intercept), 4),
                    "std_error": round(float(std_err), 4),
                    "equation": f"y = {slope:.4f}x + {intercept:.4f}",
                    "r_squared": round(float(r_value ** 2), 4)
                },
                "plot_3d": plot_data_3d
            }
            
        else:
            # Single analysis logic (existing + refined)
            if requested_type == "spearman":
                correlation, p_value = stats.spearmanr(x, y)
                method_name = "Spearman (ρ)"
            elif requested_type == "kendall":
                correlation, p_value = stats.kendalltau(x, y)
                method_name = "Kendall (τ)"
            else:
                correlation, p_value = stats.pearsonr(x, y)
                method_name = "Pearson (r)"
                requested_type = "pearson"
            
            # Calcular regresión lineal
            slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
            
            # 2D Plot logic (Standard Scatter)
            x_range = np.linspace(float(x.min()), float(x.max()), 100)
            y_trend = slope * x_range + intercept
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x.tolist(), y=y.tolist(), mode='markers', name='Datos',
                marker=dict(size=8, color='rgba(99, 102, 241, 0.6)', line=dict(width=1, color='white'))
            ))
            fig.add_trace(go.Scatter(
                x=x_range.tolist(), y=y_trend.tolist(), mode='lines', 
                name=f'Tendencia (R²={r_value**2:.3f})', line=dict(color='red', width=2, dash='dash')
            ))
            fig.update_layout(
                title=f'{request.variable_y} vs {request.variable_x} ({method_name})',
                xaxis_title=request.variable_x, yaxis_title=request.variable_y,
                plot_bgcolor='rgba(255, 255, 255, 0.03)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f8fafc'), showlegend=True
            )
            
            return {
                "success": True,
                "variable_x": request.variable_x,
                "variable_y": request.variable_y,
                "correlation_type": requested_type,
                "correlation_method": method_name,
                "n_observations": int(len(data)),
                "correlation": {
                    "coefficient": round(float(correlation), 4),
                    "p_value": round(float(p_value), 6),
                    "r_squared": round(float(r_value ** 2), 4),
                    "is_significant": bool(p_value < 0.05)
                },
                "regression": {
                    "slope": round(float(slope), 4),
                    "intercept": round(float(intercept), 4),
                    "std_error": round(float(std_err), 4),
                    "equation": f"y = {slope:.4f}x + {intercept:.4f}"
                },
                "interpretation": get_interpretation(correlation, method_name),
                "plot": fig.to_json(),
                "plot_3d": plot_data_3d # Also return 3D data for single analysis if UI wants it
            }
        
    except Exception as e:
        logger.error(f"Error in analyze_dual_variables: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al analizar variables: {str(e)}")


@router.post("/time-series")
async def analyze_time_series(request: TimeSeriesRequest):
    """
    Análisis de series temporales con ARIMA
    """
    try:
        # Obtener dataset
        df = dataset_manager.get_dataset(request.dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Validar columnas
        if request.time_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna temporal '{request.time_column}' no encontrada")
        if request.value_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna de valores '{request.value_column}' no encontrada")
        
        # Importar analizador
        from ...time_series_analyzer import TimeSeriesAnalyzer
        
        # Realizar análisis
        analyzer = TimeSeriesAnalyzer(df)
        result = analyzer.analyze_arima(
            time_column=request.time_column,
            value_column=request.value_column,
            periods_ahead=request.periods_ahead,
            auto_select=request.auto_select_params
        )
        
        # Agregar interpretación
        result['interpretation'] = _generate_arima_interpretation(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en análisis ARIMA: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


def _generate_arima_interpretation(result):
    """Genera interpretación del modelo ARIMA"""
    order = result['model_params']['order']
    is_stationary = result['stationarity']['is_stationary']
    
    interpretation = f"""
Modelo ARIMA{order} ajustado exitosamente.

📊 Estacionariedad: {'✅ Serie estacionaria' if is_stationary else '⚠️ Serie no estacionaria (considere diferenciar)'}
📈 Parámetros: AR={order[0]}, I={order[1]}, MA={order[2]}
📉 AIC: {result['model_params']['aic']:.2f} (menor es mejor)

El modelo proyecta {len(result['forecast']['values'])} períodos hacia adelante con intervalos de confianza del 95%.
"""
    return interpretation.strip()


@router.post("/export")
async def export_quick_stats(request: QuickStatsExportRequest):
    """
    Exporta los resultados del análisis a Excel con reporte detallado y gráficos
    """
    try:
        # 1. Obtener resultados según el tipo de análisis
        results = None
        df_source = None # To hold raw data for "Data" sheet
        
        # Necesitamos el dataframe original para la pestaña de Datos
        # Asi que accederemos a el antes de llamar a las funciones de analisis
        
        if request.analysis_type == "single":
            req = SingleVariableRequest(**request.params)
            df_source = dataset_manager.get_dataset(req.dataset_id)
            if df_source is not None and req.variable in df_source.columns:
                 df_source = df_source[[req.variable]].dropna()
            results = await analyze_single_variable(req)
            
        elif request.analysis_type == "dual":
            req = DualVariableRequest(**request.params)
            df_source = dataset_manager.get_dataset(req.dataset_id)
            if df_source is not None and req.variable_x in df_source.columns and req.variable_y in df_source.columns:
                df_source = df_source[[req.variable_x, req.variable_y]].dropna()
            results = await analyze_dual_variables(req)
            
        elif request.analysis_type == "timeseries":
            req = TimeSeriesRequest(**request.params)
            df_source = dataset_manager.get_dataset(req.dataset_id)
            if df_source is not None and req.time_column in df_source.columns and req.value_column in df_source.columns:
                 df_source = df_source[[req.time_column, req.value_column]].dropna()
            results = await analyze_time_series(req)
            
        if not results:
            raise HTTPException(status_code=400, detail="Tipo de análisis no válido")

        # 2. Generar Excel
        output = io.BytesIO()
        
        # Use existing matplotlib backend from other services to avoid GUI errors
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formatos
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
            cell_fmt = workbook.add_format({'border': 1})
            title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1F497D'})
            
            # --- Sheet 1: Reporte Summary ---
            worksheet_report = workbook.add_worksheet('Reporte')
            worksheet_report.write('A1', f'Reporte de Análisis: {request.analysis_type.capitalize()}', title_fmt)
            worksheet_report.write('A2', f'Fecha: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
            
            img_buffer = None
            
            if request.analysis_type == "single":
                # --- Single Variable Logic ---
                var_name = results['variable']
                
                # Table 1: Key Metrics
                worksheet_report.write('A4', 'Estadísticas Clave', header_fmt)
                worksheet_report.write('B4', 'Valor', header_fmt)
                
                row = 4
                metrics = []
                if results['type'] == 'numeric':
                    stats = results['statistics']
                    metrics = [
                        ('Observaciones', results['n_observations']),
                        ('Media', stats['central_tendency']['mean']),
                        ('Mediana', stats['central_tendency']['median']),
                        ('Desv. Std', stats['dispersion']['std']),
                        ('Min', stats['range']['min']),
                        ('Max', stats['range']['max']),
                        ('Asimetría', stats['shape']['skewness']),
                        ('Curtosis', stats['shape']['kurtosis'])
                    ]
                else: 
                     metrics = [
                        ('Observaciones', results['n_observations']),
                        ('Categorías Únicas', results['n_unique']),
                        ('Moda', results['mode'])
                    ]

                for name, value in metrics:
                    worksheet_report.write(row, 0, name, cell_fmt)
                    worksheet_report.write(row, 1, value, cell_fmt)
                    row += 1
                
                # Generate Plot
                plt.figure(figsize=(10, 6))
                if results['type'] == 'numeric':
                    sns.histplot(df_source[var_name], kde=True, color='skyblue')
                    plt.title(f'Distribución de {var_name}')
                    plt.xlabel(var_name)
                    plt.ylabel('Frecuencia')
                else:
                    top_cats = df_source[var_name].value_counts().head(10)
                    sns.barplot(x=top_cats.index, y=top_cats.values, palette='viridis')
                    plt.title(f'Top 10 Categorías de {var_name}')
                    plt.xlabel(var_name)
                    plt.ylabel('Conteo')
                    plt.xticks(rotation=45)
                
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=100)
                plt.close()
                
            elif request.analysis_type == "dual":
                # --- Dual Variable Logic ---
                x_name = results['variable_x']
                y_name = results['variable_y']
                
                # Table 1: Key Metrics
                worksheet_report.write('A4', 'Métricas de Relación', header_fmt)
                worksheet_report.write('B4', 'Valor', header_fmt)
                
                row = 4
                metrics = []
                if 'correlation' in results:
                     metrics = [
                        ('Correlación', results['correlation']['coefficient']),
                        ('P-Value', results['correlation']['p_value']),
                        ('R-Cuadrado', results['correlation']['r_squared']),
                        ('Significancia', 'Sí' if results['correlation']['is_significant'] else 'No')
                    ]
                if 'regression' in results:
                     metrics.extend([
                         ('Pendiente', results['regression']['slope']),
                         ('Intercepto', results['regression']['intercept']),
                         ('Ecuación', results['regression']['equation'])
                     ])

                for name, value in metrics:
                    worksheet_report.write(row, 0, name, cell_fmt)
                    worksheet_report.write(row, 1, value, cell_fmt)
                    row += 1
                
                # Generate Plot
                plt.figure(figsize=(10, 6))
                sns.scatterplot(x=df_source[x_name], y=df_source[y_name], alpha=0.6)
                
                # Reg line
                if 'regression' in results:
                    slope = results['regression']['slope']
                    intercept = results['regression']['intercept']
                    x_vals = np.array([df_source[x_name].min(), df_source[x_name].max()])
                    y_vals = slope * x_vals + intercept
                    plt.plot(x_vals, y_vals, color='red', linestyle='--', label='Tendencia')
                    plt.legend()
                    
                plt.title(f'Relación: {y_name} vs {x_name}')
                plt.xlabel(x_name)
                plt.ylabel(y_name)
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=100)
                plt.close()

            elif request.analysis_type == "timeseries":
                # --- Time Series Logic ---
                # Table 1: Model Metrics
                worksheet_report.write('A4', 'Métricas del Modelo ARIMA', header_fmt)
                worksheet_report.write('B4', 'Valor', header_fmt)
                
                row = 4
                metrics = [
                    ('Orden (p,d,q)', str(results['model_params']['order'])),
                    ('AIC', results['model_params']['aic']),
                    ('RMSE', results['metrics']['rmse']),
                    ('MAE', results['metrics']['mae']),
                    ('Estacionariedad', 'Sí' if results['stationarity']['is_stationary'] else 'No')
                ]
                
                for name, value in metrics:
                    worksheet_report.write(row, 0, name, cell_fmt)
                    worksheet_report.write(row, 1, value, cell_fmt)
                    row += 1
                    
                # Full Summary
                worksheet_report.write('D4', 'Resumen del Modelo', header_fmt)
                # Split summary by newlines and write
                summary_lines = results.get('model_summary', '').split('\n')
                summ_row = 5
                for line in summary_lines:
                    worksheet_report.write(summ_row, 3, line)
                    summ_row += 1
                
                # Generate Plot
                plt.figure(figsize=(12, 6))
                
                # Historical
                hist_dates = [pd.to_datetime(d) for d in results['historical_data']['dates']]
                plt.plot(hist_dates, results['historical_data']['values'], label='Histórico', color='blue')
                plt.plot(hist_dates, results['historical_data']['fitted_values'], label='Ajuste', color='green', linestyle='--')
                
                # Forecast
                forecast_dates = [pd.to_datetime(d) for d in results['forecast']['dates']]
                plt.plot(forecast_dates, results['forecast']['values'], label='Pronóstico', color='orange')
                plt.fill_between(forecast_dates, results['forecast']['lower_bound'], results['forecast']['upper_bound'], color='orange', alpha=0.2, label='IC 95%')
                
                plt.title('Análisis y Pronóstico ARIMA')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=100)
                plt.close()

            # Insert Image if generated summary_lines
            if img_buffer:
                worksheet_report.insert_image('A15', 'chart.png', {'image_data': img_buffer})

            # --- Sheet 2: Data (Raw Data) ---
            if df_source is not None:
                df_source.to_excel(writer, sheet_name='Datos Crudos', index=False)
            
            # --- Sheet 3: Detailed Stats (Original structured tables) ---
            # Reuse logic from original export but put in separate sheet or appending
            # For simplicity, let's dump the JSON structure as flattened key-value if simple
            # Or just specific detailed tables
            
            if request.analysis_type == "single" and results['type'] == 'numeric':
                 stats = results['statistics']
                 detailed_data = []
                 for cat, submetrics in stats.items():
                     if isinstance(submetrics, dict):
                         for k, v in submetrics.items():
                             detailed_data.append({'Categoría': cat, 'Métrica': k, 'Valor': v})
                 pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detalles Estadísticos', index=False)
                 
            elif request.analysis_type == "dual" and results['correlation_type'] == 'full':
                res_full = results['results']
                rows = []
                for method, data in res_full.items():
                    rows.append({
                        'Método': data['name'],
                        'Coeficiente': data['coefficient'],
                        'P-Value': data['p_value'],
                        'Significativo': data['is_significant'],
                        'Interpretación': data['interpretation']
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name='Detalles Correlación', index=False)
            
            elif request.analysis_type == "timeseries":
                # Forecast Data Table
                forecast_df = pd.DataFrame({
                    "Fecha": results['forecast']['dates'],
                    "Pronóstico": results['forecast']['values'],
                    "Límite Inferior": results['forecast']['lower_bound'],
                    "Límite Superior": results['forecast']['upper_bound']
                })
                forecast_df.to_excel(writer, sheet_name='Datos Pronóstico', index=False)

        output.seek(0)
        headers = {
            'Content-Disposition': f'attachment; filename="quick_stats_report_{request.analysis_type}.xlsx"'
        }
        return StreamingResponse(
            output, 
            headers=headers, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"Error exportando Excel: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

