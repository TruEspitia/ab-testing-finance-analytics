"""
Gestor de datasets en memoria
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
from pathlib import Path

from .models import DatasetInfo, FileFormat


class DatasetManager:
    """Gestor centralizado de datasets en memoria"""
    
    def __init__(self, max_datasets: int = 10):
        """
        Inicializa el gestor de datasets
        
        Args:
            max_datasets: Número máximo de datasets a mantener en memoria
        """
        self._datasets: Dict[str, pd.DataFrame] = {}
        self._metadata: Dict[str, DatasetInfo] = {}
        self.max_datasets = max_datasets
    
    def add_dataset(
        self, 
        df: pd.DataFrame, 
        filename: str,
        file_format: FileFormat,
        size_bytes: int
    ) -> str:
        """
        Agrega un nuevo dataset
        
        Args:
            df: DataFrame a almacenar
            filename: Nombre del archivo original
            file_format: Formato del archivo
            size_bytes: Tamaño del archivo en bytes
            
        Returns:
            ID del dataset generado
            
        Raises:
            ValueError: Si se alcanzó el límite de datasets
        """
        # Verificar límite
        if len(self._datasets) >= self.max_datasets:
            # Eliminar el dataset más antiguo
            oldest_id = min(self._metadata.keys(), key=lambda k: self._metadata[k].uploaded_at)
            self.delete_dataset(oldest_id)
        
        # Generar ID único
        dataset_id = str(uuid.uuid4())
        
        # Almacenar DataFrame
        self._datasets[dataset_id] = df.copy()
        
        # Almacenar metadata
        self._metadata[dataset_id] = DatasetInfo(
            id=dataset_id,
            name=filename,
            format=file_format,
            size_bytes=size_bytes,
            rows=len(df),
            columns=df.columns.tolist(),
            uploaded_at=datetime.now()
        )
        
        return dataset_id
    
    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """
        Obtiene un dataset por su ID
        
        Args:
            dataset_id: ID del dataset
            
        Returns:
            DataFrame o None si no existe
        """
        return self._datasets.get(dataset_id)
    
    def get_metadata(self, dataset_id: str) -> Optional[DatasetInfo]:
        """
        Obtiene la metadata de un dataset
        
        Args:
            dataset_id: ID del dataset
            
        Returns:
            DatasetInfo o None si no existe
        """
        return self._metadata.get(dataset_id)
    
    def list_datasets(self) -> List[DatasetInfo]:
        """
        Lista todos los datasets disponibles
        
        Returns:
            Lista de DatasetInfo
        """
        return list(self._metadata.values())
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Elimina un dataset
        
        Args:
            dataset_id: ID del dataset a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
            del self._metadata[dataset_id]
            return True
        return False
    
    def clear_all(self):
        """Elimina todos los datasets"""
        self._datasets.clear()
        self._metadata.clear()
    
    def get_preview(self, dataset_id: str, n_rows: int = 100) -> Optional[pd.DataFrame]:
        """
        Obtiene un preview del dataset (primeras n filas)
        
        Args:
            dataset_id: ID del dataset
            n_rows: Número de filas a retornar
            
        Returns:
            DataFrame con las primeras n filas o None si no existe
        """
        df = self.get_dataset(dataset_id)
        if df is not None:
            return df.head(n_rows)
        return None
    
    def dataset_exists(self, dataset_id: str) -> bool:
        """Verifica si un dataset existe"""
        return dataset_id in self._datasets
    
    def get_total_memory_usage(self) -> int:
        """Obtiene el uso total de memoria en bytes"""
        total = 0
        for df in self._datasets.values():
            total += df.memory_usage(deep=True).sum()
        return total
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del gestor"""
        return {
            'total_datasets': len(self._datasets),
            'max_datasets': self.max_datasets,
            'total_memory_mb': self.get_total_memory_usage() / 1024 / 1024,
            'datasets': [
                {
                    'id': info.id,
                    'name': info.name,
                    'rows': info.rows,
                    'columns_count': len(info.columns)
                }
                for info in self._metadata.values()
            ]
        }


# Instancia global del gestor de datasets
dataset_manager = DatasetManager(max_datasets=10)
