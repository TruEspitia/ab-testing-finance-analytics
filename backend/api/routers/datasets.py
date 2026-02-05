"""
Dataset management router
Handles file uploads, dataset listing, previews, and deletion
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import tempfile
from typing import List

from backend.models import (
    UploadResponse, 
    DatasetListResponse, 
    DatasetPreview,
    FileFormat
)
from backend.data_loader import DataLoader, DataLoaderError
from backend.dataset_manager import dataset_manager
from backend.validators import DataValidator


router = APIRouter(prefix="/api", tags=["datasets"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint para subir archivos (CSV, XLSX, JSON)
    
    Args:
        file: Archivo subido
        
    Returns:
        UploadResponse con información del dataset cargado
    """
    try:
        # Validar que se subió un archivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo")
        
        # Detectar formato del archivo
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        
        # Mapear extensión a FileFormat
        format_mapping = {
            'csv': FileFormat.CSV,
            'xlsx': FileFormat.XLSX,
            'xls': FileFormat.XLSX,
            'json': FileFormat.JSON
        }
        
        if file_extension not in format_mapping:
            return UploadResponse(
                success=False,
                message="Formato no soportado",
                error=f"Formato '{file_extension}' no soportado. Use CSV, XLSX o JSON"
            )
        
        file_format = format_mapping[file_extension]
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
            # Copiar contenido del archivo subido
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Obtener tamaño del archivo
            file_size = tmp_path.stat().st_size
            
            # Cargar el archivo usando DataLoader
            df = DataLoader.load_file(tmp_path, file_format.value)
            
            # Agregar al gestor de datasets
            dataset_id = dataset_manager.add_dataset(
                df=df,
                filename=file.filename,
                file_format=file_format,
                size_bytes=file_size
            )
            
            # Obtener metadata
            metadata = dataset_manager.get_metadata(dataset_id)
            
            return UploadResponse(
                success=True,
                message=f"Archivo '{file.filename}' cargado exitosamente",
                dataset=metadata
            )
            
        finally:
            # Limpiar archivo temporal
            tmp_path.unlink(missing_ok=True)
            
    except DataLoaderError as e:
        return UploadResponse(
            success=False,
            message="Error al cargar el archivo",
            error=str(e)
        )
    except Exception as e:
        return UploadResponse(
            success=False,
            message="Error inesperado",
            error=str(e)
        )


@router.post("/upload-batch")
async def upload_batch_files(files: List[UploadFile] = File(...)):
    """
    Endpoint para subir múltiples archivos a la vez
    
    Args:
        files: Lista de archivos a subir
        
    Returns:
        Lista de respuestas de carga
    """
    results = []
    
    for file in files:
        try:
            # Validar que se subió un archivo
            if not file.filename:
                results.append({
                    "filename": "unknown",
                    "success": False,
                    "error": "No se proporcionó ningún archivo"
                })
                continue
            
            # Detectar formato del archivo
            file_extension = Path(file.filename).suffix.lower().lstrip('.')
            
            # Mapear extensión a FileFormat
            format_mapping = {
                'csv': FileFormat.CSV,
                'xlsx': FileFormat.XLSX,
                'xls': FileFormat.XLSX,
                'json': FileFormat.JSON
            }
            
            if file_extension not in format_mapping:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Formato '{file_extension}' no soportado"
                })
                continue
            
            file_format = format_mapping[file_extension]
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                # Copiar contenido del archivo subido
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = Path(tmp_file.name)
            
            try:
                # Obtener tamaño del archivo
                file_size = tmp_path.stat().st_size
                
                # Cargar el archivo usando DataLoader
                df = DataLoader.load_file(tmp_path, file_format.value)
                
                # Agregar al gestor de datasets
                dataset_id = dataset_manager.add_dataset(
                    df=df,
                    filename=file.filename,
                    file_format=file_format,
                    size_bytes=file_size
                )
                
                # Obtener metadata
                metadata = dataset_manager.get_metadata(dataset_id)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "dataset": metadata.dict()
                })
                
            finally:
                # Limpiar archivo temporal
                tmp_path.unlink(missing_ok=True)
                
        except DataLoaderError as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            })
    
    return {
        "total_files": len(files),
        "successful": sum(1 for r in results if r.get("success", False)),
        "failed": sum(1 for r in results if not r.get("success", False)),
        "results": results
    }


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets():
    """
    Lista todos los datasets cargados
    
    Returns:
        DatasetListResponse con la lista de datasets
    """
    datasets = dataset_manager.list_datasets()
    return DatasetListResponse(
        datasets=datasets,
        total=len(datasets)
    )


