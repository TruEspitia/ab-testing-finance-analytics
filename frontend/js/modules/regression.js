// =============================================
// Regresión / Curve Fitting
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { runRegression, fetchAvailableFunctions } from '../api/client.js';

/**
 * Inicializa el formulario de regresión
 */
export async function initRegressionForm() {
    const form = document.getElementById('regressionForm');
    const datasetSelect = document.getElementById('regressionDataset');
    const xColumnSelect = document.getElementById('xColumn');
    const yColumnSelect = document.getElementById('yColumn');
    const functionSelect = document.getElementById('functionSelect');
    const functionFormula = document.getElementById('functionFormula');

    if (!form || !datasetSelect) return;

    // Cargar funciones disponibles
    try {
        const functionsData = await fetchAvailableFunctions();
        if (functionsData.success) {
            appState.availableFunctions = functionsData.functions;
            populateFunctionSelect();
        }
    } catch (error) {
        console.error('Error loading functions:', error);
    }

    // Cuando se selecciona un dataset, actualizar las columnas
    datasetSelect.addEventListener('change', () => {
        const datasetId = datasetSelect.value;
        if (datasetId) {
            const dataset = appState.datasets.find(d => d.id === datasetId);
            if (dataset) {
                populateRegressionColumnSelects(dataset.columns);
            }
        } else {
            if (xColumnSelect) xColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
            if (yColumnSelect) yColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
        }
    });

    // Mostrar fórmula cuando se selecciona una función
    if (functionSelect) {
        functionSelect.addEventListener('change', () => {
            const funcName = functionSelect.value;
            const func = appState.availableFunctions.find(f => f.name === funcName);
            if (func) {
                if (functionFormula) functionFormula.textContent = `Fórmula: ${func.formula}`;
            } else {
                if (functionFormula) functionFormula.textContent = 'Selecciona una función para ver su fórmula';
            }
        });
    }

    // Submit del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleRegressionSubmit();
    });
}

/**
 * Puebla los selects de columnas para regresión
 */
export function populateRegressionColumnSelects(columns) {
    const xColumnSelect = document.getElementById('xColumn');
    const yColumnSelect = document.getElementById('yColumn');

    [xColumnSelect, yColumnSelect].forEach(select => {
        if (!select) return;
        select.innerHTML = '<option value="">Selecciona columna...</option>';
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            select.appendChild(option);
        });
    });
}

/**
 * Puebla el select de funciones matemáticas
 */
export function populateFunctionSelect() {
    const functionSelect = document.getElementById('functionSelect');
    if (!functionSelect) return;

    functionSelect.innerHTML = '<option value="">Selecciona una función...</option>';

    const groups = {};
    appState.availableFunctions.forEach(func => {
        const parts = func.name.split('_');
        const prefix = parts[0];
        if (!groups[prefix]) {
            groups[prefix] = [];
        }
        groups[prefix].push(func);
    });

    Object.keys(groups).sort().forEach(groupName => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = groupName.charAt(0).toUpperCase() + groupName.slice(1);

        groups[groupName].sort((a, b) => a.name.localeCompare(b.name)).forEach(func => {
            const option = document.createElement('option');
            option.value = func.name;
            option.textContent = func.name.replace(/_/g, ' ');
            optgroup.appendChild(option);
        });

        functionSelect.appendChild(optgroup);
    });
}

/**
 * Maneja el submit del formulario de regresión
 */
export async function handleRegressionSubmit() {
    const config = {
        dataset_id: document.getElementById('regressionDataset')?.value,
        x_column: document.getElementById('xColumn')?.value,
        y_column: document.getElementById('yColumn')?.value,
        function_name: document.getElementById('functionSelect')?.value,
        engine_type: document.getElementById('engineSelect')?.value
    };

    if (!config.dataset_id || !config.x_column || !config.y_column || !config.function_name) {
        showToast('Por favor completa todos los campos', 'error');
        return;
    }

    try {
        setLoading(true);

        const result = await runRegression(config);

        if (result.success) {
            appState.lastRegressionResults = result;
            renderRegressionResults(result);
            document.getElementById('regressionResultsSection')?.classList.remove('hidden');

            document.getElementById('regressionResultsSection')?.scrollIntoView({
                behavior: 'smooth'
            });

            showToast('Regresión completada', 'success');
        } else {
            showToast(result.error || 'Error en la regresión', 'error');
        }

    } catch (error) {
        showToast('Error al ejecutar regresión', 'error');
        console.error('Regression error:', error);
    } finally {
        setLoading(false);
    }
}

/**
 * Renderiza los resultados de la regresión
 */
export function renderRegressionResults(result) {
    const container = document.getElementById('regressionResultsContent');
    if (!container) return;

    const r2Class = result.r_squared >= 0.85 ? 'positive' : result.r_squared >= 0.70 ? '' : 'negative';

    container.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">R² (Coef. Determinación)</div>
                <div class="metric-value ${r2Class}">${result.r_squared.toFixed(4)}</div>
                <div class="metric-sublabel">Calidad del ajuste</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">RMSE</div>
                <div class="metric-value">${result.rmse.toFixed(4)}</div>
                <div class="metric-sublabel">Error cuadrático medio</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">MAPE</div>
                <div class="metric-value">${(result.mape || 0).toFixed(2)}%</div>
                <div class="metric-sublabel">Error porcentual</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Iteraciones</div>
                <div class="metric-value">${result.iterations || 'N/A'}</div>
            </div>
        </div>
        
        <div class="glass-card" style="margin-top: var(--spacing-md); padding: var(--spacing-md);">
            <h3 style="margin-bottom: var(--spacing-sm);">📝 Parámetros Optimizados</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--spacing-md);">
                ${Object.entries(result.parameters).map(([param, value]) => `
                    <div class="param-card" style="background: var(--glass-bg); padding: var(--spacing-sm); border-radius: var(--radius-sm); border: 1px solid var(--glass-border);">
                        <div style="color: var(--text-muted); font-size: 0.8rem;">Parámetro <strong>${param}</strong></div>
                        <div style="font-weight: 600; font-size: 1.1rem;">${value.toFixed(6)}</div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Gráfico de Ajuste</h3>
            <div id="regressionPlotlyChart" style="width: 100%; height: 500px;"></div>
        </div>
    `;

    renderRegressionChart(result);
}

function renderRegressionChart(result) {
    if (typeof Plotly === 'undefined') return;

    const traces = [
        {
            x: result.plot_data.x_original,
            y: result.plot_data.y_original,
            mode: 'markers',
            name: 'Datos Originales',
            marker: { color: '#94a3b8', size: 6, opacity: 0.6 }
        },
        {
            x: result.plot_data.x_fit,
            y: result.plot_data.y_fit,
            mode: 'lines',
            name: 'Curva de Ajuste',
            line: { color: '#6366f1', width: 3 }
        }
    ];

    const layout = {
        title: `Ajuste: ${result.function_name.replace(/_/g, ' ')}`,
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        xaxis: { title: result.x_column, gridcolor: '#334155' },
        yaxis: { title: result.y_column, gridcolor: '#334155' }
    };

    Plotly.newPlot('regressionPlotlyChart', traces, layout, { responsive: true });
}

export function updateRegressionSection() {
    const section = document.getElementById('regressionSection');
    const select = document.getElementById('regressionDataset');
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
