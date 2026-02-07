// =============================================
// Quick Stats - Análisis Rápido
// =============================================

import { API_BASE_URL } from '../core/config.js';
import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';

/**
 * API calls for Quick Stats
 */
export async function analyzeSingleVariable(datasetId, variable) {
    const response = await fetch(`${API_BASE_URL}/quick-stats/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, variable })
    });
    return await response.json();
}

export async function analyzeDualVariables(datasetId, variableX, variableY, correlationType = 'pearson') {
    const response = await fetch(`${API_BASE_URL}/quick-stats/dual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            dataset_id: datasetId,
            variable_x: variableX,
            variable_y: variableY,
            correlation_type: correlationType
        })
    });
    return await response.json();
}

export async function analyzeTimeSeries(datasetId, timeColumn, valueColumn, periodsAhead, autoSelect) {
    const response = await fetch(`${API_BASE_URL}/quick-stats/time-series`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            dataset_id: datasetId,
            time_column: timeColumn,
            value_column: valueColumn,
            periods_ahead: periodsAhead,
            auto_select_params: autoSelect
        })
    });
    return await response.json();
}

/**
 * Initialize Quick Stats section
 */
export function initQuickStats() {
    const datasetSelect = document.getElementById('quickStatsDataset');
    const singleVarSelect = document.getElementById('singleVariable');
    const variableXSelect = document.getElementById('variableX');
    const variableYSelect = document.getElementById('variableY');
    const analyzeSingleBtn = document.getElementById('analyzeSingleBtn');
    const analyzeDualBtn = document.getElementById('analyzeDualBtn');

    if (!datasetSelect) return;

    // Tab switching
    document.querySelectorAll('.stats-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.stats-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabType = tab.dataset.tab;
            document.getElementById('singleVarPanel')?.classList.toggle('hidden', tabType !== 'single');
            document.getElementById('dualVarPanel')?.classList.toggle('hidden', tabType !== 'dual');
            document.getElementById('timeSeriesPanel')?.classList.toggle('hidden', tabType !== 'timeseries');
        });
    });

    // Dataset selection
    datasetSelect.addEventListener('change', async (e) => {
        const datasetId = e.target.value;
        if (!datasetId) {
            [singleVarSelect, variableXSelect, variableYSelect].forEach(sel => {
                if (sel) sel.innerHTML = '<option value="">Selecciona una variable...</option>';
            });
            return;
        }

        try {
            const dataset = appState.datasets.find(d => d.id === datasetId);
            if (!dataset) return;

            const columnOptions = dataset.columns.map(col =>
                `<option value="${col}">${col}</option>`
            ).join('');

            if (singleVarSelect) singleVarSelect.innerHTML = '<option value="">Selecciona una variable...</option>' + columnOptions;
            if (variableXSelect) variableXSelect.innerHTML = '<option value="">Selecciona variable X...</option>' + columnOptions;
            if (variableYSelect) variableYSelect.innerHTML = '<option value="">Selecciona variable Y...</option>' + columnOptions;

            // Time Series specific
            const timeColSelect = document.getElementById('qsTimeColumn');
            const valueColSelect = document.getElementById('qsValueColumn');
            if (timeColSelect) timeColSelect.innerHTML = '<option value="">Selecciona columna temporal...</option>' + columnOptions;
            if (valueColSelect) valueColSelect.innerHTML = '<option value="">Selecciona valores a analizar...</option>' + columnOptions;
        } catch (error) {
            showToast('Error al cargar columnas', 'error');
        }
    });

    // Single variable analysis
    analyzeSingleBtn?.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const variable = singleVarSelect?.value;

        const currentParams = { dataset_id: datasetId, variable: variable };

        if (!datasetId || !variable) {
            showToast('Selecciona un dataset y una variable', 'error');
            return;
        }

        try {
            setLoading(true);
            const result = await analyzeSingleVariable(datasetId, variable);

            if (result.success) {
                renderSingleVariableResults(result, currentParams);
                document.getElementById('quickStatsResultsSection')?.classList.remove('hidden');
                showToast('Análisis completado', 'success');
            } else {
                showToast('Error en el análisis', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'error');
            console.error('Single variable analysis error:', error);
        } finally {
            setLoading(false);
        }
    });

    // Dual variable analysis
    analyzeDualBtn?.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const variableX = variableXSelect?.value;
        const variableY = variableYSelect?.value;
        const correlationType = document.getElementById('correlationType')?.value;

        const currentParams = {
            dataset_id: datasetId,
            variable_x: variableX,
            variable_y: variableY,
            correlation_type: correlationType
        };

        if (!datasetId || !variableX || !variableY) {
            showToast('Selecciona un dataset y ambas variables', 'error');
            return;
        }

        if (variableX === variableY) {
            showToast('Selecciona variables diferentes', 'error');
            return;
        }

        try {
            setLoading(true);
            const result = await analyzeDualVariables(datasetId, variableX, variableY, correlationType);

            if (result.success) {
                renderDualVariableResults(result, currentParams);
                document.getElementById('quickStatsResultsSection')?.classList.remove('hidden');
                showToast('Análisis completado', 'success');
            } else {
                showToast('Error en el análisis', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'error');
            console.error('Dual variable analysis error:', error);
        } finally {
            setLoading(false);
        }
    });

    // Time Series Analysis
    document.getElementById('analyzeTimeSeriesBtn')?.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const timeColumn = document.getElementById('qsTimeColumn')?.value;
        const valueColumn = document.getElementById('qsValueColumn')?.value;
        const periodsAhead = parseInt(document.getElementById('forecastPeriods')?.value || "10");
        const autoSelect = document.getElementById('autoSelectParams')?.checked;

        const currentParams = {
            dataset_id: datasetId,
            time_column: timeColumn,
            value_column: valueColumn,
            periods_ahead: periodsAhead,
            auto_select_params: autoSelect
        };

        if (!datasetId || !timeColumn || !valueColumn) {
            showToast('Por favor completa todos los campos', 'error');
            return;
        }

        try {
            setLoading(true);
            const result = await analyzeTimeSeries(
                datasetId, timeColumn, valueColumn, periodsAhead, autoSelect
            );

            if (result.success) {
                renderTimeSeriesResults(result, currentParams);
                document.getElementById('quickStatsResultsSection')?.classList.remove('hidden');
                showToast('Análisis ARIMA completado', 'success');
            } else {
                showToast(result.detail || 'Error en el análisis', 'error');
            }
        } catch (error) {
            showToast('Error en el análisis', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    });
}

