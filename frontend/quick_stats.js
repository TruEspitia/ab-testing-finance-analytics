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

async function analyzeDualVariables(datasetId, variableX, variableY, correlationType = 'pearson') {
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

async function analyzeTimeSeries(datasetId, timeColumn, valueColumn, periodsAhead, autoSelect) {
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
            document.getElementById('timeSeriesPanel').classList.toggle('hidden', tabType !== 'timeseries');
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

            // Time Series specific
            const timeColSelect = document.getElementById('qsTimeColumn');
            const valueColSelect = document.getElementById('qsValueColumn');
            if (timeColSelect && valueColSelect) {
                timeColSelect.innerHTML = '<option value="">Selecciona columna temporal...</option>' + columnOptions;
                valueColSelect.innerHTML = '<option value="">Selecciona valores a analizar...</option>' + columnOptions;
            }
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
        const correlationType = document.getElementById('correlationType').value;

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

    // Time Series Analysis
    document.getElementById('analyzeTimeSeriesBtn')?.addEventListener('click', async () => {
        const datasetId = datasetSelect.value;
        const timeColumn = document.getElementById('qsTimeColumn').value;
        const valueColumn = document.getElementById('qsValueColumn').value;
        const periodsAhead = parseInt(document.getElementById('forecastPeriods').value);
        const autoSelect = document.getElementById('autoSelectParams').checked;

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
                renderTimeSeriesResults(result);
                document.getElementById('quickStatsResultsSection').classList.remove('hidden');
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

        // Helper to get current theme color
        const textColor = getComputedStyle(document.body).getPropertyValue('--text-primary').trim();

        // Override font colors for visibility
        if (!plotData.layout.font) plotData.layout.font = {};
        plotData.layout.font.color = textColor;

        Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });
    }
}

/**
 * Render dual variable results
 */
