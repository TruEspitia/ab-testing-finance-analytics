"""
Single Stats Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.dataset_manager import dataset_manager
from backend.analyzers.single_variable_analyzer import SingleVariableAnalyzer

router = APIRouter(prefix="/api/quick-stats", tags=["quick-stats"])

class SingleVariableRequest(BaseModel):
    dataset_id: str
    variable: str

@router.post("/single")
async def analyze_single_variable(request: SingleVariableRequest):
    """
    Calcula estadísticas descriptivas para una variable
    """
    # Obtener dataset
    df = dataset_manager.get_dataset(request.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    try:
        analyzer = SingleVariableAnalyzer()
        return analyzer.analyze(df, request.variable)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
