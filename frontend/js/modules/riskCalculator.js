// =============================================
// Risk Calculator - Complete Risk Analysis Suite
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { fetchDatasetColumns, runRiskAnalysis } from '../api/client.js';
import { API_BASE_URL } from '../core/config.js';
import { handleExportExcel } from './exportManager.js';

/**
 * Initialize sub-menu navigation for Risk Calculator
 */
export function initRiskSubmenu() {
    const submenuBtns = document.querySelectorAll('.submenu-btn');

    submenuBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const service = btn.getAttribute('data-service');
            switchRiskService(service);
        });
    });
}

/**
 * Switch between risk services
 */
function switchRiskService(service) {
    // Update active button
    document.querySelectorAll('.submenu-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-service="${service}"]`).classList.add('active');

    // Update active view
    document.querySelectorAll('.risk-service-view').forEach(view => {
        view.classList.remove('active');
        view.classList.add('hidden');
    });
    document.getElementById(`risk-service-${service}`).classList.remove('hidden');
    document.getElementById(`risk-service-${service}`).classList.add('active');
}

/**
 * Inicializa todos los formularios de Risk Calculator
 */
export function initRiskForms() {
    initRiskSubmenu();
    initVarCvarForm();
    initBacktestingForm();
    initDrawdownForm();
    initVarMcForm();
}

/**
 * VaR/CVaR Form (Original)
 */
function initVarCvarForm() {
    const riskForm = document.getElementById('riskForm');
    const datasetSelect = document.getElementById('riskDataset');

    if (!riskForm || !datasetSelect) return;

    datasetSelect.addEventListener('change', riskDatasetChangeHandler);

    riskForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const datasetId = document.getElementById('riskDataset').value;
        const variable = document.getElementById('riskVariable').value;
        const method = document.getElementById('riskMethod').value;
        const confidence = parseFloat(document.getElementById('riskConfidence').value);
        const horizon = parseInt(document.getElementById('riskHorizon').value);

        if (!datasetId || !variable) {
            showToast('Selecciona dataset y variable', 'error');
            return;
        }

        setLoading(true);
        try {
            const result = await runRiskAnalysis({
                dataset_id: datasetId,
                variable: variable,
                confidence_level: confidence,
                horizon: horizon,
                method: method
            });

            if (result.success) {
                // Store results in global state for export
                appState.lastRiskResults = result.results;
                console.log('Risk results stored in appState:', appState.lastRiskResults);
                renderVarCvarResults(result.results);
                showToast('Cálculo de Riesgo completado', 'success');
            } else {
                showToast(result.error || result.detail || 'Error en cálculo', 'error');
            }

        } catch (error) {
            console.error("Error risk analysis:", error);
            showToast('Error de conexión', 'error');
        } finally {
            setLoading(false);
        }
    });
}

/**
 * Backtesting Form
 */
function initBacktestingForm() {
    const form = document.getElementById('backtestingForm');
    const datasetSelect = document.getElementById('backtestingDataset');

    if (!form || !datasetSelect) return;

    datasetSelect.addEventListener('change', async (e) => {
        await loadVariablesForRisk(e.target.value, 'backtestingVariable');
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const datasetId = document.getElementById('backtestingDataset').value;
        const variable = document.getElementById('backtestingVariable').value;
        const varMethod = document.getElementById('backtestingMethod').value;
        const confidence = parseFloat(document.getElementById('backtestingConfidence').value);
        const windowSize = parseInt(document.getElementById('backtestingWindow').value);

        if (!datasetId || !variable) {
            showToast('Selecciona dataset y variable', 'error');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/risk/backtesting`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_id: datasetId,
                    variable: variable,
                    var_method: varMethod,
                    confidence_level: confidence,
                    horizon: 1,
                    window_size: windowSize
                })
            });

            const result = await response.json();

            if (result.success) {
                // Store results in global state for export
                appState.lastRiskResults = result.results;
                renderBacktestingResults(result.results);
                showToast('Backtesting completado', 'success');
            } else {
                showToast(result.detail || 'Error en backtesting', 'error');
            }

        } catch (error) {
            console.error("Error backtesting:", error);
            showToast('Error de conexión', 'error');
        } finally {
            setLoading(false);
        }
    });
}

/**
 * Maximum Drawdown Form
 */
function initDrawdownForm() {
    const form = document.getElementById('drawdownForm');
    const datasetSelect = document.getElementById('drawdownDataset');

    if (!form || !datasetSelect) return;

    datasetSelect.addEventListener('change', async (e) => {
        await loadVariablesForRisk(e.target.value, 'drawdownVariable');
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const datasetId = document.getElementById('drawdownDataset').value;
        const variable = document.getElementById('drawdownVariable').value;

        if (!datasetId || !variable) {
            showToast('Selecciona dataset y variable', 'error');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/risk/maximum-drawdown`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_id: datasetId,
                    variable: variable
                })
            });

            const result = await response.json();

            if (result.success) {
                // Store results in global state for export
                appState.lastRiskResults = result.results;
                renderDrawdownResults(result.results);
                showToast('Maximum Drawdown calculado', 'success');
            } else {
                showToast(result.detail || 'Error en cálculo', 'error');
            }

        } catch (error) {
            console.error("Error drawdown:", error);
            showToast('Error de conexión', 'error');
        } finally {
            setLoading(false);
        }
    });
}

