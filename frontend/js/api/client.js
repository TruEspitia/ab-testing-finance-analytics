// =============================================
// Cliente API - Todas las llamadas al backend
// =============================================

import { API_BASE_URL } from '../core/config.js';

/**
 * Sube un archivo al servidor
 */
export async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

/**
 * Sube múltiples archivos al servidor
 */
export async function uploadBatchFiles(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    const response = await fetch(`${API_BASE_URL}/upload-batch`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

/**
 * Obtiene la lista de datasets
 */
export async function fetchDatasets() {
    const response = await fetch(`${API_BASE_URL}/datasets`);
    return await response.json();
}

/**
 * Obtiene preview de un dataset
 */
export async function fetchDatasetPreview(datasetId, nRows = 100) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/preview?n_rows=${nRows}`);
    return await response.json();
}

/**
 * Obtiene información de un dataset específico
 */
export async function fetchDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}`);
    return await response.json();
}

/**
 * Elimina un dataset
 */
export async function deleteDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}`, {
        method: 'DELETE'
    });
    return await response.json();
}

/**
 * Valida un dataset
 */
export async function validateDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/validate`);
    return await response.json();
}

/**
 * Obtiene información de columnas
 */
export async function fetchDatasetColumns(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/columns`);
    return await response.json();
}

/**
 * Obtiene estadísticas del sistema
 */
export async function fetchStats() {
    const response = await fetch(`${API_BASE_URL}/stats`);
    return await response.json();
}

/**
 * Obtiene las funciones matemáticas disponibles para regresión
 */
export async function fetchAvailableFunctions() {
    const response = await fetch(`${API_BASE_URL}/functions`);
    return await response.json();
}

/**
 * Ejecuta análisis A/B
 */
export async function runAnalysis(config) {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Ejecuta regresión/curve fitting
 */
export async function runRegression(config) {
    const response = await fetch(`${API_BASE_URL}/regression`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Ejecuta análisis de clustering
 */
export async function runClustering(config) {
    const response = await fetch(`${API_BASE_URL}/clustering`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Genera el gráfico del codo
 */
export async function fetchElbowPlot(config) {
    const response = await fetch(`${API_BASE_URL}/clustering/elbow-plot`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Ejecuta simulación Monte Carlo
 */
export async function runMonteCarlo(config) {
    const response = await fetch(`${API_BASE_URL}/analyze/monte-carlo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Ejecuta cálculo de riesgo (VaR)
 */
export async function runRiskAnalysis(config) {
    const response = await fetch(`${API_BASE_URL}/risk/var`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Envía datos para exportación a Excel
 */
export async function exportToExcel(type, data, charts) {
    const response = await fetch(`${API_BASE_URL}/export/excel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            analysis_type: type,
            data: data,
            charts: charts
        })
    });

    if (!response.ok) {
        throw new Error('Error en el servidor al generar el Excel');
    }

    return await response.blob();
}
