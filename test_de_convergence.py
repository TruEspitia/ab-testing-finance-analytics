"""
Test script to verify DE convergence improvements
"""
import sys
import numpy as np
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import optimization engine
from backend.math_core.ffunc_parser import FFuncModel
from backend.math_core.optimization import OptimizationEngine

# Create test data - exponential decay with noise
np.random.seed(42)
x_data = np.linspace(0, 10, 50)
true_params = {'A': 5.0, 'tau': 2.0, 'C': 1.0}
y_true = true_params['A'] * np.exp(-x_data / true_params['tau']) + true_params['C']
y_data = y_true + np.random.normal(0, 0.2, len(x_data))

# Create exponential model
model = FFuncModel(
    name="exponential_single",
    parameters={'A': 1.0, 'tau': 1.0, 'C': 0.0},
    formula_str="y = A * exp(-x / tau) + C",
    metadata={'complexity': 2}
)

print("=" * 60)
print("Testing DE Convergence Improvements")
print("=" * 60)
print(f"Model: Exponential Decay")
print(f"Parameters: {model.parameters}")
print(f"Data points: {len(x_data)}")
print(f"True parameters: {true_params}")
print()

# Test with sequential engine (includes DE)
print("Running Sequential Engine (DE + LM)...")
result = OptimizationEngine.fit_data(
    model, 
    x_data, 
    y_data, 
    engine_type="sequential",
    options={}
)

print()
print("Results:")
print(f"  Success: {result.get('success')}")
print(f"  Engine: {result.get('engine')}")
print(f"  R²: {result.get('r_squared', 0):.6f}")
print(f"  RMSE: {result.get('rmse', float('inf')):.6f}")
print(f"  Iterations: {result.get('iterations', 0)}")
print(f"  Function Evaluations: {result.get('function_evaluations', 0)}")
print()
print("Fitted Parameters:")
for param, value in result.get('parameters', {}).items():
    true_val = true_params.get(param, None)
    error_pct = abs(value - true_val) / true_val * 100 if true_val else 0
    print(f"  {param}: {value:.4f} (true: {true_val}, error: {error_pct:.1f}%)")
print()
print(f"Message: {result.get('message', 'No message')}")
print("=" * 60)

# Check success
if result.get('success') and result.get('r_squared', 0) > 0.95:
    print("✅ TEST PASSED: Optimization converged successfully!")
    sys.exit(0)
else:
    print("❌ TEST FAILED: Optimization did not converge properly")
    sys.exit(1)
