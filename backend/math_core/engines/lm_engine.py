import numpy as np
from scipy.optimize import curve_fit, OptimizeResult
from scipy.linalg import LinAlgError
import warnings
from .base_engine import BaseEngine, FitResult, FitOptions, OptimizationStatus

class LMEngine(BaseEngine):
    """
    Motor Levenberg-Marquardt optimizado con manejo robusto de errores
    y estimación inteligente de parámetros iniciales.
    """
    
    def __init__(self):
        super().__init__("LevenbergMarquardt")
        self.adaptive_initial_guess = True
        self.multi_start = True
        self.n_starts = 3
    
    def _optimize(self, model, x_data: np.ndarray, y_data: np.ndarray, 
                  options: FitOptions) -> FitResult:
        """Optimización LM con múltiples inicios y manejo robusto."""
        
        best_result = None
        best_cost = float('inf')
        attempts = []
        
        # Generar múltiples puntos de inicio si está habilitado
        initial_guesses = self._generate_initial_guesses(model, x_data, y_data, options)
        
        for i, initial_guess in enumerate(initial_guesses):
            try:
                result = self._single_lm_fit(model, x_data, y_data, options, initial_guess)
                attempts.append(result)
                
                # Evaluar calidad del resultado
                if result.success and result.rmse < best_cost:
                    best_cost = result.rmse
                    best_result = result
                    
            except Exception as e:
                self.logger.warning(f"LM attempt {i+1} failed: {str(e)}")
                continue
        
        # Si no hay resultado exitoso, retornar el mejor intento
        if best_result is None:
            best_result = attempts[0] if attempts else self._create_error_result("All LM attempts failed")
        
        # Añadir información sobre intentos múltiples
        best_result.warnings.extend([f"Tried {len(initial_guesses)} initial guesses"])
        
        return best_result
    
    def _single_lm_fit(self, model, x_data: np.ndarray, y_data: np.ndarray,
                       options: FitOptions, initial_params: dict) -> FitResult:
        """Ajuste LM individual con manejo de errores específicos."""
        
        param_names = list(model.parameters.keys())
        p0 = [initial_params.get(name, 1.0) for name in param_names]
        
        # Preparar bounds para scipy
        bounds = self._prepare_scipy_bounds(model, options)
        
        # Configurar pesos si existen
        sigma = None
        if options.weights is not None:
            sigma = 1.0 / np.sqrt(options.weights)
        
        # Función objetivo optimizada
        def objective_func(x, *params):
            try:
                # model.evaluate expects individual parameter values, not a dict
                result = model.evaluate(x, *params)
                
                # Verificar resultado válido
                if np.any(np.isnan(result)) or np.any(np.isinf(result)):
                    return np.full_like(x, 1e10)
                return result
            except:
                return np.full_like(x, 1e10)
        
        # Ejecutar optimización con configuración robusta
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            try:
                popt, pcov, infodict, mesg, ier = curve_fit(
                    objective_func, 
                    x_data, 
                    y_data,
                    p0=p0,
                    sigma=sigma,
                    bounds=bounds,
                    maxfev=options.max_iterations * len(param_names),
                    ftol=options.tolerance,
                    xtol=options.tolerance,
                    full_output=True,
                    method='lm' if bounds == (-np.inf, np.inf) else 'trf'
                )
                
                # Calcular errores de parámetros
                param_errors = self._calculate_parameter_errors(pcov, len(y_data), len(popt))
                
                # Crear resultado
                parameters = dict(zip(param_names, popt))
                errors = dict(zip(param_names, param_errors))
                
                # Calcular métricas
                y_pred = objective_func(x_data, *popt)
                r_squared = self._calculate_r_squared(y_data, y_pred)
                
                return FitResult(
                    success=ier in [1, 2, 3, 4],
                    status=OptimizationStatus.SUCCESS if ier in [1, 2, 3, 4] else OptimizationStatus.CONVERGENCE_FAILED,
                    parameters=parameters,
                    errors=errors,
                    r_squared=r_squared,
                    rmse=np.sqrt(np.mean((y_data - y_pred)**2)),
                    iterations=infodict.get('nfev', 0),
                    function_evaluations=infodict.get('nfev', 0),
                    message=mesg,
                    engine_name=self.name
                )
                
            except (RuntimeError, LinAlgError, ValueError) as e:
                return FitResult(
                    success=False,
                    status=OptimizationStatus.ERROR,
                    parameters={name: p0[i] for i, name in enumerate(param_names)},
                    errors={name: float('inf') for name in param_names},
                    r_squared=0.0,
                    rmse=float('inf'),
                    message=f"LM Error: {str(e)}",
                    engine_name=self.name
                )
    
    def _generate_initial_guesses(self, model, x_data, y_data, options):
        """Genera múltiples estimaciones iniciales inteligentes."""
        guesses = []
        
        # Primer intento: parámetros proporcionados por el usuario
        if options.initial_guess:
            guesses.append(options.initial_guess)
        
        if self.multi_start and len(guesses) < self.n_starts:
            # Estimaciones basadas en características de los datos
            y_min, y_max = np.min(y_data), np.max(y_data)
            y_mean, y_std = np.mean(y_data), np.std(y_data)
            x_range = np.ptp(x_data)
            
            for i in range(self.n_starts - len(guesses)):
                guess = {}
                for param_name, param_info in model.parameters.items():
                    if 'amplitude' in param_name.lower() or 'a' in param_name.lower():
                        guess[param_name] = y_std * (1 + 0.5 * i)
                    elif 'offset' in param_name.lower() or 'c' in param_name.lower():
                        guess[param_name] = y_mean + 0.1 * y_std * (i - 1)
                    elif 'freq' in param_name.lower() or 'omega' in param_name.lower():
                        guess[param_name] = 2 * np.pi / (x_range / (2 + i))
                    elif 'decay' in param_name.lower() or 'tau' in param_name.lower():
                        guess[param_name] = x_range / (5 + 2 * i)
                    else:
                        # Valor por defecto con variación
                        guess[param_name] = param_info.get('default', 1.0) * (0.5 + i * 0.5)
                
                guesses.append(guess)
        
        return guesses if guesses else [{}]
    
    def _prepare_scipy_bounds(self, model, options):
        """Convierte bounds del modelo al formato de scipy."""
        if not options.bounds:
            return (-np.inf, np.inf)
        
        param_names = list(model.parameters.keys())
        lower = [options.bounds.get(name, (-np.inf, np.inf))[0] for name in param_names]
        upper = [options.bounds.get(name, (-np.inf, np.inf))[1] for name in param_names]
        
        return (lower, upper)
    
    def _calculate_parameter_errors(self, pcov, n_data, n_params):
        """Calcula errores de parámetros desde la matriz de covarianza."""
        try:
            if pcov is None:
                return [float('inf')] * n_params
            
            # Calcular errores estándar
            param_errors = np.sqrt(np.diag(pcov))
            
            # Verificar validez
            if np.any(np.isnan(param_errors)) or np.any(np.isinf(param_errors)):
                return [float('inf')] * n_params
            
            return param_errors.tolist()
            
        except:
            return [float('inf')] * n_params