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
