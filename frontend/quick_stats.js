// =============================================
// Quick Stats - Análisis Rápido
// =============================================

/**
 * API calls for Quick Stats
 */
async function analyzeSingleVariable(datasetId, variable) {
    const response = await fetch(`${API_BASE_URL}/quick-stats/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, variable })
    });
    return await response.json();
}

async function analyzeDualVariables(datasetId, variableX, variableY) {
    const response = await fetch(`${API_BASE_URL}/quick-stats/dual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, variable_x: variableX, variable_y: variableY })
    });
    return await response.json();
}

/**
 * Initialize Quick Stats section
 */
function initQuickStats() {
    const datasetSelect = document.getElementById('quickStatsDataset');
    const singleVarSelect = document.getElementById('singleVariable');
    const variableXSelect = document.getElementById('variableX');
    const variableYSelect = document.getElementById('variableY');
    const analyzeSingleBtn = document.getElementById('analyzeSingleBtn');
    const analyzeDualBtn = document.getElementById('analyzeDualBtn');

    // Tab switching
    document.querySelectorAll('.stats-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.stats-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabType = tab.dataset.tab;
            document.getElementById('singleVarPanel').classList.toggle('hidden', tabType !== 'single');
            document.getElementById('dualVarPanel').classList.toggle('hidden', tabType !== 'dual');
        });
    });

    // Dataset selection
    datasetSelect.addEventListener('change', async (e) => {
        const datasetId = e.target.value;
        if (!datasetId) {
            [singleVarSelect, variableXSelect, variableYSelect].forEach(sel => {
                sel.innerHTML = '<option value="">Selecciona una variable...</option>';
            });
            return;
        }

        try {
            const dataset = appState.datasets.find(d => d.id === datasetId);
            if (!dataset) return;

            const columnOptions = dataset.columns.map(col =>
                `<option value="${col}">${col}</option>`
            ).join('');

            singleVarSelect.innerHTML = '<option value="">Selecciona una variable...</option>' + columnOptions;
            variableXSelect.innerHTML = '<option value="">Selecciona variable X...</option>' + columnOptions;
            variableYSelect.innerHTML = '<option value="">Selecciona variable Y...</option>' + columnOptions;
        } catch (error) {
            showToast('Error al cargar columnas', 'error');
        }
    });

    // Single variable analysis
    analyzeSingleBtn.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const variable = singleVarSelect.value;

        if (!datasetId || !variable) {
            showToast('Selecciona un dataset y una variable', 'error');
            return;
        }

        try {
            setLoading(true);
            const result = await analyzeSingleVariable(datasetId, variable);

            if (result.success) {
                renderSingleVariableResults(result);
                document.getElementById('quickStatsResultsSection').classList.remove('hidden');
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
    analyzeDualBtn.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const variableX = variableXSelect.value;
        const variableY = variableYSelect.value;

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
            const result = await analyzeDualVariables(datasetId, variableX, variableY);

            if (result.success) {
                renderDualVariableResults(result);
                document.getElementById('quickStatsResultsSection').classList.remove('hidden');
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
}

/**
 * Render single variable results
 */
function renderSingleVariableResults(result) {
    const container = document.getElementById('quickStatsResultsContent');

    if (result.type === 'categorical') {
        // Categorical variable
        const topCategoriesHtml = Object.entries(result.top_categories)
            .map(([cat, count]) => `<li>${cat}: ${count}</li>`)
            .join('');

        container.innerHTML = `
            <div class="stats-section">
                <h3 class="stats-section-title">📊 Variable Categórica: ${result.variable}</h3>
                
                <div class="stats-results-grid">
                    <div class="stats-card">
                        <div class="stats-card-title">Observaciones</div>
                        <div class="stats-card-value">${result.n_observations.toLocaleString()}</div>
                    </div>
                    <div class="stats-card">
                        <div class="stats-card-title">Categorías Únicas</div>
                        <div class="stats-card-value">${result.n_unique}</div>
                    </div>
                    <div class="stats-card">
                        <div class="stats-card-title">Moda</div>
                        <div class="stats-card-value" style="font-size: 1.2rem;">${result.mode}</div>
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
        // Numeric variable
        const stats = result.statistics;
        container.innerHTML = `
            <div class="stats-section">
                <h3 class="stats-section-title">📈 Variable Numérica: ${result.variable}</h3>
                
                <div class="stats-section">
                    <h4>Tendencia Central</h4>
                    <div class="stats-results-grid">
                        <div class="stats-card">
                            <div class="stats-card-title">Media (μ)</div>
                            <div class="stats-card-value">${stats.central_tendency.mean}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Mediana</div>
                            <div class="stats-card-value">${stats.central_tendency.median}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Moda</div>
                            <div class="stats-card-value">${stats.central_tendency.mode}</div>
                        </div>
                    </div>
                </div>

                <div class="stats-section">
                    <h4>Dispersión</h4>
                    <div class="stats-results-grid">
                        <div class="stats-card">
                            <div class="stats-card-title">Desv. Estándar (σ)</div>
                            <div class="stats-card-value">${stats.dispersion.std}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Varianza (σ²)</div>
                            <div class="stats-card-value">${stats.dispersion.variance}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Error Estándar</div>
                            <div class="stats-card-value">${stats.dispersion.sem}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Coef. Variación</div>
                            <div class="stats-card-value">${stats.dispersion.cv}%</div>
                        </div>
                    </div>
                </div>

                <div class="stats-section">
                    <h4>Rango</h4>
                    <div class="stats-results-grid">
                        <div class="stats-card">
                            <div class="stats-card-title">Mínimo</div>
                            <div class="stats-card-value">${stats.range.min}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Máximo</div>
                            <div class="stats-card-value">${stats.range.max}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Rango</div>
                            <div class="stats-card-value">${stats.range.range}</div>
                        </div>
                    </div>
                </div>

                <div class="stats-section">
                    <h4>Cuartiles</h4>
                    <div class="stats-results-grid">
                        <div class="stats-card">
                            <div class="stats-card-title">Q1 (25%)</div>
                            <div class="stats-card-value">${stats.quartiles.q1}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Q2 (50%)</div>
                            <div class="stats-card-value">${stats.quartiles.q2}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Q3 (75%)</div>
                            <div class="stats-card-value">${stats.quartiles.q3}</div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">IQR</div>
                            <div class="stats-card-value">${stats.quartiles.iqr}</div>
                        </div>
                    </div>
                </div>

                <div class="stats-section">
                    <h4>Forma de la Distribución</h4>
                    <div class="stats-results-grid">
                        <div class="stats-card">
                            <div class="stats-card-title">Asimetría</div>
                            <div class="stats-card-value">${stats.shape.skewness}</div>
                            <div class="stats-card-subtitle">
                                ${stats.shape.skewness > 0 ? 'Sesgada a la derecha' : stats.shape.skewness < 0 ? 'Sesgada a la izquierda' : 'Simétrica'}
                            </div>
                        </div>
                        <div class="stats-card">
                            <div class="stats-card-title">Curtosis</div>
                            <div class="stats-card-value">${stats.shape.kurtosis}</div>
                            <div class="stats-card-subtitle">
                                ${stats.shape.kurtosis > 0 ? 'Leptocúrtica (picos)' : stats.shape.kurtosis < 0 ? 'Platicúrtica (plana)' : 'Mesocúrtica (normal)'}
                            </div>
                        </div>
                    </div>
                </div>

                <div style="margin-top: var(--spacing-lg);">
                    <h4>Distribución</h4>
                    <div id="quickStatsPlot"></div>
                </div>
            </div>
        `;
    }

    // Render plot
    if (result.plot) {
        const plotData = JSON.parse(result.plot);
        Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });
    }
}

/**
 * Render dual variable results
 */
function renderDualVariableResults(result) {
    const container = document.getElementById('quickStatsResultsContent');

    const corr = result.correlation;
    let strengthClass = 'weak';
    if (Math.abs(corr.pearson_r) >= 0.7) strengthClass = 'strong';
    else if (Math.abs(corr.pearson_r) >= 0.4) strengthClass = 'moderate';

    container.innerHTML = `
        <div class="stats-section">
            <h3 class="stats-section-title">
                🔗 Relación: ${result.variable_y} vs ${result.variable_x}
                <span class="correlation-badge ${strengthClass}">
                    r = ${corr.pearson_r}
                </span>
            </h3>

            <div class="interpretation-box" style="margin-bottom: var(--spacing-lg);">
                ${result.interpretation}
            </div>

            <div class="stats-results-grid">
                <div class="stats-card">
                    <div class="stats-card-title">Correlación de Pearson (r)</div>
                    <div class="stats-card-value">${corr.pearson_r}</div>
                    <div class="stats-card-subtitle">
                        ${corr.is_significant ? '✅ Significativa' : '❌ No significativa'} (p=${corr.p_value})
                    </div>
                </div>
                <div class="stats-card">
                    <div class="stats-card-title">R² (Coef. Determinación)</div>
                    <div class="stats-card-value">${corr.r_squared}</div>
                    <div class="stats-card-subtitle">
                        ${(corr.r_squared * 100).toFixed(1)}% de varianza explicada
                    </div>
                </div>
                <div class="stats-card">
                    <div class="stats-card-title">Observaciones</div>
                    <div class="stats-card-value">${result.n_observations.toLocaleString()}</div>
                </div>
            </div>

            <div class="glass-card" style="padding: var(--spacing-md); margin-top: var(--spacing-lg);">
                <h4>📐 Ecuación de Regresión Lineal</h4>
                <p style="font-size: 1.25rem; font-family: monospace; margin-top: var(--spacing-sm); color: var(--primary);">
                    ${result.regression.equation}
                </p>
                <div style="margin-top: var(--spacing-md); display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--spacing-sm);">
                    <div>
                        <span style="color: var(--text-muted);">Pendiente:</span>
                        <strong>${result.regression.slope}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted);">Intercepto:</span>
                        <strong>${result.regression.intercept}</strong>
                    </div>
                    <div>
                        <span style="color: var(--text-muted);">Error Estándar:</span>
                        <strong>${result.regression.std_error}</strong>
                    </div>
                </div>
            </div>

            <div style="margin-top: var(--spacing-lg);">
                <h4>Gráfico de Dispersión</h4>
                <div id="quickStatsPlot"></div>
            </div>
        </div>
    `;

    // Render plot
    if (result.plot) {
        const plotData = JSON.parse(result.plot);
        Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });
    }
}

/**
 * Update Quick Stats section when datasets are loaded
 */
function updateQuickStatsSection() {
    const quickStatsSection = document.getElementById('view-quick-stats');
    const quickStatsDatasetSelect = document.getElementById('quickStatsDataset');

    if (!quickStatsSection || !quickStatsDatasetSelect) return;

    if (appState.datasets.length > 0) {
        quickStatsSection.classList.remove('hidden');

        // Update dataset selector
        quickStatsDatasetSelect.innerHTML = '<option value="">Selecciona un dataset...</option>';
        appState.datasets.forEach(dataset => {
            quickStatsDatasetSelect.innerHTML += `<option value="${dataset.id}">${dataset.name}</option>`;
        });
    }
}


// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initQuickStats,
        updateQuickStatsSection,
        analyzeSingleVariable,
        analyzeDualVariables
    };
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    initQuickStats();
});
