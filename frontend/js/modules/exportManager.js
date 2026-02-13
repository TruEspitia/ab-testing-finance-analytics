// =============================================
// Export Manager - Generación de Excel con Gráficos
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { exportToExcel } from '../api/client.js';

/**
 * Maneja la exportación a Excel capturando los gráficos actuales
 */
export async function handleExportExcel(type) {
    let data;
    if (type === 'ab_test') {
        data = appState.lastResults;
    } else if (type === 'scm') {
        data = appState.lastSCMResults;
    } else if (type === 'regression') {
        data = appState.lastRegressionResults;
    } else if (type === 'clustering') {
        data = appState.lastClusteringResults;
    } else if (type === 'monte_carlo') {
        data = appState.lastMonteCarloResults;
    } else if (type === 'risk') {
        data = appState.lastRiskResults;
    }

    // Debug logging
    console.log('Export type:', type);
    console.log('AppState lastRiskResults:', appState.lastRiskResults);
    console.log('Data to export:', data);

    if (!data) {
        showToast('No hay resultados para exportar. Ejecuta primero un análisis de riesgo.', 'error');
        return;
    }

    try {
        setLoading(true);
        const charts = [];

        // Capturar imágenes de Plotly si corresponde
        if (typeof Plotly !== 'undefined') {
            if (type === 'ab_test') {
                const img = await Plotly.toImage('plotlyChart', { format: 'png', width: 800, height: 500 });
                charts.push(img);
            } else if (type === 'scm') {
                const img1 = await Plotly.toImage('scmTimeSeriesChart', { format: 'png', width: 800, height: 500 });
                const img2 = await Plotly.toImage('scmWeightsChart', { format: 'png', width: 800, height: 500 });
                charts.push(img1, img2);
            } else if (type === 'regression') {
                const img = await Plotly.toImage('regressionPlotlyChart', { format: 'png', width: 800, height: 500 });
                charts.push(img);
            } else if (type === 'clustering' && data.plot_base64) {
                // El clustering ya trae la imagen base64 del backend
                charts.push(data.plot_base64);
            } else if (type === 'risk') {
                // Capturar gráficos del Risk Calculator
                // En Risk Calculator las imágenes vienen directamente en base64 desde el backend
                const riskResultsContainer = document.getElementById('riskResultsContent');
                if (riskResultsContainer) {
                    const images = riskResultsContainer.querySelectorAll('img');
                    images.forEach(img => {
                        if (img.src && img.src.startsWith('data:image/png;base64,')) {
                            charts.push(img.src);
                        }
                    });
                }
            } else if (type === 'monte_carlo') {
                // Capturar gráficos de la simulación Monte Carlo (Plotly)
                try {
                    const img1 = await Plotly.toImage('mcTrajectoriesPlot', { format: 'png', width: 800, height: 500 });
                    const img2 = await Plotly.toImage('mcDistributionPlot', { format: 'png', width: 800, height: 500 });
                    charts.push(img1, img2);
                } catch (e) {
                    console.error('Error capturing Monte Carlo charts:', e);
                }
            }
        }

        const blob = await exportToExcel(type, data, charts);
        downloadBlob(blob, getFilename(type));
        showToast('Excel generado exitosamente', 'success');
    } catch (error) {
        showToast('Error al exportar: ' + error.message, 'error');
        console.error('Export error:', error);
    } finally {
        setLoading(false);
    }
}

/**
 * Dispara la descarga del archivo binario
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Determina el nombre del archivo según el análisis
 */
function getFilename(type) {
    const names = {
        'ab_test': 'AB_Test_Report.xlsx',
        'scm': 'SCM_Report.xlsx',
        'regression': 'Regression_Report.xlsx',
        'clustering': 'Clustering_Report.xlsx',
        'monte_carlo': 'Monte_Carlo_Report.xlsx',
        'risk': 'Risk_Analysis_Report.xlsx'
    };
    return names[type] || 'Finance_Analytics_Report.xlsx';
}
