// =============================================
// Dataset Manager - Gestión y visualización de datasets
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { formatBytes, formatDate, setLoading } from '../core/utils.js';
import { fetchDatasets, deleteDataset, fetchStats, validateDataset } from '../api/client.js';

/**
 * Carga la lista de datasets desde el servidor
 */
export async function loadDatasets() {
    try {
        const data = await fetchDatasets();
        appState.datasets = data.datasets;

        renderDatasetsList();
        updateDatasetSelectors();
        await updateStats();

        // Actualizar todas las secciones que dependen de datasets
        if (window.updateSCMSection) window.updateSCMSection();
        if (window.updateRegressionSection) window.updateRegressionSection();
        if (window.updateClusteringSection) window.updateClusteringSection();
        if (window.updateQuickStatsSection) window.updateQuickStatsSection();
        if (window.updateMonteCarloSection) window.updateMonteCarloSection();
        if (window.updateRiskSection) window.updateRiskSection();

    } catch (error) {
        showToast('Error al cargar datasets', 'error');
        console.error('Load datasets error:', error);
    }
}

/**
 * Renderiza la lista de datasets en el sidebar
 */
export function renderDatasetsList() {
    const container = document.getElementById('datasetsList');
    if (!container) return;

    if (appState.datasets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>No hay datasets cargados</p>
                <p class="empty-hint">Sube un archivo para comenzar</p>
            </div>
        `;
        return;
    }

    container.innerHTML = appState.datasets.map(dataset => `
        <div class="dataset-item ${appState.selectedDataset?.id === dataset.id ? 'active' : ''}" 
             data-id="${dataset.id}">
            <div class="dataset-info">
                <div class="dataset-name">${dataset.name}</div>
                <div class="dataset-meta">
                    <span>📊 ${dataset.rows.toLocaleString()} filas</span>
                    <span>📋 ${dataset.columns.length} columnas</span>
                    <span>💾 ${formatBytes(dataset.size_bytes)}</span>
                    <span>📅 ${formatDate(dataset.uploaded_at)}</span>
                </div>
            </div>
            <div class="dataset-actions">
                <button class="btn btn-secondary btn-preview" data-id="${dataset.id}">
                    <span>👁️</span> Ver
                </button>
                <button class="btn btn-danger btn-delete" data-id="${dataset.id}">
                    <span>🗑️</span>
                </button>
            </div>
        </div>
    `).join('');

    // Event listeners
    container.querySelectorAll('.btn-preview').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            if (window.loadDatasetPreview) await window.loadDatasetPreview(id);
        });
    });

    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            if (confirm('¿Estás seguro de eliminar este dataset?')) {
                await handleDeleteDataset(id);
            }
        });
    });

    container.querySelectorAll('.dataset-item').forEach(item => {
        item.addEventListener('click', async () => {
            const id = item.dataset.id;
            if (window.loadDatasetPreview) await window.loadDatasetPreview(id);
        });
    });
}

/**
 * Maneja la eliminación de un dataset
 */
export async function handleDeleteDataset(datasetId) {
    try {
        setLoading(true);
        await deleteDataset(datasetId);
        showToast('Dataset eliminado', 'success');
        await loadDatasets();

        if (appState.selectedDataset?.id === datasetId) {
            appState.selectedDataset = null;
            appState.currentPreview = null;
            const tableBody = document.getElementById('tableBody');
            const tableHead = document.getElementById('tableHead');
            if (tableBody) tableBody.innerHTML = '';
            if (tableHead) tableHead.innerHTML = '';
        }

    } catch (error) {
        showToast('Error al eliminar dataset', 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Actualiza los selectores de dataset en los formularios
 */
export function updateDatasetSelectors() {
    const selectors = [
        document.getElementById('datasetSelector'),
        document.getElementById('analysisDataset'),
        document.getElementById('scmDataset'),
        document.getElementById('regressionDataset'),
        document.getElementById('clusteringDataset'),
        document.getElementById('quickStatsDataset'),
        document.getElementById('mcDataset'),
        document.getElementById('riskDataset'),
        document.getElementById('backtestingDataset'),
        document.getElementById('drawdownDataset'),
        document.getElementById('varMcDataset')
    ];

    selectors.forEach(selector => {
        if (!selector) return;
        const currentValue = selector.value;
        selector.innerHTML = '<option value="">Selecciona un dataset...</option>';

        appState.datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.id;
            option.textContent = `${dataset.name} (${dataset.rows} filas)`;
            selector.appendChild(option);
        });

        if (currentValue) {
            selector.value = currentValue;
        }
    });
}

/**
 * Actualiza las estadísticas globales
 */
export async function updateStats() {
    try {
        const stats = await fetchStats();
        const datasetCount = document.getElementById('datasetCount');
        const memoryUsage = document.getElementById('memoryUsage');

        if (datasetCount) datasetCount.textContent = stats.total_datasets;
        if (memoryUsage) memoryUsage.textContent = stats.total_memory_mb.toFixed(2) + ' MB';

    } catch (error) {
        console.error('Stats error:', error);
    }
}

/**
 * Ejecuta y muestra el Health Check de un dataset
 */
export async function runHealthCheck(datasetId) {
    const section = document.getElementById('healthCheckSection');
    const suggestionsContainer = document.getElementById('healthSuggestions');
    const scoreElement = document.getElementById('healthScoreValue');
    const circle = document.querySelector('.health-outer-circle');

    try {
        if (!section || !suggestionsContainer) return;

        section.classList.remove('hidden');
        suggestionsContainer.innerHTML = '<p class="loading-text">Analizando calidad de datos...</p>';

        const report = await validateDataset(datasetId);

        // Actualizar métricas básicas
        document.getElementById('nullCount').textContent = report.quality_report.null_values.total_nulls;
        document.getElementById('duplicateCount').textContent = report.quality_report.duplicate_rows;
        document.getElementById('healthColCount').textContent = Object.keys(report.column_types).length;

        // Calcular score
        let score = 100;
        const totalRows = report.quality_report.total_rows || 1000;
        const totalCells = totalRows * Object.keys(report.column_types).length || 1;
        const nullRate = report.quality_report.null_values.total_nulls / totalCells;

        score -= nullRate * 100;
        if (report.quality_report.duplicate_rows > 0) score -= 10;
        score = Math.max(0, Math.min(100, Math.round(score)));

        // Animar círculo y score
        scoreElement.textContent = score;
        if (circle) {
            circle.style.background = `conic-gradient(var(--primary) ${score}%, var(--glass-border) 0%)`;
        }

        // Renderizar sugerencias
        if (report.suggestions && report.suggestions.length > 0) {
            suggestionsContainer.innerHTML = report.suggestions.map(s => `
                <div class="suggestion-item ${s.type || 'info'}">
                    <strong>${s.column || 'Global'}:</strong> ${s.message}
                </div>
            `).join('');
        } else {
            suggestionsContainer.innerHTML = '<div class="suggestion-item success">✅ No se detectaron problemas críticos de calidad.</div>';
        }

    } catch (error) {
        console.error('Health check error:', error);
        showToast('Error al ejecutar health check', 'error');
    }
}
