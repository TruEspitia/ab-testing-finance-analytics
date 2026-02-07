// =============================================
// Synthetic Control Method (SCM)
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { fetchDatasetPreview } from '../api/client.js';
import { API_BASE_URL } from '../core/config.js';

/**
 * Ejecuta análisis de Control Sintético
 */
export async function runSCMAnalysis(config) {
    const response = await fetch(`${API_BASE_URL}/analyze/scm`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Inicializa el formulario de Control Sintético
 */
export function initSCMForm() {
    const scmForm = document.getElementById('scmForm');
    const scmDatasetSelect = document.getElementById('scmDataset');
    const unitColumnSelect = document.getElementById('unitColumn');
    const timeColumnSelect = document.getElementById('timeColumn');
    const scmTargetColumnSelect = document.getElementById('scmTargetColumn');
    const treatedUnitSelect = document.getElementById('treatedUnit');

    if (!scmForm) return;

    // Cuando cambia el dataset, llenar los selects de columnas
    scmDatasetSelect.addEventListener('change', async (e) => {
        const datasetId = e.target.value;

        if (!datasetId) {
            [unitColumnSelect, timeColumnSelect, scmTargetColumnSelect, treatedUnitSelect].forEach(sel => {
                if (sel) sel.innerHTML = '<option value="">Selecciona columna...</option>';
            });
            return;
        }

        try {
            const preview = await fetchDatasetPreview(datasetId, 100);
            const columns = preview.columns || [];

            const columnOptions = columns.map(col => `<option value="${col}">${col}</option>`).join('');

            if (timeColumnSelect) timeColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;
            if (unitColumnSelect) unitColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;
            if (scmTargetColumnSelect) scmTargetColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;

            appState.scmPreview = preview;

        } catch (error) {
            showToast('Error al cargar columnas', 'error');
        }
    });

    // Cuando cambia la columna de unidades, llenar el select de unidad tratada
    unitColumnSelect.addEventListener('change', async (e) => {
        const unitColumn = e.target.value;

        if (!unitColumn || !appState.scmPreview) {
            if (treatedUnitSelect) treatedUnitSelect.innerHTML = '<option value="">Selecciona unidad...</option>';
            return;
        }

        const data = appState.scmPreview.data || [];
        const uniqueUnits = [...new Set(data.map(row => row[unitColumn]))].filter(u => u != null);

        const unitOptions = uniqueUnits.map(unit => `<option value="${unit}">${unit}</option>`).join('');
        if (treatedUnitSelect) treatedUnitSelect.innerHTML = '<option value="">Selecciona unidad...</option>' + unitOptions;
    });

    // Envío del formulario
    scmForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const config = {
            dataset_id: scmDatasetSelect.value,
            time_column: timeColumnSelect.value,
            unit_column: unitColumnSelect.value,
            target_column: scmTargetColumnSelect.value,
            treated_unit: treatedUnitSelect.value,
            treatment_time: parseFloat(document.getElementById('treatmentTime').value)
        };

        try {
            setLoading(true);
            const result = await runSCMAnalysis(config);
            setLoading(false);

            if (result.success) {
                showToast('Análisis de Control Sintético completado', 'success');
                renderSCMResults(result);
                document.getElementById('scmResultsSection').classList.remove('hidden');
            } else {
                showToast(result.error || 'Error en el análisis', 'error');
            }
        } catch (error) {
            setLoading(false);
            showToast('Error de conexión: ' + error.message, 'error');
        }
    });
}

/**
 * Renderiza los resultados de Control Sintético
 */
