"""
Analizador de Simulación Monte Carlo para proyecciones financieras
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from scipy import stats


class MonteCarloAnalyzer:
    """
    Realiza simulaciones Monte Carlo usando Movimiento Browniano Geométrico (GBM)
    para proyecciones de variables financieras.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Inicializa el analizador con datos históricos
        
        Args:
            data: DataFrame con datos históricos
        """
        self.data = data
    
    def estimate_parameters(self, column: str) -> Tuple[float, float]:
        """
        Estima drift (tendencia) y volatilidad de los datos históricos
        
        Args:
            column: Nombre de la columna a analizar
            
        Returns:
            Tuple (drift, volatility)
        """
        # Obtener los valores
        values = self.data[column].dropna().values
        
        # Calcular retornos logarítmicos
        log_returns = np.diff(np.log(values))
        
        # Drift: media de los retornos
        drift = np.mean(log_returns)
        
        # Volatilidad: desviación estándar de los retornos
        volatility = np.std(log_returns)
        
        return drift, volatility
    
    def simulate_gbm(
        self,
        column: str,
        iterations: int = 1000,
        horizon: int = 30,
        drift: float = None,
        volatility: float = None
    ) -> Dict[str, Any]:
        """
        Realiza simulación Monte Carlo usando Movimiento Browniano Geométrico
        
        Args:
            column: Columna objetivo a proyectar
            iterations: Número de simulaciones a realizar
            horizon: Horizonte temporal (número de períodos futuros)
            drift: Drift manual (si None, se estima)
            volatility: Volatilidad manual (si None, se estima)
            
        Returns:
            Diccionario con resultados de la simulación
        """
        # Obtener valor inicial (último valor de la serie)
        S0 = self.data[column].dropna().iloc[-1]
        
        # Estimar parámetros si no se proporcionan
        if drift is None or volatility is None:
            estimated_drift, estimated_volatility = self.estimate_parameters(column)
            drift = drift if drift is not None else estimated_drift
            volatility = volatility if volatility is not None else estimated_volatility
        
        # Matriz para almacenar las simulaciones
        simulations = np.zeros((iterations, horizon + 1))
        simulations[:, 0] = S0
        
        # Realizar simulaciones
        dt = 1  # Incremento de tiempo (asumimos períodos unitarios)
        
        for i in range(iterations):
            for t in range(1, horizon + 1):
                # Generar shock aleatorio
                epsilon = np.random.standard_normal()
                
                # Ecuación de GBM: S_t = S_{t-1} * exp((drift - 0.5*vol^2)*dt + vol*sqrt(dt)*epsilon)
                simulations[i, t] = simulations[i, t-1] * np.exp(
                    (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * epsilon
                )
        
        # Calcular estadísticas
        final_values = simulations[:, -1]
        
        # Percentiles para bandas de confianza
        percentiles = [5, 25, 50, 75, 95]
        confidence_bands = {}
        
        for p in percentiles:
            band = np.percentile(simulations, p, axis=0).tolist()
            confidence_bands[f'p{p}'] = band
        
        # Métricas financieras
        expected_return = np.mean(final_values)
        median_return = np.median(final_values)
        std_return = np.std(final_values)
        
        # Value at Risk (VaR) al 95% de confianza
        var_95 = np.percentile(final_values, 5)
        
        # Probabilidad de ganancia (valor final > valor inicial)
        prob_profit = np.sum(final_values > S0) / iterations
        
        # Distribución final
        hist, bin_edges = np.histogram(final_values, bins=50)
        
        return {
            'simulations': simulations.tolist(),
            'confidence_bands': confidence_bands,
            'metrics': {
                'initial_value': float(S0),
                'expected_final_value': float(expected_return),
                'median_final_value': float(median_return),
                'std_final_value': float(std_return),
                'var_95': float(var_95),
                'probability_profit': float(prob_profit),
                'drift': float(drift),
                'volatility': float(volatility),
                'horizon': horizon,
                'iterations': iterations
            },
            'final_distribution': {
                'values': final_values.tolist(),
                'histogram': {
                    'counts': hist.tolist(),
                    'bin_edges': bin_edges.tolist()
                }
            }
        }
    
    def analyze(
        self,
        target_column: str,
        iterations: int = 1000,
        horizon: int = 30,
        drift: float = None,
        volatility: float = None
    ) -> Dict[str, Any]:
        """
        Método principal de análisis
        
        Args:
            target_column: Columna objetivo
            iterations: Número de simulaciones
            horizon: Horizonte temporal
            drift: Drift opcional
            volatility: Volatilidad opcional
            
        Returns:
            Resultados completos del análisis
        """
        try:
            # Validar columna
            if target_column not in self.data.columns:
                raise ValueError(f"Columna '{target_column}' no encontrada en el dataset")
            
            # Validar que hay suficientes datos
            valid_data = self.data[target_column].dropna()
            if len(valid_data) < 2:
                raise ValueError(f"Datos insuficientes en '{target_column}' para análisis")
            
            # Realizar simulación
            results = self.simulate_gbm(
                column=target_column,
                iterations=iterations,
                horizon=horizon,
                drift=drift,
                volatility=volatility
            )
            
            # Agregar interpretación
            metrics = results['metrics']
            interpretation = self._generate_interpretation(metrics)
            results['interpretation'] = interpretation
            
            return {
                'success': True,
                **results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_interpretation(self, metrics: Dict[str, Any]) -> str:
        """
        Genera interpretación en español de los resultados
        
        Args:
            metrics: Métricas calculadas
            
        Returns:
            Texto de interpretación
        """
        initial = metrics['initial_value']
        expected = metrics['expected_final_value']
        var_95 = metrics['var_95']
        prob_profit = metrics['probability_profit']
        
        change = ((expected - initial) / initial) * 100
        risk = ((initial - var_95) / initial) * 100
        
        interpretation = f"""
Simulación Monte Carlo completada con {metrics['iterations']} iteraciones para {metrics['horizon']} períodos.

Valor Inicial: {initial:.2f}
Valor Esperado Final: {expected:.2f} (cambio de {change:+.2f}%)
Valor en Riesgo (VaR 95%): {var_95:.2f} (riesgo máximo del {risk:.2f}% con 95% de confianza)

Probabilidad de Ganancia: {prob_profit*100:.1f}%

Parámetros estimados:
- Drift (tendencia): {metrics['drift']:.6f}
- Volatilidad: {metrics['volatility']:.6f}
"""
        
        if prob_profit > 0.7:
            interpretation += "\n✅ Alta probabilidad de resultados positivos."
        elif prob_profit > 0.5:
            interpretation += "\n⚠️ Probabilidad moderada de resultados positivos."
        else:
            interpretation += "\n⚠️ Alta incertidumbre o riesgo de pérdida."
        
        return interpretation.strip()
