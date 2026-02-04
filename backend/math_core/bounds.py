import numpy as np

class BoundsGenerator:
    @staticmethod
    def generate_bounds(model, x_data, y_data):
        """
        Generates automatic bounds based on parameter names and data.
        Returns a list of (min, max) tuples matching the sorted parameter keys.
        """
        param_names = sorted(model.parameters.keys())
        bounds = []
        
        y_min = np.min(y_data)
        y_max = np.max(y_data)
        y_range = y_max - y_min if y_max != y_min else 1.0
        x_min = np.min(x_data)
        x_max = np.max(x_data)
        x_range = x_max - x_min if x_max != x_min else 1.0
        
        for name in param_names:
            low = -np.inf
            high = np.inf
            
            # Heuristics based on parameter name
            
            # Amplitudes / Offsets
            if name.startswith('A') or name == 'Vmax' or name == 'plateau':
                # Likely amplitude or offset. 
                # Bound to reasonable multiples of Y range
                high = y_max + 10 * y_range
                low = y_min - 10 * y_range
                
            # Rates / Constants
            elif name.startswith('k') or name.startswith('b') or name.startswith('c'):
                # Rate constants usually positive
                low = 0
                high = 1000 # Generic large number, tricky to guess without 1/x context
                
            # Positions / Thresholds
            elif name in ['x0', 'x50', 'Km', 'KD', 'Tu', 'Tm']:
                # Constants in domain of X
                low = x_min - x_range
                high = x_max + x_range
                
            # Widths / Sigmas
            elif name in ['sigma', 'width', 'w']:
                low = 0
                high = x_range * 2
                
            # Exponents
            elif name in ['n', 'lambda']:
                low = 0.1
                high = 20
                
            # Angles 
            elif name == 'phi':
                low = -2 * np.pi
                high = 2 * np.pi
                
            # Fallback for unknown parameters
            if np.isinf(low): low = -1e9
            if np.isinf(high): high = 1e9
            
            # Ensure low < high
            if low >= high:
                low = high - 100
                
            bounds.append((low, high))
            
        return bounds