/**
 * VaR Monte Carlo Form
 */
function initVarMcForm() {
    const form = document.getElementById('varMcForm');
    const datasetSelect = document.getElementById('varMcDataset');

    if (!form || !datasetSelect) return;

    datasetSelect.addEventListener('change', async (e) => {
        await loadVariablesForRisk(e.target.value, 'varMcVariable');
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const datasetId = document.getElementById('varMcDataset').value;
        const variable = document.getElementById('varMcVariable').value;
        const distribution = document.getElementById('varMcDistribution').value;
        const confidence = parseFloat(document.getElementById('varMcConfidence').value);
        const horizon = parseInt(document.getElementById('varMcHorizon').value);
        const iterations = parseInt(document.getElementById('varMcIterations').value);

        if (!datasetId || !variable) {
            showToast('Selecciona dataset y variable', 'error');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/risk/var-montecarlo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_id: datasetId,
                    variable: variable,
                    confidence_level: confidence,
                    horizon: horizon,
                    iterations: iterations,
                    distribution: distribution
                })
            });

            const result = await response.json();

            if (result.success) {
                // Store results in global state for export
                appState.lastRiskResults = result.results;
                renderVarMcResults(result.results);
                showToast('VaR Monte Carlo completado', 'success');
            } else {
                showToast(result.detail || 'Error en simulación', 'error');
            }

        } catch (error) {
            console.error("Error VaR MC:", error);
            showToast('Error de conexión', 'error');
        } finally {
            setLoading(false);
        }
    });
}

/**
 * Helper: Load variables for any risk form
 * Improved with robust error handling and wider numeric type support
 */
async function loadVariablesForRisk(datasetId, selectId) {
    const variableSelect = document.getElementById(selectId);
    if (!variableSelect) return;

    // Set loading state
    variableSelect.innerHTML = '<option value="">Cargando...</option>';
    variableSelect.disabled = true;

    // Handle empty dataset selection
    if (!datasetId) {
        variableSelect.innerHTML = '<option value="">Selecciona variable...</option>';
        variableSelect.disabled = false;
        return;
    }

    try {
        const result = await fetchDatasetColumns(datasetId);
        console.log('Columns API response:', result);

        if (result && result.columns && Array.isArray(result.columns)) {
            variableSelect.innerHTML = '<option value="">Selecciona variable...</option>';

            // Enhanced numeric type detection - supports wider range of formats
            const numericCols = result.columns.filter(c => {
                const colType = (c.type || c.dtype || '').toLowerCase();
                const numericTypes = [
                    'int64', 'float64', 'int32', 'float32', 'int16', 'float16',
                    'number', 'int', 'float', 'double', 'decimal', 'numeric',
                    'integer', 'real', 'bigint', 'smallint'
                ];

                return numericTypes.some(type => colType.includes(type)) ||
                    colType.match(/^(int|float|double|decimal|numeric|real)\d*$/);
            });

            console.log('Numeric columns found:', numericCols);

            if (numericCols.length === 0) {
                variableSelect.innerHTML = '<option value="" disabled>⚠️ No hay columnas numéricas disponibles</option>';
                showToast('Este dataset no contiene columnas numéricas válidas para análisis de riesgo', 'warning');
            } else {
                numericCols.forEach(col => {
                    const option = document.createElement('option');
                    option.value = col.name;
                    option.textContent = `${col.name} (${col.type || col.dtype || 'numeric'})`;
                    variableSelect.appendChild(option);
                });
            }
        } else {
            console.error('Invalid columns response structure:', result);
            variableSelect.innerHTML = '<option value="" disabled>❌ Error en estructura de respuesta</option>';
            showToast('Error al procesar la respuesta del servidor', 'error');
        }
    } catch (error) {
        console.error("Error loading columns:", error);
        variableSelect.innerHTML = '<option value="" disabled>❌ Error de conexión</option>';
        showToast(`Error al cargar columnas: ${error.message}`, 'error');
    } finally {
        // ALWAYS ensure the select is enabled, regardless of success or failure
        variableSelect.disabled = false;
    }
}

