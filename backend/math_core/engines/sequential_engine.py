from .base_engine import BaseEngine, FitResult, FitOptions, OptimizationStatus
from .de_engine import DEEngine
from .lm_engine import LMEngine
import numpy as np
import time

class SequentialEngine(BaseEngine):
    """
    Motor híbrido inteligente que combina DE y LM de manera adaptativa
    para lograr tanto robustez global como precisión local.
    """
    
    def __init__(self):
        super().__init__("SequentialHybrid")
        self.de_engine = DEEngine()
        self.lm_engine = LMEngine()
        
        # Configuración adaptativa
        self.adaptive_switching = True
        self.de_fraction = 0.6  # Fracción del tiempo para DE
        self.convergence_threshold = 1e-3
        
    def _optimize(self, model, x_data: np.ndarray, y_data: np.ndarray, 
                  options: FitOptions) -> FitResult:
        """Optimización híbrida inteligente."""
        
        total_time_budget = getattr(options, 'timeout', 300.0)
        start_time = time.time()
        
        # Fase 1: Exploración global con DE
        de_time_budget = total_time_budget * self.de_fraction
        de_options = self._prepare_de_options(options, de_time_budget)
        
        self.logger.info("Phase 1: Global exploration with Differential Evolution")
        de_result = self.de_engine._optimize(model, x_data, y_data, de_options)
        
        phase1_time = time.time() - start_time
        remaining_time = total_time_budget - phase1_time
        
        # Evaluar si proceder a LM
        # CHANGED: Allow proceeding if DE provided valid parameters, even if not marked 'success'
        # DE is just an initializer here.
        proceed_to_lm = True
        
        # Check if DE returned valid parameters
        if not de_result.parameters or len(de_result.parameters) == 0:
            self.logger.warning("DE phase returned no parameters. Cannot proceed to LM refinement.")
            proceed_to_lm = False
        elif not de_result.success:
            self.logger.warning("DE phase did not fully converge. Attempting LM refinement with best found parameters.")
        
        # Check if we have enough time for LM to be meaningful
        if remaining_time < 0.1:  # Reduced from 0.5 to 0.1
             self.logger.warning("Insufficient time for LM phase.")
             proceed_to_lm = False
             
        if not proceed_to_lm:
            self.logger.warning("Returning DE result without refinement.")
            de_result.engine_name = self.name
            de_result.message += " (DE only - no LM refinement)"
            return de_result
        
        # Fase 2: Refinamiento local con LM
        self.logger.info("Phase 2: Local refinement with Levenberg-Marquardt")
        
        # Preparar opciones LM con resultado DE como punto inicial
        lm_options = self._prepare_lm_options(options, de_result, remaining_time)
        lm_result = self.lm_engine._optimize(model, x_data, y_data, lm_options)
        
        # Decidir cuál resultado usar
        final_result = self._select_best_result(de_result, lm_result, model, x_data, y_data)
        
        # Combinar información de ambas fases
        final_result = self._combine_results(de_result, lm_result, final_result)
        
        total_time = time.time() - start_time
        final_result.execution_time = total_time
        final_result.engine_name = self.name
        
        return final_result
    
    def _prepare_de_options(self, original_options: FitOptions, time_budget: float) -> FitOptions:
        """Prepara opciones optimizadas para la fase DE."""
        de_options = FitOptions(
            max_iterations=min(original_options.max_iterations, 100),  # Limitado para DE
            tolerance=original_options.tolerance * 10,  # Menos estricto para DE
            timeout=time_budget,
            verbose=original_options.verbose,
            seed=original_options.seed,
            weights=original_options.weights,
            bounds=original_options.bounds,
            validate_inputs=False  # Ya validado
        )
        return de_options
    
    def _prepare_lm_options(self, original_options: FitOptions, 
                           de_result: FitResult, time_budget: float) -> FitOptions:
        """Prepara opciones para LM usando resultado DE como inicial."""
        lm_options = FitOptions(
            max_iterations=original_options.max_iterations,
            tolerance=original_options.tolerance,
            timeout=time_budget,
            verbose=original_options.verbose,
            seed=original_options.seed,
            weights=original_options.weights,
            bounds=original_options.bounds,
            initial_guess=de_result.parameters,  # ¡Clave: usar resultado DE!
            validate_inputs=False
        )
        return lm_options
    
    def _select_best_result(self, de_result: FitResult, lm_result: FitResult,
                           model, x_data: np.ndarray, y_data: np.ndarray) -> FitResult:
        """Selecciona inteligentemente el mejor resultado."""
        
        # Validar que tenemos FitResult válidos
        if de_result is None or lm_result is None:
            self.logger.error("Invalid result objects in comparison")
            return de_result if de_result else lm_result
        
        # Validar RMSE
        de_rmse = float(de_result.rmse) if de_result.rmse is not None else float('inf')
        lm_rmse = float(lm_result.rmse) if lm_result.rmse is not None else float('inf')
        
        # Si LM falló, usar DE
        if not lm_result.success:
            self.logger.info("LM refinement failed, using DE result")
            return de_result
        
        # Si DE falló pero LM funcionó (raro pero posible)
        if not de_result.success:
            self.logger.info("Using LM result (DE failed)")
            return lm_result
        
        # Ambos exitosos: comparar calidad (verificar que rmse sea válido)
        if de_rmse < 1e-10 or np.isinf(de_rmse):
            self.logger.warning(f"Invalid DE RMSE: {de_rmse}, using LM result")
            return lm_result
        
        improvement = (de_rmse - lm_rmse) / de_rmse
        
        if improvement > 0.01:  # Mejora significativa (>1%)
            self.logger.info(f"LM improved RMSE by {improvement:.1%}, using LM result")
            return lm_result
        else:
            self.logger.info(f"LM improvement minimal ({improvement:.1%}), using DE result")
            return de_result
    
    def _combine_results(self, de_result: FitResult, lm_result: FitResult, 
                        final_result: FitResult) -> FitResult:
        """Combina información útil de ambas fases."""
        
        # Preservar historia de convergencia de ambas fases
        combined_history = []
        if de_result.convergence_history:
            combined_history.extend(de_result.convergence_history)
        if lm_result.convergence_history:
            combined_history.extend(lm_result.convergence_history)
        
        final_result.convergence_history = combined_history
        
        # Sumar evaluaciones de función
        final_result.function_evaluations = (
            de_result.function_evaluations + lm_result.function_evaluations
        )
        
        # Combinar iteraciones
        final_result.iterations = de_result.iterations + lm_result.iterations
        
        # Información adicional en mensaje
        final_result.message = (
            f"Hybrid optimization: DE({de_result.iterations} iter, "
            f"RMSE={de_result.rmse:.6f}) -> "
            f"LM({'success' if lm_result.success else 'failed'}, "
            f"RMSE={lm_result.rmse:.6f})"
        )
        
        # Combinar advertencias
        all_warnings = []
        if de_result.warnings:
            all_warnings.extend([f"DE: {w}" for w in de_result.warnings])
        if lm_result.warnings:
            all_warnings.extend([f"LM: {w}" for w in lm_result.warnings])
        final_result.warnings = all_warnings
        
        return final_result
    
    def set_de_fraction(self, fraction: float):
        """Permite ajustar la fracción de tiempo dedicada a DE."""
        if 0.1 <= fraction <= 0.9:
            self.de_fraction = fraction
        else:
            raise ValueError("DE fraction must be between 0.1 and 0.9")
    
    def get_engine_info(self):
        """Información sobre la configuración del motor híbrido."""
        return {
            'name': self.name,
            'de_fraction': self.de_fraction,
            'adaptive_switching': self.adaptive_switching,
            'de_engine': self.de_engine.get_stats(),
            'lm_engine': self.lm_engine.get_stats()
        }