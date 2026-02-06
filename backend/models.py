"""
Modelos Pydantic para validación de requests y responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class FileFormat(str, Enum):
    """Formatos de archivo soportados"""
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class DatasetInfo(BaseModel):
    """Información de un dataset cargado"""
    id: str
    name: str
    format: FileFormat
    size_bytes: int
    rows: int
    columns: List[str]
    uploaded_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UploadResponse(BaseModel):
    """Respuesta después de subir un archivo"""
    success: bool
    message: str
    dataset: Optional[DatasetInfo] = None
    error: Optional[str] = None


class DatasetListResponse(BaseModel):
    """Lista de datasets disponibles"""
    datasets: List[DatasetInfo]
    total: int


class DatasetPreview(BaseModel):
    """Preview de datos de un dataset"""
    dataset_id: str
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


class ABTestConfig(BaseModel):
    """Configuración para análisis A/B Testing"""
    dataset_id: str
    group_column: str = Field(..., description="Columna que identifica el grupo (control/treatment)")
    target_column: str = Field(..., description="Columna con el resultado medido")
    control_value: str = Field(..., description="Valor que identifica el grupo control")
    treatment_value: str = Field(..., description="Valor que identifica el grupo treatment")
    alpha: float = Field(default=0.05, description="Nivel de significancia")


class ABTestResult(BaseModel):
    """Resultados del análisis A/B Testing (soporta categórico y continuo)"""
    success: bool
    dataset_id: str
    
    # Tipo de análisis realizado
    analysis_type: str = "categorical"  # 'categorical' o 'continuous'
    
    # Para análisis categórico binario/multi-categoría
    is_binary: Optional[bool] = None
    n_categories: Optional[int] = None
    control_signup_rate: Optional[float] = None
    treatment_signup_rate: Optional[float] = None
    lift: Optional[float] = None
    lift_percentage: Optional[float] = None
    chi2_statistic: Optional[float] = None
    degrees_of_freedom: Optional[int] = None
    contingency_table: Optional[Dict[str, Dict[str, int]]] = None
    
    # Para análisis continuo (t-test)
    control_mean: Optional[float] = None
    treatment_mean: Optional[float] = None
    control_std: Optional[float] = None
    treatment_std: Optional[float] = None
    control_median: Optional[float] = None
    treatment_median: Optional[float] = None
    difference: Optional[float] = None
    percentage_change: Optional[float] = None
    t_statistic: Optional[float] = None
    
    # Comunes a ambos tipos
    p_value: float
    is_significant: bool
    alpha: float
    sample_sizes: Optional[Dict[str, int]] = None
    
    # Interpretación
    interpretation: str
    
    # Error si lo hay
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class SCMConfig(BaseModel):
    """Configuración para análisis de Control Sintético"""
    dataset_id: str
    time_column: str = Field(..., description="Columna que contiene el tiempo")
    unit_column: str = Field(..., description="Columna que identifica las unidades")
    target_column: str = Field(..., description="Columna con la variable de resultado")
    treated_unit: str = Field(..., description="Nombre/ID de la unidad tratada")
    treatment_time: float = Field(..., description="Momento en que ocurrió el tratamiento")


class SCMResult(BaseModel):
    """Resultados del análisis de Control Sintético"""
    success: bool
    dataset_id: str
    analysis_type: str = "synthetic_control"
    
    # Información del análisis
    treated_unit: Optional[str] = None
    treatment_time: Optional[float] = None
    
    # Pesos de las unidades de control
    weights: Optional[Dict[str, float]] = None
    
    # Series temporales
    synthetic_values: Optional[List[float]] = None
    treated_values: Optional[List[float]] = None
    time_values: Optional[List[Any]] = None
    
    # Métricas
    pre_treatment_rmspe: Optional[float] = None
    post_treatment_effect: Optional[float] = None
    average_treatment_effect: Optional[float] = None
    n_pre_periods: Optional[int] = None
    n_post_periods: Optional[int] = None
    n_control_units: Optional[int] = None
    
    # Interpretación
    interpretation: str = ""
    
    # Error si lo hay
    error: Optional[str] = None


class ExportRequest(BaseModel):
    """Request para exportación de resultados a Excel"""
    analysis_type: str = Field(..., description="'ab_test' o 'scm'")
    data: Dict[str, Any] = Field(..., description="Datos completos del resultado del análisis")
    charts: List[str] = Field(default=[], description="Lista de imágenes de gráficos en base64")


# =============================================
# Modelos para Regresión / Curve Fitting
# =============================================

class FunctionInfo(BaseModel):
    """Información de una función matemática disponible"""
    name: str
    parameters: Dict[str, float]
    formula: str
    complexity: int = 1


class RegressionConfig(BaseModel):
    """Configuración para análisis de regresión/curve fitting"""
    dataset_id: str
    x_column: str = Field(..., description="Columna con los valores X")
    y_column: str = Field(..., description="Columna con los valores Y")
    function_name: str = Field(..., description="Nombre de la función a ajustar")
    engine_type: str = Field(default="sequential", description="Motor: 'lm', 'de', o 'sequential'")


class RegressionResult(BaseModel):
    """Resultados del análisis de regresión"""
    success: bool
    dataset_id: str
    function_name: str
    engine_used: str
    
    # Parámetros ajustados
    parameters: Optional[Dict[str, float]] = None
    errors: Optional[Dict[str, float]] = None
    
    # Métricas
    r_squared: Optional[float] = None
    rmse: Optional[float] = None
    
    # Datos para visualización
    fitted_x: Optional[List[float]] = None
    fitted_y: Optional[List[float]] = None
    original_x: Optional[List[float]] = None
    original_y: Optional[List[float]] = None
    residuals: Optional[List[float]] = None
    
    # Interpretación
    interpretation: str = ""
    
    # Error si lo hay
    error: Optional[str] = None


# =============================================
# Modelos para Clustering
# =============================================

class ClusteringConfig(BaseModel):
    """Configuración para análisis de clustering"""
    dataset_id: str
    feature_columns: List[str] = Field(..., description="Columnas a usar como features")
    algorithm: str = Field(..., description="'kmeans' o 'dbscan'")
    
    # Parámetros para K-means
    n_clusters: Optional[int] = Field(None, description="Número de clusters (solo para kmeans)")
    
    # Parámetros para DBSCAN
    eps: Optional[float] = Field(0.5, description="Radio de vecindad (solo para dbscan)")
    min_samples: Optional[int] = Field(5, description="Mínimo de muestras (solo para dbscan)")
    
    random_state: int = Field(42, description="Semilla para reproducibilidad")


class ClusterStats(BaseModel):
    """Estadísticas de un cluster individual"""
    cluster_id: int
    size: int
    percentage: float
    centroid: Optional[List[float]] = None
    is_noise: Optional[bool] = False


class ClusteringResult(BaseModel):
    """Resultados del análisis de clustering"""
    success: bool
    dataset_id: str
    algorithm: str
    
    # Número de clusters encontrados
    n_clusters: int
    n_noise: Optional[int] = None  # Solo para DBSCAN
    
    # Etiquetas de cluster para cada punto
    labels: List[int]
    
    # Métricas de calidad
    silhouette_score: float
    davies_bouldin_score: float
    inertia: Optional[float] = None  # Solo para K-means
    
    # Estadísticas por cluster
    cluster_stats: List[ClusterStats]
    
    # Coordenadas PCA para visualización
    pca_coordinates: List[List[float]]
    
    # Gráfico en base64
    plot_base64: str
    
    # Parámetros usados
    eps: Optional[float] = None
    min_samples: Optional[int] = None
    
    # Error si lo hay
    error: Optional[str] = None


class ElbowPlotRequest(BaseModel):
    """Request para generar el gráfico del codo"""
    dataset_id: str
    feature_columns: List[str]
    max_k: int = Field(10, description="Máximo número de clusters a probar")


# =============================================
# Modelos para Monte Carlo Simulation
# =============================================

class MonteCarloConfig(BaseModel):
    """Configuración para simulación Monte Carlo"""
    dataset_id: str
    target_column: str = Field(..., description="Columna que contiene la variable a proyectar")
    iterations: int = Field(1000, description="Número de simulaciones a realizar", ge=100, le=10000)
    horizon: int = Field(30, description="Horizonte temporal (número de períodos futuros)", ge=1, le=365)
    drift: Optional[float] = Field(None, description="Drift manual (si None, se estima automáticamente)")
    volatility: Optional[float] = Field(None, description="Volatilidad manual (si None, se estima automáticamente)")


class MonteCarloResult(BaseModel):
    """Resultados de la simulación Monte Carlo"""
    success: bool
    dataset_id: str
    
    # Simulaciones completas
    simulations: Optional[List[List[float]]] = None
    
    # Bandas de confianza (percentiles 5, 25, 50, 75, 95)
    confidence_bands: Optional[Dict[str, List[float]]] = None
    
    # Métricas financieras
    metrics: Optional[Dict[str, float]] = None
    
    # Distribución final
    final_distribution: Optional[Dict[str, Any]] = None
    
    # Interpretación
    interpretation: str = ""
    
    # Error si lo hay
    error: Optional[str] = None