function renderDualVariableResults(result) {
    const container = document.getElementById('quickStatsResultsContent');

    if (result.correlation_type === 'full') {
        const res = result.results;

        container.innerHTML = `
            <div class="stats-section">
                <h3 class="stats-section-title">
                    🔮 Análisis Completo: ${result.variable_y} vs ${result.variable_x}
                </h3>
                
                <div class="stats-results-grid" style="grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));">
                    <!-- Pearson -->
                    <div class="glass-card" style="padding: var(--spacing-md);">
                        <h4>${res.pearson.name}</h4>
                        <div class="stats-card-value">${res.pearson.coefficient}</div>
                        <div class="stats-card-subtitle">
                           ${res.pearson.interpretation}
                        </div>
                        <div class="stats-card-subtitle">
                           p-value: ${res.pearson.p_value} (${res.pearson.is_significant ? 'Significativo' : 'No Sig.'})
                        </div>
                    </div>
                    
                    <!-- Spearman -->
                    <div class="glass-card" style="padding: var(--spacing-md);">
                        <h4>${res.spearman.name}</h4>
                        <div class="stats-card-value">${res.spearman.coefficient}</div>
                        <div class="stats-card-subtitle">
                           ${res.spearman.interpretation}
                        </div>
                         <div class="stats-card-subtitle">
                           p-value: ${res.spearman.p_value} (${res.spearman.is_significant ? 'Significativo' : 'No Sig.'})
                        </div>
                    </div>
                    
                    <!-- Kendall -->
                    <div class="glass-card" style="padding: var(--spacing-md);">
                        <h4>${res.kendall.name}</h4>
                        <div class="stats-card-value">${res.kendall.coefficient}</div>
                         <div class="stats-card-subtitle">
                           ${res.kendall.interpretation}
                        </div>
                        <div class="stats-card-subtitle">
                           p-value: ${res.kendall.p_value} (${res.kendall.is_significant ? 'Significativo' : 'No Sig.'})
                        </div>
                    </div>
                </div>

                 <div class="glass-card" style="padding: var(--spacing-md); margin-top: var(--spacing-lg);">
                    <h4>📐 Regresión Lineal (Referencia)</h4>
                    <p style="font-family: monospace; color: var(--primary);">
                        ${result.regression.equation} (R² = ${result.regression.r_squared})
                    </p>
                </div>

                <div style="margin-top: var(--spacing-lg);">
                    <h4>Visualización 3D (Relación + Movimiento)</h4>
                    <p style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 10px;">
                        El eje Z representa la "distancia de rango" entre las variables, destacando discrepancias no lineales.
                    </p>
                    <div id="quickStatsPlot3D" style="height: 600px;"></div>
                </div>
            </div>
        `;

        // Render 3D Plot
        if (result.plot_3d) {
            const textColor = getComputedStyle(document.body).getPropertyValue('--text-primary').trim();

            const layout3d = {
                title: 'Análisis de Relación 3D',
                autosize: true,
                scene: {
                    xaxis: { title: result.variable_x, titlefont: { color: textColor }, tickfont: { color: textColor } },
                    yaxis: { title: result.variable_y, titlefont: { color: textColor }, tickfont: { color: textColor } },
                    zaxis: { title: 'Divergencia (Rank Diff)', titlefont: { color: textColor }, tickfont: { color: textColor } },
                    camera: {
                        eye: { x: 1.5, y: 1.5, z: 1.5 }
                    }
                },
                margin: { l: 0, r: 0, b: 0, t: 30 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: textColor }
            };

            Plotly.newPlot('quickStatsPlot3D', [result.plot_3d], layout3d, { responsive: true, displayModeBar: true });
        }

    } else {
        // Standard Single Analysis Render (Legacy + supported)
        const corr = result.correlation;
        const methodLabel = result.correlation_method || 'Correlación de Pearson (r)';
        let strengthClass = 'weak';
        if (Math.abs(corr.coefficient) >= 0.7) strengthClass = 'strong';
        else if (Math.abs(corr.coefficient) >= 0.4) strengthClass = 'moderate';

        container.innerHTML = `
            <div class="stats-section">
                <h3 class="stats-section-title">
                    🔗 Relación: ${result.variable_y} vs ${result.variable_x}
                    <span class="correlation-badge ${strengthClass}">
                        ${methodLabel.split(' ')[0]} = ${corr.coefficient}
                    </span>
                </h3>

                <div class="interpretation-box" style="margin-bottom: var(--spacing-lg);">
                    ${result.interpretation}
                </div>

                <div class="stats-results-grid">
                    <div class="stats-card">
                        <div class="stats-card-title">${methodLabel}</div>
                        <div class="stats-card-value">${corr.coefficient}</div>
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
                
                 <!-- Optional 3D Plot for Single Analysis if returned -->
                 ${result.plot_3d ? `
                 <div style="margin-top: var(--spacing-lg);">
                    <h4>Visualización 3D (Relación + Movimiento)</h4>
                     <div id="quickStatsPlot3D" style="height: 500px;"></div>
                 </div>` : ''}
            </div>
        `;

        // Helper to get current theme color
        const getThemeColor = () => getComputedStyle(document.body).getPropertyValue('--text-primary').trim();

        // Render 2D plot
        if (result.plot) {
            const plotData = JSON.parse(result.plot);
            const textColor = getThemeColor();

            // Override font colors for visibility
            if (!plotData.layout.font) plotData.layout.font = {};
            plotData.layout.font.color = textColor;

            // Ensure titles are colored correctly
            if (plotData.layout.title) plotData.layout.title.font = { color: textColor };
            if (plotData.layout.xaxis && plotData.layout.xaxis.title) plotData.layout.xaxis.title.font = { color: textColor };
            if (plotData.layout.yaxis && plotData.layout.yaxis.title) plotData.layout.yaxis.title.font = { color: textColor };

            Plotly.newPlot('quickStatsPlot', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });
        }

        // Render 3D plot if available
        if (result.plot_3d) {
            const textColor = getThemeColor();
            const layout3d = {
                title: 'Relación 3D',
                autosize: true,
                scene: {
                    xaxis: { title: result.variable_x, titlefont: { color: textColor }, tickfont: { color: textColor } },
                    yaxis: { title: result.variable_y, titlefont: { color: textColor }, tickfont: { color: textColor } },
                    zaxis: { title: 'Divergencia', titlefont: { color: textColor }, tickfont: { color: textColor } },
                },
                margin: { l: 0, r: 0, b: 0, t: 30 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: textColor }
            };
            Plotly.newPlot('quickStatsPlot3D', [result.plot_3d], layout3d, { responsive: true, displayModeBar: true });
        }
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


function renderTimeSeriesResults(result) {
    const container = document.getElementById('quickStatsResultsContent');

    container.innerHTML = `
        <div class="stats-section">
            <h3 class="stats-section-title">📈 Análisis de Serie Temporal - ARIMA${result.model_params.order}</h3>
            
            <div class="interpretation-box" style="margin-bottom: 20px;">
                <pre style="white-space: pre-wrap; font-family: inherit;">${result.interpretation}</pre>
            </div>
            
            <div class="stats-results-grid">
                <div class="stats-card">
                    <div class="stats-card-title">RMSE</div>
                    <div class="stats-card-value">${result.metrics.rmse.toFixed(4)}</div>
                </div>
                <div class="stats-card">
                    <div class="stats-card-title">MAE</div>
                    <div class="stats-card-value">${result.metrics.mae.toFixed(4)}</div>
                </div>
                <div class="stats-card">
                    <div class="stats-card-title">AIC</div>
                    <div class="stats-card-value">${result.model_params.aic.toFixed(2)}</div>
                </div>
            </div>
            
            <div id="arimaPlot" style="margin-top: 20px; height: 500px;"></div>
        </div>
    `;

    // Crear gráfico con Plotly
    renderARIMAPlot(result);
}

function renderARIMAPlot(result) {
    // Helper to get current theme color
    const textColor = getComputedStyle(document.body).getPropertyValue('--text-primary').trim();

    const historical = {
        x: result.historical_data.dates,
        y: result.historical_data.values,
        name: 'Datos Históricos',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#3b82f6' }
    };

    const fitted = {
        x: result.historical_data.dates,
        y: result.historical_data.fitted_values,
        name: 'Valores Ajustados',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#10b981', dash: 'dot' }
    };

    const forecast = {
        x: result.forecast.dates,
        y: result.forecast.values,
        name: 'Pronóstico',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#f59e0b' }
    };

    // Banda de confianza
    const upperBound = {
        x: result.forecast.dates,
        y: result.forecast.upper_bound,
        fill: 'tonexty',
        fillcolor: 'rgba(245, 158, 11, 0.2)',
        line: { color: 'transparent' },
        showlegend: false,
        type: 'scatter',
        name: 'IC Superior'
    };

    const lowerBound = {
        x: result.forecast.dates,
        y: result.forecast.lower_bound,
        fill: 'tonexty',
        fillcolor: 'rgba(245, 158, 11, 0.2)',
        line: { color: 'transparent' }, // Transparent line for lower bound to avoid double drawing
        name: 'IC 95%',
        type: 'scatter'
    };

    const layout = {
        title: 'Serie Temporal con Pronóstico ARIMA',
        xaxis: { title: 'Fecha', titlefont: { color: textColor }, tickfont: { color: textColor } },
        yaxis: { title: 'Valor', titlefont: { color: textColor }, tickfont: { color: textColor } },
        hovermode: 'x unified',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: textColor },
        legend: { orientation: 'h', y: -0.2 }
    };

    Plotly.newPlot('arimaPlot',
        [historical, fitted, lowerBound, upperBound, forecast],
        layout,
        { responsive: true }
    );
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initQuickStats,
        updateQuickStatsSection,
        analyzeSingleVariable,
        analyzeDualVariables,
        analyzeTimeSeries
    };
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    initQuickStats();
});