export function renderSCMResults(result) {
    appState.lastSCMResults = result;
    const container = document.getElementById('scmResultsContent');
    if (!container) return;

    const effectClass = result.average_treatment_effect > 0 ? 'positive' : 'negative';
    const effectIcon = result.average_treatment_effect > 0 ? '📈' : '📉';

    container.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">Unidad Tratada</div>
                <div class="metric-value" style="font-size: 1.2rem;">${result.treated_unit}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Efecto Promedio ${effectIcon}</div>
                <div class="metric-value ${effectClass}">${result.average_treatment_effect?.toFixed(4) || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">RMSPE Pre-tratamiento</div>
                <div class="metric-value">${result.pre_treatment_rmspe?.toFixed(4) || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Efecto Total</div>
                <div class="metric-value">${result.post_treatment_effect?.toFixed(4) || 'N/A'}</div>
            </div>
        </div>
        <div class="interpretation-box success">
            ${result.interpretation.replace(/\n/g, '<br>')}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md); margin-top: var(--spacing-lg);">
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Información del Análisis</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Periodos Pre-tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.n_pre_periods || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Periodos Post-tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.n_post_periods || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Unidades de Control</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.n_control_units || 'N/A'}</td>
                    </tr>
                </table>
            </div>
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">⚖️ Pesos de las Unidades de Control</h3>
                <div id="weightsContainer" style="max-height: 200px; overflow-y: auto;"></div>
            </div>
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📈 Series Temporales: Tratado vs. Sintético</h3>
            <div id="scmTimeSeriesChart" style="width: 100%; height: 450px;"></div>
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Pesos de las Unidades de Control</h3>
            <div id="scmWeightsChart" style="width: 100%; height: 350px;"></div>
        </div>
    `;

    renderWeightsTable(result.weights);
    renderSCMTimeSeries(result);
    renderSCMWeightsChart(result.weights);
}

function renderWeightsTable(weights) {
    const container = document.getElementById('weightsContainer');
    if (!weights || !container) return;

    const sortedWeights = Object.entries(weights).sort((a, b) => b[1] - a[1]);

    let html = '<table style="width: 100%; font-size: 0.85rem;">';
    for (const [unit, weight] of sortedWeights) {
        if (weight > 0.001) {
            html += `
                <tr>
                    <td style="padding: var(--spacing-xs); color: var(--text-secondary);">${unit}</td>
                    <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${(weight * 100).toFixed(2)}%</td>
                </tr>
            `;
        }
    }
    html += '</table>';
    container.innerHTML = html;
}

function renderSCMTimeSeries(result) {
    if (typeof Plotly === 'undefined') return;
    const treatmentTime = result.treatment_time;

    const data = [
        {
            x: result.time_values,
            y: result.treated_values,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${result.treated_unit} (Tratada)`,
            line: { color: '#6366f1', width: 3 }
        },
        {
            x: result.time_values,
            y: result.synthetic_values,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Control Sintético',
            line: { color: '#8b5cf6', width: 3, dash: 'dash' }
        }
    ];

    const layout = {
        title: 'Unidad Tratada vs. Control Sintético',
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        shapes: [{
            type: 'line', x0: treatmentTime, x1: treatmentTime, y0: 0, y1: 1, yref: 'paper',
            line: { color: '#ef4444', width: 2, dash: 'dot' }
        }]
    };

    Plotly.newPlot('scmTimeSeriesChart', data, layout, { responsive: true });
}

function renderSCMWeightsChart(weights) {
    if (typeof Plotly === 'undefined' || !weights) return;

    const sortedWeights = Object.entries(weights)
        .filter(([_, w]) => w > 0.001)
        .sort((a, b) => b[1] - a[1]);

    const data = [{
        x: sortedWeights.map(([unit, _]) => unit),
        y: sortedWeights.map(([_, weight]) => weight * 100),
        type: 'bar',
        marker: { color: '#8b5cf6' }
    }];

    const layout = {
        title: 'Contribución de Unidades de Control (%)',
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' }
    };

    Plotly.newPlot('scmWeightsChart', data, layout, { responsive: true });
}

/**
 * Updates the SCM dataset select dropdown when datasets change
 */
export function updateSCMSection() {
    const select = document.getElementById('scmDataset');
    if (!select) return;

    if (appState.datasets.length > 0) {
        const current = select.value;
        select.innerHTML = '<option value="">Selecciona un dataset...</option>';
        appState.datasets.forEach(d => {
            select.innerHTML += `<option value="${d.id}">${d.name}</option>`;
        });
        if (current) select.value = current;
    }
}
