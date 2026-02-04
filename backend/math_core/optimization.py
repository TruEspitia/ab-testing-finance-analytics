import numpy as np
from .ffunc_parser import FFuncModel
from .validators import Validator
from .bounds import BoundsGenerator
from .engines.lm_engine import LMEngine
from .engines.de_engine import DEEngine
from .engines.sequential_engine import SequentialEngine

class OptimizationEngine:
    @staticmethod
    def fit_data(func_model: FFuncModel, x_data, y_data, engine_type="sequential", options=None):
        """
        Performs curve fitting using the selected engine.
        
        Args:
            func_model: FFuncModel instance
            x_data: list or array of x values
            y_data: list or array of y values
            engine_type: "lm", "de", or "sequential"
        """
        options = options or {}
        
        # 1. Validate Data
        valid, message = Validator.validate_data(x_data, y_data)
        if not valid:
            return {"success": False, "error": message}
            
        valid, message = Validator.validate_model_requirements(func_model, len(x_data))
        if not valid:
             return {"success": False, "error": message}

        x_arr = np.array(x_data, dtype=float)
        y_arr = np.array(y_data, dtype=float)

        # 2. Generate Bounds
        bounds_list = BoundsGenerator.generate_bounds(func_model, x_arr, y_arr)
        
        # Create dictionary for new engines
        param_names = sorted(func_model.parameters.keys())
        bounds_dict = {name: bound for name, bound in zip(param_names, bounds_list)}
        
        # 3. Prepare Engine Options
        engine_options = options.copy()
        engine_options['bounds_dict'] = bounds_dict
        engine_options['bounds_list'] = bounds_list # Keep for legacy/backup
        
        # Generate initial guesses if not provided
        if 'p0' not in engine_options:
             engine_options['p0'] = [func_model.parameters[name] for name in param_names]

        # 4. Select and Run Engine
        if engine_type == "lm":
            engine = LMEngine()
        elif engine_type == "de":
            engine = DEEngine()
        else:
             engine = SequentialEngine()
             
        result = engine.fit(func_model, x_arr, y_arr, engine_options)
        
        if not result['success']:
            return result
            
        # 5. Calculate Standard Metrics (R², RMSE, AIC)
        # result es un diccionario retornado por engine.fit()
        
        # Extraer popt y perr de forma segura
        popt = result.get('popt') if isinstance(result, dict) else None
        perr = result.get('perr') if isinstance(result, dict) else None
        parameters_dict = result.get('parameters', {}) if isinstance(result, dict) else {}
        errors_dict = result.get('errors', {}) if isinstance(result, dict) else {}
        
        # Convertir a arrays si es necesario
        if isinstance(popt, (list, np.ndarray)):
            popt_array = np.array(popt, dtype=float)
        elif isinstance(parameters_dict, dict) and parameters_dict:
            param_names = sorted(func_model.parameters.keys())
            popt_array = np.array([parameters_dict.get(name, 0) for name in param_names], dtype=float)
        else:
            return {
                "success": False,
                "error": "Failed to extract optimization parameters",
                "engine": engine_type
            }
        
        if len(popt_array) == 0:
            return {
                "success": False,
                "error": "No parameters returned from optimization",
                "engine": engine_type
            }
        
        try:
            y_pred = func_model.evaluate(x_arr, *popt_array)
            residuals = y_arr - y_pred
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_arr - np.mean(y_arr))**2)
            
            # R-squared
            if ss_tot == 0:
                r_squared = 0
            else:
                r_squared = 1 - (ss_res / ss_tot)
                
            # RMSE
            rmse = np.sqrt(np.mean(residuals**2))
            
            # Format results con nombre de parámetros
            param_names = sorted(func_model.parameters.keys())
            if isinstance(parameters_dict, dict):
                result_params = parameters_dict
                result_errors = errors_dict
            else:
                result_params = {name: float(val) for name, val in zip(param_names, popt_array)}
                if isinstance(perr, (list, np.ndarray)):
                    result_errors = {name: float(val) for name, val in zip(param_names, perr)}
                else:
                    result_errors = {name: 0.0 for name in param_names}
            
            # Enrich the result
            result.update({
                "parameters": result_params,
                "errors": result_errors,
                "r_squared": float(r_squared),
                "rmse": float(rmse),
                "fitted_curve": y_pred.tolist(),
                "residuals": residuals.tolist(),
                "success": True
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False, 
                "error": f"Metrics calculation failed: {str(e)}",
                "engine": engine_type
            }
