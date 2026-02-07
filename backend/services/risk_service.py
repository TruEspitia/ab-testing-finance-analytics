
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import logging

logger = logging.getLogger(__name__)

class RiskService:
    def calculate_var(self, data: pd.Series, confidence_level: float = 0.95, horizon: int = 1, method: str = 'parametric', iterations: int = 10000):
        """
        Calcula el Value at Risk (VaR) y Conditional VaR (CVaR).
        
        Args:
            data (pd.Series): Serie de retornos o precios. Si son precios, se calcularán retornos.
            confidence_level (float): Nivel de confianza (ej. 0.95 para 95%).
            horizon (int): Horizonte temporal en días.
            method (str): 'parametric', 'historical', 'monte_carlo'.
            iterations (int): Número de simulaciones para Monte Carlo.
            
        Returns:
            dict: Resultados del análisis incluyendo VaR, CVaR y gráfico.
        """
        try:
            # Calcular retornos si los datos no parecen serlo (ej. media > 1 o < -1 podría indicar precios, pero mejor calcular siempre log returns si son precios)
            # Asumiremos que el usuario selecciona la columna correcta. Si es precios, calculamos retornos.
            # Una heurística simple: si todos los valores son positivos y > 0.5, probablemente son precios.
            if (data > 0).all() and data.mean() > 0.5:
                returns = np.log(data / data.shift(1)).dropna()
            else:
                returns = data.dropna()

            if returns.empty:
                raise ValueError("No hay suficientes datos para calcular retornos.")

            mu = returns.mean()
            sigma = returns.std()
            
            var_value = 0.0
            cvar_value = 0.0
            simulated_returns = None
            
            # Ajuste por horizonte temporal (Raíz cuadrada del tiempo para volatilidad, lineal para retorno)
            # Nota: VaR suele reportarse en términos de pérdidas (positivo) o retorno negativo. Usaremos retorno negativo.
            
            if method == 'parametric':
                # VaR Paramétrico (Distribución Normal)
                # Z-score para el nivel de confianza
                z_score = stats.norm.ppf(1 - confidence_level)
                
                # VaR = mu * horizon + z * sigma * sqrt(horizon)
                # Pero normalmente nos interesa la pérdida máxima
                var_return = (mu * horizon) + (z_score * sigma * np.sqrt(horizon))
                var_value = -var_return # Convertir a positivo para expresar "Monto en Riesgo" si fuera dinero, aquí es %
                
                # CVaR (Expected Shortfall) para distribución normal
                # CVaR = - (mu + sigma * (pdf(z) / (1-alpha)))
                # pdf(z) es la densidad en el punto de corte
                pdf_z = stats.norm.pdf(z_score)
                cvar_return = (mu * horizon) - (sigma * np.sqrt(horizon) * (pdf_z / (1 - confidence_level)))
                cvar_value = -cvar_return

                # Generar datos teóricos para el gráfico
                simulated_returns = np.random.normal(mu * horizon, sigma * np.sqrt(horizon), 10000)

            elif method == 'historical':
                # VaR Histórico
                # Escalar retornos al horizonte
                # Aproximación simple: multiplicar retornos por sqrt(horizon) no es exacto para histórico puro, 
                # pero proyectar la distribución empírica suele hacerse asumiendo i.i.d.
                # Una forma es tomar retornos de N días, pero si solo tenemos 1 dia, escalamos la distribución.
                
                scaled_returns = returns * np.sqrt(horizon) # Aproximación de escalado
                
                var_return = np.percentile(scaled_returns, (1 - confidence_level) * 100)
                var_value = -var_return
                
                # CVaR: Promedio de los retornos peores que el VaR
                cvar_return = scaled_returns[scaled_returns <= var_return].mean()
                cvar_value = -cvar_return
                
                simulated_returns = scaled_returns

            elif method == 'monte_carlo':
                # Simulación Monte Carlo (Geometric Brownian Motion Simplificado para returns)
                # Simular proyecciones al horizonte
                # return_T = sum(daily_returns) ~ Normal(mu*T, sigma*sqrt(T)) en log returns
                # Simular N caminos
                
                # Generar retornos aleatorios normales ajustados a T
                sim_rets = np.random.normal(mu * horizon, sigma * np.sqrt(horizon), iterations)
                
                var_return = np.percentile(sim_rets, (1 - confidence_level) * 100)
                var_value = -var_return
                
                cvar_return = sim_rets[sim_rets <= var_return].mean()
                cvar_value = -cvar_return
                
                simulated_returns = sim_rets

            else:
                raise ValueError(f"Método desconocido: {method}")

            # Generar Gráfico
            plot_base64 = self._generate_plot(simulated_returns, -var_value, -cvar_value, confidence_level, method)
            
            return {
                "var": float(var_value), # Porcentaje de pérdida esperado
                "cvar": float(cvar_value), # Pérdida esperada en el peor caso
                "confidence_level": confidence_level,
                "horizon": horizon,
                "method": method,
                "mu_daily": float(mu),
                "sigma_daily": float(sigma),
                "plot": plot_base64
            }

        except Exception as e:
            logger.error(f"Error en cálculo de VaR: {str(e)}")
            raise e

    def _generate_plot(self, data, var_threshold, cvar_threshold, confidence, method):
        plt.figure(figsize=(10, 6))
        
        # Histograma de retornos/pérdidas
        plt.hist(data, bins=50, density=True, alpha=0.6, color='#4F81BD', label='Distribución de Retornos')
        
        # Línea de VaR
        plt.axvline(var_threshold, color='red', linestyle='--', linewidth=2, label=f'VaR {int(confidence*100)}%: {var_threshold:.4f}')
        
        # Línea de CVaR
        plt.axvline(cvar_threshold, color='darkred', linestyle=':', linewidth=2, label=f'CVaR: {cvar_threshold:.4f}')
        
        # Sombrear área de pérdida
        # min_val = np.min(data)
        # x = np.linspace(min_val, var_threshold, 100)
        # ... (sería complejo sombrear histograma exacto, simpleaxvspan es mejor)
        plt.axvspan(plt.xlim()[0], var_threshold, alpha=0.2, color='red')

        plt.title(f'Distribución de Pérdidas/Ganancias Proyectadas ({method.replace("_", " ").title()})')
        plt.xlabel('Retorno Proyectado')
        plt.ylabel('Frecuencia')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

risk_service = RiskService()
