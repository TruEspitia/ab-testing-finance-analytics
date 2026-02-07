// =============================================
// Preview de Datos - Visualización de tablas
// =============================================

import { appState } from '../core/state.js';
import { setLoading } from '../core/utils.js';
import { showToast } from '../ui/notifications.js';
import { fetchDatasetPreview } from '../api/client.js';
import { renderDatasetsList, runHealthCheck } from './datasetManager.js';

/**
 * Carga el preview de un dataset
 */
export async function loadDatasetPreview(datasetId) {
    try {
        setLoading(true);

        const preview = await fetchDatasetPreview(datasetId);
        appState.currentPreview = preview;
        appState.selectedDataset = appState.datasets.find(d => d.id === datasetId);

        renderDataTable(preview);
        renderDatasetsList(); // Actualizar para marcar el activo

        // Actualizar selector de preview
        const selector = document.getElementById('datasetSelector');
        if (selector) selector.value = datasetId;

        // Refresh Health Check
        await runHealthCheck(datasetId);

        showToast('Preview cargado', 'success');

    } catch (error) {
        showToast('Error al cargar preview', 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Renderiza los datos en la tabla HTML
 */
export function renderDataTable(preview) {
    const tableHead = document.getElementById('tableHead');
    const tableBody = document.getElementById('tableBody');
    const previewInfo = document.getElementById('previewInfo');

    if (!tableHead || !tableBody || !preview) return;

    // Header
    tableHead.innerHTML = `
        <tr>
            ${preview.columns.map(col => `<th>${col}</th>`).join('')}
        </tr>
    `;

    // Body
    tableBody.innerHTML = preview.data.map(row => `
        <tr>
            ${preview.columns.map(col => {
        let value = row[col];
        if (value === null || value === undefined) {
            value = '<span style="color: var(--text-muted); font-style: italic;">null</span>';
        }
        return `<td>${value}</td>`;
    }).join('')}
        </tr>
    `).join('');

    // Info
    if (previewInfo) {
        previewInfo.textContent =
            `Mostrando ${preview.preview_rows} de ${preview.total_rows.toLocaleString()} filas`;
    }
}

/**
 * Inicializa controles de preview
 */
export function initPreviewControls() {
    const selector = document.getElementById('datasetSelector');
    const refreshBtn = document.getElementById('refreshPreviewBtn');

    if (selector) {
        selector.addEventListener('change', async (e) => {
            if (e.target.value) {
                await loadDatasetPreview(e.target.value);
            }
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (appState.selectedDataset) {
                await loadDatasetPreview(appState.selectedDataset.id);
            } else {
                showToast('Selecciona un dataset primero', 'info');
            }
        });
    }
}