/**
 * Maneja el cambio de dataset para VaR/CVaR (legacy)
 */
export async function riskDatasetChangeHandler(e) {
    await loadVariablesForRisk(e.target.value, 'riskVariable');
}

/**
 * Render VaR/CVaR Results
 */
export function renderVarCvarResults(results) {
    const container = document.getElementById('riskResultsSection');
    const content = document.getElementById('riskResultsContent');
    if (!container || !content) return;

    container.classList.remove('hidden');

    const varPct = (results.var * 100).toFixed(2) + '%';
    const cvarPct = (results.cvar * 100).toFixed(2) + '%';
    const horizon = results.horizon;
    const confidence = (results.confidence_level * 100).toFixed(0) + '%';

    let methodTitle = "";
    if (results.method === 'parametric') methodTitle = "Paramétrico (Normal)";
    else if (results.method === 'historical') methodTitle = "Histórico";
    else if (results.method === 'monte_carlo') methodTitle = "Monte Carlo";

    content.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">VaR (${confidence})</div>
                <div class="metric-value" style="color: #ef4444">${varPct}</div>
                <div class="metric-sublabel">Pérdida Máxima (${horizon} d)</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CVaR (Expected Shortfall)</div>
                <div class="metric-value" style="color: #b91c1c">${cvarPct}</div>
                <div class="metric-sublabel">Pérdida en el peor ${(100 - results.confidence_level * 100).toFixed(0)}%</div>
            </div>
            <div class=" metric-card">
                <div class="metric-label">Volatilidad Diaria</div>
                <div class="metric-value">${(results.sigma_daily * 100).toFixed(2)}%</div>
            </div>
        </div>
        
        <div class="plot-container glass-card" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md);">
                <h3 style="margin: 0;">Distribución de Pérdidas y Ganancias - ${methodTitle}</h3>
                <button class="btn btn-secondary export-risk-btn" style="display: flex; align-items: center; gap: 8px;">
                    <span>📊</span> Exportar a Excel
                </button>
            </div>
            ${results.plot ? `<img src="data:image/png;base64,${results.plot}" style="width: 100%; border-radius: var(--radius-md);" alt="Risk Plot" />` : '<p>No se pudo generar el gráfico</p>'}
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });

    // Add export button event listener
    const exportBtns = content.querySelectorAll('.export-risk-btn');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            handleExportExcel('risk');
        });
    });
}

/**
 * Render Backtesting Results
 */
function renderBacktestingResults(results) {
    const container = document.getElementById('riskResultsSection');
    const content = document.getElementById('riskResultsContent');
    if (!container || !content) return;

    container.classList.remove('hidden');

    const testPassed = results.test_passed ? '✅ Aprobado' : '❌ Rechazado';
    const testColor = results.test_passed ? '#10b981' : '#ef4444';

    content.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">Observaciones</div>
                <div class="metric-value">${results.total_observations}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Violaciones</div>
                <div class="metric-value" style="color: #ef4444">${results.num_violations}</div>
                <div class="metric-sublabel">${(results.violation_rate * 100).toFixed(2)}% real vs ${(results.expected_rate * 100).toFixed(2)}% esperado</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Test de Kupiec</div>
                <div class="metric-value" style="color: ${testColor}">${testPassed}</div>
                <div class="metric-sublabel">p-value: ${results.kupiec_p_value.toFixed(4)}</div>
            </div>
        </div>
        
        <div class="plot-container glass-card" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md);">
                <h3 style="margin: 0;">Backtesting: Violaciones vs VaR Predicho</h3>
                <button class="btn btn-secondary export-risk-btn" style="display: flex; align-items: center; gap: 8px;">
                    <span>📊</span> Exportar a Excel
                </button>
            </div>
            ${results.plot ? `<img src="data:image/png;base64,${results.plot}" style="width: 100%; border-radius: var(--radius-md);" alt="Backtesting Plot" />` : '<p>No se pudo generar el gráfico</p>'}
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });

    // Add export button event listener
    const exportBtns = content.querySelectorAll('.export-risk-btn');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            handleExportExcel('risk');
        });
    });
}

