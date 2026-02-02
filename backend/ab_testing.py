"""
Módulo de análisis A/B Testing con pruebas estadísticas
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, ttest_ind, f_oneway
from typing import Dict, Tuple, Optional, Literal


class ABTestAnalyzer:
    """Analizador de pruebas A/B"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa el analizador
        
        Args:
            df: DataFrame con los datos a analizar
        """
        self.df = df.copy()
    
    def detect_variable_type(self, column: str) -> Literal['categorical', 'continuous']:
        """
        Detecta automáticamente si una variable es categórica o continua
        
        Args:
            column: Nombre de la columna a analizar
            
        Returns:
            'categorical' o 'continuous'
        """
        if column not in self.df.columns:
            raise ValueError(f"Columna '{column}' no encontrada en el dataset")
        
        col_data = self.df[column].dropna()
        
        # Si es de tipo objeto/string, es categórica
        if col_data.dtype == 'object' or col_data.dtype.name == 'category':
            return 'categorical'
        
        # Si es booleano, es categórica
        if col_data.dtype == 'bool':
            return 'categorical'
        
        # Si es numérica, verificar número de valores únicos
        if pd.api.types.is_numeric_dtype(col_data):
            unique_count = col_data.nunique()
            total_count = len(col_data)
            
            # Si tiene pocos valores únicos relativos al total, es categórica
            # Típicamente valores binarios (0/1) o pocas categorías
            if unique_count <= 10 and unique_count / total_count < 0.05:
                return 'categorical'
            
            # Si solo tiene valores enteros y pocos únicos, es categórica
            if unique_count <= 20 and (col_data == col_data.astype(int)).all():
                return 'categorical'
            
            return 'continuous'
        
        # Por defecto, categórica
        return 'categorical'
    
    def auto_analyze(
        self,
        group_column: str,
        target_column: str,
        control_value: str,
        treatment_value: str,
        alpha: float = 0.05
    ) -> Dict:
        """
        Detecta automáticamente el tipo de variable y ejecuta el análisis apropiado
        
        Args:
            group_column: Columna que identifica el grupo (control/treatment)
            target_column: Columna con el resultado
            control_value: Valor que identifica el grupo control
            treatment_value: Valor que identifica el grupo treatment
            alpha: Nivel de significancia (default: 0.05)
            
        Returns:
            Dict con los resultados del análisis
        """
        variable_type = self.detect_variable_type(target_column)
        
        if variable_type == 'continuous':
            return self.analyze_continuous(
                group_column=group_column,
                target_column=target_column,
                control_value=control_value,
                treatment_value=treatment_value,
                alpha=alpha
            )
        else:
            return self.analyze_categorical(
                group_column=group_column,
                target_column=target_column,
                control_value=control_value,
                treatment_value=treatment_value,
                alpha=alpha
            )
    
    def analyze_categorical(
        self,
        group_column: str,
        target_column: str,
        control_value: str,
        treatment_value: str,
        alpha: float = 0.05
    ) -> Dict:
        """
        Realiza análisis A/B para variables categóricas (puede tener múltiples categorías)
        
        Args:
            group_column: Columna que identifica el grupo (control/treatment)
            target_column: Columna con el resultado (puede ser binaria o multi-categoría)
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
        
        # Convertir índices a string para una comparación más robusta
        index_list = [str(x) for x in contingency_table.index]
        
        # Verificar que existen los grupos
        if str(control_value) not in index_list:
            raise ValueError(f"Valor de control '{control_value}' no encontrado en '{group_column}'. Valores disponibles: {index_list}")
        if str(treatment_value) not in index_list:
            raise ValueError(f"Valor de treatment '{treatment_value}' no encontrado en '{group_column}'. Valores disponibles: {index_list}")
        
        # Obtener los valores originales del index
        actual_control_val = contingency_table.index[index_list.index(str(control_value))]
        actual_treatment_val = contingency_table.index[index_list.index(str(treatment_value))]
        
        control_value = actual_control_val
        treatment_value = actual_treatment_val
        
        # Realizar test chi-cuadrado
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Calcular totales por grupo
        group_totals = contingency_table.sum(axis=1)
        control_total = group_totals[control_value]
        treatment_total = group_totals[treatment_value]
        
        # Obtener número de categorías en la variable objetivo
        n_categories = len(contingency_table.columns)
        is_binary = n_categories == 2
        
        # Para variables binarias, calcular tasa de "éxito"
        if is_binary:
            # Identificar columna de "éxito" (típicamente 'Yes', 'True', 1, etc.)
            success_columns = [col for col in contingency_table.columns 
                              if str(col).lower() in ['yes', 'true', '1', 'si', 'sí']]
            
            if success_columns:
                success_col = success_columns[0]
            else:
                # Usar la última columna como éxito (convención común)
                success_col = contingency_table.columns[-1]
            
            control_success = contingency_table.loc[control_value, success_col]
            treatment_success = contingency_table.loc[treatment_value, success_col]
            
            control_rate = control_success / control_total if control_total > 0 else 0
            treatment_rate = treatment_success / treatment_total if treatment_total > 0 else 0
            
            lift = treatment_rate - control_rate
            lift_percentage = (lift / control_rate * 100) if control_rate > 0 else 0
            
            interpretation = self._generate_interpretation(
                control_rate, treatment_rate, lift_percentage, 
                p_value < alpha, p_value, alpha
            )
        else:
            # Para variables multi-categoría, calcular distribución
            control_dist = contingency_table.loc[control_value] / control_total
            treatment_dist = contingency_table.loc[treatment_value] / treatment_total
            
            # El "rate" será la proporción de la categoría más común en treatment
            most_common_cat = treatment_dist.idxmax()
            control_rate = control_dist[most_common_cat]
            treatment_rate = treatment_dist[most_common_cat]
            
            lift = treatment_rate - control_rate
            lift_percentage = (lift / control_rate * 100) if control_rate > 0 else 0
            
            interpretation = self._generate_categorical_interpretation(
                contingency_table, control_value, treatment_value,
                control_total, treatment_total,
                p_value < alpha, p_value, alpha
            )
        
        is_significant = p_value < alpha
        
        # Convertir tabla de contingencia a dict
        contingency_raw = contingency_table.to_dict()
        contingency_dict = {
            str(outer_key): {str(inner_key): int(value) for inner_key, value in inner_map.items()}
            for outer_key, inner_map in contingency_raw.items()
        }
        
        return {
            'analysis_type': 'categorical',
            'is_binary': is_binary,
            'n_categories': n_categories,
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
        # Convertir valores a su tipo correcto si es necesario
        group_values = self.df[group_column].unique()
        actual_control = None
        actual_treatment = None
        
        for val in group_values:
            if str(val) == str(control_value):
                actual_control = val
            if str(val) == str(treatment_value):
                actual_treatment = val
        
        if actual_control is None:
            raise ValueError(f"Valor de control '{control_value}' no encontrado en '{group_column}'")
        if actual_treatment is None:
            raise ValueError(f"Valor de treatment '{treatment_value}' no encontrado en '{group_column}'")
        
        # Filtrar datos
        control_data = self.df[self.df[group_column] == actual_control][target_column].dropna()
        treatment_data = self.df[self.df[group_column] == actual_treatment][target_column].dropna()
        
        if len(control_data) == 0 or len(treatment_data) == 0:
            raise ValueError("No hay datos suficientes en uno de los grupos")
        
        # Realizar t-test
        t_stat, p_value = ttest_ind(control_data, treatment_data)
        
        # Calcular estadísticas descriptivas
        control_mean = control_data.mean()
        treatment_mean = treatment_data.mean()
        control_std = control_data.std()
        treatment_std = treatment_data.std()
        control_median = control_data.median()
        treatment_median = treatment_data.median()
        
        # Calcular diferencia
        difference = treatment_mean - control_mean
        percentage_change = (difference / control_mean * 100) if control_mean != 0 else 0
        
        # Determinar significancia
        is_significant = p_value < alpha
        
        # Generar interpretación
        interpretation = self._generate_continuous_interpretation(
            control_mean, treatment_mean, difference, percentage_change,
            is_significant, p_value, alpha
        )
        
        return {
            'analysis_type': 'continuous',
            'control_mean': round(control_mean, 4),
            'treatment_mean': round(treatment_mean, 4),
            'control_std': round(control_std, 4),
            'treatment_std': round(treatment_std, 4),
            'control_median': round(control_median, 4),
            'treatment_median': round(treatment_median, 4),
            'difference': round(difference, 4),
            'percentage_change': round(percentage_change, 2),
            't_statistic': round(t_stat, 4),
            'p_value': round(p_value, 6),
            'is_significant': is_significant,
            'alpha': alpha,
            'interpretation': interpretation,
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
        """Genera interpretación en lenguaje natural para variables binarias"""
        
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
    
    @staticmethod
    def _generate_categorical_interpretation(
        contingency_table: pd.DataFrame,
        control_value,
        treatment_value,
        control_total: int,
        treatment_total: int,
        is_significant: bool,
        p_value: float,
        alpha: float
    ) -> str:
        """Genera interpretación para variables categóricas multi-categoría"""
        
        n_categories = len(contingency_table.columns)
        categories = [str(c) for c in contingency_table.columns]
        
        if is_significant:
            return (
                f"✅ **Resultado significativo**: La distribución de las {n_categories} categorías "
                f"({', '.join(categories)}) es significativamente diferente entre los grupos control y tratamiento "
                f"(p-value = {p_value:.4f} < {alpha}). "
                f"Tamaños de muestra: Control = {control_total}, Tratamiento = {treatment_total}."
            )
        else:
            return (
                f"❌ **No significativo**: No hay diferencia significativa en la distribución "
                f"de las {n_categories} categorías ({', '.join(categories)}) entre los grupos "
                f"(p-value = {p_value:.4f} ≥ {alpha}). "
                f"Tamaños de muestra: Control = {control_total}, Tratamiento = {treatment_total}."
            )
    
    @staticmethod
    def _generate_continuous_interpretation(
        control_mean: float,
        treatment_mean: float,
        difference: float,
        percentage_change: float,
        is_significant: bool,
        p_value: float,
        alpha: float
    ) -> str:
        """Genera interpretación para variables continuas"""
        
        if is_significant:
            direction = "aumentó" if difference > 0 else "disminuyó"
            return (
                f"✅ **Resultado significativo**: El grupo de tratamiento {direction} "
                f"el valor promedio en {abs(percentage_change):.2f}% "
                f"(de {control_mean:.4f} a {treatment_mean:.4f}, diferencia = {difference:.4f}). "
                f"Esta diferencia es estadísticamente significativa (p-value = {p_value:.4f} < {alpha})."
            )
        else:
            return (
                f"❌ **No significativo**: Aunque se observó una diferencia de {percentage_change:.2f}% "
                f"en el valor promedio entre los grupos (Control: {control_mean:.4f}, Tratamiento: {treatment_mean:.4f}), "
                f"esta diferencia NO es estadísticamente significativa "
                f"(p-value = {p_value:.4f} ≥ {alpha}). No hay evidencia suficiente para concluir "
                f"que el tratamiento tuvo un efecto real."
            )
    
    def get_summary_statistics(self, group_column: str) -> Dict:
        """Obtiene estadísticas descriptivas por grupo"""
        return self.df.groupby(group_column).describe().to_dict()
