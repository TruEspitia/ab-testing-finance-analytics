

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


class MaxDrawdownRequest(BaseModel):
    dataset_id: str
    variable: str

@router.post("/maximum-drawdown")
async def calculate_maximum_drawdown_endpoint(request: MaxDrawdownRequest):
    """
    Calcula el Maximum Drawdown de una serie de precios.
    """
    try:
        df = dataset_manager.get_dataset(request.dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
            
        if request.variable not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna '{request.variable}' no encontrada")
            
        series = pd.to_numeric(df[request.variable], errors='coerce').dropna()
        
        if series.empty:
            raise HTTPException(status_code=400, detail="La columna seleccionada no contiene datos numéricos válidos")
        
        results = risk_service.calculate_maximum_drawdown(data=series)
        
        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error en endpoint Maximum Drawdown: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class BacktestingRequest(BaseModel):
    dataset_id: str
    variable: str
    var_method: str = 'parametric'
    confidence_level: float = 0.95
    horizon: int = 1
    window_size: int = 250

@router.post("/backtesting")
async def perform_backtesting_endpoint(request: BacktestingRequest):
    """
    Realiza backtesting de VaR usando rolling window.
    """
    try:
        df = dataset_manager.get_dataset(request.dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
            
        if request.variable not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna '{request.variable}' no encontrada")
            
        series = pd.to_numeric(df[request.variable], errors='coerce').dropna()
        
        if series.empty:
            raise HTTPException(status_code=400, detail="La columna seleccionada no contiene datos numéricos válidos")
        
        results = risk_service.perform_backtesting(
            data=series,
            var_method=request.var_method,
            confidence_level=request.confidence_level,
            horizon=request.horizon,
            window_size=request.window_size
        )
        
        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error en endpoint Backtesting: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class VaRMonteCarloRequest(BaseModel):
    dataset_id: str
    variable: str
    confidence_level: float = 0.95
    horizon: int = 10
    iterations: int = 10000
    distribution: str = 'normal'  # normal, t-student, bootstrap

@router.post("/var-montecarlo")
async def calculate_var_montecarlo_endpoint(request: VaRMonteCarloRequest):
    """
    Calcula VaR usando Monte Carlo avanzado con trayectorias completas.
    """
    try:
        df = dataset_manager.get_dataset(request.dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
            
        if request.variable not in df.columns:
            raise HTTPException(status_code=400, detail=f"Columna '{request.variable}' no encontrada")
            
        series = pd.to_numeric(df[request.variable], errors='coerce').dropna()
        
        if series.empty:
            raise HTTPException(status_code=400, detail="La columna seleccionada no contiene datos numéricos válidos")
        
        results = risk_service.calculate_var_monte_carlo_advanced(
            data=series,
            confidence_level=request.confidence_level,
            horizon=request.horizon,
            iterations=request.iterations,
            distribution=request.distribution
        )
        
        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error en endpoint VaR Monte Carlo: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
