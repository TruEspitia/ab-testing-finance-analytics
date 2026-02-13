"""
Dual Stats Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.dataset_manager import dataset_manager
from backend.analyzers.dual_variable_analyzer import DualVariableAnalyzer

router = APIRouter(prefix="/api/quick-stats", tags=["quick-stats"])

class DualVariableRequest(BaseModel):
    dataset_id: str
    variable_x: str
    variable_y: str
    correlation_type: Optional[str] = "pearson"

@router.post("/dual")
async def analyze_dual_variables(request: DualVariableRequest):
    """
    Analiza la relación entre dos variables
    """
    df = dataset_manager.get_dataset(request.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        analyzer = DualVariableAnalyzer()
        return analyzer.analyze(
            df, 
            request.variable_x, 
            request.variable_y, 
            request.correlation_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
