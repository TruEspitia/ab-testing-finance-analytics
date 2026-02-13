"""
Dual Variable Analyzer
Analiza la relación entre dos variables
"""
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go

class DualVariableAnalyzer:
    """Analizador de relaciones entre dos variables"""
    
    def analyze(self, df: pd.DataFrame, var_x: str, var_y: str, corr_type: str = "pearson") -> dict:
        """
        Analiza la relación entre dos variables
        
        Args:
            df: DataFrame con los datos
            var_x: Nombre de la variable X
            var_y: Nombre de la variable Y
            corr_type: Tipo de correlación ('pearson', 'spearman', 'kendall', 'full')
            
        Returns:
            dict con resultados de correlación, regresión y plot
        """
        # Validar variables
        if var_x not in df.columns:
            raise ValueError(f"Variable X '{var_x}' no encontrada")
        if var_y not in df.columns:
            raise ValueError(f"Variable Y '{var_y}' no encontrada")
        
        # Obtener datos limpios
        data = df[[var_x, var_y]].dropna()
        
        if len(data) < 2:
            raise ValueError("No hay suficientes datos válidos")
        
        x = data[var_x]
        y = data[var_y]
        
        # Verificar si ambas son numéricas
        x_numeric = pd.api.types.is_numeric_dtype(x)
        y_numeric = pd.api.types.is_numeric_dtype(y)
        
        if not (x_numeric and y_numeric):
            raise ValueError("Ambas variables deben ser numéricas para análisis dual")
        
        requested_type = corr_type.lower() if corr_type else "pearson"
        
        # Generar datos para plot 3D (como en el original)
        plot_data_3d = self._generate_3d_plot_data(x, y)
        
        if requested_type == "full":
            return self._analyze_full(x, y, var_x, var_y, plot_data_3d)
        else:
            return self._analyze_single_method(x, y, var_x, var_y, requested_type, plot_data_3d)
    
    def _generate_3d_plot_data(self, x: pd.Series, y: pd.Series) -> dict:
        """Genera datos para visualización 3D"""
        x_rank = stats.rankdata(x)
        y_rank = stats.rankdata(y)
        z_movement = np.abs(x_rank - y_rank)
        
        z_scale = (float(x.max()) - float(x.min()) + float(y.max()) - float(y.min())) / 2
        if z_scale == 0: z_scale = 1
        z_values = (z_movement / len(x)) * z_scale
        
        return {
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
    
    def _get_interpretation(self, corr_val, name):
        """Genera interpretación textual de la correlación"""
        if abs(corr_val) >= 0.7: strength = "fuerte"
        elif abs(corr_val) >= 0.4: strength = "moderada"
        elif abs(corr_val) >= 0.2: strength = "débil"
        else: strength = "muy débil o nula"
        direction = "positiva" if corr_val > 0 else "negativa"
        return f"Correlación {strength} {direction} ({name})"

    def _analyze_full(self, x: pd.Series, y: pd.Series, var_x: str, var_y: str, plot_data_3d: dict) -> dict:
        """Calcula todas las correlaciones"""
        pearson_r, pearson_p = stats.pearsonr(x, y)
        spearman_r, spearman_p = stats.spearmanr(x, y)
        kendall_r, kendall_p = stats.kendalltau(x, y)
        
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
        
        return {
            "success": True,
            "variable_x": var_x,
            "variable_y": var_y,
            "correlation_type": "full",
            "n_observations": int(len(x)),
            "results": {
                "pearson": {
                    "name": "Pearson (r)",
                    "coefficient": round(float(pearson_r), 4),
                    "p_value": round(float(pearson_p), 6),
                    "is_significant": bool(pearson_p < 0.05),
                    "interpretation": self._get_interpretation(pearson_r, "Pearson")
                },
                "spearman": {
                    "name": "Spearman (ρ)",
                    "coefficient": round(float(spearman_r), 4),
                    "p_value": round(float(spearman_p), 6),
                    "is_significant": bool(spearman_p < 0.05),
                    "interpretation": self._get_interpretation(spearman_r, "Spearman")
                },
                "kendall": {
                    "name": "Kendall (τ)",
                    "coefficient": round(float(kendall_r), 4),
                    "p_value": round(float(kendall_p), 6),
                    "is_significant": bool(kendall_p < 0.05),
                    "interpretation": self._get_interpretation(kendall_r, "Kendall")
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

    def _analyze_single_method(self, x: pd.Series, y: pd.Series, var_x: str, var_y: str, method: str, plot_data_3d: dict) -> dict:
        """Calcula una correlación específica"""
        if method == "spearman":
            correlation, p_value = stats.spearmanr(x, y)
            method_name = "Spearman (ρ)"
        elif method == "kendall":
            correlation, p_value = stats.kendalltau(x, y)
            method_name = "Kendall (τ)"
        else:
            correlation, p_value = stats.pearsonr(x, y)
            method_name = "Pearson (r)"
            method = "pearson"
        
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
        
        # Plot 2D
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
            title=dict(
                text=f'{var_y} vs {var_x} ({method_name})',
                font=dict(size=18, color='#f8fafc')
            ),
            xaxis=dict(
                title=dict(text=var_x, font=dict(size=14, color='#f8fafc')),
                gridcolor='rgba(255, 255, 255, 0.1)',
                showgrid=True
            ),
            yaxis=dict(
                title=dict(text=var_y, font=dict(size=14, color='#f8fafc')),
                gridcolor='rgba(255, 255, 255, 0.1)',
                showgrid=True
            ),
            plot_bgcolor='rgba(255, 255, 255, 0.03)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc', size=12),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(30, 30, 30, 0.8)',
                bordercolor='rgba(255, 255, 255, 0.2)',
                borderwidth=1,
                font=dict(size=12, color='#f8fafc')
            ),
            hovermode='closest'
        )
        
        return {
            "success": True,
            "variable_x": var_x,
            "variable_y": var_y,
            "correlation_type": method,
            "correlation_method": method_name,
            "n_observations": int(len(x)),
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
            "interpretation": self._get_interpretation(correlation, method_name),
            "plot": fig.to_json(),
            "plot_3d": plot_data_3d
        }
