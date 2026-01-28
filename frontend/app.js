// =============================================
// Configuración y constantes
// =============================================
const API_BASE_URL = '/api';

// Estado global de la aplicación
const appState = {
    datasets: [],
    selectedDataset: null,
    currentPreview: null
};

// =============================================
// Utilidades
// =============================================

/**
 * Muestra una notificación toast
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span style="font-size: 1.5rem;">${icon}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/**
 * Muestra/oculta el overlay de loading
 */
function setLoading(isLoading) {
    const overlay = document.getElementById('loadingOverlay');
    if (isLoading) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

/**
 * Formatea bytes a formato legible
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Formatea fecha
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// =============================================
// API Calls
// =============================================

/**
 * Sube un archivo al servidor
 */
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

/**
 * Obtiene la lista de datasets
 */
async function fetchDatasets() {
    const response = await fetch(`${API_BASE_URL}/datasets`);
    return await response.json();
}

/**
 * Obtiene preview de un dataset
 */
async function fetchDatasetPreview(datasetId, nRows = 100) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/preview?n_rows=${nRows}`);
    return await response.json();
}

/**
 * Elimina un dataset
 */
async function deleteDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}`, {
        method: 'DELETE'
    });
    return await response.json();
}

/**
 * Ejecuta análisis A/B
 */
async function runAnalysis(config) {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}

/**
 * Obtiene estadísticas del sistema
 */
async function fetchStats() {
    const response = await fetch(`${API_BASE_URL}/stats`);
    return await response.json();
}

// =============================================
// Gestión de Archivos
// =============================================

function initFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Click para seleccionar archivo
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag & Drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await handleFileUpload(files[0]);
        }
    });

    // Cambio de archivo input
    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            await handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    // Validar tamaño (50MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Archivo demasiado grande. Máximo 50MB', 'error');
        return;
    }

    // Validar formato
    const validExtensions = ['csv', 'xlsx', 'xls', 'json'];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(extension)) {
        showToast('Formato no soportado. Use CSV, XLSX o JSON', 'error');
        return;
    }

    // Mostrar progreso
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadArea = document.getElementById('uploadArea');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    progressFill.style.width = '30%';
    progressText.textContent = 'Subiendo archivo...';

    try {
        // Subir archivo
        const result = await uploadFile(file);

        progressFill.style.width = '100%';
        progressText.textContent = 'Archivo cargado exitosamente';

        if (result.success) {
            showToast(result.message, 'success');

            // Actualizar lista de datasets
            await loadDatasets();

            // Mostrar secciones
            document.getElementById('previewSection').classList.remove('hidden');
            document.getElementById('analysisSection').classList.remove('hidden');

        } else {
            showToast(result.error || 'Error al cargar archivo', 'error');
        }

    } catch (error) {
        showToast('Error de conexión con el servidor', 'error');
        console.error('Upload error:', error);
    } finally {
        // Resetear UI
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            uploadArea.classList.remove('hidden');
            progressFill.style.width = '0%';
            document.getElementById('fileInput').value = '';
        }, 2000);
    }
}

// =============================================
// Gestión de Datasets
// =============================================

async function loadDatasets() {
    try {
        const data = await fetchDatasets();
        appState.datasets = data.datasets;

        renderDatasetsList();
        updateDatasetSelectors();
        await updateStats();

    } catch (error) {
        showToast('Error al cargar datasets', 'error');
        console.error('Load datasets error:', error);
    }
}

