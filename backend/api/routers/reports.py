"""
Reports router
Handles export to Excel and report generation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime

from backend.models import ExportRequest
from backend.report_generator import ReportGenerator


router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/export/excel")
async def export_excel(request: ExportRequest):
    """
    Exporta los resultados de un análisis a un archivo Excel
    
    Args:
        request: Datos del análisis e imágenes de gráficos
        
    Returns:
        StreamingResponse con el archivo Excel
    """
    try:
        if request.analysis_type == 'ab_test':
            excel_io = ReportGenerator.generate_ab_test_report(request.data, request.charts)
            filename = f"AB_Test_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif request.analysis_type == 'scm':
            excel_io = ReportGenerator.generate_scm_report(request.data, request.charts)
            filename = f"SCM_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif request.analysis_type == 'regression':
            excel_io = ReportGenerator.generate_regression_report(request.data, request.charts)
            filename = f"Regression_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif request.analysis_type == 'clustering':
            excel_io = ReportGenerator.generate_clustering_report(request.data, request.charts)
            filename = f"Clustering_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif request.analysis_type == 'risk':
            excel_io = ReportGenerator.generate_risk_report(request.data, request.charts)
            filename = f"Risk_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif request.analysis_type == 'monte_carlo':
            excel_io = ReportGenerator.generate_monte_carlo_report(request.data, request.charts)
            filename = f"Monte_Carlo_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            raise HTTPException(status_code=400, detail="Tipo de análisis no soportado para exportación")
        
        return StreamingResponse(
            excel_io,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el reporte: {str(e)}")
