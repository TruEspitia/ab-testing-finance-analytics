import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuración
np.random.seed(42)
n_days = 1000  # Casi 4 años de datos diarios
start_date = datetime(2020, 1, 1)

# Parámetros para Simulación (GBM)
mu = 0.0005  # Retorno diario promedio (~12% anual)
sigma = 0.02  # Volatilidad diaria (~32% anual)
initial_price = 100

# Generar Retornos Logarítmicos
daily_returns = np.random.normal(mu, sigma, n_days)

# Generar Serie de Precios
price_series = [initial_price]
for r in daily_returns:
    price_series.append(price_series[-1] * np.exp(r))

# Crear DataFrame
dates = [start_date + timedelta(days=i) for i in range(len(price_series))]
df = pd.DataFrame({
    'Fecha': dates,
    'Precio_Activo': price_series,
    'Retorno_Diario': [0] + list(daily_returns)
})

# Agregar una caída fuerte (Black Swan) para probar Drawdown y VaR
# Caída del 15% en un solo día cerca del final
df.loc[900, 'Precio_Activo'] *= 0.85
df.loc[900, 'Retorno_Diario'] = -0.15

# Guardar
output_file = 'risk_test_data.csv'
df.to_csv(output_file, index=False)
print(f"✅ Dataset generado exitosamente: {output_file}")
print(f"📊 Registros: {len(df)}")
print(f"📉 Max Drawdown teórico incluido.")
