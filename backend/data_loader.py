"""
Data Loader con soporte para múltiples formatos: CSV, XLSX, JSON
"""
import pandas as pd
import json
from pathlib import Path
from typing import Union, Optional, List
import chardet


class DataLoaderError(Exception):
    """Excepción personalizada para errores del data loader"""
    pass


class DataLoader:
    """Cargador de datos multi-formato"""
    
    # Tamaño máximo de archivo: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    SUPPORTED_FORMATS = ['csv', 'xlsx', 'json']
    
    @classmethod
    def load_file(cls, file_path: Union[str, Path], file_format: Optional[str] = None) -> pd.DataFrame:
        """
        Carga un archivo y retorna un DataFrame de pandas
        
        Args:
            file_path: Ruta al archivo
            file_format: Formato del archivo (csv, xlsx, json). Si es None, se detecta automáticamente
            
        Returns:
            DataFrame de pandas
            
        Raises:
            DataLoaderError: Si hay un error al cargar el archivo
        """
        file_path = Path(file_path)
        
        # Validar que el archivo existe
        if not file_path.exists():
            raise DataLoaderError(f"El archivo no existe: {file_path}")
        
        # Validar tamaño
        file_size = file_path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE:
            raise DataLoaderError(
                f"Archivo demasiado grande: {file_size / 1024 / 1024:.2f}MB. "
                f"Máximo permitido: {cls.MAX_FILE_SIZE / 1024 / 1024:.2f}MB"
            )
        
        # Detectar formato si no se especifica
        if file_format is None:
            file_format = cls.detect_format(file_path)
        
        file_format = file_format.lower()
        
        # Validar formato soportado
        if file_format not in cls.SUPPORTED_FORMATS:
            raise DataLoaderError(
                f"Formato no soportado: {file_format}. "
                f"Formatos válidos: {', '.join(cls.SUPPORTED_FORMATS)}"
            )
        
        # Cargar según el formato
        try:
            if file_format == 'csv':
                return cls.load_csv(file_path)
            elif file_format == 'xlsx':
                return cls.load_xlsx(file_path)
            elif file_format == 'json':
                return cls.load_json(file_path)
        except Exception as e:
            raise DataLoaderError(f"Error al cargar el archivo: {str(e)}")
    
    @staticmethod
    def detect_format(file_path: Path) -> str:
        """Detecta el formato del archivo por su extensión"""
        extension = file_path.suffix.lower().lstrip('.')
        if extension in ['csv', 'txt']:
            return 'csv'
        elif extension in ['xlsx', 'xls']:
            return 'xlsx'
        elif extension == 'json':
            return 'json'
        else:
            raise DataLoaderError(f"No se pudo detectar el formato del archivo: {file_path}")
    
    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """Detecta el encoding de un archivo de texto"""
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read(10000))  # Leer primeros 10KB
        return result['encoding'] or 'utf-8'
    
    @classmethod
    def load_csv(cls, file_path: Path) -> pd.DataFrame:
        """
        Carga un archivo CSV
        
        Intenta detectar automáticamente:
        - Encoding
        - Delimitador (coma, punto y coma, tabulador)
        """
        encoding = cls.detect_encoding(file_path)
        
        # Intentar con diferentes delimitadores
        delimiters = [',', ';', '\t', '|']
        
        for delimiter in delimiters:
            try:
                df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                
                # Verificar que se leyó correctamente (más de una columna generalmente)
                if len(df.columns) > 1 or (len(df.columns) == 1 and not df.columns[0].count(delimiter)):
                    return cls.validate_dataframe(df)
            except Exception:
                continue
        
        # Si ninguno funcionó, usar el delimitador por defecto
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            return cls.validate_dataframe(df)
        except Exception as e:
            raise DataLoaderError(f"Error al leer CSV: {str(e)}")
    
    @classmethod
    def load_xlsx(cls, file_path: Path, sheet_name: Optional[Union[str, int]] = 0) -> pd.DataFrame:
        """
        Carga un archivo Excel
        
        Args:
            file_path: Ruta al archivo
            sheet_name: Nombre o índice de la hoja. Por defecto, primera hoja (0)
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            return cls.validate_dataframe(df)
        except Exception as e:
            raise DataLoaderError(f"Error al leer XLSX: {str(e)}")
    
    @classmethod
    def load_json(cls, file_path: Path, orient: str = 'records') -> pd.DataFrame:
        """
        Carga un archivo JSON
        
        Args:
            file_path: Ruta al archivo
            orient: Orientación del JSON ('records', 'index', 'columns', 'values', 'table')
        """
        try:
            # Primero intentar leer como JSON válido
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convertir a DataFrame según la estructura
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Intentar diferentes orientaciones
                try:
                    df = pd.DataFrame.from_dict(data, orient=orient)
                except:
                    # Si falla, intentar como 'index'
                    df = pd.DataFrame.from_dict(data, orient='index')
            else:
                raise DataLoaderError("Formato JSON no soportado")
            
            return cls.validate_dataframe(df)
            
        except json.JSONDecodeError as e:
            raise DataLoaderError(f"JSON inválido: {str(e)}")
        except Exception as e:
            raise DataLoaderError(f"Error al leer JSON: {str(e)}")
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y limpia un DataFrame
        
        Args:
            df: DataFrame a validar
            
        Returns:
            DataFrame validado
            
        Raises:
            DataLoaderError: Si el DataFrame no es válido
        """
        # Verificar que no esté vacío
        if df.empty:
            raise DataLoaderError("El archivo está vacío")
        
        # Verificar que tenga columnas
        if len(df.columns) == 0:
            raise DataLoaderError("El archivo no tiene columnas")
        
        # Limpiar nombres de columnas (eliminar espacios y caracteres extraños)
        df.columns = df.columns.str.strip()
        
        # Verificar columnas duplicadas
        if df.columns.duplicated().any():
            raise DataLoaderError("El archivo tiene columnas duplicadas")
        
        return df
    
    @staticmethod
    def get_dataframe_info(df: pd.DataFrame) -> dict:
        """
        Obtiene información sobre un DataFrame
        
        Returns:
            Dict con información del DataFrame
        """
        return {
            'rows': len(df),
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'missing_values': df.isnull().sum().to_dict()
        }
