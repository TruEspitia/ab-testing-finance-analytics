"""
Time Series Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.dataset_manager import dataset_manager
from backend.time_series_analyzer import TimeSeriesAnalyzer
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quick-stats", tags=["quick-stats"])

class TimeSeriesRequest(BaseModel):
    dataset_id: str
    time_column: str
    value_column: str
    periods_ahead: int = Field(default=10, ge=1, le=365)
    auto_select_params: bool = True

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
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en análisis ARIMA: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
