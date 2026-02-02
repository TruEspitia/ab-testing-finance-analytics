"""
Módulo de análisis A/B Testing con pruebas estadísticas
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, ttest_ind
from typing import Dict, Tuple, Optional


class ABTestAnalyzer:
    """Analizador de pruebas A/B"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa el analizador
        
        Args:
            df: DataFrame con los datos a analizar
        """
        self.df = df.copy()
    
    def analyze_categorical(
        self,
        group_column: str,
        target_column: str,
        control_value: str,
        treatment_value: str,
        alpha: float = 0.05
    ) -> Dict:
        """
        Realiza análisis A/B para variables categóricas (ej: conversión sí/no)
        
        Args:
            group_column: Columna que identifica el grupo (control/treatment)
            target_column: Columna con el resultado (ej: signed_up)
            control_value: Valor que identifica el grupo control
            treatment_value: Valor que identifica el grupo treatment
            alpha: Nivel de significancia (default: 0.05)
            
        Returns:
            Dict con los resultados del análisis
        """
        # Validar columnas
        if group_column not in self.df.columns:
            raise ValueError(f"Columna '{group_column}' no encontrada en el dataset")
        if target_column not in self.df.columns:
            raise ValueError(f"Columna '{target_column}' no encontrada en el dataset")
        
        # Crear tabla de contingencia
        contingency_table = pd.crosstab(
            self.df[group_column], 
            self.df[target_column]
        )
        
        # Convertir índices a string para una comparación más robusta si los valores de entrada son strings
        # pero los del index son numéricos (común en APIs)
        index_list = [str(x) for x in contingency_table.index]
        
        # Verificar que existen los grupos
        if str(control_value) not in index_list:
            raise ValueError(f"Valor de control '{control_value}' no encontrado en '{group_column}'. Valores disponibles: {index_list}")
        if str(treatment_value) not in index_list:
            raise ValueError(f"Valor de treatment '{treatment_value}' no encontrado en '{group_column}'. Valores disponibles: {index_list}")
        
        # Obtener los valores originales del index que corresponden a los strings proporcionados
        actual_control_val = contingency_table.index[index_list.index(str(control_value))]
        actual_treatment_val = contingency_table.index[index_list.index(str(treatment_value))]
        
        # Reasignar para usar en el resto del método
        control_value = actual_control_val
        treatment_value = actual_treatment_val

        
        # Realizar test chi-cuadrado
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Calcular tasas de conversión
        group_totals = contingency_table.sum(axis=1)
        
        # Identificar columna de "éxito" (típicamente 'Yes', 'True', 1, etc.)
        success_columns = [col for col in contingency_table.columns 
                          if str(col).lower() in ['yes', 'true', '1', 'si', 'sí']]
        
        if success_columns:
            success_col = success_columns[0]
        else:
            # Si no se encuentra, usar la primera columna
            success_col = contingency_table.columns[0]
        
        control_success = contingency_table.loc[control_value, success_col] if success_col in contingency_table.columns else 0
        treatment_success = contingency_table.loc[treatment_value, success_col] if success_col in contingency_table.columns else 0
        
        control_total = group_totals[control_value]
        treatment_total = group_totals[treatment_value]
        
        control_rate = control_success / control_total if control_total > 0 else 0
        treatment_rate = treatment_success / treatment_total if treatment_total > 0 else 0
        
        # Calcular lift
        lift = treatment_rate - control_rate
        lift_percentage = (lift / control_rate * 100) if control_rate > 0 else 0
        
        # Determinar si es significativo
        is_significant = p_value < alpha
        
        # Crear interpretación
        interpretation = self._generate_interpretation(
            control_rate, 
            treatment_rate, 
            lift_percentage, 
            is_significant, 
            p_value, 
            alpha
        )
        
        # Convertir tabla de contingencia a dict con llaves string para serialización (requisito de Pydantic)
        contingency_raw = contingency_table.to_dict()
        contingency_dict = {
            str(outer_key): {str(inner_key): int(value) for inner_key, value in inner_map.items()}
            for outer_key, inner_map in contingency_raw.items()
        }

        
        return {
            'control_signup_rate': round(control_rate, 4),
            'treatment_signup_rate': round(treatment_rate, 4),
            'lift': round(lift, 4),
            'lift_percentage': round(lift_percentage, 2),
            'chi2_statistic': round(chi2, 4),
            'p_value': round(p_value, 6),
            'degrees_of_freedom': int(dof),
            'is_significant': is_significant,
            'alpha': alpha,
            'contingency_table': contingency_dict,
            'interpretation': interpretation,
            'sample_sizes': {
                'control': int(control_total),
                'treatment': int(treatment_total)
            }
        }
    
    def analyze_continuous(
        self,
        group_column: str,
        target_column: str,
        control_value: str,
        treatment_value: str,
        alpha: float = 0.05
    ) -> Dict:
        """
        Realiza análisis A/B para variables continuas (ej: gasto promedio)
        
        Args:
            group_column: Columna que identifica el grupo
            target_column: Columna con valores numéricos
            control_value: Valor que identifica el grupo control
            treatment_value: Valor que identifica el grupo treatment
            alpha: Nivel de significancia
            
        Returns:
            Dict con los resultados del análisis
        """
        # Filtrar datos
        control_data = self.df[self.df[group_column] == control_value][target_column].dropna()
        treatment_data = self.df[self.df[group_column] == treatment_value][target_column].dropna()
        
        if len(control_data) == 0 or len(treatment_data) == 0:
            raise ValueError("No hay datos suficientes en uno de los grupos")
        
        # Realizar t-test
        t_stat, p_value = ttest_ind(control_data, treatment_data)
        
        # Calcular estadísticas descriptivas
        control_mean = control_data.mean()
        treatment_mean = treatment_data.mean()
        control_std = control_data.std()
        treatment_std = treatment_data.std()
        
        # Calcular diferencia
        difference = treatment_mean - control_mean
        percentage_change = (difference / control_mean * 100) if control_mean != 0 else 0
        
        # Determinar significancia
        is_significant = p_value < alpha
        
        return {
            'control_mean': round(control_mean, 4),
            'treatment_mean': round(treatment_mean, 4),
            'control_std': round(control_std, 4),
            'treatment_std': round(treatment_std, 4),
            'difference': round(difference, 4),
            'percentage_change': round(percentage_change, 2),
            't_statistic': round(t_stat, 4),
            'p_value': round(p_value, 6),
            'is_significant': is_significant,
            'alpha': alpha,
            'sample_sizes': {
                'control': len(control_data),
                'treatment': len(treatment_data)
            }
        }
    
    @staticmethod
    def _generate_interpretation(
        control_rate: float,
        treatment_rate: float,
        lift_percentage: float,
        is_significant: bool,
        p_value: float,
        alpha: float
    ) -> str:
        """Genera interpretación en lenguaje natural de los resultados"""
        
        if is_significant:
            direction = "incrementó" if lift_percentage > 0 else "disminuyó"
            return (
                f"✅ **Resultado significativo**: El grupo de tratamiento {direction} "
                f"la tasa de conversión en {abs(lift_percentage):.2f}% "
                f"(de {control_rate*100:.2f}% a {treatment_rate*100:.2f}%). "
                f"Esta diferencia es estadísticamente significativa (p-value = {p_value:.4f} < {alpha})."
            )
        else:
            return (
                f"❌ **No significativo**: Aunque se observó una diferencia de {lift_percentage:.2f}% "
                f"entre los grupos, esta diferencia NO es estadísticamente significativa "
                f"(p-value = {p_value:.4f} ≥ {alpha}). No hay evidencia suficiente para concluir "
                f"que el tratamiento tuvo un efecto real."
            )
    
    def get_summary_statistics(self, group_column: str) -> Dict:
        """Obtiene estadísticas descriptivas por grupo"""
        return self.df.groupby(group_column).describe().to_dict()
