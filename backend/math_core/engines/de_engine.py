from scipy.optimize import differential_evolution
import numpy as np
from .base_engine import BaseEngine, FitResult, FitOptions, OptimizationStatus

def _de_objective_func(params_array, model, x_data, y_data, weights, bounds, param_names):
    """
    Top-level objective function for Differential Evolution.
    Must be top-level to be pickleable for multiprocessing.
    """
    try:
        # model.evaluate expects individual parameter values, not a dict
        y_pred = model.evaluate(x_data, *params_array)
        
        # Check validity
        if np.any(np.isnan(y_pred)) or np.any(np.isinf(y_pred)):
            return 1e10
        
        # Robust error calculation with weights
        residuals = y_data - y_pred
        weighted_sse = np.sum(weights * residuals**2)
        
        # Penalty for values out of bounds (soft constraints)
        penalty = 0.0
        for i, (param_val, (lower, upper)) in enumerate(zip(params_array, bounds)):
            if param_val < lower:
                penalty += 1000 * (lower - param_val)**2
            elif param_val > upper:
                penalty += 1000 * (param_val - upper)**2
        
        return weighted_sse + penalty
        
    except Exception:
        return 1e10

class DEEngine(BaseEngine):
    """
    Motor Differential Evolution optimizado con estrategias adaptativas
    y manejo inteligente de poblaciones.
    """
    
    def __init__(self):
        super().__init__("DifferentialEvolution")
        self.adaptive_population = True
        self.strategy_rotation = True
        self.strategies = ['best1bin', 'rand1bin', 'best2bin', 'randtobest1bin']
        
    def _optimize(self, model, x_data: np.ndarray, y_data: np.ndarray, 
                  options: FitOptions) -> FitResult:
        """Optimización DE con estrategias adaptativas."""
        
        param_names = list(model.parameters.keys())
        n_params = len(param_names)
        
        # Preparar bounds inteligentes
        bounds = self._prepare_de_bounds(model, x_data, y_data, options)
        
        # Log bounds for debugging
        self.logger.info(f"DE bounds for {len(param_names)} params: {bounds}")
        
        # Configurar población adaptativa
        popsize = self._calculate_population_size(n_params)
        self.logger.info(f"DE population size: {popsize}")
        
        # Configurar pesos si existen
        weights = options.weights if options.weights is not None else np.ones(len(y_data))
        
        # Callback para monitoreo
        iteration_count = 0
        convergence_history = []
        
        # Note: We need a partial wrapper for callback because Scipy DE callback 
        # signature is (xk, convergence), it doesn't accept args.
        def callback_wrapper(xk, convergence):
            nonlocal iteration_count
            iteration_count += 1
            # Recalculate cost for history
            try:
                cost = _de_objective_func(xk, model, x_data, y_data, weights, bounds, param_names)
                if isinstance(cost, (int, float)) and not np.isnan(cost):
                    convergence_history.append(float(cost))
            except:
                pass  # Ignorar errores en callback
            
            if options.iteration_callback and callable(options.iteration_callback):
                try:
                    options.iteration_callback(iteration_count, xk, convergence)
                except:
                    pass
            
            return False  # No detener optimización
        
        best_result = None
        best_cost = float('inf')
        
        # Track time for timeout enforcement
        import time
        start_time = time.time()
        time_budget = options.timeout if options.timeout else 300.0
        
        # Probar múltiples estrategias si está habilitado
        strategies_to_try = self.strategies if self.strategy_rotation else ['best1bin']
        
        # Arguments to pass to objective function
        args = (model, x_data, y_data, weights, bounds, param_names)

        for strategy in strategies_to_try:
            # Check if we've exceeded our time budget
            elapsed = time.time() - start_time
            if elapsed >= time_budget:
                self.logger.warning(f"DE timeout reached after {elapsed:.1f}s")
                break
                
            try:
                # Calculate remaining time for this strategy
                strategy_timeout = (time_budget - elapsed) / len(strategies_to_try)
                
                # Limit maxiter based on remaining time (rough heuristic: ~1-10 iter/sec)
                effective_maxiter = min(options.max_iterations, int(strategy_timeout * 5))
                
                result = differential_evolution(
                    _de_objective_func,
                    bounds,
                    args=args,
                    strategy=strategy,
                    maxiter=max(10, effective_maxiter),  # At least 10 iterations
                    popsize=popsize,
                    tol=options.tolerance,
                    atol=options.tolerance,
                    callback=callback_wrapper,
                    polish=True,  # Refinamiento local final
                    init='latinhypercube',  # Mejor distribución inicial
                    workers=-1,  # Paralelización si es posible
                    seed=options.seed,
                    updating='deferred'  # Mejor para funciones costosas
                )
                
                if result.success and result.fun < best_cost:
                    best_cost = result.fun
                    best_result = result
                    best_result.strategy_used = strategy
                    self.logger.info(f"DE strategy '{strategy}' succeeded with cost {result.fun:.6f}")
                elif not result.success:
                    self.logger.warning(f"DE strategy '{strategy}' did not converge (message: {result.message})")
                    # Keep best partial result even if not marked as success
                    if best_result is None or result.fun < best_cost:
                        best_cost = result.fun
                        best_result = result
                        best_result.strategy_used = strategy
                
            except Exception as e:
                self.logger.error(f"DE strategy {strategy} crashed: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                continue
        
        if best_result is None:
            self.logger.error("All DE strategies failed - no result was obtained")
            return self._create_error_result("All DE strategies failed")
        
        # Convertir resultado a nuestro formato
        parameters = dict(zip(param_names, best_result.x))
        
        # Estimar errores usando Hessiana numérica
        errors = self._estimate_parameter_errors(_de_objective_func, best_result.x, bounds, args)
        
        # Calcular métricas finales
        try:
            param_values = [parameters[name] for name in param_names]
            y_pred = model.evaluate(x_data, *param_values)
            r_squared = self._calculate_r_squared(y_data, y_pred)
            rmse = np.sqrt(np.mean((y_data - y_pred)**2))
        except:
            r_squared = 0.0
            rmse = float('inf')
        
        return FitResult(
            success=best_result.success,
            status=OptimizationStatus.SUCCESS if best_result.success else OptimizationStatus.CONVERGENCE_FAILED,
            parameters=parameters,
            errors=dict(zip(param_names, errors)),
            r_squared=r_squared,
            rmse=rmse,
            iterations=best_result.nit,
            function_evaluations=best_result.nfev,
            convergence_history=convergence_history,
            message=f"DE completed with strategy: {getattr(best_result, 'strategy_used', 'unknown')}",
            engine_name=self.name
        )
    
    def _prepare_de_bounds(self, model, x_data, y_data, options):
        """Prepara bounds inteligentes para DE."""
        bounds = []
        
        # Características de los datos para bounds inteligentes
        y_min, y_max = np.min(y_data), np.max(y_data)
        y_range = y_max - y_min
        x_range = np.ptp(x_data)
        
        for param_name in model.parameters.keys():
            if options.bounds and param_name in options.bounds:
                bounds.append(options.bounds[param_name])
            else:
                # Bounds automáticos basados en el nombre del parámetro
                if 'amplitude' in param_name.lower() or param_name.lower() == 'a':
                    bounds.append((0.01 * y_range, 10 * y_range))
                elif 'offset' in param_name.lower() or param_name.lower() == 'c':
                    bounds.append((y_min - y_range, y_max + y_range))
                elif 'freq' in param_name.lower() or 'omega' in param_name.lower():
                    bounds.append((0.1 / x_range, 10 / x_range))
                elif 'decay' in param_name.lower() or 'tau' in param_name.lower():
                    bounds.append((x_range / 1000, x_range * 10))
                elif 'phase' in param_name.lower():
                    bounds.append((-2*np.pi, 2*np.pi))
                else:
                    # Bounds genéricos
                    bounds.append((-100, 100))
        
        return bounds
    
    def _calculate_population_size(self, n_params):
        """Calcula tamaño de población adaptativo."""
        if self.adaptive_population:
            # Regla heurística: más parámetros necesitan más población
            return max(15, min(50, 5 * n_params))
        return 15
    
    def _estimate_parameter_errors(self, objective_func, best_params, bounds, args):
        """Estima errores de parámetros usando diferencias finitas."""
        errors = []
        
        for i in range(len(best_params)):
            try:
                # Calcular paso adaptativo
                param_val = best_params[i]
                lower, upper = bounds[i]
                param_range = upper - lower
                h = max(abs(param_val) * 1e-5, param_range * 1e-6, 1e-8)
                
                # Diferencia finita central
                params_plus = best_params.copy()
                params_minus = best_params.copy()
                
                params_plus[i] = min(param_val + h, upper)
                params_minus[i] = max(param_val - h, lower)
                
                f_plus = objective_func(params_plus, *args)
                f_minus = objective_func(params_minus, *args)
                f_center = objective_func(best_params, *args)
                
                # Aproximación de la curvatura (segunda derivada)
                if f_plus < 1e9 and f_minus < 1e9 and f_center < 1e9:
                    curvature = abs((f_plus - 2*f_center + f_minus) / h**2)
                    if curvature > 1e-10:
                        error = 1.0 / np.sqrt(curvature)
                        errors.append(min(error, param_range * 0.1))
                    else:
                        errors.append(param_range * 0.05)
                else:
                    errors.append(param_range * 0.1)
                    
            except:
                # Error por defecto
                lower, upper = bounds[i]
                errors.append((upper - lower) * 0.1)
        
        return errors