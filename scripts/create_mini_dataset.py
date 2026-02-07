import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mini_risk_data():
    # Parámetros
    n_days = 200
    start_date = datetime(2023, 1, 1)
    initial_price = 100
    volatility = 0.015  # 1.5% diaria
    drift = 0.0005     # 0.05% diario (~12% anual)
    
    # Fechas
    dates = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # Retornos aleatorios (Normales)
    np.random.seed(42)
    daily_returns = np.random.normal(drift, volatility, n_days)
    
    # Precios (Geometric Brownian Motion)
    price_multipliers = np.exp(daily_returns)
    prices = [initial_price]
    for m in price_multipliers[:-1]:
        prices.append(prices[-1] * m)
    
    # Crear DataFrame
    df = pd.DataFrame({
        'Date': [d.strftime('%Y-%m-%d') for d in dates],
        'Price': np.round(prices, 2),
        'Returns': np.round(daily_returns, 4)
    })
    
    # Guardar
    output_path = 'c:/Users/miguel.espitia/Desktop/ad-test-espitia/ab-testing-finance-analytics/sample_data/risk_test_mini.csv'
    df.to_csv(output_path, index=False)
    print(f"Dataset generado en: {output_path}")
    print(f"Tamaño aproximado: {df.memory_usage().sum() / 1024:.2f} KB en memoria")

if __name__ == "__main__":
    generate_mini_risk_data()
