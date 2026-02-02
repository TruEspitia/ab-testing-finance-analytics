"""
Módulo de Análisis de Control Sintético (Synthetic Control Method)

Este módulo implementa el Método de Control Sintético para estimar efectos causales
de intervenciones en estudios observacionales con datos de panel.
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SCMResult:
    """Resultado del análisis de Control Sintético"""
    success: bool
    treated_unit: str
    treatment_time: float
    weights: Dict[str, float]
    synthetic_values: List[float]
    treated_values: List[float]
    time_values: List[float]
    pre_treatment_rmspe: float
    post_treatment_effect: float
    average_treatment_effect: float
    interpretation: str
    error: Optional[str] = None


class SyntheticControlAnalyzer:
    """
    Analizador de Control Sintético
    
    Implementa el método de control sintético para estimar el efecto causal
    de una intervención en una unidad tratada, utilizando una combinación
    ponderada de unidades de control para crear un "contrafactual sintético".
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa el analizador
        
        Args:
            df: DataFrame con datos de panel (unidades x tiempo)
        """
        self.df = df.copy()
    
    def analyze(
        self,
        time_column: str,
        unit_column: str,
        target_column: str,
        treated_unit: str,
        treatment_time: float
    ) -> Dict:
        """
        Realiza el análisis de Control Sintético
        
        Args:
            time_column: Columna que contiene el tiempo
            unit_column: Columna que identifica las unidades
            target_column: Columna con la variable de resultado
            treated_unit: Nombre/ID de la unidad tratada
            treatment_time: Momento en que ocurrió el tratamiento
            
        Returns:
            Dict con los resultados del análisis
        """
        # Validar columnas
        for col in [time_column, unit_column, target_column]:
            if col not in self.df.columns:
                raise ValueError(f"Columna '{col}' no encontrada en el dataset")
        
        # Convertir valores de tiempo a numéricos si es posible
        try:
            self.df[time_column] = pd.to_numeric(self.df[time_column], errors='coerce')
        except Exception:
            pass
        
        # Verificar que la unidad tratada existe
        units = self.df[unit_column].unique()
        if treated_unit not in units:
            # Intentar conversión de tipo
            str_units = [str(u) for u in units]
            if str(treated_unit) in str_units:
                treated_unit = units[str_units.index(str(treated_unit))]
            else:
                raise ValueError(f"Unidad tratada '{treated_unit}' no encontrada. Unidades disponibles: {list(units)}")
        
        # Obtener unidades de control (todas excepto la tratada)
        control_units = [u for u in units if u != treated_unit]
        
        if len(control_units) < 1:
            raise ValueError("Se necesita al menos una unidad de control")
        
        # Pivotar datos para tener unidades como columnas
        pivot_df = self.df.pivot_table(
            index=time_column,
            columns=unit_column,
            values=target_column,
            aggfunc='mean'
        ).sort_index()
        
        # Manejar valores faltantes
        # Eliminar filas con demasiados NaN
        pivot_df = pivot_df.dropna(thresh=len(pivot_df.columns) * 0.5)
        
        # Llenar NaN restantes con interpolación o forward fill
        pivot_df = pivot_df.interpolate(method='linear', limit_direction='both')
        pivot_df = pivot_df.ffill().bfill()
        
        # Si aún hay NaN, llenar con la media de la columna
        pivot_df = pivot_df.fillna(pivot_df.mean())
        
        # Verificar que la unidad tratada esté en las columnas después del pivot
        if treated_unit not in pivot_df.columns:
            available_units = list(pivot_df.columns)
            raise ValueError(f"Unidad tratada '{treated_unit}' no tiene datos suficientes. Unidades con datos: {available_units[:10]}...")
        
        # Separar periodos pre y post tratamiento
        pre_treatment = pivot_df[pivot_df.index < treatment_time]
        post_treatment = pivot_df[pivot_df.index >= treatment_time]
        
        if len(pre_treatment) < 2:
            raise ValueError(f"Se necesitan al menos 2 periodos pre-tratamiento. Solo hay {len(pre_treatment)} periodos antes de {treatment_time}")
        
        # Datos de la unidad tratada (pre-tratamiento)
        y_treated_pre = pre_treatment[treated_unit].values
        
        # Verificar que no haya NaN en los datos tratados
        if np.any(np.isnan(y_treated_pre)):
            raise ValueError("La unidad tratada tiene valores faltantes en el periodo pre-tratamiento")
        
        # Datos de las unidades de control (pre-tratamiento)
        X_control_pre = pre_treatment[control_units].values
        
        # Eliminar unidades de control con NaN
        valid_control_mask = ~np.any(np.isnan(X_control_pre), axis=0)
        X_control_pre = X_control_pre[:, valid_control_mask]
        control_units = [u for u, valid in zip(control_units, valid_control_mask) if valid]
        
        if len(control_units) < 1:
            raise ValueError("No hay unidades de control con datos completos")
        
        # Optimizar pesos
        weights = self._optimize_weights(y_treated_pre, X_control_pre)
        
        # Crear diccionario de pesos
        weights_dict = {str(unit): round(float(w), 6) for unit, w in zip(control_units, weights)}
        
        # Calcular valores sintéticos para todo el periodo
        X_control_all = pivot_df[control_units].values
        synthetic_values = X_control_all @ weights
        
        # Valores de la unidad tratada
        treated_values = pivot_df[treated_unit].values
        time_values = pivot_df.index.tolist()
        
        # Calcular RMSPE pre-tratamiento
        synthetic_pre = X_control_pre @ weights
        pre_rmspe = np.sqrt(np.mean((y_treated_pre - synthetic_pre) ** 2))
        
        # Calcular efecto post-tratamiento
        if len(post_treatment) > 0:
            y_treated_post = post_treatment[treated_unit].values
            X_control_post = post_treatment[control_units].values
            synthetic_post = X_control_post @ weights
            
            # Efecto promedio del tratamiento
            treatment_effects = y_treated_post - synthetic_post
            avg_effect = float(np.mean(treatment_effects))
            total_effect = float(np.sum(treatment_effects))
        else:
            avg_effect = 0.0
            total_effect = 0.0
        
        # Generar interpretación
        interpretation = self._generate_interpretation(
            treated_unit=treated_unit,
            treatment_time=treatment_time,
            pre_rmspe=pre_rmspe,
            avg_effect=avg_effect,
            weights_dict=weights_dict
        )
        
        return {
            'success': True,
            'analysis_type': 'synthetic_control',
            'treated_unit': str(treated_unit),
            'treatment_time': float(treatment_time),
            'weights': weights_dict,
            'synthetic_values': [float(v) for v in synthetic_values],
            'treated_values': [float(v) for v in treated_values],
            'time_values': [float(t) if isinstance(t, (int, float, np.number)) else str(t) for t in time_values],
            'pre_treatment_rmspe': round(pre_rmspe, 6),
            'post_treatment_effect': round(total_effect, 4),
            'average_treatment_effect': round(avg_effect, 4),
            'n_pre_periods': len(pre_treatment),
            'n_post_periods': len(post_treatment),
            'n_control_units': len(control_units),
            'interpretation': interpretation
        }
    
    def _optimize_weights(self, y_treated: np.ndarray, X_control: np.ndarray) -> np.ndarray:
        """
        Optimiza los pesos del control sintético usando SLSQP
        
        Args:
            y_treated: Vector de valores de la unidad tratada (pre-tratamiento)
            X_control: Matriz de valores de unidades de control (pre-tratamiento)
            
        Returns:
            Vector de pesos óptimos
        """
        n_controls = X_control.shape[1]
        
        # Función objetivo: minimizar MSE
        def objective(w):
            synthetic = X_control @ w
            return np.mean((y_treated - synthetic) ** 2)
        
        # Restricción: los pesos suman 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        
        # Límites: pesos no negativos
        bounds = [(0, 1) for _ in range(n_controls)]
        
        # Valor inicial: pesos uniformes
        w0 = np.ones(n_controls) / n_controls
        
        # Optimizar
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-10}
        )
        
        return result.x
    
    def _generate_interpretation(
        self,
        treated_unit: str,
        treatment_time: float,
        pre_rmspe: float,
        avg_effect: float,
        weights_dict: Dict[str, float]
    ) -> str:
        """Genera interpretación del análisis en lenguaje natural"""
        
        # Identificar contribuidores principales
        sorted_weights = sorted(weights_dict.items(), key=lambda x: x[1], reverse=True)
        top_contributors = [f"{unit} ({w*100:.1f}%)" for unit, w in sorted_weights[:3] if w > 0.01]
        
        # Evaluar calidad del ajuste
        if pre_rmspe < 0.05:
            fit_quality = "excelente"
        elif pre_rmspe < 0.1:
            fit_quality = "bueno"
        elif pre_rmspe < 0.2:
            fit_quality = "aceptable"
        else:
            fit_quality = "moderado"
        
        # Evaluar efecto
        if avg_effect > 0:
            effect_direction = "positivo"
            effect_emoji = "📈"
        else:
            effect_direction = "negativo"
            effect_emoji = "📉"
        
        interpretation = (
            f"**Análisis de Control Sintético para '{treated_unit}'**\n\n"
            f"📊 **Calidad del ajuste**: {fit_quality.capitalize()} (RMSPE = {pre_rmspe:.4f})\n\n"
            f"{effect_emoji} **Efecto estimado**: El tratamiento tuvo un efecto {effect_direction} "
            f"promedio de **{abs(avg_effect):.4f}** unidades por periodo post-intervención.\n\n"
            f"🧩 **Principales contribuidores al control sintético**: {', '.join(top_contributors) if top_contributors else 'Distribución uniforme'}\n\n"
            f"⏱️ **Momento del tratamiento**: {treatment_time}"
        )
        
        return interpretation
