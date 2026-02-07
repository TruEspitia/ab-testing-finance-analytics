// =============================================
// Monte Carlo Simulation
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { fetchDatasetPreview, runMonteCarlo } from '../api/client.js';

/**
 * Inicializa el formulario de Monte Carlo
 */
export function initMonteCarloForm() {
    const form = document.getElementById('monteCarloForm');
    const datasetSelect = document.getElementById('mcDataset');
    const targetColumnSelect = document.getElementById('mcTargetColumn');

    if (!form || !datasetSelect) return;

    // Cuando se selecciona un dataset, cargar sus columnas
    datasetSelect.addEventListener('change', async (e) => {
        const datasetId = e.target.value;
        if (!datasetId) {
            if (targetColumnSelect) targetColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
            return;
        }

        try {
            const result = await fetchDatasetPreview(datasetId, 1);
            if (result.columns) {
                if (targetColumnSelect) {
                    targetColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
                    result.columns.forEach(col => {
                        targetColumnSelect.innerHTML += `<option value="${col}">${col}</option>`;
                    });
                }
            }
        } catch (error) {
            showToast('Error al cargar columnas', 'error');
        }
    });

    // Submit del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const datasetId = datasetSelect.value;
        const targetColumn = targetColumnSelect?.value;
        const iterations = parseInt(document.getElementById('mcIterations')?.value || "1000");
        const horizon = parseInt(document.getElementById('mcHorizon')?.value || "30");
        const driftInput = document.getElementById('mcDrift')?.value;
        const volatilityInput = document.getElementById('mcVolatility')?.value;

        if (!datasetId || !targetColumn) {
            showToast('Por favor completa todos los campos requeridos', 'error');
            return;
        }

        // Validar valores
        if (iterations < 100 || iterations > 10000) {
            showToast('El número de simulaciones debe estar entre 100 y 10,000', 'error');
            return;
        }

        if (horizon < 1 || horizon > 365) {
            showToast('El horizonte debe estar entre 1 y 365 períodos', 'error');
            return;
        }

        const config = {
            dataset_id: datasetId,
            target_column: targetColumn,
            iterations: iterations,
            horizon: horizon,
            drift: driftInput ? parseFloat(driftInput) : null,
            volatility: volatilityInput ? parseFloat(volatilityInput) : null
        };

        setLoading(true);

        try {
            const result = await runMonteCarlo(config);

            if (result.success) {
                appState.lastMonteCarloResults = result;
                displayMonteCarloResults(result);
                showToast('Simulación Monte Carlo completada', 'success');
            } else {
                showToast(result.error || 'Error en la simulación', 'error');
            }
        } catch (error) {
            showToast('Error al ejecutar simulación', 'error');
            console.error('Monte Carlo error:', error);
        } finally {
            setLoading(false);
        }
    });
}

/**
 * Muestra los resultados de Monte Carlo
 */
