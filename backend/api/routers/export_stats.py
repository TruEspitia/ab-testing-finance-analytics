"""
Export Stats Router
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging
import traceback
from backend.dataset_manager import dataset_manager
from backend.services.excel_export_service import ExcelExportService
from backend.analyzers.single_variable_analyzer import SingleVariableAnalyzer
from backend.analyzers.dual_variable_analyzer import DualVariableAnalyzer
from backend.time_series_analyzer import TimeSeriesAnalyzer
from backend.api.routers.time_series import _generate_arima_interpretation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quick-stats", tags=["quick-stats"])

class ExportRequest(BaseModel):
    analysis_type: str  # "single", "dual", "timeseries"
    params: Dict[str, Any]

@router.post("/export")
async def export_stats(request: ExportRequest):
    """
    Exporta estadísticas a Excel
    """
    try:
        export_service = ExcelExportService()
        dataset_id = request.params.get('dataset_id')
        
        if not dataset_id:
             raise HTTPException(status_code=400, detail="Dataset ID requerido")

        df = dataset_manager.get_dataset(dataset_id)
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")

        if request.analysis_type == "single":
            variable = request.params.get('variable')
            analyzer = SingleVariableAnalyzer()
            results = analyzer.analyze(df, variable)
             # Filter df for export
            df_source = df[[variable]].dropna()
            output = export_service.export_single(results, df_source)
            
        elif request.analysis_type == "dual":
            var_x = request.params.get('variable_x')
            var_y = request.params.get('variable_y')
            ctype = request.params.get('correlation_type')
            analyzer = DualVariableAnalyzer()
            results = analyzer.analyze(df, var_x, var_y, ctype)
            df_source = df[[var_x, var_y]].dropna()
            output = export_service.export_dual(results, df_source)
            
        elif request.analysis_type == "timeseries":
            time_col = request.params.get('time_column')
            val_col = request.params.get('value_column')
            periods = request.params.get('periods_ahead', 10)
            auto = request.params.get('auto_select_params', True)
            
            analyzer = TimeSeriesAnalyzer(df)
            results = analyzer.analyze_arima(time_col, val_col, periods, auto)
            results['interpretation'] = _generate_arima_interpretation(results) # Re-use interpretation
            
            df_source = df[[time_col, val_col]].dropna()
            output = export_service.export_timeseries(results, df_source)
            
        else:
            raise HTTPException(status_code=400, detail="Tipo de análisis no válido")

        headers = {
            'Content-Disposition': f'attachment; filename="analytics_report_{request.analysis_type}.xlsx"'
        }
        
        return StreamingResponse(
            output, 
            headers=headers, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exportando: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
