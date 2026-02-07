// =============================================
// Risk Calculator - Cálculo de VaR y CVaR
// =============================================

import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { fetchDatasetColumns, runRiskAnalysis } from '../api/client.js';

/**
 * Inicializa el formulario de Risk Calculator
 */
export function initRiskForm() {
    const riskForm = document.getElementById('riskForm');
    const datasetSelect = document.getElementById('riskDataset');

    if (!riskForm || !datasetSelect) return;

    // Listener para cargar columnas
    datasetSelect.addEventListener('change', riskDatasetChangeHandler);

    // Initial populate if dataset already selected (part of updateRiskSection)

    // Form submit
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
                renderRiskResults(result.results);
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
 * Maneja el cambio de dataset para cargar columnas numéricas
 */
export async function riskDatasetChangeHandler(e) {
    const datasetId = e.target.value;
    const variableSelect = document.getElementById('riskVariable');
    if (!variableSelect) return;

    variableSelect.innerHTML = '<option value="">Cargando...</option>';
    variableSelect.disabled = true;

    if (!datasetId) {
        variableSelect.innerHTML = '<option value="">Selecciona variable...</option>';
        return;
    }

    try {
        const result = await fetchDatasetColumns(datasetId);
        if (result.success) {
            variableSelect.innerHTML = '<option value="">Selecciona variable...</option>';

            // Filtrar solo numéricas
            const numericCols = result.columns.filter(c =>
                ['int64', 'float64', 'int32', 'float32', 'number'].some(type => c.type.includes(type))
            );

            numericCols.forEach(col => {
                const option = document.createElement('option');
                option.value = col.name;
                option.textContent = col.name;
                variableSelect.appendChild(option);
            });
            variableSelect.disabled = false;
        }
    } catch (error) {
        console.error("Error loading columns for risk:", error);
        variableSelect.innerHTML = '<option value="">Error al cargar</option>';
    }
}

/**
 * Renderiza los resultados del cálculo de riesgo
 */
export function renderRiskResults(results) {
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
            <div class="metric-card">
                <div class="metric-label">Volatilidad Diaria</div>
                <div class="metric-value">${(results.sigma_daily * 100).toFixed(2)}%</div>
            </div>
        </div>
        
        <div class="plot-container glass-card" style="margin-top: var(--spacing-lg); padding: var(--spacing-md); border-radius: var(--radius-lg); border: 1px solid var(--glass-border);">
            <h3 style="margin-bottom: var(--spacing-md);">Distribución de Pérdidas y Ganancias - ${methodTitle}</h3>
            ${results.plot ? `<img src="data:image/png;base64,${results.plot}" style="width: 100%; border-radius: var(--radius-md);" alt="Risk Plot" />` : '<p>No se pudo generar el gráfico</p>'}
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });
}

export function updateRiskSection() {
    const datasetSelect = document.getElementById('riskDataset');
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
}
