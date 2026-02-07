// =============================================
// A/B Testing - Análisis estadístico de grupos
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { runAnalysis } from '../api/client.js';

/**
 * Inicializa el formulario de análisis A/B
 */
export function initAnalysisForm() {
    const form = document.getElementById('analysisForm');
    const datasetSelect = document.getElementById('analysisDataset');
    const groupColumnSelect = document.getElementById('groupColumn');
    const targetColumnSelect = document.getElementById('targetColumn');

    if (!form || !datasetSelect) return;

    // Cuando se selecciona un dataset, actualizar las columnas
    datasetSelect.addEventListener('change', () => {
        const datasetId = datasetSelect.value;
        if (datasetId) {
            const dataset = appState.datasets.find(d => d.id === datasetId);
            if (dataset) {
                populateColumnSelects(dataset.columns);
            }
        } else {
            if (groupColumnSelect) groupColumnSelect.innerHTML = '<option value="">Selecciona una columna...</option>';
            if (targetColumnSelect) targetColumnSelect.innerHTML = '<option value="">Selecciona una columna...</option>';
        }
    });

    // Submit del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleAnalysisSubmit();
    });
}

function populateColumnSelects(columns) {
    const groupColumnSelect = document.getElementById('groupColumn');
    const targetColumnSelect = document.getElementById('targetColumn');

    [groupColumnSelect, targetColumnSelect].forEach(select => {
        if (!select) return;
        select.innerHTML = '<option value="">Selecciona una columna...</option>';
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            select.appendChild(option);
        });
    });
}

async function handleAnalysisSubmit() {
    const config = {
        dataset_id: document.getElementById('analysisDataset').value,
        group_column: document.getElementById('groupColumn').value,
        target_column: document.getElementById('targetColumn').value,
        control_value: document.getElementById('controlValue').value,
        treatment_value: document.getElementById('treatmentValue').value,
        alpha: parseFloat(document.getElementById('alphaValue').value)
    };

    if (!config.dataset_id || !config.group_column || !config.target_column ||
        !config.control_value || !config.treatment_value) {
        showToast('Por favor completa todos los campos', 'error');
        return;
    }

    try {
        setLoading(true);

        const result = await runAnalysis(config);

        if (result.success) {
            renderResults(result);
            document.getElementById('resultsSection').classList.remove('hidden');

            document.getElementById('resultsSection').scrollIntoView({
                behavior: 'smooth'
            });

            showToast('Análisis completado', 'success');
        } else {
            showToast(result.error || 'Error en el análisis', 'error');
        }

    } catch (error) {
        showToast('Error al ejecutar análisis', 'error');
        console.error('Analysis error:', error);
    } finally {
        setLoading(false);
    }
}

