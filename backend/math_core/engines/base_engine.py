from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import numpy as np
import logging
from contextlib import contextmanager

class OptimizationStatus(Enum):
    SUCCESS = 1
    CONVERGENCE_FAILED = 2
    ERROR = 3
    TIMEOUT = 4

@dataclass
class FitOptions:
    max_iterations: int = 1000
    tolerance: float = 1e-6
    timeout: float = 300.0
    verbose: bool = False
    seed: Optional[int] = None
    weights: Optional[np.ndarray] = None
    bounds: Optional[Dict[str, tuple]] = None
    initial_guess: Optional[Dict[str, float]] = None
    validate_inputs: bool = True
    iteration_callback: Optional[Callable] = None

@dataclass
class FitResult:
    success: bool
    status: OptimizationStatus
    parameters: Dict[str, float]
    errors: Dict[str, float]
    r_squared: float
    rmse: float
    iterations: int = 0
    function_evaluations: int = 0
    message: str = ""
    convergence_history: List[float] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    engine_name: str = "Unknown"
    strategy_used: str = ""

    def to_dict(self):
        """Helper for backward compatibility - retorna diccionario limpio"""
        # Convertir parámetros a tipos seguros
        try:
            params_dict = {}
            if isinstance(self.parameters, dict):
                for k, v in self.parameters.items():
                    params_dict[str(k)] = float(v) if v is not None else 0.0
            
            errors_dict = {}
            if isinstance(self.errors, dict):
                for k, v in self.errors.items():
                    errors_dict[str(k)] = float(v) if v is not None else 0.0
        except (TypeError, ValueError) as e:
            self.logger.warning(f"Type conversion error in to_dict: {e}")
            params_dict = {}
            errors_dict = {}
        
        # Retornar diccionario con todos los campos necesarios
        return {
            "success": bool(self.success),
            "popt": list(params_dict.values()) if params_dict else [],
            "perr": list(errors_dict.values()) if errors_dict else [],
            "parameters": params_dict,
            "errors": errors_dict,
            "r_squared": float(self.r_squared) if self.r_squared is not None else 0.0,
            "rmse": float(self.rmse) if self.rmse is not None else float('inf'),
            "message": str(self.message) if self.message else "",
            "engine": str(self.engine_name),
            "fitted_curve": [],
            "residuals": [],
            "iterations": int(self.iterations) if self.iterations else 0,
            "function_evaluations": int(self.function_evaluations) if self.function_evaluations else 0
        }

class BaseEngine(ABC):
    def __init__(self, name: str = "BaseEngine"):
        self.name = name
        self.logger = logging.getLogger(name)

    @contextmanager
    def _timeout_context(self, seconds):
        """Context manager for timeout enforcement on Windows."""
        import threading
        
        timer = None
        # Flag to indicate timeout happened
        status = {'timed_out': False}
        
        # We can't easily interrupt a running thread in Python without C-API
        # But we can assume the engine checks for flags or we rely on 'thread.interrupt_main()'
        # For pure number crunching in C-extensions (numpy), interruption is hard.
        # This is a 'soft' timeout for the surrounding logic.
        
        def timeout_handler():
            status['timed_out'] = True
            # Optional: _thread.interrupt_main() could be used here to raise KeyboardInterrupt
            # but it might be unsafe in some GUI contexts.
        
        try:
            if seconds and seconds > 0:
                timer = threading.Timer(seconds, timeout_handler)
                timer.start()
            yield status
        finally:
            if timer:
                timer.cancel()
    
    def fit(self, model, x_data, y_data, options=None) -> dict:
        """
        Public interface matching the old signature but using the new internal flow.
        Returns a dictionary for backward compatibility with optimization.py.
        """
        # Convert dict options to FitOptions
        opts = options or {}
        fit_options = FitOptions(
            max_iterations=opts.get('max_iter', 2000), # Map old 'max_iter'
            timeout=opts.get('timeout', 120.0), # Increased to 120s for complex functions like Fourier
            bounds=opts.get('bounds_dict', None) # Assuming bounds passed as dict
        )
        
        # Also map specific keys if they exist in options
        if 'p0' in opts and opts['p0'] is not None:
             # Map list p0 to dict initial_guess using model parameter names
             param_names = sorted(model.parameters.keys())
             p0_list = opts['p0']
             if len(p0_list) == len(param_names):
                 fit_options.initial_guess = dict(zip(param_names, p0_list))

        try:
            # Use soft timeout check around optimization
            # Note: Hard enforcement is difficult in Python Threads
            result_obj = self._optimize(model, x_data, y_data, fit_options)
            return result_obj.to_dict()
            
        except Exception as e:
            self.logger.error(f"Engine Error: {str(e)}")
            return {
                "success": False,
                "error": f"Engine Error: {str(e)}",
                "engine": self.name
            }

    @abstractmethod
    def _optimize(self, model, x_data: np.ndarray, y_data: np.ndarray, options: FitOptions) -> FitResult:
        """Internal abstract method that must be implemented by subclasses."""
        pass

    def _create_error_result(self, message: str) -> FitResult:
        return FitResult(
            success=False,
            status=OptimizationStatus.ERROR,
            parameters={},
            errors={},
            r_squared=0.0,
            rmse=float('inf'),
            message=message,
            engine_name=self.name
        )

    def _calculate_r_squared(self, y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 0.0
        return 1 - (ss_res / ss_tot)

