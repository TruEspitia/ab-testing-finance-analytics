

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import logging
import traceback

from backend.services.risk_service import risk_service
from backend.dataset_manager import dataset_manager

router = APIRouter(
    prefix="/api/risk",
    tags=["Risk Calculator"]
)


logger = logging.getLogger(__name__)

class VaRRequest(BaseModel):
    dataset_id: str
    variable: str
    confidence_level: float = 0.95
    horizon: int = 1
    method: str = 'parametric' # parametric, historical, monte_carlo
    iterations: Optional[int] = 10000

@router.post("/var")
async def calculate_var_endpoint(request: VaRRequest):
    """
    Calcula el Value at Risk (VaR) de una variable financiera.
    """
    try:
        df = dataset_manager.get_dataset(request.dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
            
        if request.variable not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna '{request.variable}' no encontrada")
            
        # Get data series
        # Asegurar que sean numéricos
        series = pd.to_numeric(df[request.variable], errors='coerce').dropna()
        
        if series.empty:
            raise HTTPException(status_code=400, detail="La columna seleccionada no contiene datos numéricos válidos")

        results = risk_service.calculate_var(
            data=series,
            confidence_level=request.confidence_level,
            horizon=request.horizon,
            method=request.method,
            iterations=request.iterations or 10000
        )
        
        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error en endpoint VaR: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
