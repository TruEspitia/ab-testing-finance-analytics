
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

    def calculate_maximum_drawdown(self, data: pd.Series):
        """
        Calcula el Maximum Drawdown (MDD) y drawdown series.
        
        Args:
            prices (pd.Series): Serie de precios.
            
        Returns:
            dict: MDD, peak, trough, recovery info, y serie de drawdown.
        """
        try:
            if data.empty:
                raise ValueError("Serie de precios vacía")
            
            # Calcular running maximum (peak)
            running_max = data.expanding().max()
            
            # Calcular drawdown en cada punto
            drawdown = (data - running_max) / running_max
            
            # Maximum Drawdown
            max_dd = drawdown.min()
            max_dd_idx = drawdown.idxmin()
            
            # Encontrar el peak anterior al MDD
            peak_idx = running_max[:max_dd_idx].idxmax()
            peak_value = data[peak_idx]
            trough_value = data[max_dd_idx]
            
            # Calcular recovery (si existe)
            recovery_idx = None
            recovery_days = None
            if max_dd_idx < len(data) - 1:
                future_prices = data[max_dd_idx:]
                recovered = future_prices[future_prices >= peak_value]
                if not recovered.empty:
                    recovery_idx = recovered.index[0]
                    recovery_days = (recovery_idx - max_dd_idx) if hasattr(max_dd_idx, '__sub__') else len(data[max_dd_idx:recovery_idx])
            
            # Generar gráfico
            plot_base64 = self._generate_drawdown_plot(data, drawdown, peak_idx, max_dd_idx, recovery_idx)
            
            return {
                "max_drawdown": float(max_dd * 100),  # Convertir a porcentaje
                "peak_date": str(peak_idx),
                "peak_value": float(peak_value),
                "trough_date": str(max_dd_idx),
                "trough_value": float(trough_value),
                "recovery_date": str(recovery_idx) if recovery_idx else None,
                "recovery_days": int(recovery_days) if recovery_days else None,
                "drawdown_series": drawdown.tolist(),
                "dates": data.index.astype(str).tolist() if hasattr(data.index, 'astype') else list(range(len(data))),
                "plot": plot_base64
            }
            
        except Exception as e:
            logger.error(f"Error en cálculo de Maximum Drawdown: {str(e)}")
            raise e

    def perform_backtesting(self, data: pd.Series, var_method: str = 'parametric', 
                           confidence_level: float = 0.95, horizon: int = 1, window_size: int = 250):
        """
        Realiza backtesting de VaR mediante rolling window.
        
        Args:
            data (pd.Series): Serie de retornos o precios.
            var_method (str): Método VaR a testear.
            confidence_level (float): Nivel de confianza.
            horizon (int): Horizonte temporal.
            window_size (int): Tamaño de ventana para rolling VaR.
            
        Returns:
            dict: Resultados de backtesting incluyendo violaciones y test de Kupiec.
        """
        try:
            # Preparar retornos
            if (data > 0).all() and data.mean() > 0.5:
                returns = np.log(data / data.shift(1)).dropna()
            else:
                returns = data.dropna()
            
            if len(returns) < window_size + 100:
                raise ValueError(f"Se necesitan al menos {window_size + 100} observaciones para backtesting")
            
            # Rolling VaR calculation
            var_predictions = []
            actual_returns = []
            dates = []
            
            for i in range(window_size, len(returns)):
                window = returns.iloc[i-window_size:i]
                next_return = returns.iloc[i]
                
                # Calcular VaR sobre la ventana
                mu = window.mean()
                sigma = window.std()
                
                if var_method == 'parametric':
                    z_score = stats.norm.ppf(1 - confidence_level)
                    var_return = (mu * horizon) + (z_score * sigma * np.sqrt(horizon))
                elif var_method == 'historical':
                    scaled_returns = window * np.sqrt(horizon)
                    var_return = np.percentile(scaled_returns, (1 - confidence_level) * 100)
                else:  # monte_carlo
                    sim_rets = np.random.normal(mu * horizon, sigma * np.sqrt(horizon), 10000)
                    var_return = np.percentile(sim_rets, (1 - confidence_level) * 100)
                
                var_predictions.append(-var_return)  # Como pérdida positiva
                actual_returns.append(next_return)
                dates.append(returns.index[i] if hasattr(returns.index, '__getitem__') else i)
            
            var_predictions = np.array(var_predictions)
            actual_returns = np.array(actual_returns)
            
            # Contar violaciones (cuando la pérdida real excede el VaR)
            violations = actual_returns < -var_predictions
            num_violations = violations.sum()
            total_obs = len(violations)
            violation_rate = num_violations / total_obs
            expected_rate = 1 - confidence_level
            
            # Kupiec Test (Likelihood Ratio Test)
            # H0: violation_rate = expected_rate
            if num_violations == 0 or num_violations == total_obs:
                # Caso degenerado
                lr_stat = np.inf if num_violations != total_obs * expected_rate else 0
                p_value = 0.0 if num_violations != total_obs * expected_rate else 1.0
            else:
                likelihood_ratio = -2 * np.log(
                    ((expected_rate ** num_violations) * ((1 - expected_rate) ** (total_obs - num_violations))) /
                    ((violation_rate ** num_violations) * ((1 - violation_rate) ** (total_obs - num_violations)))
                )
                lr_stat = likelihood_ratio
                # LR sigue chi-cuadrado con 1 grado de libertad
                p_value = 1 - stats.chi2.cdf(lr_stat, df=1)
            
            # Generar plot
            plot_base64 = self._generate_backtesting_plot(dates, actual_returns, var_predictions, violations)
            
            return {
                "total_observations": int(total_obs),
                "num_violations": int(num_violations),
                "violation_rate": float(violation_rate),
                "expected_rate": float(expected_rate),
                "kupiec_lr_stat": float(lr_stat),
                "kupiec_p_value": float(p_value),
                "test_passed": bool(p_value > 0.05),  # No rechazamos H0
                "var_method": var_method,
                "confidence_level": confidence_level,
                "window_size": window_size,
                "plot": plot_base64
            }
            
        except Exception as e:
            logger.error(f"Error en backtesting: {str(e)}")
            raise e

    def calculate_var_monte_carlo_advanced(self, data: pd.Series, confidence_level: float = 0.95, 
                                          horizon: int = 10, iterations: int = 10000, 
                                          distribution: str = 'normal'):
        """
        VaR Monte Carlo avanzado con simulación de trayectorias completas.
        
        Args:
            data (pd.Series): Serie de retornos o precios.
            confidence_level (float): Nivel de confianza.
            horizon (int): Horizonte de proyección (días).
            iterations (int): Número de simulaciones.
            distribution (str): 'normal', 't-student', 'bootstrap'.
            
        Returns:
            dict: VaR, CVaR, trayectorias simuladas, peores escenarios.
        """
        try:
            # Preparar retornos
            if (data > 0).all() and data.mean() > 0.5:
                returns = np.log(data / data.shift(1)).dropna()
            else:
                returns = data.dropna()
            
            if returns.empty:
                raise ValueError("No hay suficientes datos")
            
            mu = returns.mean()
            sigma = returns.std()
            
            # Simular trayectorias completas (paths de horizon días)
            paths = np.zeros((iterations, horizon))
            
            if distribution == 'normal':
                for t in range(horizon):
                    paths[:, t] = np.random.normal(mu, sigma, iterations)
            
            elif distribution == 't-student':
                # Usar t-student con grados de libertad estimados
                df_param = 5  # Típico para finanzas (colas más pesadas)
                for t in range(horizon):
                    paths[:, t] = stats.t.rvs(df=df_param, loc=mu, scale=sigma, size=iterations)
            
            elif distribution == 'bootstrap':
                # Bootstrap histórico
                for t in range(horizon):
                    paths[:, t] = np.random.choice(returns, size=iterations, replace=True)
            
            else:
                raise ValueError(f"Distribución desconocida: {distribution}")
            
            # Retorno acumulado al final del horizonte
            cumulative_returns = paths.sum(axis=1)
            
            # VaR y CVaR
            var_return = np.percentile(cumulative_returns, (1 - confidence_level) * 100)
            var_value = -var_return
            
            cvar_return = cumulative_returns[cumulative_returns <= var_return].mean()
            cvar_value = -cvar_return
            
            # Peores 10 escenarios
            worst_indices = np.argsort(cumulative_returns)[:10]
            worst_paths = paths[worst_indices].tolist()
            
            # Generar plot con algunas trayectorias
            plot_base64 = self._generate_mc_paths_plot(paths, var_return, cvar_return, horizon)
            
            return {
                "var": float(var_value),
                "cvar": float(cvar_value),
                "confidence_level": confidence_level,
                "horizon": horizon,
                "iterations": iterations,
                "distribution": distribution,
                "mu_daily": float(mu),
                "sigma_daily": float(sigma),
                "worst_paths": worst_paths,
                "plot": plot_base64
            }
            
        except Exception as e:
            logger.error(f"Error en VaR Monte Carlo avanzado: {str(e)}")
            raise e

    def _generate_drawdown_plot(self, prices, drawdown, peak_idx, trough_idx, recovery_idx):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot 1: Prices
        ax1.plot(prices.index if hasattr(prices, 'index') else range(len(prices)), prices, label='Precio', color='#4F81BD')
        ax1.scatter([peak_idx], [prices[peak_idx]], color='green', s=100, label='Peak', zorder=5)
        ax1.scatter([trough_idx], [prices[trough_idx]], color='red', s=100, label='Trough', zorder=5)
        if recovery_idx:
            ax1.scatter([recovery_idx], [prices[recovery_idx]], color='orange', s=100, label='Recovery', zorder=5)
        ax1.set_ylabel('Precio')
        ax1.set_title('Precio y Maximum Drawdown')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Drawdown
        ax2.fill_between(drawdown.index if hasattr(drawdown, 'index') else range(len(drawdown)), 
                         drawdown * 100, 0, color='red', alpha=0.3, label='Drawdown')
        ax2.plot(drawdown.index if hasattr(drawdown, 'index') else range(len(drawdown)), 
                drawdown * 100, color='darkred', linewidth=1.5)
        ax2.axhline(y=drawdown.min() * 100, color='red', linestyle='--', label=f'Max DD: {drawdown.min()*100:.2f}%')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Tiempo')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def _generate_backtesting_plot(self, dates, actual_returns, var_predictions, violations):
        plt.figure(figsize=(12, 6))
        
        # Plot actual returns
        colors = ['red' if v else 'green' for v in violations]
        plt.scatter(range(len(actual_returns)), actual_returns, c=colors, alpha=0.6, s=20, label='Retornos Reales')
        
        # Plot VaR boundary
        plt.plot(range(len(var_predictions)), -var_predictions, color='blue', linestyle='--', linewidth=2, label='VaR Predicho')
        
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.title('Backtesting de VaR: Violaciones vs Predicciones')
        plt.xlabel('Observación')
        plt.ylabel('Retorno')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def _generate_mc_paths_plot(self, paths, var_threshold, cvar_threshold, horizon):
        plt.figure(figsize=(12, 7))
        
        # Plot sample paths (100 random)
        sample_indices = np.random.choice(len(paths), min(100, len(paths)), replace=False)
        for idx in sample_indices:
            cumulative = np.cumsum(paths[idx])
            plt.plot(range(horizon), cumulative, color='gray', alpha=0.1, linewidth=0.5)
        
        # Plot mean path
        mean_path = np.cumsum(paths.mean(axis=0))
        plt.plot(range(horizon), mean_path, color='blue', linewidth=2, label='Media', zorder=5)
        
        # Plot worst path
        worst_idx = np.argmin(paths.sum(axis=1))
        worst_cumulative = np.cumsum(paths[worst_idx])
        plt.plot(range(horizon), worst_cumulative, color='red', linewidth=2, label='Peor Caso', zorder=5)
        
        # VaR and CVaR lines at horizon
        plt.axhline(y=var_threshold, color='orange', linestyle='--', linewidth=2, label=f'VaR: {var_threshold:.4f}')
        plt.axhline(y=cvar_threshold, color='darkred', linestyle=':', linewidth=2, label=f'CVaR: {cvar_threshold:.4f}')
        
        plt.title('Simulación Monte Carlo: Trayectorias de Retorno')
        plt.xlabel('Días')
        plt.ylabel('Retorno Acumulado')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

risk_service = RiskService()
