"""
Excel Export Service
Servicio para exportar resultados de análisis a Excel
"""
import io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


class ExcelExportService:
    """Servicio para generar reportes Excel"""
    
    def _create_base_writer(self):
        """Crea el writer base"""
        output = io.BytesIO()
        return output
    
    def _setup_formats(self, workbook):
        """Configura formatos comunes"""
        return {
            'header': workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1}),
            'cell': workbook.add_format({'border': 1}),
            'title': workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1F497D'})
        }

    def _save_plot_to_buffer(self, fig):
        """Guarda un plot actual en un buffer"""
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=100)
        plt.close(fig)
        return img_buffer

    def export_single(self, results: dict, df_source: pd.DataFrame) -> io.BytesIO:
        """Exporta análisis de variable individual"""
        output = self._create_base_writer()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            fmt = self._setup_formats(workbook)
            
            # --- Sheet 1: Reporte Summary ---
            ws = workbook.add_worksheet('Reporte')
            ws.write('A1', 'Reporte de Análisis: Single Variable', fmt['title'])
            ws.write('A2', f'Fecha: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
            
            var_name = results['variable']
            
            # Table 1: Key Metrics
            ws.write('A4', 'Estadísticas Clave', fmt['header'])
            ws.write('B4', 'Valor', fmt['header'])
            
            row = 4
            metrics = []
            if results['type'] == 'numeric':
                stats = results['statistics']
                metrics = [
                    ('Observaciones', results['n_observations']),
                    ('Media', stats['central_tendency']['mean']),
                    ('Mediana', stats['central_tendency']['median']),
                    ('Desv. Std', stats['dispersion']['std']),
                    ('Min', stats['range']['min']),
                    ('Max', stats['range']['max']),
                    ('Asimetría', stats['shape']['skewness']),
                    ('Curtosis', stats['shape']['kurtosis'])
                ]
            else: 
                 metrics = [
                    ('Observaciones', results['n_observations']),
                    ('Categorías Únicas', results['n_unique']),
                    ('Moda', results['mode'])
                ]

            for name, value in metrics:
                ws.write(row, 0, name, fmt['cell'])
                ws.write(row, 1, value, fmt['cell'])
                row += 1
            
            # Generate Plot
            fig = plt.figure(figsize=(10, 6))
            if results['type'] == 'numeric':
                sns.histplot(df_source[var_name], kde=True, color='skyblue')
                plt.title(f'Distribución de {var_name}')
                plt.xlabel(var_name)
                plt.ylabel('Frecuencia')
            else:
                top_cats = df_source[var_name].value_counts().head(10)
                sns.barplot(x=top_cats.index, y=top_cats.values, palette='viridis')
                plt.title(f'Top 10 Categorías de {var_name}')
                plt.xlabel(var_name)
                plt.ylabel('Conteo')
                plt.xticks(rotation=45)
            
            plt.tight_layout()
            img_buffer = self._save_plot_to_buffer(fig)
            ws.insert_image('A15', 'chart.png', {'image_data': img_buffer})
            
            # --- Sheet 2: Data ---
            if df_source is not None:
                df_source.to_excel(writer, sheet_name='Datos Crudos', index=False)
                
            # --- Sheet 3: Details ---
            if results['type'] == 'numeric':
                 stats = results['statistics']
                 detailed_data = []
                 for cat, submetrics in stats.items():
                     if isinstance(submetrics, dict):
                         for k, v in submetrics.items():
                             detailed_data.append({'Categoría': cat, 'Métrica': k, 'Valor': v})
                 pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detalles Estadísticos', index=False)
                 
        output.seek(0)
        return output

    def export_dual(self, results: dict, df_source: pd.DataFrame) -> io.BytesIO:
        """Exporta análisis de dos variables"""
        output = self._create_base_writer()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            fmt = self._setup_formats(workbook)
            
            # --- Sheet 1: Reporte Summary ---
            ws = workbook.add_worksheet('Reporte')
            ws.write('A1', 'Reporte de Análisis: Dual Variables', fmt['title'])
            ws.write('A2', f'Fecha: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
            
            x_name = results['variable_x']
            y_name = results['variable_y']
            
            # Table 1: Key Metrics
            ws.write('A4', 'Métricas de Relación', fmt['header'])
            ws.write('B4', 'Valor', fmt['header'])
            
            row = 4
            metrics = []
            if 'correlation' in results:
                 metrics = [
                    ('Correlación', results['correlation']['coefficient']),
                    ('P-Value', results['correlation']['p_value']),
                    ('R-Cuadrado', results['correlation']['r_squared']),
                    ('Significancia', 'Sí' if results['correlation']['is_significant'] else 'No')
                ]
            if 'regression' in results:
                 metrics.extend([
                     ('Pendiente', results['regression']['slope']),
                     ('Intercepto', results['regression']['intercept']),
                     ('Ecuación', results['regression']['equation'])
                 ])

            for name, value in metrics:
                ws.write(row, 0, name, fmt['cell'])
                ws.write(row, 1, value, fmt['cell'])
                row += 1
            
            # Generate Plot
            fig = plt.figure(figsize=(10, 6))
            sns.scatterplot(x=df_source[x_name], y=df_source[y_name], alpha=0.6)
            
            if 'regression' in results:
                slope = results['regression']['slope']
                intercept = results['regression']['intercept']
                x_vals = np.array([df_source[x_name].min(), df_source[x_name].max()])
                y_vals = slope * x_vals + intercept
                plt.plot(x_vals, y_vals, color='red', linestyle='--', label='Tendencia')
                plt.legend()
                
            plt.title(f'Relación: {y_name} vs {x_name}')
            plt.xlabel(x_name)
            plt.ylabel(y_name)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            img_buffer = self._save_plot_to_buffer(fig)
            ws.insert_image('A15', 'chart.png', {'image_data': img_buffer})

            # --- Sheet 2: Data ---
            if df_source is not None:
                df_source.to_excel(writer, sheet_name='Datos Crudos', index=False)
                
            # --- Sheet 3: Details ---
            if results['correlation_type'] == 'full':
                res_full = results['results']
                rows = []
                for method, data in res_full.items():
                    rows.append({
                        'Método': data['name'],
                        'Coeficiente': data['coefficient'],
                        'P-Value': data['p_value'],
                        'Significativo': data['is_significant'],
                        'Interpretación': data['interpretation']
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name='Detalles Correlación', index=False)
                
        output.seek(0)
        return output

    def export_timeseries(self, results: dict, df_source: pd.DataFrame) -> io.BytesIO:
        """Exporta análisis de series temporales"""
        output = self._create_base_writer()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            fmt = self._setup_formats(workbook)
            
            # --- Sheet 1: Reporte Summary ---
            ws = workbook.add_worksheet('Reporte')
            ws.write('A1', 'Reporte de Análisis: Time Series (ARIMA)', fmt['title'])
            ws.write('A2', f'Fecha: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}')
            
            # Table 1: Model Metrics
            ws.write('A4', 'Métricas del Modelo', fmt['header'])
            ws.write('B4', 'Valor', fmt['header'])
            
            row = 4
            metrics = [
                ('Orden (p,d,q)', str(results['model_params']['order'])),
                ('AIC', results['model_params']['aic']),
                ('RMSE', results['metrics']['rmse']),
                ('MAE', results['metrics']['mae']),
                ('Estacionariedad', 'Sí' if results['stationarity']['is_stationary'] else 'No')
            ]
            
            for name, value in metrics:
                ws.write(row, 0, name, fmt['cell'])
                ws.write(row, 1, value, fmt['cell'])
                row += 1
                
            # Full Summary
            ws.write('D4', 'Resumen del Modelo', fmt['header'])
            summary_lines = results.get('model_summary', '').split('\n')
            summ_row = 5
            for line in summary_lines:
                ws.write(summ_row, 3, line)
                summ_row += 1
            
            # Generate Plot
            fig = plt.figure(figsize=(12, 6))
            
            # Historical
            hist_dates = [pd.to_datetime(d) for d in results['historical_data']['dates']]
            plt.plot(hist_dates, results['historical_data']['values'], label='Histórico', color='blue')
            plt.plot(hist_dates, results['historical_data']['fitted_values'], label='Ajuste', color='green', linestyle='--')
            
            # Forecast
            forecast_dates = [pd.to_datetime(d) for d in results['forecast']['dates']]
            plt.plot(forecast_dates, results['forecast']['values'], label='Pronóstico', color='orange')
            plt.fill_between(forecast_dates, results['forecast']['lower_bound'], results['forecast']['upper_bound'], color='orange', alpha=0.2, label='IC 95%')
            
            plt.title('Análisis y Pronóstico ARIMA')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            img_buffer = self._save_plot_to_buffer(fig)
            ws.insert_image('A15', 'chart.png', {'image_data': img_buffer})
            
            # --- Sheet 2: Data ---
            if df_source is not None:
                df_source.to_excel(writer, sheet_name='Datos Crudos', index=False)
            
            # --- Sheet 3: Forecast Data ---
            forecast_df = pd.DataFrame({
                "Fecha": results['forecast']['dates'],
                "Pronóstico": results['forecast']['values'],
                "Límite Inferior": results['forecast']['lower_bound'],
                "Límite Superior": results['forecast']['upper_bound']
            })
            forecast_df.to_excel(writer, sheet_name='Datos Pronóstico', index=False)

        output.seek(0)
        return output
