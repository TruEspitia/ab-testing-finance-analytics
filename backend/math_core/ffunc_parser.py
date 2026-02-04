import os
import numpy as np

class FFuncModel:
    def __init__(self, name, parameters, formula_str, metadata=None):
        self.name = name
        self.parameters = parameters # dict of {param_name: default_value}
        self.formula_str = formula_str
        self.metadata = metadata or {}
        self.compiled_formula = None

    def evaluate(self, x, *params):
        """
        Evaluates the function.
        x: numpy array of x values
        params: list of parameter values in alphabetical order of keys (A0, A1, ...)
        """
        # Create a local context with numpy functions available
        local_context = {
            'x': x,
            'np': np,
            'exp': np.exp,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'tan': np.tan,
            'log': np.log,
            'log10': np.log10,
            'sqrt': np.sqrt,
            'pi': np.pi,
            'power': np.power,
            'tanh': np.tanh,
            'sinh': np.sinh,
            'cosh': np.cosh,
            'arctan': np.arctan,
            'arcsin': np.arcsin,
            'arccos': np.arccos,
            'abs': np.abs
        }
        
        # Sort parameter names to match the *params order
        param_names = sorted(self.parameters.keys())
        
        if len(params) != len(param_names):
             raise ValueError(f"Expected {len(param_names)} parameters, got {len(params)}")

        for name, val in zip(param_names, params):
            local_context[name] = val

        # Evaluate
        # We replace 'y =' part if it exists
        formula = self.formula_str
        if "=" in formula:
            formula = formula.split("=")[1].strip()
            
        try:
            # Suppress warnings during evaluation (expected in optimization)
            with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                result = eval(formula, {"__builtins__": {}}, local_context)
            
            # Validate result
            if not isinstance(result, np.ndarray):
                # Handle scalar result for vector input
                if isinstance(x, np.ndarray):
                    result = np.full_like(x, result, dtype=float)
                else:
                    result = np.asarray(result)
                
            # Check for NaN or Inf (return as signals to optimizer, don't crash)
            # Optimizers usually handle NaNs as bad scores, but we want to be explicit
            # However, for evaluate(), we just return the array even if it has NaNs
            # The engine is responsible for penalizing it.
            return result
            
        except Exception as e:
            # In case of syntax error or other eval issues
            raise ValueError(f"Evaluation error: {str(e)}")

class FFuncParser:
    @staticmethod
    def parse_file(filepath):
        name = os.path.basename(filepath).replace(".ffunc", "")
        parameters = {}
        metadata = {"complexity": 1} # Default complexity
        formula_lines = []
        
        mode = None # 'PARAMETERS', 'FORMULA', 'METADATA'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                if line == "<PARAMETERS>":
                    mode = "PARAMETERS"
                    continue
                elif line == "<FORMULA>":
                    mode = "FORMULA"
                    continue
                elif line == "<METADATA>":
                    mode = "METADATA"
                    continue
                
                if mode == "METADATA":
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip().lower()
                        if key == "complexity":
                            try:
                                metadata[key] = int(val.strip())
                            except:
                                pass
                        else:
                            metadata[key] = val.strip()

                elif mode == "PARAMETERS":
                    # Parse "Name, Value"
                    parts = line.split(",")
                    if len(parts) >= 2:
                        p_name = parts[0].strip()
                        try:
                            p_val = float(parts[1].strip())
                            parameters[p_name] = p_val
                        except ValueError:
                            pass # Skip invalid params
                
                elif mode == "FORMULA":
                    if line.startswith("#"): continue
                    formula_lines.append(line)
        
        formula_str = " ".join(formula_lines)
        return FFuncModel(name, parameters, formula_str, metadata)

    @staticmethod
    def get_available_functions(functions_dir):
        models = []
        if not os.path.exists(functions_dir):
            return models
            
        for root, dirs, files in os.walk(functions_dir):
            for file in files:
                if file.endswith(".ffunc"):
                    full_path = os.path.join(root, file)
                    try:
                        model = FFuncParser.parse_file(full_path)
                        models.append(model)
                    except Exception as e:
                        print(f"Error parsing {file}: {e}")
        return models