function renderDatasetsList() {
    const container = document.getElementById('datasetsList');

    if (appState.datasets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>No hay datasets cargados</p>
                <p class="empty-hint">Sube un archivo para comenzar</p>
            </div>
        `;
        return;
    }

    container.innerHTML = appState.datasets.map(dataset => `
        <div class="dataset-item ${appState.selectedDataset?.id === dataset.id ? 'active' : ''}" 
             data-id="${dataset.id}">
            <div class="dataset-info">
                <div class="dataset-name">${dataset.name}</div>
                <div class="dataset-meta">
                    <span>📊 ${dataset.rows.toLocaleString()} filas</span>
                    <span>📋 ${dataset.columns.length} columnas</span>
                    <span>💾 ${formatBytes(dataset.size_bytes)}</span>
                    <span>📅 ${formatDate(dataset.uploaded_at)}</span>
                </div>
            </div>
            <div class="dataset-actions">
                <button class="btn btn-secondary btn-preview" data-id="${dataset.id}">
                    <span>👁️</span> Ver
                </button>
                <button class="btn btn-danger btn-delete" data-id="${dataset.id}">
                    <span>🗑️</span>
                </button>
            </div>
        </div>
    `).join('');

    // Event listeners
    container.querySelectorAll('.btn-preview').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            await loadDatasetPreview(id);
        });
    });

    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            if (confirm('¿Estás seguro de eliminar este dataset?')) {
                await handleDeleteDataset(id);
            }
        });
    });

    container.querySelectorAll('.dataset-item').forEach(item => {
        item.addEventListener('click', async () => {
            const id = item.dataset.id;
            await loadDatasetPreview(id);
        });
    });
}

async function handleDeleteDataset(datasetId) {
    try {
        setLoading(true);
        await deleteDataset(datasetId);
        showToast('Dataset eliminado', 'success');
        await loadDatasets();

        // Si era el dataset seleccionado, limpiar preview
        if (appState.selectedDataset?.id === datasetId) {
            appState.selectedDataset = null;
            appState.currentPreview = null;
            document.getElementById('tableBody').innerHTML = '';
            document.getElementById('tableHead').innerHTML = '';
        }

    } catch (error) {
        showToast('Error al eliminar dataset', 'error');
    } finally {
        setLoading(false);
    }
}

function updateDatasetSelectors() {
    const selectors = [
        document.getElementById('datasetSelector'),
        document.getElementById('analysisDataset')
    ];

    selectors.forEach(selector => {
        const currentValue = selector.value;
        selector.innerHTML = '<option value="">Selecciona un dataset...</option>';

        appState.datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.id;
            option.textContent = `${dataset.name} (${dataset.rows} filas)`;
            selector.appendChild(option);
        });

        // Restaurar selección si existe
        if (currentValue) {
            selector.value = currentValue;
        }
    });
}

async function updateStats() {
    try {
        const stats = await fetchStats();

        document.getElementById('datasetCount').textContent = stats.total_datasets;
        document.getElementById('memoryUsage').textContent =
            stats.total_memory_mb.toFixed(2) + ' MB';

    } catch (error) {
        console.error('Stats error:', error);
    }
}

// =============================================
// Preview de Datos
// =============================================

async function loadDatasetPreview(datasetId) {
    try {
        setLoading(true);

        const preview = await fetchDatasetPreview(datasetId);
        appState.currentPreview = preview;
        appState.selectedDataset = appState.datasets.find(d => d.id === datasetId);

        renderDataTable(preview);
        renderDatasetsList(); // Actualizar para marcar el activo

        // Actualizar selector de preview
        document.getElementById('datasetSelector').value = datasetId;

        showToast('Preview cargado', 'success');

    } catch (error) {
        showToast('Error al cargar preview', 'error');
    } finally {
        setLoading(false);
    }
}

function renderDataTable(preview) {
    const tableHead = document.getElementById('tableHead');
    const tableBody = document.getElementById('tableBody');
    const previewInfo = document.getElementById('previewInfo');

    // Header
    tableHead.innerHTML = `
        <tr>
            ${preview.columns.map(col => `<th>${col}</th>`).join('')}
        </tr>
    `;

    // Body
    tableBody.innerHTML = preview.data.map(row => `
        <tr>
            ${preview.columns.map(col => {
        let value = row[col];
        if (value === null || value === undefined) {
            value = '<span style="color: var(--text-muted); font-style: italic;">null</span>';
        }
        return `<td>${value}</td>`;
    }).join('')}
        </tr>
    `).join('');

    // Info
    previewInfo.textContent =
        `Mostrando ${preview.preview_rows} de ${preview.total_rows.toLocaleString()} filas`;
}

function initPreviewControls() {
    const selector = document.getElementById('datasetSelector');
    const refreshBtn = document.getElementById('refreshPreviewBtn');

    selector.addEventListener('change', async (e) => {
        if (e.target.value) {
            await loadDatasetPreview(e.target.value);
        }
    });

    refreshBtn.addEventListener('click', async () => {
        if (appState.selectedDataset) {
            await loadDatasetPreview(appState.selectedDataset.id);
        } else {
            showToast('Selecciona un dataset primero', 'info');
        }
    });
}

// =============================================
// Análisis A/B Testing
// =============================================

function initAnalysisForm() {
    const form = document.getElementById('analysisForm');
    const datasetSelect = document.getElementById('analysisDataset');
    const groupColumnSelect = document.getElementById('groupColumn');
    const targetColumnSelect = document.getElementById('targetColumn');

    // Cuando se selecciona un dataset, actualizar las columnas
    datasetSelect.addEventListener('change', () => {
        const datasetId = datasetSelect.value;
        if (datasetId) {
            const dataset = appState.datasets.find(d => d.id === datasetId);
            if (dataset) {
                populateColumnSelects(dataset.columns);
            }
        } else {
            groupColumnSelect.innerHTML = '<option value="">Selecciona una columna...</option>';
            targetColumnSelect.innerHTML = '<option value="">Selecciona una columna...</option>';
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

    // Validar
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

            // Scroll to results
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

function renderResults(result) {
    const container = document.getElementById('resultsContent');

    // Determinar color del lift
    const liftClass = result.lift_percentage > 0 ? 'positive' : 'negative';
    const liftIcon = result.lift_percentage > 0 ? '📈' : '📉';

    container.innerHTML = `
        <!-- Métricas Principales -->
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
        
        <!-- Interpretación -->
        <div class="interpretation-box ${result.is_significant ? 'success' : 'warning'}">
            ${result.interpretation}
        </div>
        
        <!-- Estadísticas Detalladas -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md); margin-top: var(--spacing-lg);">
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Estadísticas Chi-cuadrado</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Estadístico χ²</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.chi2_statistic.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Grados de libertad</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.degrees_of_freedom}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Nivel de significancia</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.alpha}</td>
                    </tr>
                    <tr style="border-top: 1px solid var(--glass-border);">
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">¿Significativo?</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600; color: ${result.is_significant ? 'var(--success)' : 'var(--error)'};">
                            ${result.is_significant ? '✅ Sí' : '❌ No'}
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📋 Tabla de Contingencia</h3>
                <div id="contingencyTable"></div>
            </div>
        </div>
        
        <!-- Gráfico -->
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Visualización de Resultados</h3>
            <div id="plotlyChart" style="width: 100%; height: 400px;"></div>
        </div>
    `;

    // Renderizar tabla de contingencia
    renderContingencyTable(result.contingency_table);

    // Renderizar gráfico
    renderPlotlyChart(result);
}

function renderContingencyTable(contingencyTable) {
    const container = document.getElementById('contingencyTable');

    // Convertir a formato de tabla
    const rows = Object.keys(contingencyTable);
    const cols = rows.length > 0 ? Object.keys(contingencyTable[rows[0]]) : [];

    let html = '<table class="data-table" style="font-size: 0.85rem;">';

    // Header
    html += '<thead><tr><th></th>';
    cols.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '<th>Total</th></tr></thead>';

    // Body
    html += '<tbody>';
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
    const data = [
        {
            x: ['Control', 'Treatment'],
            y: [
                result.control_signup_rate * 100,
                result.treatment_signup_rate * 100
            ],
            type: 'bar',
            marker: {
                color: ['#6366f1', '#8b5cf6'],
                line: {
                    color: '#fff',
                    width: 2
                }
            },
            text: [
                `${(result.control_signup_rate * 100).toFixed(2)}%`,
                `${(result.treatment_signup_rate * 100).toFixed(2)}%`
            ],
            textposition: 'outside',
            textfont: {
                size: 14,
                color: '#f8fafc'
            }
        }
    ];

    const layout = {
        title: {
            text: 'Tasas de Conversión por Grupo',
            font: {
                size: 18,
                color: '#f8fafc'
            }
        },
        xaxis: {
            title: 'Grupo',
            color: '#f8fafc',
            gridcolor: '#334155'
        },
        yaxis: {
            title: 'Tasa de Conversión (%)',
            color: '#f8fafc',
            gridcolor: '#334155'
        },
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: {
            color: '#f8fafc'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('plotlyChart', data, layout, config);
}

// =============================================
// Inicialización
// =============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando aplicación...');

    // Inicializar componentes
    initFileUpload();
    initPreviewControls();
    initAnalysisForm();

    // Cargar datasets existentes
    await loadDatasets();

    console.log('✅ Aplicación lista');
});
