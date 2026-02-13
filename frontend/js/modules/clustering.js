// =============================================
// Clustering - Segmentación de datos
// =============================================

import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { appState } from '../core/state.js';
import { runClustering, fetchElbowPlot, fetchDatasetColumns } from '../api/client.js';

/**
 * Inicializa el formulario de clustering
 */
export function initClusteringForm() {
    const form = document.getElementById('clusteringForm');
    const datasetSelect = document.getElementById('clusteringDataset');
    const algorithmSelect = document.getElementById('algorithmSelect');
    const elbowBtn = document.getElementById('elbowPlotBtn');

    if (!form) return;

    // Cambio de dataset
    datasetSelect?.addEventListener('change', async (e) => {
        const datasetId = e.target.value;
        if (datasetId) {
            try {
                const columnsData = await fetchDatasetColumns(datasetId);
                populateClusteringColumnSelects(columnsData.columns);
            } catch (error) {
                showToast('Error al cargar columnas', 'error');
            }
        }
    });

    // Cambio de algoritmo
    algorithmSelect?.addEventListener('change', (e) => {
        const kmeansOptions = document.getElementById('kmeansOptions');
        const dbscanOptions = document.getElementById('dbscanOptions');

        if (e.target.value === 'kmeans') {
            if (kmeansOptions) kmeansOptions.classList.remove('hidden');
            if (dbscanOptions) dbscanOptions.classList.add('hidden');
        } else {
            if (kmeansOptions) kmeansOptions.classList.add('hidden');
            if (dbscanOptions) dbscanOptions.classList.remove('hidden');
        }
    });

    // Botón de gráfico del codo
    elbowBtn?.addEventListener('click', async () => {
        await handleElbowPlot();
    });

    // Submit del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleClusteringSubmit();
    });
}

/**
 * Puebla los selects de columnas para clustering
 */
export function populateClusteringColumnSelects(columns) {
    const featureSelect = document.getElementById('featureColumns');
    if (!featureSelect) return;

    featureSelect.innerHTML = '';

    // Filtrar solo columnas numéricas
    const numericColumns = columns.filter(col =>
        col.dtype.includes('int') || col.dtype.includes('float') || col.dtype.includes('number')
    );

    numericColumns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.name;
        option.textContent = `${col.name} (${col.dtype})`;
        featureSelect.appendChild(option);
    });

    if (numericColumns.length === 0) {
        featureSelect.innerHTML = '<option value="">No hay columnas numéricas</option>';
    }
}

/**
 * Maneja el gráfico del codo
 */
export async function handleElbowPlot() {
    const datasetId = document.getElementById('clusteringDataset')?.value;
    const featureSelect = document.getElementById('featureColumns');
    if (!featureSelect) return;

    const selectedFeatures = Array.from(featureSelect.selectedOptions).map(opt => opt.value);

    if (!datasetId) {
        showToast('Selecciona un dataset primero', 'error');
        return;
    }

    if (selectedFeatures.length < 1) {
        showToast('Selecciona al menos una columna', 'error');
        return;
    }

    try {
        setLoading(true);

        const config = {
            dataset_id: datasetId,
            feature_columns: selectedFeatures,
            max_k: 10
        };

        const result = await fetchElbowPlot(config);

        if (result.success) {
            const elbowSection = document.getElementById('elbowSection');
            const container = document.getElementById('elbowPlotContainer');

            if (elbowSection) elbowSection.classList.remove('hidden');
            if (container) {
                container.innerHTML = `<img src="data:image/png;base64,${result.plot_base64}" alt="Elbow Plot" style="max-width: 100%; border-radius: 8px;">`;
            }

            showToast('Gráfico del codo generado', 'success');
        } else {
            showToast(result.error || 'Error al generar gráfico', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
        console.error('Elbow plot error:', error);
    } finally {
        setLoading(false);
    }
}

/**
 * Maneja el submit del formulario de clustering
 */
export async function handleClusteringSubmit() {
    const datasetId = document.getElementById('clusteringDataset')?.value;
    const featureSelect = document.getElementById('featureColumns');
    if (!featureSelect) return;

    const selectedFeatures = Array.from(featureSelect.selectedOptions).map(opt => opt.value);
    const algorithm = document.getElementById('algorithmSelect')?.value;

    if (!datasetId) {
        showToast('Selecciona un dataset', 'error');
        return;
    }

    if (selectedFeatures.length < 1) {
        showToast('Selecciona al menos una columna', 'error');
        return;
    }

    try {
        setLoading(true);

        const config = {
            dataset_id: datasetId,
            feature_columns: selectedFeatures,
            algorithm: algorithm
        };

        if (algorithm === 'kmeans') {
            config.n_clusters = parseInt(document.getElementById('nClusters')?.value) || 3;
        } else {
            config.eps = parseFloat(document.getElementById('eps')?.value) || 0.5;
            config.min_samples = parseInt(document.getElementById('minSamples')?.value) || 5;
        }

        const result = await runClustering(config);

        if (result.success) {
            appState.lastClusteringResults = result;
            renderClusteringResults(result);
            showToast('Clustering completado', 'success');
        } else {
            showToast(result.error || 'Error en clustering', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
        console.error('Clustering error:', error);
    } finally {
        setLoading(false);
    }
}

/**
 * Renderiza los resultados del clustering
 */
export function renderClusteringResults(result) {
    const resultsSection = document.getElementById('clusteringResultsSection');
    const resultsContent = document.getElementById('clusteringResultsContent');

    if (!resultsSection || !resultsContent) return;

    resultsSection.classList.remove('hidden');

    const algorithmLabel = result.algorithm === 'kmeans' ? 'K-Means' : 'DBSCAN';
    const silhouetteClass = result.silhouette_score >= 0.5 ? 'positive' : result.silhouette_score >= 0.25 ? '' : 'negative';

    let metricsHtml = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">Algoritmo</div>
                <div class="metric-value" style="font-size: 1.2rem;">${algorithmLabel}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Clusters Encontrados</div>
                <div class="metric-value">${result.n_clusters}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Silhouette Score</div>
                <div class="metric-value ${silhouetteClass}">${result.silhouette_score.toFixed(4)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Davies-Bouldin</div>
                <div class="metric-value">${result.davies_bouldin_score.toFixed(4)}</div>
            </div>
    `;

    if (result.algorithm === 'kmeans' && result.inertia !== undefined) {
        metricsHtml += `
            <div class="metric-card">
                <div class="metric-label">Inercia</div>
                <div class="metric-value">${result.inertia.toFixed(2)}</div>
            </div>
        `;
    }

    metricsHtml += '</div>';

    resultsContent.innerHTML = `
        ${metricsHtml}
        <div class="interpretation-box success" style="margin-top: var(--spacing-md);">
            <p>${result.interpretation || 'Segmentación de datos completada exitosamente.'}</p>
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Visualización de Clusters</h3>
            <div class="plot-container" style="background: var(--glass-bg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
                <img src="data:image/png;base64,${result.plot_base64}" alt="Clustering Plot" style="width: 100%; border-radius: var(--radius-md);">
            </div>
        </div>
    `;
}

export function updateClusteringSection() {
    const section = document.getElementById('clusteringSection');
    const select = document.getElementById('clusteringDataset');
    if (!section || !select) return;

    if (appState.datasets.length > 0) {
        section.classList.remove('hidden');
        const current = select.value;
        select.innerHTML = '<option value="">Selecciona un dataset...</option>';
        appState.datasets.forEach(d => {
            select.innerHTML += `<option value="${d.id}">${d.name}</option>`;
        });
        if (current) select.value = current;
    }
}