/**
 * Render Maximum Drawdown Results
 */
function renderDrawdownResults(results) {
    const container = document.getElementById('riskResultsSection');
    const content = document.getElementById('riskResultsContent');
    if (!container || !content) return;

    container.classList.remove('hidden');

    content.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">Maximum Drawdown</div>
                <div class="metric-value" style="color: #ef4444">${results.max_drawdown.toFixed(2)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Peak</div>
                <div class="metric-value">${results.peak_value.toFixed(2)}</div>
                <div class="metric-sublabel">${results.peak_date}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Trough</div>
                <div class="metric-value">${results.trough_value.toFixed(2)}</div>
                <div class="metric-sublabel">${results.trough_date}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Recuperación</div>
                <div class="metric-value">${results.recovery_days !== null ? results.recovery_days + ' días' : 'No recuperado'}</div>
                ${results.recovery_date ? `<div class="metric-sublabel">${results.recovery_date}</div>` : ''}
            </div>
        </div>
        
        <div class="plot-container glass-card" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md);">
                <h3 style="margin: 0;">Análisis de Drawdown</h3>
                <button class="btn btn-secondary export-risk-btn" style="display: flex; align-items: center; gap: 8px;">
                    <span>📊</span> Exportar a Excel
                </button>
            </div>
            ${results.plot ? `<img src="data:image/png;base64,${results.plot}" style="width: 100%; border-radius: var(--radius-md);" alt="Drawdown Plot" />` : '<p>No se pudo generar el gráfico</p>'}
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });

    // Add export button event listener
    const exportBtns = content.querySelectorAll('.export-risk-btn');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            handleExportExcel('risk');
        });
    });
}

/**
 * Render VaR Monte Carlo Results
 */
function renderVarMcResults(results) {
    const container = document.getElementById('riskResultsSection');
    const content = document.getElementById('riskResultsContent');
    if (!container || !content) return;

    container.classList.remove('hidden');

    const varPct = (results.var * 100).toFixed(2) + '%';
    const cvarPct = (results.cvar * 100).toFixed(2) + '%';

    content.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">VaR (${(results.confidence_level * 100).toFixed(0)}%)</div>
                <div class="metric-value" style="color: #ef4444">${varPct}</div>
                <div class="metric-sublabel">Horizonte: ${results.horizon} días</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CVaR</div>
                <div class="metric-value" style="color: #b91c1c">${cvarPct}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Iteraciones</div>
                <div class="metric-value">${results.iterations.toLocaleString()}</div>
                <div class="metric-sublabel">${results.distribution}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Volatilidad Diaria</div>
                <div class="metric-value">${(results.sigma_daily * 100).toFixed(2)}%</div>
            </div>
        </div>
        
        <div class="plot-container glass-card" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md);">
                <h3 style="margin: 0;">Monte Carlo: Simulación de Trayectorias</h3>
                <button class="btn btn-secondary export-risk-btn" style="display: flex; align-items: center; gap: 8px;">
                    <span>📊</span> Exportar a Excel
                </button>
            </div>
            ${results.plot ? `<img src="data:image/png;base64,${results.plot}" style="width: 100%; border-radius: var(--radius-md);" alt="Monte Carlo Plot" />` : '<p>No se pudo generar el gráfico</p>'}
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });

    // Add export button event listener
    const exportBtns = content.querySelectorAll('.export-risk-btn');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            handleExportExcel('risk');
        });
    });
}

/**
 * Update all risk dataset selects when datasets change
 */
export function updateRiskSection() {
    const selects = [
        'riskDataset',
        'backtestingDataset',
        'drawdownDataset',
        'varMcDataset'
    ];

    selects.forEach(selectId => {
        const datasetSelect = document.getElementById(selectId);
        if (!datasetSelect) return;

        const currentSelection = datasetSelect.value;
        datasetSelect.innerHTML = '<option value="">Selecciona un dataset...</option>';

        appState.datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.id;
            option.textContent = dataset.name;
            datasetSelect.appendChild(option);
        });

        if (currentSelection && appState.datasets.find(d => d.id === currentSelection)) {
            datasetSelect.value = currentSelection;
            datasetSelect.dispatchEvent(new Event('change'));
        }
    });
}

// Legacy export for compatibility
export function initRiskForm() {
    initRiskForms();
}

export function renderRiskResults(results) {
    renderVarCvarResults(results);
}
