"""
Clustering router
Handles K-means and DBSCAN clustering analysis
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.models import (
    ClusteringConfig,
    ClusteringResult,
    ElbowPlotRequest
)
from backend.dataset_manager import dataset_manager
from backend.services.clustering_service import ClusteringService


router = APIRouter(prefix="/api", tags=["clustering"])


@router.post("/clustering", response_model=ClusteringResult)
async def perform_clustering(config: ClusteringConfig):
    """
    Ejecuta clustering sobre un dataset
    
    Soporta dos algoritmos:
    - K-means: Requiere especificar n_clusters
    - DBSCAN: Requiere especificar eps y min_samples
    
    Args:
        config: Configuración del clustering
        
    Returns:
        ClusteringResult con las etiquetas, métricas y visualización
    """
    try:
        # Obtener el dataset
        df = dataset_manager.get_dataset(config.dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Validar algoritmo
        if config.algorithm not in ['kmeans', 'dbscan']:
            raise HTTPException(
                status_code=400, 
                detail="Algoritmo no soportado. Use 'kmeans' o 'dbscan'"
            )
        
        # Ejecutar el algoritmo correspondiente
        if config.algorithm == 'kmeans':
            result = ClusteringService.kmeans_clustering(
                df=df,
                feature_columns=config.feature_columns,
                n_clusters=config.n_clusters,
                random_state=config.random_state
            )
        else:  # dbscan
            result = ClusteringService.dbscan_clustering(
                df=df,
                feature_columns=config.feature_columns,
                eps=config.eps,
                min_samples=config.min_samples
            )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Error desconocido en clustering')
            )
        
        # Agregar dataset_id
        result['dataset_id'] = config.dataset_id
        
        return ClusteringResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/clustering/elbow-plot")
async def generate_elbow_plot(request: ElbowPlotRequest):
    """
    Genera el gráfico del codo para ayudar a elegir el número óptimo de clusters
    
    Args:
        request: Dataset y features a analizar
        
    Returns:
        Gráfico en base64
    """
    try:
        # Obtener el dataset
        df = dataset_manager.get_dataset(request.dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Generar gráfico
        plot_base64 = ClusteringService.generate_elbow_plot(
            df=df,
            feature_columns=request.feature_columns,
            max_k=request.max_k
        )
        
        return {
            "success": True,
            "plot_base64": plot_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando gráfico: {str(e)}")