/**
 * Render single variable results
 */
export function renderSingleVariableResults(result, params) {
    const container = document.getElementById('quickStatsResultsContent');
    if (!container) return;

    const exportBtnId = `exportSingle_${Date.now()}`;
    const headerHtml = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 class="stats-section-title" style="margin-bottom: 0;">${result.type === 'categorical' ? '📊' : '📈'} ${result.variable}</h3>
            <button id="${exportBtnId}" class="btn btn-secondary output-btn">
                <span class="material-icons" style="font-size: 18px; margin-right: 5px;">download</span> 
                Excel
            </button>
        </div>
    `;

    if (result.type === 'categorical') {
        const topCategoriesHtml = Object.entries(result.top_categories)
            .map(([cat, count]) => `<li>${cat}: ${count}</li>`)
            .join('');

        container.innerHTML = `
            <div class="stats-section">
                ${headerHtml}
                
                <div class="results-metrics">
                    <div class="metric-card">
                        <div class="metric-label">Observaciones</div>
                        <div class="metric-value">${result.n_observations.toLocaleString()}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Categorías Únicas</div>
                        <div class="metric-value">${result.n_unique}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Moda</div>
                        <div class="metric-value" style="font-size: 1.2rem;">${result.mode}</div>
                    </div>
                </div>

                <div class="glass-card" style="padding: var(--spacing-md); margin-top: var(--spacing-lg);">
                    <h4>Top 10 Categorías</h4>
                    <ul style="margin-top: var(--spacing-sm);">
                        ${topCategoriesHtml}
                    </ul>
                </div>

                <div style="margin-top: var(--spacing-lg);">
                    <div id="quickStatsPlot"></div>
                </div>
            </div>
        `;
    } else {
        const stats = result.statistics;
        container.innerHTML = `
            <div class="stats-section">
                ${headerHtml}
                
                <div class="results-metrics">
                    <div class="metric-card">
                        <div class="metric-label">Media (μ)</div>
                        <div class="metric-value">${stats.central_tendency.mean}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Mediana</div>
                        <div class="metric-value">${stats.central_tendency.median}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Desv. Estándar (σ)</div>
                        <div class="metric-value">${stats.dispersion.std}</div>
                    </div>
                </div>

                <div style="margin-top: var(--spacing-lg);">
                    <div id="quickStatsPlot"></div>
                </div>
            </div>
        `;
    }

    if (result.plot) {
        const plotData = JSON.parse(result.plot);
        Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true });
    }

    document.getElementById(exportBtnId)?.addEventListener('click', () => {
        exportQuickStats('single', params);
    });
}

/**
 * Render dual variable results
 */
export function renderDualVariableResults(result, params) {
    const container = document.getElementById('quickStatsResultsContent');
    if (!container) return;

    const exportBtnId = `exportDual_${Date.now()}`;
    const headerHtml = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 class="stats-section-title" style="margin-bottom: 0;">🔮 ${result.variable_y} vs ${result.variable_x}</h3>
             <button id="${exportBtnId}" class="btn btn-secondary output-btn">
                <span class="material-icons" style="font-size: 18px; margin-right: 5px;">download</span> 
                Excel
            </button>
        </div>
    `;

    // Check if this is a "full" analysis with multiple correlation methods
    if (result.correlation_type === 'full' && result.results) {
        // Full analysis with Pearson, Spearman, and Kendall
        const { pearson, spearman, kendall } = result.results;
        const regression = result.regression;

        container.innerHTML = `
            <div class="stats-section">
                ${headerHtml}
                
                <div class="glass-card" style="padding: var(--spacing-md); margin-bottom: var(--spacing-lg);">
                    <h4 style="margin-bottom: var(--spacing-md);">📊 Análisis Comparativo de Correlaciones</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid rgba(255,255,255,0.1);">
                                <th style="padding: var(--spacing-sm); text-align: left;">Método</th>
                                <th style="padding: var(--spacing-sm); text-align: center;">Coeficiente</th>
                                <th style="padding: var(--spacing-sm); text-align: center;">P-Value</th>
                                <th style="padding: var(--spacing-sm); text-align: center;">Significativo</th>
                                <th style="padding: var(--spacing-sm); text-align: left;">Interpretación</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <td style="padding: var(--spacing-sm); font-weight: 600;">${pearson.name}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${pearson.coefficient}</td>
                                <td style="padding: var(--spacing-sm); text-align: center; font-size: 0.9em;">${pearson.p_value}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${pearson.is_significant ? '✅' : '❌'}</td>
                                <td style="padding: var(--spacing-sm); font-size: 0.9em;">${pearson.interpretation}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <td style="padding: var(--spacing-sm); font-weight: 600;">${spearman.name}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${spearman.coefficient}</td>
                                <td style="padding: var(--spacing-sm); text-align: center; font-size: 0.9em;">${spearman.p_value}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${spearman.is_significant ? '✅' : '❌'}</td>
                                <td style="padding: var(--spacing-sm); font-size: 0.9em;">${spearman.interpretation}</td>
                            </tr>
                            <tr>
                                <td style="padding: var(--spacing-sm); font-weight: 600;">${kendall.name}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${kendall.coefficient}</td>
                                <td style="padding: var(--spacing-sm); text-align: center; font-size: 0.9em;">${kendall.p_value}</td>
                                <td style="padding: var(--spacing-sm); text-align: center;">${kendall.is_significant ? '✅' : '❌'}</td>
                                <td style="padding: var(--spacing-sm); font-size: 0.9em;">${kendall.interpretation}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="glass-card" style="padding: var(--spacing-md); margin-bottom: var(--spacing-lg);">
                    <h4 style="margin-bottom: var(--spacing-md);">📐 Regresión Lineal</h4>
                    <div class="results-metrics">
                        <div class="metric-card">
                            <div class="metric-label">R² (Bondad de Ajuste)</div>
                            <div class="metric-value">${regression.r_squared}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Ecuación</div>
                            <div class="metric-value" style="font-size: 1rem;">${regression.equation}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Pendiente</div>
                            <div class="metric-value">${regression.slope}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Intercepto</div>
                            <div class="metric-value">${regression.intercept}</div>
                        </div>
                    </div>
                </div>

                <div id="quickStatsPlot3D" style="margin-top: var(--spacing-lg); height: 600px;"></div>
            </div>
        `;

        // Render 3D plot
        if (result.plot_3d) {
            const plot3d = result.plot_3d;
            const layout = {
                title: `Visualización 3D: ${result.variable_y} vs ${result.variable_x}`,
                scene: {
                    xaxis: { title: result.variable_x },
                    yaxis: { title: result.variable_y },
                    zaxis: { title: 'Diferencia de Rangos (Métrica de No-Linealidad)' },
                    bgcolor: 'rgba(255, 255, 255, 0.03)'
                },
                plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
                paper_bgcolor: 'transparent',
                font: { color: '#f8fafc' }
            };

            Plotly.newPlot('quickStatsPlot3D', [plot3d], layout, { responsive: true });
        }

    } else {
        // Standard single-method analysis
        container.innerHTML = `
            <div class="stats-section">
                ${headerHtml}
                <div class="interpretation-box success" style="margin-bottom: var(--spacing-lg);">
                    ${result.interpretation}
                </div>
                <div class="results-metrics">
                    <div class="metric-card">
                        <div class="metric-label">${result.correlation_method || 'Correlación'}</div>
                        <div class="metric-value">${result.correlation.coefficient}</div>
                        <div class="metric-sublabel">${result.correlation.is_significant ? 'Significativa' : 'No Sig.'}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">R²</div>
                        <div class="metric-value">${result.correlation.r_squared}</div>
                    </div>
                </div>
                <div id="quickStatsPlot" style="margin-top: var(--spacing-lg); height: 500px;"></div>
            </div>
        `;

        if (result.plot) {
            const plotData = JSON.parse(result.plot);
            Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true });
        }
    }

    document.getElementById(exportBtnId)?.addEventListener('click', () => {
        exportQuickStats('dual', params);
    });
}

