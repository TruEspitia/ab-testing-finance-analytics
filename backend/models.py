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
