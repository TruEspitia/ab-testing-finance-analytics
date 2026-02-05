"""
Analysis router
Handles A/B testing, SCM, and regression analysis
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import numpy as np

from backend.models import (
    ABTestConfig,
    ABTestResult,
    SCMConfig,
    SCMResult,
    RegressionConfig,
    RegressionResult
)
from backend.dataset_manager import dataset_manager
from backend.ab_testing import ABTestAnalyzer
from backend.synthetic_control import  SyntheticControlAnalyzer


router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=ABTestResult)
async def analyze_ab_test(config: ABTestConfig):
    """
    Realiza un análisis A/B Testing
    
    Detecta automáticamente si la variable objetivo es:
    - Categórica (binaria o multi-categoría): usa Chi-cuadrado
    - Continua: usa t-test
    
    Args:
        config: Configuración del análisis
        
    Returns:
        ABTestResult con los resultados del análisis
    """
    try:
        # Obtener el dataset
        df = dataset_manager.get_dataset(config.dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Crear analizador
        analyzer = ABTestAnalyzer(df)
        
        # Realizar análisis automático (detecta tipo de variable)
        results = analyzer.auto_analyze(
            group_column=config.group_column,
            target_column=config.target_column,
            control_value=config.control_value,
            treatment_value=config.treatment_value,
            alpha=config.alpha
        )
        
        # Agregar dataset_id a los resultados
        results['dataset_id'] = config.dataset_id
        results['success'] = True
        
        return ABTestResult(**results)
        
    except ValueError as e:
        return ABTestResult(
            success=False,
            dataset_id=config.dataset_id,
            analysis_type="unknown",
            p_value=1,
            is_significant=False,
            alpha=config.alpha,
            interpretation="",
            error=str(e)
        )
    except Exception as e:
        return ABTestResult(
            success=False,
            dataset_id=config.dataset_id,
            analysis_type="unknown",
            p_value=1,
            is_significant=False,
            alpha=config.alpha,
            interpretation="",
            error=f"Error inesperado: {str(e)}"
        )


@router.post("/analyze/scm", response_model=SCMResult)
async def analyze_synthetic_control(config: SCMConfig):
    """
    Realiza un análisis de Control Sintético (Synthetic Control Method)
    
    Este método estima el efecto causal de una intervención en una unidad
    tratada, utilizando una combinación ponderada de unidades de control
    para crear un "contrafactual sintético".
    
    Args:
        config: Configuración del análisis SCM
        
    Returns:
        SCMResult con los resultados del análisis
    """
    try:
        # Obtener el dataset
        df = dataset_manager.get_dataset(config.dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Crear analizador
        analyzer = SyntheticControlAnalyzer(df)
        
        # Realizar análisis
        results = analyzer.analyze(
            time_column=config.time_column,
            unit_column=config.unit_column,
            target_column=config.target_column,
            treated_unit=config.treated_unit,
            treatment_time=config.treatment_time
        )
        
        # Agregar dataset_id a los resultados
        results['dataset_id'] = config.dataset_id
        
        return SCMResult(**results)
        
    except ValueError as e:
        return SCMResult(
            success=False,
            dataset_id=config.dataset_id,
            interpretation="",
            error=str(e)
        )
    except Exception as e:
        return SCMResult(
            success=False,
            dataset_id=config.dataset_id,
            interpretation="",
            error=f"Error inesperado: {str(e)}"
        )


@router.get("/functions")
async def get_available_functions():
    """
    Lista todas las funciones matemáticas disponibles para regresión
    
    Returns:
        Lista de funciones con nombre, parámetros, fórmula y complejidad
    """
    from ..math_core.ffunc_parser import FFuncParser
    
    functions_dir = Path(__file__).parent.parent / "functions"
    models = FFuncParser.get_available_functions(str(functions_dir))
    
    return {
        "success": True,
        "functions": [
            {
                "name": m.name,
                "parameters": m.parameters,
                "formula": m.formula_str,
                "complexity": m.metadata.get("complexity", 1)
            }
            for m in sorted(models, key=lambda x: x.name)
        ],
        "total": len(models)
    }


@router.post("/regression", response_model=RegressionResult)
async def perform_regression(config: RegressionConfig):
    """
    Ejecuta curve fitting sobre un dataset
    
    Args:
        config: Configuración con dataset_id, columnas X/Y, función y motor
        
    Returns:
        RegressionResult con parámetros ajustados y métricas
    """
    from ..math_core.ffunc_parser import FFuncParser
    from ..math_core.optimization import OptimizationEngine
    
    try:
        # Obtener el dataset
        df = dataset_manager.get_dataset(config.dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset no encontrado")
        
        # Validar columnas
        if config.x_column not in df.columns:
            return RegressionResult(
                success=False,
                dataset_id=config.dataset_id,
                function_name=config.function_name,
                engine_used=config.engine_type,
                error=f"Columna X '{config.x_column}' no encontrada"
            )
        
        if config.y_column not in df.columns:
            return RegressionResult(
                success=False,
                dataset_id=config.dataset_id,
                function_name=config.function_name,
                engine_used=config.engine_type,
                error=f"Columna Y '{config.y_column}' no encontrada"
            )
        
        # Obtener datos X e Y (eliminar NaN)
        data = df[[config.x_column, config.y_column]].dropna()
        x_data = data[config.x_column].values.astype(float)
        y_data = data[config.y_column].values.astype(float)
        
        if len(x_data) < 3:
            return RegressionResult(
                success=False,
                dataset_id=config.dataset_id,
                function_name=config.function_name,
                engine_used=config.engine_type,
                error="Se necesitan al menos 3 puntos de datos"
            )
        
        # Cargar la función
        functions_dir = Path(__file__).parent.parent / "functions"
        func_path = functions_dir / f"{config.function_name}.ffunc"
        
        # Buscar en subdirectorios si no está en raíz
        if not func_path.exists():
            for subdir in functions_dir.iterdir():
                if subdir.is_dir():
                    potential_path = subdir / f"{config.function_name}.ffunc"
                    if potential_path.exists():
                        func_path = potential_path
                        break
        
        if not func_path.exists():
            return RegressionResult(
                success=False,
                dataset_id=config.dataset_id,
                function_name=config.function_name,
                engine_used=config.engine_type,
                error=f"Función '{config.function_name}' no encontrada"
            )
        
        func_model = FFuncParser.parse_file(str(func_path))
        
        # Ejecutar ajuste
        result = OptimizationEngine.fit_data(
            func_model=func_model,
            x_data=x_data.tolist(),
            y_data=y_data.tolist(),
            engine_type=config.engine_type
        )
        
        if not result.get('success', False):
            return RegressionResult(
                success=False,
                dataset_id=config.dataset_id,
                function_name=config.function_name,
                engine_used=config.engine_type,
                error=result.get('error', 'Error desconocido en el ajuste')
            )
        
        # Generar curva suave para visualización
        x_min, x_max = float(np.min(x_data)), float(np.max(x_data))
        x_fit = np.linspace(x_min, x_max, 200)
        
        # Obtener parámetros en orden
        param_names = sorted(func_model.parameters.keys())
        popt = [result['parameters'][name] for name in param_names]
        y_fit = func_model.evaluate(x_fit, *popt)
        
        # Generar interpretación
        r_sq = result.get('r_squared', 0)
        rmse = result.get('rmse', 0)
        
        if r_sq >= 0.95:
            quality = "excelente"
        elif r_sq >= 0.85:
            quality = "bueno"
        elif r_sq >= 0.70:
            quality = "aceptable"
        else:
            quality = "pobre"
        
        interpretation = (
            f"El ajuste de la función '{config.function_name}' tiene un R² de {r_sq:.4f}, "
            f"lo cual indica un ajuste {quality}. "
            f"El error cuadrático medio (RMSE) es {rmse:.4f}."
        )
        
        return RegressionResult(
            success=True,
            dataset_id=config.dataset_id,
            function_name=config.function_name,
            engine_used=config.engine_type,
            parameters=result.get('parameters', {}),
            errors=result.get('errors', {}),
            r_squared=r_sq,
            rmse=rmse,
            fitted_x=x_fit.tolist(),
            fitted_y=y_fit.tolist(),
            original_x=x_data.tolist(),
            original_y=y_data.tolist(),
            residuals=result.get('residuals', []),
            interpretation=interpretation
        )
        
    except Exception as e:
        return RegressionResult(
            success=False,
            dataset_id=config.dataset_id,
            function_name=config.function_name,
            engine_used=config.engine_type,
            error=f"Error inesperado: {str(e)}"
        )
