import xlsxwriter
import io
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime

class ReportGenerator:
    """
    Genera informes en formato Excel para los análisis del sistema.
    """
    
    @staticmethod
    def generate_ab_test_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados de A/B Testing.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Resultados A-B Test')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#6366f1'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#f1f5f9', 'border': 1})
        metric_fmt = workbook.add_format({'bold': True, 'size': 12})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        highlight_success = workbook.add_format({'bg_color': '#dcfce7', 'font_color': '#166534', 'bold': True})
        highlight_fail = workbook.add_format({'bg_color': '#fee2e2', 'font_color': '#991b1b', 'bold': True})
        
        # Título
        sheet.write('A1', 'Informe de Análisis A/B Testing', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Métricas principales
        sheet.write('A4', 'Resumen de Resultados', header_fmt)
        sheet.write('A5', 'Dataset ID:', label_fmt)
        sheet.write('B5', data.get('dataset_id', 'N/A'))
        
        sheet.write('A6', 'Tipo de Análisis:', label_fmt)
        sheet.write('B6', data.get('analysis_type', 'N/A').capitalize())
        
        # Significancia
        is_significant = data.get('is_significant', False)
        sheet.write('A7', '¿Es Estadísticamente Significativo?:', label_fmt)
        sheet.write('B7', 'SÍ' if is_significant else 'NO', highlight_success if is_significant else highlight_fail)
        
        sheet.write('A8', 'P-Valor:', label_fmt)
        sheet.write('B8', data.get('p_value', 1.0))
        
        # Métricas según tipo de análisis
        row = 10
        if data.get('analysis_type') == 'categorical':
            sheet.write(f'A{row}', 'Métricas Categóricas', header_fmt)
            row += 1
            sheet.write(f'A{row}', 'Tasa Control:', label_fmt)
            sheet.write(f'B{row}', f"{data.get('control_signup_rate', 0):.2%}")
            row += 1
            sheet.write(f'A{row}', 'Tasa Treatment:', label_fmt)
            sheet.write(f'B{row}', f"{data.get('treatment_signup_rate', 0):.2%}")
            row += 1
            sheet.write(f'A{row}', 'Lift:', label_fmt)
            sheet.write(f'B{row}', f"{data.get('lift_percentage', 0):.2f}%")
        else:
            sheet.write(f'A{row}', 'Métricas Continuas', header_fmt)
            row += 1
            sheet.write(f'A{row}', 'Media Control:', label_fmt)
            sheet.write(f'B{row}', data.get('control_mean', 0))
            row += 1
            sheet.write(f'A{row}', 'Media Treatment:', label_fmt)
            sheet.write(f'B{row}', data.get('treatment_mean', 0))
            row += 1
            sheet.write(f'A{row}', 'Diferencia:', label_fmt)
            sheet.write(f'B{row}', data.get('difference', 0))
            row += 1
            sheet.write(f'A{row}', 'Cambio %:', label_fmt)
            sheet.write(f'B{row}', f"{data.get('percentage_change', 0):.2f}%")
            
        # Interpretación
        row += 2
        sheet.write(f'A{row}', 'Interpretación', header_fmt)
        sheet.merge_range(f'A{row+1}:E{row+5}', data.get('interpretation', ''), workbook.add_format({'text_wrap': True, 'align': 'top'}))
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                # El string suele venir como 'data:image/png;base64,...'
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                sheet.insert_image(f'G{img_row}', f'chart_{i}.png', {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20  # Dejar espacio para la siguiente imagen
        
        workbook.close()
        output.seek(0)
        return output

    @staticmethod
    def generate_risk_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados de análisis de riesgo (VaR/CVaR, Maximum Drawdown, Backtesting).
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Análisis de Riesgo')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#dc2626'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#fef2f2', 'border': 1})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        metric_fmt = workbook.add_format({'num_format': '0.0000', 'bold': True})
        percent_fmt = workbook.add_format({'num_format': '0.00%', 'bold': True})
        date_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        
        # Título
        sheet.write('A1', 'Informe de Análisis de Riesgo', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Información básica
        sheet.write('A4', 'Configuración del Análisis', header_fmt)
        sheet.write('A5', 'Dataset ID:', label_fmt)
        sheet.write('B5', data.get('dataset_id', 'N/A'))
        
        row = 7
        
        # VaR/CVaR Analysis
        if 'var' in data or 'cvar' in data:
            sheet.write(f'A{row}', 'Análisis VaR/CVaR', header_fmt)
            row += 1
            
            if 'var' in data:
                sheet.write(f'A{row}', 'Value at Risk (VaR):', label_fmt)
                sheet.write(f'B{row}', data.get('var', 0), percent_fmt)
                row += 1
            
            if 'cvar' in data:
                sheet.write(f'A{row}', 'Conditional VaR (CVaR):', label_fmt)
                sheet.write(f'B{row}', data.get('cvar', 0), percent_fmt)
                row += 1
            
            if 'confidence_level' in data:
                sheet.write(f'A{row}', 'Nivel de Confianza:', label_fmt)
                sheet.write(f'B{row}', data.get('confidence_level', 0), percent_fmt)
                row += 1
            
            if 'horizon' in data:
                sheet.write(f'A{row}', 'Horizonte Temporal:', label_fmt)
                sheet.write(f'B{row}', f"{data.get('horizon', 0)} días")
                row += 1
            
            if 'method' in data:
                sheet.write(f'A{row}', 'Método:', label_fmt)
                sheet.write(f'B{row}', data.get('method', 'N/A').title())
                row += 1
            
            row += 1
        
        # Maximum Drawdown Analysis
        if 'max_drawdown' in data:
            sheet.write(f'A{row}', 'Análisis Maximum Drawdown', header_fmt)
            row += 1
            
            sheet.write(f'A{row}', 'Maximum Drawdown:', label_fmt)
            sheet.write(f'B{row}', data.get('max_drawdown', 0), percent_fmt)
            row += 1
            
            if 'peak_date' in data:
                sheet.write(f'A{row}', 'Fecha del Peak:', label_fmt)
                sheet.write(f'B{row}', data.get('peak_date', 'N/A'))
                row += 1
            
            if 'peak_value' in data:
                sheet.write(f'A{row}', 'Valor del Peak:', label_fmt)
                sheet.write(f'B{row}', data.get('peak_value', 0), metric_fmt)
                row += 1
            
            if 'trough_date' in data:
                sheet.write(f'A{row}', 'Fecha del Trough:', label_fmt)
                sheet.write(f'B{row}', data.get('trough_date', 'N/A'))
                row += 1
            
            if 'trough_value' in data:
                sheet.write(f'A{row}', 'Valor del Trough:', label_fmt)
                sheet.write(f'B{row}', data.get('trough_value', 0), metric_fmt)
                row += 1
            
            if 'recovery_date' in data:
                sheet.write(f'A{row}', 'Fecha de Recuperación:', label_fmt)
                sheet.write(f'B{row}', data.get('recovery_date', 'No recuperado'))
                row += 1
            
            if 'recovery_days' in data and data.get('recovery_days'):
                sheet.write(f'A{row}', 'Días para Recuperación:', label_fmt)
                sheet.write(f'B{row}', data.get('recovery_days', 0))
                row += 1
            
            row += 1
        
        # Backtesting Analysis
        if 'total_observations' in data:
            sheet.write(f'A{row}', 'Análisis de Backtesting', header_fmt)
            row += 1
            
            sheet.write(f'A{row}', 'Observaciones Totales:', label_fmt)
            sheet.write(f'B{row}', data.get('total_observations', 0))
            row += 1
            
            sheet.write(f'A{row}', 'Número de Violaciones:', label_fmt)
            sheet.write(f'B{row}', data.get('num_violations', 0))
            row += 1
            
            sheet.write(f'A{row}', 'Tasa de Violación:', label_fmt)
            sheet.write(f'B{row}', data.get('violation_rate', 0), percent_fmt)
            row += 1
            
            sheet.write(f'A{row}', 'Tasa Esperada:', label_fmt)
            sheet.write(f'B{row}', data.get('expected_rate', 0), percent_fmt)
            row += 1
            
            sheet.write(f'A{row}', 'Test de Kupiec (LR Stat):', label_fmt)
            sheet.write(f'B{row}', data.get('kupiec_lr_stat', 0), metric_fmt)
            row += 1
            
            sheet.write(f'A{row}', 'P-Valor:', label_fmt)
            sheet.write(f'B{row}', data.get('kupiec_p_value', 0), metric_fmt)
            row += 1
            
            test_passed = data.get('test_passed', False)
            sheet.write(f'A{row}', 'Test Aprobado:', label_fmt)
            sheet.write(f'B{row}', 'SÍ' if test_passed else 'NO', 
                       workbook.add_format({'bg_color': '#dcfce7', 'font_color': '#166534', 'bold': True}) if test_passed 
                       else workbook.add_format({'bg_color': '#fee2e2', 'font_color': '#991b1b', 'bold': True}))
            row += 1
            
            row += 1
        
        # Interpretación
        if 'interpretation' in data:
            sheet.write(f'A{row}', 'Interpretación', header_fmt)
            sheet.merge_range(f'A{row+1}:E{row+6}', data.get('interpretation', ''), 
                              workbook.add_format({'text_wrap': True, 'align': 'top'}))
            row += 7
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                sheet.insert_image(f'G{img_row}', f'risk_chart_{i}.png', 
                                   {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20
        
        workbook.close()
        output.seek(0)
        return output

    @staticmethod
    def generate_monte_carlo_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados de simulación Monte Carlo.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Monte Carlo')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#7c3aed'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#f3f4f6', 'border': 1})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        metric_fmt = workbook.add_format({'num_format': '0.0000', 'bold': True})
        percent_fmt = workbook.add_format({'num_format': '0.00%', 'bold': True})
        
        # Título
        sheet.write('A1', 'Informe de Simulación Monte Carlo', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Información básica
        sheet.write('A4', 'Configuración de la Simulación', header_fmt)
        sheet.write('A5', 'Dataset ID:', label_fmt)
        sheet.write('B5', data.get('dataset_id', 'N/A'))
        
        # Métricas principales
        metrics = data.get('metrics', {})
        if metrics:
            sheet.write('A7', 'Métricas de la Simulación', header_fmt)
            row = 8
            
            if 'initial_value' in metrics:
                sheet.write(f'A{row}', 'Valor Inicial:', label_fmt)
                sheet.write(f'B{row}', metrics.get('initial_value', 0), metric_fmt)
                row += 1
            
            if 'expected_final_value' in metrics:
                sheet.write(f'A{row}', 'Valor Final Esperado:', label_fmt)
                sheet.write(f'B{row}', metrics.get('expected_final_value', 0), metric_fmt)
                row += 1
            
            if 'median_final_value' in metrics:
                sheet.write(f'A{row}', 'Valor Final Mediano:', label_fmt)
                sheet.write(f'B{row}', metrics.get('median_final_value', 0), metric_fmt)
                row += 1
            
            if 'std_final_value' in metrics:
                sheet.write(f'A{row}', 'Desviación Estándar:', label_fmt)
                sheet.write(f'B{row}', metrics.get('std_final_value', 0), metric_fmt)
                row += 1
            
            if 'var_95' in metrics:
                sheet.write(f'A{row}', 'VaR 95%:', label_fmt)
                sheet.write(f'B{row}', metrics.get('var_95', 0), metric_fmt)
                row += 1
            
            if 'probability_profit' in metrics:
                sheet.write(f'A{row}', 'Probabilidad de Ganancia:', label_fmt)
                sheet.write(f'B{row}', metrics.get('probability_profit', 0), percent_fmt)
                row += 1
            
            if 'iterations' in metrics:
                sheet.write(f'A{row}', 'Número de Iteraciones:', label_fmt)
                sheet.write(f'B{row}', metrics.get('iterations', 0))
                row += 1
            
            if 'horizon' in metrics:
                sheet.write(f'A{row}', 'Horizonte Temporal:', label_fmt)
                sheet.write(f'B{row}', f"{metrics.get('horizon', 0)} períodos")
                row += 1
            
            if 'drift' in metrics:
                sheet.write(f'A{row}', 'Drift (Tendencia):', label_fmt)
                sheet.write(f'B{row}', metrics.get('drift', 0), metric_fmt)
                row += 1
            
            if 'volatility' in metrics:
                sheet.write(f'A{row}', 'Volatilidad:', label_fmt)
                sheet.write(f'B{row}', metrics.get('volatility', 0), metric_fmt)
                row += 1
            
            row += 1
        
        # Bandas de confianza
        confidence_bands = data.get('confidence_bands', {})
        if confidence_bands:
            sheet.write(f'A{row}', 'Bandas de Confianza (Valores Finales)', header_fmt)
            row += 1
            
            percentiles = ['p5', 'p25', 'p50', 'p75', 'p95']
            percentile_names = ['5%', '25%', '50% (Mediana)', '75%', '95%']
            
            for i, (p_key, p_name) in enumerate(zip(percentiles, percentile_names)):
                if p_key in confidence_bands:
                    final_values = confidence_bands[p_key]
                    if final_values:
                        sheet.write(f'A{row}', f'Percentil {p_name}:', label_fmt)
                        sheet.write(f'B{row}', final_values[-1], metric_fmt)  # Último valor (final)
                        row += 1
            
            row += 1
        
        # Interpretación
        if 'interpretation' in data:
            sheet.write(f'A{row}', 'Interpretación', header_fmt)
            sheet.merge_range(f'A{row+1}:E{row+6}', data.get('interpretation', ''), 
                              workbook.add_format({'text_wrap': True, 'align': 'top'}))
            row += 7
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                sheet.insert_image(f'G{img_row}', f'monte_carlo_chart_{i}.png', 
                                   {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20
        
        workbook.close()
        output.seek(0)
        return output

    @staticmethod
    def generate_scm_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados del Método de Control Sintético.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Control Sintético')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#8b5cf6'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#f5f3ff', 'border': 1})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        
        # Título
        sheet.write('A1', 'Informe de Control Sintético (SCM)', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Información del Análisis
        sheet.write('A4', 'Detalles del Análisis', header_fmt)
        sheet.write('A5', 'Unidad Tratada:', label_fmt)
        sheet.write('B5', data.get('treated_unit', 'N/A'))
        sheet.write('A6', 'Momento del Tratamiento:', label_fmt)
        sheet.write('B6', data.get('treatment_time', 'N/A'))
        sheet.write('A7', 'Dataset ID:', label_fmt)
        sheet.write('B7', data.get('dataset_id', 'N/A'))
        
        # Métricas
        sheet.write('A9', 'Métricas de Impacto', header_fmt)
        sheet.write('A10', 'Efecto Promedio:', label_fmt)
        sheet.write('B10', data.get('average_treatment_effect', 0))
        sheet.write('A11', 'Efecto Post-Tratamiento Total:', label_fmt)
        sheet.write('B11', data.get('post_treatment_effect', 0))
        sheet.write('A12', 'RMSPE Pre-Tratamiento:', label_fmt)
        sheet.write('B12', data.get('pre_treatment_rmspe', 0))
        
        # Pesos
        sheet.write('A14', 'Pesos de Unidades de Control', header_fmt)
        weights = data.get('weights', {})
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        row = 15
        for unit, weight in sorted_weights:
            if weight > 0.001:
                sheet.write(f'A{row}', unit, label_fmt)
                sheet.write(f'B{row}', f"{weight:.2%}")
                row += 1
        
        # Interpretación
        row += 2
        sheet.write(f'A{row}', 'Interpretación', header_fmt)
        sheet.merge_range(f'A{row+1}:E{row+6}', data.get('interpretation', '').replace('**', ''), workbook.add_format({'text_wrap': True, 'align': 'top'}))
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                # Ajustar tamaño para que quepan bien
                sheet.insert_image(f'G{img_row}', f'scm_chart_{i}.png', {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20
        
        workbook.close()
        output.seek(0)
        return output

    @staticmethod
    def generate_regression_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados de Curve Fitting / Regresión.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Regresión')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#10b981'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#ecfdf5', 'border': 1})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        param_fmt = workbook.add_format({'num_format': '0.0000', 'align': 'right'})
        metric_fmt = workbook.add_format({'num_format': '0.0000', 'bold': True})
        
        # Título
        sheet.write('A1', 'Informe de Regresión / Curve Fitting', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Información básica
        sheet.write('A4', 'Configuración del Análisis', header_fmt)
        sheet.write('A5', 'Dataset ID:', label_fmt)
        sheet.write('B5', data.get('dataset_id', 'N/A'))
        sheet.write('A6', 'Función:', label_fmt)
        sheet.write('B6', data.get('function_name', 'N/A'))
        sheet.write('A7', 'Motor de Optimización:', label_fmt)
        sheet.write('B7', data.get('engine_used', 'N/A'))
        
        # Métricas de calidad
        sheet.write('A9', 'Métricas de Ajuste', header_fmt)
        sheet.write('A10', 'R² (Coeficiente de Determinación):', label_fmt)
        sheet.write('B10', data.get('r_squared', 0), metric_fmt)
        sheet.write('A11', 'RMSE (Error Cuadrático Medio):', label_fmt)
        sheet.write('B11', data.get('rmse', 0), metric_fmt)
        
        # Parámetros ajustados
        sheet.write('A13', 'Parámetros Ajustados', header_fmt)
        sheet.write('B13', 'Valor', header_fmt)
        sheet.write('C13', 'Error', header_fmt)
        
        parameters = data.get('parameters', {})
        errors = data.get('errors', {})
        row = 14
        for param_name in sorted(parameters.keys()):
            sheet.write(f'A{row}', param_name, label_fmt)
            sheet.write(f'B{row}', parameters.get(param_name, 0), param_fmt)
            sheet.write(f'C{row}', errors.get(param_name, 0), param_fmt)
            row += 1
        
        # Interpretación
        row += 1
        sheet.write(f'A{row}', 'Interpretación', header_fmt)
        sheet.merge_range(f'A{row+1}:E{row+4}', data.get('interpretation', ''), 
                          workbook.add_format({'text_wrap': True, 'align': 'top'}))
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                sheet.insert_image(f'G{img_row}', f'regression_chart_{i}.png', 
                                   {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20
        
        workbook.close()
        output.seek(0)
        return output

    @staticmethod
    def generate_clustering_report(data: Dict[str, Any], chart_images: List[str]) -> io.BytesIO:
        """
        Genera un Excel con los resultados de Clustering.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Clustering')
        
        # Estilos
        title_fmt = workbook.add_format({'bold': True, 'size': 16, 'font_color': '#f59e0b'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#fef3c7', 'border': 1})
        label_fmt = workbook.add_format({'font_color': '#64748b'})
        metric_fmt = workbook.add_format({'num_format': '0.0000', 'bold': True})
        percent_fmt = workbook.add_format({'num_format': '0.00%'})
        
        # Título
        sheet.write('A1', 'Informe de Clustering', title_fmt)
        sheet.write('A2', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', label_fmt)
        
        # Información básica
        sheet.write('A4', 'Configuración del Análisis', header_fmt)
        sheet.write('A5', 'Dataset ID:', label_fmt)
        sheet.write('B5', data.get('dataset_id', 'N/A'))
        sheet.write('A6', 'Algoritmo:', label_fmt)
        sheet.write('B6', data.get('algorithm', 'N/A').upper())
        sheet.write('A7', 'Número de Clusters:', label_fmt)
        sheet.write('B7', data.get('n_clusters', 0))
        
        if data.get('algorithm') == 'dbscan':
            sheet.write('A8', 'Puntos de Ruido:', label_fmt)
            sheet.write('B8', data.get('n_noise', 0))
            sheet.write('A9', 'Epsilon:', label_fmt)
            sheet.write('B9', data.get('eps', 0))
            sheet.write('A10', 'Min Samples:', label_fmt)
            sheet.write('B10', data.get('min_samples', 0))
            metric_row = 12
        else:
            sheet.write('A8', 'Inercia:', label_fmt)
            sheet.write('B8', data.get('inertia', 0), metric_fmt)
            metric_row = 10
        
        # Métricas de calidad
        sheet.write(f'A{metric_row}', 'Métricas de Calidad', header_fmt)
        sheet.write(f'A{metric_row+1}', 'Silhouette Score:', label_fmt)
        sheet.write(f'B{metric_row+1}', data.get('silhouette_score', 0), metric_fmt)
        sheet.write(f'A{metric_row+2}', 'Davies-Bouldin Score:', label_fmt)
        sheet.write(f'B{metric_row+2}', data.get('davies_bouldin_score', 0), metric_fmt)
        
        # Estadísticas por cluster
        stats_row = metric_row + 4
        sheet.write(f'A{stats_row}', 'Estadísticas por Cluster', header_fmt)
        sheet.write(f'B{stats_row}', 'Tamaño', header_fmt)
        sheet.write(f'C{stats_row}', 'Porcentaje', header_fmt)
        
        cluster_stats = data.get('cluster_stats', [])
        row = stats_row + 1
        for stat in cluster_stats:
            cluster_id = stat.get('cluster_id', 0)
            cluster_name = f"Ruido (ID={cluster_id})" if stat.get('is_noise') else f"Cluster {cluster_id}"
            sheet.write(f'A{row}', cluster_name, label_fmt)
            sheet.write(f'B{row}', stat.get('size', 0))
            sheet.write(f'C{row}', stat.get('percentage', 0) / 100, percent_fmt)
            row += 1
        
        # Imágenes de los gráficos
        img_row = 4
        for i, img_data in enumerate(chart_images):
            if img_data:
                if ',' in img_data:
                    header, encoded = img_data.split(',', 1)
                else:
                    encoded = img_data
                
                image_bytes = io.BytesIO(base64.b64decode(encoded))
                sheet.insert_image(f'E{img_row}', f'clustering_chart_{i}.png', 
                                   {'image_data': image_bytes, 'x_scale': 0.6, 'y_scale': 0.6})
                img_row += 20
        
        workbook.close()
        output.seek(0)
        return output