export function renderResults(result) {
    appState.lastResults = result;
    const container = document.getElementById('resultsContent');
    if (!container) return;

    const isContinuous = result.analysis_type === 'continuous';

    let metricsHtml = '';
    let statsCardHtml = '';

    if (isContinuous) {
        const changeClass = result.percentage_change > 0 ? 'positive' : 'negative';
        const changeIcon = result.percentage_change > 0 ? '📈' : '📉';

        metricsHtml = `
            <div class="results-metrics">
                <div class="metric-card">
                    <div class="metric-label">Control (Media)</div>
                    <div class="metric-value">${result.control_mean.toFixed(4)}</div>
                    <div class="metric-sublabel">σ = ${result.control_std.toFixed(4)}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Treatment (Media)</div>
                    <div class="metric-value">${result.treatment_mean.toFixed(4)}</div>
                    <div class="metric-sublabel">σ = ${result.treatment_std.toFixed(4)}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Cambio ${changeIcon}</div>
                    <div class="metric-value ${changeClass}">${result.percentage_change.toFixed(2)}%</div>
                    <div class="metric-sublabel">Δ = ${result.difference.toFixed(4)}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">P-value</div>
                    <div class="metric-value">${result.p_value.toFixed(6)}</div>
                </div>
            </div>
        `;

        statsCardHtml = `
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Estadísticas T-test</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Estadístico t</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.t_statistic.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Media Control</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.control_mean.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Media Tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.treatment_mean.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">¿Significativo?</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600; color: ${result.is_significant ? 'var(--success)' : 'var(--error)'};">
                            ${result.is_significant ? '✅ Sí' : '❌ No'}
                        </td>
                    </tr>
                </table>
            </div>
        `;
    } else {
        const liftClass = result.lift_percentage > 0 ? 'positive' : 'negative';
        const liftIcon = result.lift_percentage > 0 ? '📈' : '📉';

        metricsHtml = `
            <div class="results-metrics">
                <div class="metric-card">
                    <div class="metric-label">Control</div>
                    <div class="metric-value">${(result.control_signup_rate * 100).toFixed(2)}%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Treatment</div>
                    <div class="metric-value">${(result.treatment_signup_rate * 100).toFixed(2)}%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Lift ${liftIcon}</div>
                    <div class="metric-value ${liftClass}">${result.lift_percentage.toFixed(2)}%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">P-value</div>
                    <div class="metric-value">${result.p_value.toFixed(6)}</div>
                </div>
            </div>
        `;

        statsCardHtml = `
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Estadísticas Chi-cuadrado</h3>
                <div id="contingencyTable"></div>
            </div>
        `;
    }

    const analysisTypeTitle = isContinuous
        ? '🔢 Análisis de Variable Continua (T-test)'
        : `📊 Análisis de Variable Categórica (Chi-cuadrado)`;

    container.innerHTML = `
        <div class="analysis-type-badge" style="background: var(--glass-bg); padding: var(--spacing-sm) var(--spacing-md); border-radius: var(--radius-md); margin-bottom: var(--spacing-md); display: inline-block;">
            ${analysisTypeTitle}
        </div>
        ${metricsHtml}
        <div class="interpretation-box ${result.is_significant ? 'success' : 'warning'}">
            ${result.interpretation}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md); margin-top: var(--spacing-lg);">
            ${statsCardHtml}
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Visualización de Resultados</h3>
            <div id="plotlyChart" style="width: 100%; height: 400px;"></div>
        </div>
    `;

    if (!isContinuous && result.contingency_table) {
        renderContingencyTable(result.contingency_table);
    }

    renderPlotlyChart(result);
}

function renderContingencyTable(contingencyTable) {
    const container = document.getElementById('contingencyTable');
    if (!container) return;

    const rows = Object.keys(contingencyTable);
    const cols = rows.length > 0 ? Object.keys(contingencyTable[rows[0]]) : [];

    let html = '<table class="data-table" style="font-size: 0.85rem;">';
    html += '<thead><tr><th></th>';
    cols.forEach(col => { html += `<th>${col}</th>`; });
    html += '<th>Total</th></tr></thead><tbody>';

    rows.forEach(row => {
        html += `<tr><td style="font-weight: 600;">${row}</td>`;
        let rowTotal = 0;
        cols.forEach(col => {
            const value = contingencyTable[row][col] || 0;
            rowTotal += value;
            html += `<td>${value}</td>`;
        });
        html += `<td style="font-weight: 600;">${rowTotal}</td></tr>`;
    });
    html += '</tbody></table>';

    container.innerHTML = html;
}

function renderPlotlyChart(result) {
    if (typeof Plotly === 'undefined') {
        console.warn('Plotly not found');
        return;
    }

    const isContinuous = result.analysis_type === 'continuous';
    let data, layout;

    if (isContinuous) {
        data = [{
            x: ['Control', 'Treatment'],
            y: [result.control_mean, result.treatment_mean],
            error_y: {
                type: 'data',
                array: [result.control_std, result.treatment_std],
                visible: true,
                color: '#94a3b8'
            },
            type: 'bar',
            marker: { color: ['#6366f1', '#8b5cf6'] }
        }];

        layout = {
            title: 'Comparación de Medias',
            plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
            paper_bgcolor: 'transparent',
            font: { color: '#f8fafc' }
        };
    } else {
        data = [{
            x: ['Control', 'Treatment'],
            y: [result.control_signup_rate * 100, result.treatment_signup_rate * 100],
            type: 'bar',
            marker: { color: ['#6366f1', '#8b5cf6'] }
        }];

        layout = {
            title: 'Tasas de Conversión (%)',
            plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
            paper_bgcolor: 'transparent',
            font: { color: '#f8fafc' }
        };
    }

    Plotly.newPlot('plotlyChart', data, layout, { responsive: true });
}
