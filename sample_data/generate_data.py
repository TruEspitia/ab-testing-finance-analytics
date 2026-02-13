import csv
import random
import math
from datetime import datetime, timedelta
import os

def generate_financial_data_std():
    days = 500
    initial_price = 150.0
    mu = 0.0004  # Drift diario
    sigma = 0.015 # Volatilidad diaria
    
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=x)) for x in range(days)]
    dates.sort()
    
    current_price = initial_price
    data = []
    
    for date in dates:
        # Shock aleatorio normal aproximado (Box-Muller)
        u1 = random.random()
        u2 = random.random()
        epsilon = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        
        # GBM step
        current_price = current_price * math.exp((mu - 0.5 * sigma**2) + sigma * epsilon)
        
        row = {
            'Date': date.strftime('%Y-%m-%d'),
            'Symbol': 'MGL_TECH',
            'Close': round(current_price, 2),
            'Open': round(current_price * (1 + (random.random() - 0.5) * 0.01), 2),
            'High': round(current_price * (1 + random.random() * 0.015), 2),
            'Low': round(current_price * (1 - random.random() * 0.015), 2),
            'Volume': random.randint(100000, 1000000)
        }
        data.append(row)
    
    output_dir = 'sample_data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'historical_stock_data.csv')
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Symbol', 'Close', 'Open', 'High', 'Low', 'Volume'])
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Dataset creado exitosamente en: {output_path}")

if __name__ == "__main__":
    generate_financial_data_std()
