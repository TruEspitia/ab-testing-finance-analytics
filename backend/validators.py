"""
Módulo de validadores para datasets
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
import numpy as np


class DataValidator:
    """Validador de datasets con detección automática de tipos y anomalías"""
    
    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Detecta automáticamente los tipos de cada columna
        
        Args:
            df: DataFrame a analizar
            
        Returns:
            Dict con nombre de columna y tipo detectado
        """
        types = {}
        
        for col in df.columns:
            # Eliminar NaN para el análisis
            non_null = df[col].dropna()
            
            if len(non_null) == 0:
                types[col] = "empty"
                continue
            
            # Verificar si es numérico
            if pd.api.types.is_numeric_dtype(df[col]):
                # Verificar si es entero o flotante
                if pd.api.types.is_integer_dtype(df[col]):
                    types[col] = "integer"
                else:
                    types[col] = "float"
            
            # Verificar si es datetime
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                types[col] = "datetime"
            
            # Verificar si es booleano
            elif pd.api.types.is_bool_dtype(df[col]):
                types[col] = "boolean"
            
            # Si no, es categórico/texto
            else:
                # Verificar si tiene pocos valores únicos (categórico)
                unique_ratio = len(non_null.unique()) / len(non_null)
                if unique_ratio < 0.5:
                    types[col] = "categorical"
                else:
                    types[col] = "text"
        
        return types
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame) -> Dict:
        """
        Valida la calidad de los datos
        
        Args:
            df: DataFrame a validar
            
        Returns:
            Dict con métricas de calidad
        """
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        
        quality_report = {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "total_cells": int(total_cells),
            "duplicate_rows": int(df.duplicated().sum()),
            "null_values": {
                "total_nulls": int(missing_cells),
                "percentage": float(round((missing_cells / total_cells * 100), 2)) if total_cells > 0 else 0.0,
                "columns_with_nulls": df.columns[df.isnull().any()].tolist()
            },
            "memory_usage_mb": float(round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2))
        }

        
        return quality_report
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str, method: str = "iqr") -> List[int]:
        """
        Detecta outliers en una columna numérica
        
        Args:
            df: DataFrame
            column: Nombre de la columna
            method: Método de detección ("iqr" o "zscore")
            
        Returns:
            Lista de índices con outliers
        """
        if column not in df.columns:
            return []
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            return []
        
        data = df[column].dropna()
        
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)].index.tolist()
        
        elif method == "zscore":
            z_scores = np.abs((data - data.mean()) / data.std())
            outliers = df[column][z_scores > 3].index.tolist()
        
        else:
            outliers = []
        
        return outliers
    
    @staticmethod
    def suggest_corrections(df: pd.DataFrame) -> List[Dict]:
        """
        Sugiere correcciones para problemas comunes
        
        Args:
            df: DataFrame a analizar
            
        Returns:
            Lista de sugerencias
        """
        suggestions = []
        
        # Detectar columnas con muchos valores faltantes
        for col in df.columns:
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            if missing_pct > 50:
                suggestions.append({
                    "type": "high_missing",
                    "column": col,
                    "severity": "warning",
                    "message": f"La columna '{col}' tiene {missing_pct:.1f}% de valores faltantes. Considera eliminarla o imputar valores."
                })
        
        # Detectar columnas constantes
        for col in df.columns:
            if df[col].nunique() == 1:
                suggestions.append({
                    "type": "constant_column",
                    "column": col,
                    "severity": "info",
                    "message": f"La columna '{col}' tiene un solo valor único. Considera eliminarla ya que no aporta información."
                })
        
        # Detectar filas duplicadas
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            suggestions.append({
                "type": "duplicates",
                "column": None,
                "severity": "warning",
                "message": f"Se encontraron {dup_count} filas duplicadas. Considera eliminarlas."
            })
        
        return suggestions
    
    @staticmethod
    def get_summary_statistics(df: pd.DataFrame) -> Dict:
        """
        Obtiene estadísticas resumidas del dataset
        
        Args:
            df: DataFrame
            
        Returns:
            Dict con estadísticas
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        stats = {
            "numeric_columns": int(len(numeric_cols)),
            "categorical_columns": int(len(categorical_cols)),
            "total_columns": int(len(df.columns)),
            "total_rows": int(len(df)),
            "numeric_summary": {},
            "categorical_summary": {}
        }
        
        # Estadísticas de columnas numéricas
        if numeric_cols:
            for col in numeric_cols:
                stats["numeric_summary"][col] = {
                    "mean": float(round(df[col].mean(), 4)) if not df[col].isnull().all() else None,
                    "median": float(round(df[col].median(), 4)) if not df[col].isnull().all() else None,
                    "std": float(round(df[col].std(), 4)) if not df[col].isnull().all() else None,
                    "min": float(round(df[col].min(), 4)) if not df[col].isnull().all() else None,
                    "max": float(round(df[col].max(), 4)) if not df[col].isnull().all() else None
                }
        
        # Estadísticas de columnas categóricas
        if categorical_cols:
            for col in categorical_cols:
                unique_count = df[col].nunique()
                stats["categorical_summary"][col] = {
                    "unique_values": int(unique_count),
                    "most_common": str(df[col].mode()[0]) if len(df[col].mode()) > 0 else None,
                    "most_common_count": int(df[col].value_counts().iloc[0]) if len(df[col]) > 0 else 0
                }
        
        return stats