@router.get("/dataset/{dataset_id}/preview", response_model=DatasetPreview)
async def get_dataset_preview(dataset_id: str, n_rows: int = 100):
    """
    Obtiene un preview de un dataset
    
    Args:
        dataset_id: ID del dataset
        n_rows: Número de filas a retornar (default: 100)
        
    Returns:
        DatasetPreview con las primeras filas
    """
    # Verificar que el dataset existe
    if not dataset_manager.dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    # Obtener preview
    df_preview = dataset_manager.get_preview(dataset_id, n_rows)
    metadata = dataset_manager.get_metadata(dataset_id)
    
    if df_preview is None:
        raise HTTPException(status_code=500, detail="Error al obtener preview")
    
    # Convertir a lista de dicts
    data_records = df_preview.to_dict('records')
    
    # Convertir NaN a None para serialización JSON
    for record in data_records:
        for key, value in record.items():
            if isinstance(value, float):
                import math
                if math.isnan(value):
                    record[key] = None
    
    return DatasetPreview(
        dataset_id=dataset_id,
        columns=metadata.columns,
        data=data_records,
        total_rows=metadata.rows,
        preview_rows=len(df_preview)
    )


@router.get("/dataset/{dataset_id}")
async def get_dataset(dataset_id: str):
    """
    Obtiene información de un dataset específico
    
    Args:
        dataset_id: ID del dataset
        
    Returns:
        Información del dataset
    """
    metadata = dataset_manager.get_metadata(dataset_id)
    
    if metadata is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    return metadata


@router.delete("/dataset/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """
    Elimina un dataset
    
    Args:
        dataset_id: ID del dataset a eliminar
        
    Returns:
        Mensaje de confirmación
    """
    success = dataset_manager.delete_dataset(dataset_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    return {"message": "Dataset eliminado exitosamente", "dataset_id": dataset_id}


@router.get("/dataset/{dataset_id}/validate")
async def validate_dataset(dataset_id: str):
    """
    Valida la calidad de un dataset y proporciona sugerencias
    
    Args:
        dataset_id: ID del dataset
        
    Returns:
        Reporte de validación con calidad de datos y sugerencias
    """
    # Verificar que el dataset existe
    if not dataset_manager.dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    df = dataset_manager.get_dataset(dataset_id)
    
    if df is None:
        raise HTTPException(status_code=500, detail="Error al obtener dataset")
    
    # Ejecutar validaciones
    validator = DataValidator()
    
    return {
        "dataset_id": dataset_id,
        "column_types": validator.detect_column_types(df),
        "quality_report": validator.validate_data_quality(df),
        "suggestions": validator.suggest_corrections(df),
        "summary_statistics": validator.get_summary_statistics(df)
    }


@router.get("/dataset/{dataset_id}/columns")
async def get_dataset_columns(dataset_id: str):
    """
    Obtiene información detallada sobre las columnas de un dataset
    
    Args:
        dataset_id: ID del dataset
        
    Returns:
        Información de columnas
    """
    if not dataset_manager.dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    
    df = dataset_manager.get_dataset(dataset_id)
    metadata = dataset_manager.get_metadata(dataset_id)
    
    validator = DataValidator()
    column_types = validator.detect_column_types(df)
    
    columns_info = []
    for col in df.columns:
        columns_info.append({
            "name": col,
            "type": column_types.get(col, "unknown"),
            "missing_count": int(df[col].isnull().sum()),
            "missing_percentage": round((df[col].isnull().sum() / len(df)) * 100, 2),
            "unique_values": int(df[col].nunique()),
            "dtype": str(df[col].dtype)
        })
    
    return {
        "dataset_id": dataset_id,
        "total_columns": len(columns_info),
        "columns": columns_info
    }


@router.get("/stats")
async def get_stats():
    """
    Obtiene estadísticas del sistema
    
    Returns:
        Estadísticas generales
    """
    return dataset_manager.get_stats()
