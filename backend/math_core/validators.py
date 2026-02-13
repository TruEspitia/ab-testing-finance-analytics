import numpy as np

class Validator:
    @staticmethod
    def validate_data(x, y):
        # Convert to numpy arrays
        x_arr = np.array(x, dtype=float)
        y_arr = np.array(y, dtype=float)
        
        # Check for NaNs or Infs
        if not np.isfinite(x_arr).all() or not np.isfinite(y_arr).all():
            return False, "Data contains NaN or Infinite values"
            
        # Check lengths
        if len(x_arr) != len(y_arr):
            return False, "X and Y data must have the same length"
            
        # Check for empty
        if len(x_arr) == 0:
            return False, "Data is empty"

        # Check for variation in Y
        if np.std(y_arr) == 0:
            return False, "Y data has no variation (cannot fit a curve)"

        return True, ""

    @staticmethod
    def validate_model_requirements(model, x_len):
        param_count = len(model.parameters)
        if x_len < param_count + 1:
             return False, f"Not enough data points. Need at least {param_count + 1} points for {param_count} parameters."
        return True, ""