export function displayMonteCarloResults(result) {
    const resultsSection = document.getElementById('monteCarloResultsSection');
    const resultsContent = document.getElementById('monteCarloResultsContent');

    if (!resultsSection || !resultsContent) return;

    resultsSection.classList.remove('hidden');

    if (!result.success || !result.simulations) {
        resultsContent.innerHTML = `
            <div class="error-message">
                <p>${result.error || 'Error desconocido'}</p>
            </div>
        `;
        return;
    }

    const metrics = result.metrics;

    // Métricas principales
    let metricsHtml = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">Valor Inicial</div>
                <div class="metric-value">${metrics.initial_value.toFixed(2)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Valor Esperado Final</div>
                <div class="metric-value">${metrics.expected_final_value.toFixed(2)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">VaR 95%</div>
                <div class="metric-value">${metrics.var_95.toFixed(2)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Prob. Ganancia</div>
                <div class="metric-value">${(metrics.probability_profit * 100).toFixed(1)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Drift Anual</div>
                <div class="metric-value">${(metrics.drift * 252 * 100).toFixed(2)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Volatilidad Anual</div>
                <div class="metric-value">${(metrics.volatility * Math.sqrt(252) * 100).toFixed(2)}%</div>
            </div>
        </div>
    `;

    resultsContent.innerHTML = `
        ${metricsHtml}
        <div class="interpretation-box success" style="margin-top: var(--spacing-md);">
            <p style="white-space: pre-line;">${result.interpretation}</p>
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📈 Proyecciones de Precios</h3>
            <div id="mcTrajectoriesPlot" style="width: 100%; height: 500px;"></div>
        </div>
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Distribución de Valores Finales</h3>
            <div id="mcDistributionPlot" style="width: 100%; height: 400px;"></div>
        </div>
    `;

    renderMonteCarloCharts(result);
}

/**
 * Renderiza los gráficos de Monte Carlo usando Plotly
 */
function renderMonteCarloCharts(result) {
    if (typeof Plotly === 'undefined') return;

    const confidenceBands = result.confidence_bands;
    const metrics = result.metrics;
    const xValues = Array.from({ length: metrics.horizon + 1 }, (_, i) => i);

    // Gráfico de proyecciones
    const trajectoryTraces = [
        {
            x: xValues,
            y: confidenceBands.p50,
            name: 'Mediana (p50)',
            line: { color: '#6366f1', width: 3 },
            type: 'scatter',
            mode: 'lines'
        },
        {
            x: xValues,
            y: confidenceBands.p5,
            name: 'Percentil 5',
            line: { color: 'rgba(239, 68, 68, 0.3)', width: 1 },
            type: 'scatter',
            mode: 'lines',
            fill: null
        },
        {
            x: xValues,
            y: confidenceBands.p95,
            name: 'Percentil 95',
            line: { color: 'rgba(34, 197, 94, 0.3)', width: 1 },
            type: 'scatter',
            mode: 'lines',
            fill: 'tonexty',
            fillcolor: 'rgba(99, 102, 241, 0.1)'
        }
    ];

    // Mostrar algunas trayectorias individuales aleatorias (ej. 10)
    const numRandomSims = Math.min(10, result.simulations.length);
    for (let i = 0; i < numRandomSims; i++) {
        trajectoryTraces.push({
            x: xValues,
            y: result.simulations[i],
            name: `Sim ${i + 1}`,
            line: { color: 'rgba(148, 163, 184, 0.2)', width: 1 },
            type: 'scatter',
            mode: 'lines',
            showlegend: false
        });
    }

    const trajectoryLayout = {
        title: 'Simulación de Caminos de Precios (Brownian Motion)',
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        xaxis: { title: 'Días (Horizonte)', gridcolor: '#334155' },
        yaxis: { title: 'Precio', gridcolor: '#334155' }
    };

    Plotly.newPlot('mcTrajectoriesPlot', trajectoryTraces, trajectoryLayout, { responsive: true });

    // Histograma de valores finales
    const finalValues = result.simulations.map(sim => sim[sim.length - 1]);

    const distTraces = [{
        x: finalValues,
        type: 'histogram',
        nbinsx: 50,
        marker: { color: '#8b5cf6', opacity: 0.7 },
        name: 'Distribución Final'
    }];

    const distLayout = {
        title: 'Distribución de Resultados Finales',
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        xaxis: { title: 'Precio Final', gridcolor: '#334155' },
        yaxis: { title: 'Frecuencia', gridcolor: '#334155' },
        shapes: [
            {
                type: 'line', x0: metrics.expected_final_value, x1: metrics.expected_final_value,
                y0: 0, y1: 1, yref: 'paper', line: { color: '#6366f1', width: 2, dash: 'dash' }
            },
            {
                type: 'line', x0: metrics.var_95, x1: metrics.var_95,
                y0: 0, y1: 1, yref: 'paper', line: { color: '#ef4444', width: 2, dash: 'dot' }
            }
        ]
    };

    Plotly.newPlot('mcDistributionPlot', distTraces, distLayout, { responsive: true });
}

export function updateMonteCarloSection() {
    const section = document.getElementById('mcSection');
    const select = document.getElementById('mcDataset');
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