/**
 * Render time series results
 */
export function renderTimeSeriesResults(result, params) {
    const container = document.getElementById('quickStatsResultsContent');
    if (!container) return;

    const exportBtnId = `exportTS_${Date.now()}`;
    container.innerHTML = `
        <div class="stats-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3>📈 Pronóstico ARIMA</h3>
                <button id="${exportBtnId}" class="btn btn-secondary output-btn">Excel</button>
            </div>
            <div class="interpretation-box success" style="margin-bottom: 20px;">
                <p>${result.interpretation}</p>
            </div>
            <div id="arimaPlot" style="height: 500px;"></div>
        </div>
    `;

    renderARIMAPlot(result);

    document.getElementById(exportBtnId)?.addEventListener('click', () => {
        exportQuickStats('timeseries', params);
    });
}

function renderARIMAPlot(result) {
    const historical = {
        x: result.historical_data.dates,
        y: result.historical_data.values,
        name: 'Histórico',
        type: 'scatter',
        mode: 'lines'
    };
    const forecast = {
        x: result.forecast.dates,
        y: result.forecast.values,
        name: 'Pronóstico',
        type: 'scatter',
        mode: 'lines+markers'
    };
    Plotly.newPlot('arimaPlot', [historical, forecast], { responsive: true });
}

/**
 * Export Quick Stats Results to Excel
 */
export async function exportQuickStats(analysisType, params) {
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/quick-stats/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                analysis_type: analysisType,
                params: params
            })
        });

        if (!response.ok) throw new Error('Error al exportar');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Quick_Stats_${analysisType}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast('Excel generado', 'success');
    } catch (error) {
        showToast('Error al exportar', 'error');
    } finally {
        setLoading(false);
    }
}

export function updateQuickStatsSection() {
    const select = document.getElementById('quickStatsDataset');
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
