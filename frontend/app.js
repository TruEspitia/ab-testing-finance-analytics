// =============================================
// Configuración y constantes
// =============================================
const API_BASE_URL = '/api';

// Estado global de la aplicación
const appState = {
    datasets: [],
    selectedDataset: null,
    currentPreview: null,
    lastResults: null,
    lastSCMResults: null,
    lastRegressionResults: null,
    availableFunctions: [],
    currentView: 'ab-testing', // Por defecto
    theme: localStorage.getItem('theme') || 'dark'
};

// =============================================
// Navegación
// =============================================

/**
 * Cambia la vista activa del sistema
 */
function switchView(viewId) {
    // 1. Ocultar todas las vistas
    document.querySelectorAll('.analysis-view').forEach(view => {
        view.classList.add('hidden');
    });

    // 2. Mostrar la seleccionada
    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        appState.currentView = viewId;
    }

    // 3. Actualizar estado del sidebar
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewId) {
            item.classList.add('active');
        }
    });

    // 4. Actualizar título en top-bar
    const titleMap = {
        'ab-testing': 'Análisis A/B',
        'scm': 'Pruebas de Control (SCM)',
        'regression': 'Regresión / Curve Fitting'
    };
    document.getElementById('currentViewTitle').textContent = titleMap[viewId] || 'Análisis';

    showToast(`Cambiado a ${titleMap[viewId]}`, 'info');
}

/**
 * Inicializa los eventos del sidebar y navegación
 */
function initNavigation() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebar');

    // Toggle sidebar
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Nav items click
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = item.dataset.view;
            if (viewId) {
                switchView(viewId);
            }
        });
    });
}

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

/**
 * Sube múltiples archivos al servidor
 */
async function uploadBatchFiles(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    const response = await fetch(`${API_BASE_URL}/upload-batch`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

/**
 * Valida un dataset
 */
async function validateDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/validate`);
    return await response.json();
}

/**
 * Obtiene información de columnas
 */
async function fetchDatasetColumns(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}/columns`);
    return await response.json();
}

/**
 * Obtiene las funciones matemáticas disponibles para regresión
 */
async function fetchAvailableFunctions() {
    const response = await fetch(`${API_BASE_URL}/functions`);
    return await response.json();
}

/**
 * Ejecuta regresión/curve fitting
 */
async function runRegression(config) {
    const response = await fetch(`${API_BASE_URL}/regression`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}


// =============================================
// Gestión de Archivos
// =============================================

function initFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Habilitar múltiples archivos
    fileInput.multiple = true;

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

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            // Si hay múltiples archivos, usar carga por lotes
            if (files.length > 1) {
                await handleBatchUpload(files);
            } else {
                await handleFileUpload(files[0]);
            }
        }
    });

    // Cambio de archivo input
    fileInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            // Si hay múltiples archivos, usar carga por lotes
            if (files.length > 1) {
                await handleBatchUpload(files);
            } else {
                await handleFileUpload(files[0]);
            }
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

            // Nueva función: Health Check
            if (result.dataset && result.dataset.id) {
                await runHealthCheck(result.dataset.id);
            }

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

/**
 * Maneja la carga por lotes de múltiples archivos
 */
async function handleBatchUpload(files) {
    // Validar todos los archivos primero
    const maxSize = 50 * 1024 * 1024;
    const validExtensions = ['csv', 'xlsx', 'xls', 'json'];

    const validFiles = [];
    const invalidFiles = [];

    for (let file of files) {
        if (file.size > maxSize) {
            invalidFiles.push({ name: file.name, reason: 'Archivo demasiado grande (>50MB)' });
            continue;
        }

        const extension = file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(extension)) {
            invalidFiles.push({ name: file.name, reason: 'Formato no soportado' });
            continue;
        }

        validFiles.push(file);
    }

    // Mostrar errores de validación
    if (invalidFiles.length > 0) {
        const errorMsg = invalidFiles.map(f => `${f.name}: ${f.reason}`).join('\n');
        showToast(`${invalidFiles.length} archivo(s) inválido(s):\n${errorMsg}`, 'error');
    }

    if (validFiles.length === 0) {
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
    progressText.textContent = `Subiendo ${validFiles.length} archivo(s)...`;

    try {
        // Subir archivos
        const result = await uploadBatchFiles(validFiles);

        progressFill.style.width = '100%';
        progressText.textContent = `${result.successful} archivo(s) cargado(s) exitosamente`;

        if (result.successful > 0) {
            showToast(`${result.successful} archivo(s) cargado(s) exitosamente`, 'success');

            // Actualizar lista de datasets
            await loadDatasets();

            // Mostrar secciones
            document.getElementById('previewSection').classList.remove('hidden');
            document.getElementById('analysisSection').classList.remove('hidden');

            // Ejecutar health check para el primer dataset del lote
            if (result.results && result.results.length > 0 && result.results[0].dataset) {
                await runHealthCheck(result.results[0].dataset.id);
            }
        }

        if (result.failed > 0) {
            const failedFiles = result.results
                .filter(r => !r.success)
                .map(r => `${r.filename}: ${r.error}`)
                .join('\n');
            showToast(`${result.failed} archivo(s) fallaron:\n${failedFiles}`, 'error');
        }

    } catch (error) {
        showToast('Error de conexión con el servidor', 'error');
        console.error('Batch upload error:', error);
    } finally {
        // Resetear UI
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            uploadArea.classList.remove('hidden');
            progressFill.style.width = '0%';
            document.getElementById('fileInput').value = '';
        }, 3000);
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
        updateSCMSection();
        updateRegressionSection();

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

/**
 * Ejecuta y muestra el Health Check de un dataset
 */
async function runHealthCheck(datasetId) {
    const section = document.getElementById('healthCheckSection');
    const suggestionsContainer = document.getElementById('healthSuggestions');
    const scoreElement = document.getElementById('healthScoreValue');
    const circle = document.querySelector('.health-outer-circle');

    try {
        if (!section) return;

        section.classList.remove('hidden');
        suggestionsContainer.innerHTML = '<p class="loading-text">Analizando calidad de datos...</p>';

        const report = await validateDataset(datasetId);

        // Actualizar métricas básicas
        document.getElementById('nullCount').textContent = report.quality_report.null_values.total_nulls;
        document.getElementById('duplicateCount').textContent = report.quality_report.duplicate_rows;
        document.getElementById('healthColCount').textContent = Object.keys(report.column_types).length;

        // Calcular score (simplificado)
        let score = 100;
        const totalRows = report.quality_report.total_rows || 1000;
        const nullRate = report.quality_report.null_values.total_nulls / (totalRows * Object.keys(report.column_types).length || 1);

        score -= nullRate * 100;
        if (report.quality_report.duplicate_rows > 0) score -= 10;
        score = Math.max(0, Math.min(100, Math.round(score)));

        // Animar círculo y score
        scoreElement.textContent = score;
        circle.style.background = `conic-gradient(var(--primary) ${score}%, var(--glass-border) 0%)`;

        // Renderizar sugerencias
        if (report.suggestions && report.suggestions.length > 0) {
            suggestionsContainer.innerHTML = report.suggestions.map(s => `
                <div class="suggestion-item ${s.type || 'info'}">
                    <strong>${s.column || 'Global'}:</strong> ${s.message}
                </div>
            `).join('');
        } else {
            suggestionsContainer.innerHTML = '<div class="suggestion-item success">✅ No se detectaron problemas críticos de calidad.</div>';
        }

    } catch (error) {
        console.error('Health check error:', error);
        showToast('Error al ejecutar health check', 'error');
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

        // Refresh Health Check
        await runHealthCheck(datasetId);

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
    appState.lastResults = result;
    const container = document.getElementById('resultsContent');

    // Detectar tipo de análisis
    const isContinuous = result.analysis_type === 'continuous';

    let metricsHtml = '';
    let statsCardHtml = '';

    if (isContinuous) {
        // Métricas para análisis continuo (t-test)
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
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Mediana Control</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.control_median?.toFixed(4) || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Mediana Tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.treatment_median?.toFixed(4) || 'N/A'}</td>
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
                <h3 style="margin-bottom: var(--spacing-md);">📋 Tamaños de Muestra</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Control</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.sample_sizes?.control?.toLocaleString() || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.sample_sizes?.treatment?.toLocaleString() || 'N/A'}</td>
                    </tr>
                    <tr style="border-top: 1px solid var(--glass-border);">
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Total</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${((result.sample_sizes?.control || 0) + (result.sample_sizes?.treatment || 0)).toLocaleString()}</td>
                    </tr>
                </table>
            </div>
        `;
    } else {
        // Métricas para análisis categórico (chi-cuadrado)
        const liftClass = result.lift_percentage > 0 ? 'positive' : 'negative';
        const liftIcon = result.lift_percentage > 0 ? '📈' : '📉';

        // Determinar etiquetas según si es binario o multi-categoría
        const rateLabel = result.is_binary !== false ? 'Tasa de Conversión' : 'Proporción';

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

        const categoryInfo = result.n_categories
            ? `<tr>
                    <td style="padding: var(--spacing-xs); color: var(--text-muted);">Categorías</td>
                    <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.n_categories} (${result.is_binary ? 'binaria' : 'multi-categoría'})</td>
               </tr>`
            : '';

        statsCardHtml = `
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Estadísticas Chi-cuadrado</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Estadístico χ²</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.chi2_statistic?.toFixed(4) || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Grados de libertad</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.degrees_of_freedom || 'N/A'}</td>
                    </tr>
                    ${categoryInfo}
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
        `;
    }

    // Título del tipo de análisis
    const analysisTypeTitle = isContinuous
        ? '🔢 Análisis de Variable Continua (T-test)'
        : `📊 Análisis de Variable Categórica (Chi-cuadrado${result.is_binary === false ? ' - Multi-categoría' : ''})`;

    container.innerHTML = `
        <!-- Tipo de Análisis -->
        <div class="analysis-type-badge" style="background: var(--glass-bg); padding: var(--spacing-sm) var(--spacing-md); border-radius: var(--radius-md); margin-bottom: var(--spacing-md); display: inline-block;">
            ${analysisTypeTitle}
        </div>
        
        <!-- Métricas Principales -->
        ${metricsHtml}
        
        <!-- Interpretación -->
        <div class="interpretation-box ${result.is_significant ? 'success' : 'warning'}">
            ${result.interpretation}
        </div>
        
        <!-- Estadísticas Detalladas -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md); margin-top: var(--spacing-lg);">
            ${statsCardHtml}
        </div>
        
        <!-- Gráfico -->
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Visualización de Resultados</h3>
            <div id="plotlyChart" style="width: 100%; height: 400px;"></div>
        </div>
    `;

    // Renderizar tabla de contingencia solo para análisis categórico
    if (!isContinuous && result.contingency_table) {
        renderContingencyTable(result.contingency_table);
    }

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
    const isContinuous = result.analysis_type === 'continuous';

    let data, layout;

    if (isContinuous) {
        // Gráfico para variables continuas - Comparación de medias con barras de error
        data = [
            {
                x: ['Control', 'Treatment'],
                y: [result.control_mean, result.treatment_mean],
                error_y: {
                    type: 'data',
                    array: [result.control_std, result.treatment_std],
                    visible: true,
                    color: '#94a3b8'
                },
                type: 'bar',
                marker: {
                    color: ['#6366f1', '#8b5cf6'],
                    line: {
                        color: '#fff',
                        width: 2
                    }
                },
                text: [
                    `${result.control_mean.toFixed(2)}`,
                    `${result.treatment_mean.toFixed(2)}`
                ],
                textposition: 'outside',
                textfont: {
                    size: 14,
                    color: '#f8fafc'
                }
            }
        ];

        layout = {
            title: {
                text: 'Comparación de Medias por Grupo',
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
                title: 'Valor Promedio',
                color: '#f8fafc',
                gridcolor: '#334155'
            },
            plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
            paper_bgcolor: 'transparent',
            font: {
                color: '#f8fafc'
            },
            annotations: [{
                x: 0.5,
                y: -0.15,
                xref: 'paper',
                yref: 'paper',
                text: `Diferencia: ${result.difference >= 0 ? '+' : ''}${result.difference.toFixed(4)} (${result.percentage_change >= 0 ? '+' : ''}${result.percentage_change.toFixed(2)}%)`,
                showarrow: false,
                font: {
                    size: 12,
                    color: result.is_significant ? '#22c55e' : '#f59e0b'
                }
            }]
        };
    } else {
        // Gráfico para variables categóricas - Tasas de conversión
        data = [
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

        const chartTitle = result.is_binary !== false
            ? 'Tasas de Conversión por Grupo'
            : 'Distribución de Categorías por Grupo';

        layout = {
            title: {
                text: chartTitle,
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
                title: result.is_binary !== false ? 'Tasa de Conversión (%)' : 'Proporción (%)',
                color: '#f8fafc',
                gridcolor: '#334155'
            },
            plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
            paper_bgcolor: 'transparent',
            font: {
                color: '#f8fafc'
            },
            annotations: [{
                x: 0.5,
                y: -0.15,
                xref: 'paper',
                yref: 'paper',
                text: `Lift: ${result.lift_percentage >= 0 ? '+' : ''}${result.lift_percentage.toFixed(2)}%`,
                showarrow: false,
                font: {
                    size: 12,
                    color: result.is_significant ? '#22c55e' : '#f59e0b'
                }
            }]
        };
    }

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('plotlyChart', data, layout, config);
}

// =============================================
// Synthetic Control Method (SCM)
// =============================================

/**
 * Ejecuta análisis de Control Sintético
 */
async function runSCMAnalysis(config) {
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
function initSCMForm() {
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
                sel.innerHTML = '<option value="">Selecciona columna...</option>';
            });
            return;
        }

        try {
            const preview = await fetchDatasetPreview(datasetId, 100);
            const columns = preview.columns || [];

            // Llenar selects de columnas
            const columnOptions = columns.map(col => `<option value="${col}">${col}</option>`).join('');

            timeColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;
            unitColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;
            scmTargetColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>' + columnOptions;

            // Guardar preview para después llenar las unidades
            appState.scmPreview = preview;

        } catch (error) {
            showToast('Error al cargar columnas', 'error');
        }
    });

    // Cuando cambia la columna de unidades, llenar el select de unidad tratada
    unitColumnSelect.addEventListener('change', async (e) => {
        const unitColumn = e.target.value;

        if (!unitColumn || !appState.scmPreview) {
            treatedUnitSelect.innerHTML = '<option value="">Selecciona unidad...</option>';
            return;
        }

        // Obtener valores únicos de la columna de unidades
        const data = appState.scmPreview.data || [];
        const uniqueUnits = [...new Set(data.map(row => row[unitColumn]))].filter(u => u != null);

        const unitOptions = uniqueUnits.map(unit => `<option value="${unit}">${unit}</option>`).join('');
        treatedUnitSelect.innerHTML = '<option value="">Selecciona unidad...</option>' + unitOptions;
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
function renderSCMResults(result) {
    appState.lastSCMResults = result;
    const container = document.getElementById('scmResultsContent');

    const effectClass = result.average_treatment_effect > 0 ? 'positive' : 'negative';
    const effectIcon = result.average_treatment_effect > 0 ? '📈' : '📉';

    container.innerHTML = `
        <!-- Métricas Principales -->
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
        
        <!-- Interpretación -->
        <div class="interpretation-box success">
            ${result.interpretation.replace(/\n/g, '<br>')}
        </div>
        
        <!-- Estadísticas Detalladas -->
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
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Momento del Tratamiento</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.treatment_time}</td>
                    </tr>
                </table>
            </div>
            
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">⚖️ Pesos de las Unidades de Control</h3>
                <div id="weightsContainer" style="max-height: 200px; overflow-y: auto;"></div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📈 Series Temporales: Tratado vs. Sintético</h3>
            <div id="scmTimeSeriesChart" style="width: 100%; height: 450px;"></div>
        </div>
        
        <div style="margin-top: var(--spacing-lg);">
            <h3 style="margin-bottom: var(--spacing-md);">📊 Pesos de las Unidades de Control</h3>
            <div id="scmWeightsChart" style="width: 100%; height: 350px;"></div>
        </div>
    `;

    // Renderizar tabla de pesos
    renderWeightsTable(result.weights);

    // Renderizar gráficos
    renderSCMTimeSeries(result);
    renderSCMWeightsChart(result.weights);
}

/**
 * Renderiza la tabla de pesos
 */
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

/**
 * Renderiza el gráfico de series temporales del SCM
 */
function renderSCMTimeSeries(result) {
    const treatmentTime = result.treatment_time;

    const data = [
        {
            x: result.time_values,
            y: result.treated_values,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${result.treated_unit} (Tratada)`,
            line: { color: '#6366f1', width: 3 },
            marker: { size: 6 }
        },
        {
            x: result.time_values,
            y: result.synthetic_values,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Control Sintético',
            line: { color: '#8b5cf6', width: 3, dash: 'dash' },
            marker: { size: 6 }
        }
    ];

    const layout = {
        title: {
            text: 'Unidad Tratada vs. Control Sintético',
            font: { size: 18, color: '#f8fafc' }
        },
        xaxis: {
            title: 'Tiempo',
            color: '#f8fafc',
            gridcolor: '#334155'
        },
        yaxis: {
            title: 'Valor',
            color: '#f8fafc',
            gridcolor: '#334155'
        },
        shapes: [{
            type: 'line',
            x0: treatmentTime,
            x1: treatmentTime,
            y0: 0,
            y1: 1,
            yref: 'paper',
            line: {
                color: '#ef4444',
                width: 2,
                dash: 'dot'
            }
        }],
        annotations: [{
            x: treatmentTime,
            y: 1.02,
            yref: 'paper',
            text: 'Tratamiento',
            showarrow: false,
            font: { size: 12, color: '#ef4444' }
        }],
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        legend: {
            orientation: 'h',
            y: -0.15
        }
    };

    const config = {
        responsive: true,
        displayModeBar: true
    };

    Plotly.newPlot('scmTimeSeriesChart', data, layout, config);
}

/**
 * Renderiza el gráfico de pesos
 */
function renderSCMWeightsChart(weights) {
    if (!weights) return;

    const sortedWeights = Object.entries(weights)
        .filter(([_, w]) => w > 0.001)
        .sort((a, b) => b[1] - a[1]);

    const data = [{
        x: sortedWeights.map(([unit, _]) => unit),
        y: sortedWeights.map(([_, weight]) => weight * 100),
        type: 'bar',
        marker: {
            color: sortedWeights.map((_, i) =>
                `hsl(${240 + i * 10}, 70%, ${60 - i * 3}%)`
            ),
            line: { color: '#fff', width: 1 }
        },
        text: sortedWeights.map(([_, w]) => `${(w * 100).toFixed(1)}%`),
        textposition: 'outside'
    }];

    const layout = {
        title: {
            text: 'Contribución de Unidades de Control',
            font: { size: 18, color: '#f8fafc' }
        },
        xaxis: {
            title: 'Unidad',
            color: '#f8fafc',
            gridcolor: '#334155',
            tickangle: -45
        },
        yaxis: {
            title: 'Peso (%)',
            color: '#f8fafc',
            gridcolor: '#334155'
        },
        plot_bgcolor: 'rgba(255, 255, 255, 0.03)',
        paper_bgcolor: 'transparent',
        font: { color: '#f8fafc' },
        margin: { b: 100 }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('scmWeightsChart', data, layout, config);
}

/**
 * Muestra la sección de SCM cuando hay datasets
 */
function updateSCMSection() {
    const scmSection = document.getElementById('scmSection');
    const scmDatasetSelect = document.getElementById('scmDataset');

    if (!scmSection || !scmDatasetSelect) return;

    if (appState.datasets.length > 0) {
        scmSection.classList.remove('hidden');

        // Actualizar selector de datasets
        scmDatasetSelect.innerHTML = '<option value="">Selecciona un dataset...</option>';
        appState.datasets.forEach(dataset => {
            scmDatasetSelect.innerHTML += `<option value="${dataset.id}">${dataset.name}</option>`;
        });
    }
}

/**
 * Inicializa el cambio de tema (Oscuro/Claro)
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    // Aplicar tema guardado al inicio
    if (appState.theme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.querySelector('.material-icons').textContent = 'light_mode';
    }

    themeToggle.addEventListener('click', () => {
        const isDark = !document.body.classList.contains('light-theme');

        if (isDark) {
            // Pasar a claro
            document.body.classList.add('light-theme');
            appState.theme = 'light';
            themeToggle.querySelector('.material-icons').textContent = 'light_mode';
            showToast('Tema claro activado', 'info');
        } else {
            // Pasar a oscuro
            document.body.classList.remove('light-theme');
            appState.theme = 'dark';
            themeToggle.querySelector('.material-icons').textContent = 'dark_mode';
            showToast('Tema oscuro activado', 'info');
        }

        localStorage.setItem('theme', appState.theme);
    });
}

// =============================================
// Inicialización
// =============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando aplicación...');

    // Inicializar componentes
    initNavigation();
    initFileUpload();
    initPreviewControls();
    initAnalysisForm();
    initSCMForm();
    initThemeToggle();
    await initRegressionForm();

    // Cargar datasets existentes
    await loadDatasets();

    // Actualizar sección de SCM y Regresión
    updateSCMSection();
    updateRegressionSection();

    // Event listeners para exportación
    document.getElementById('exportABExcel')?.addEventListener('click', () => handleExportExcel('ab_test'));
    document.getElementById('exportSCMExcel')?.addEventListener('click', () => handleExportExcel('scm'));
    document.getElementById('exportRegressionExcel')?.addEventListener('click', () => handleExportExcel('regression'));

    // Inicializar Tour
    document.getElementById('startTourBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        window.appGuide.start();
    });

    window.appGuide = new Guide([
        {
            title: "¡Bienvenido a Finance Analytics!",
            content: "Este tour te guiará por las funciones principales de la herramienta para que aproveches al máximo tus análisis financieros.",
            target: null
        },
        {
            title: "Carga de Datos",
            content: "Aquí puedes subir tus archivos CSV, Excel o JSON. Puedes arrastrar varios archivos a la vez.",
            target: "#uploadArea"
        },
        {
            title: "Gestión de Datasets",
            content: "Una vez cargados, tus archivos aparecerán aquí. Puedes previsualizarlos o eliminarlos.",
            target: ".datasets-section"
        },
        {
            title: "Análisis Disponibles",
            content: "Cambia entre A/B Testing, Control Sintético o Regresión usando el menú lateral.",
            target: ".sidebar-nav"
        },
        {
            title: "Configuración y Resultados",
            content: "Configura los parámetros de tu análisis y visualiza resultados interactivos con gráficos de alta calidad.",
            target: ".main-content"
        }
    ]);

    console.log('✅ Aplicación lista');
});

/**
 * Clase Guide para el Onboarding interactivo
 */
class Guide {
    constructor(steps) {
        this.steps = steps;
        this.currentStep = 0;
        this.overlay = null;
        this.highlighter = null;
        this.tooltip = null;
    }

    start() {
        this.currentStep = 0;
        this.createUI();
        this.showStep();
        if (document.getElementById('sidebar').classList.contains('collapsed')) {
            document.getElementById('toggleSidebar').click();
        }
    }

    createUI() {
        if (this.overlay) return;

        this.overlay = document.createElement('div');
        this.overlay.className = 'tour-overlay';

        this.highlighter = document.createElement('div');
        this.highlighter.className = 'tour-highlighter';

        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tour-tooltip';

        document.body.appendChild(this.overlay);
        document.body.appendChild(this.highlighter);
        document.body.appendChild(this.tooltip);
    }

    showStep() {
        const step = this.steps[this.currentStep];
        const target = step.target ? document.querySelector(step.target) : null;

        // Actualizar Tooltip
        this.tooltip.innerHTML = `
            <div class="tour-header">
                <span class="tour-step-counter">Paso ${this.currentStep + 1} de ${this.steps.length}</span>
                <button class="icon-btn" onclick="appGuide.stop()" style="padding:0; height:20px; width:20px;">
                    <span class="material-icons" style="font-size:16px;">close</span>
                </button>
            </div>
            <div class="tour-title">${step.title}</div>
            <div class="tour-content">${step.content}</div>
            <div class="tour-footer">
                <button class="btn btn-secondary btn-small" onclick="appGuide.stop()">Saltar</button>
                <div class="tour-actions">
                    ${this.currentStep > 0 ? '<button class="btn btn-secondary btn-small" onclick="appGuide.prev()">Anterior</button>' : ''}
                    <button class="btn btn-primary btn-small" onclick="appGuide.next()">
                        ${this.currentStep === this.steps.length - 1 ? 'Finalizar' : 'Siguiente'}
                    </button>
                </div>
            </div>
        `;

        if (target) {
            const rect = target.getBoundingClientRect();
            const padding = 10;

            this.highlighter.style.display = 'block';
            this.highlighter.style.top = `${rect.top + window.scrollY - padding}px`;
            this.highlighter.style.left = `${rect.left + window.scrollX - padding}px`;
            this.highlighter.style.width = `${rect.width + (padding * 2)}px`;
            this.highlighter.style.height = `${rect.height + (padding * 2)}px`;

            // Posicionar tooltip cerca del target
            let top = rect.bottom + 20;
            let left = rect.left;

            if (top + 250 > window.innerHeight) {
                top = rect.top - 270;
            }
            if (left + 350 > window.innerWidth) {
                left = window.innerWidth - 370;
            }

            this.tooltip.style.top = `${top}px`;
            this.tooltip.style.left = `${Math.max(20, left)}px`;

            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            this.highlighter.style.display = 'none';
            this.tooltip.style.top = '50%';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
        }
    }

    next() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep();
        } else {
            this.stop();
        }
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }

    stop() {
        this.overlay?.remove();
        this.highlighter?.remove();
        this.tooltip?.remove();
        this.overlay = null;
        this.highlighter = null;
        this.tooltip = null;
        showToast("Tour finalizado", "success");
    }
}

/**
 * Maneja la exportación a Excel capturando los gráficos actuales
 */
async function handleExportExcel(type) {
    let data;
    if (type === 'ab_test') {
        data = appState.lastResults;
    } else if (type === 'scm') {
        data = appState.lastSCMResults;
    } else if (type === 'regression') {
        data = appState.lastRegressionResults;
    }

    if (!data) {
        showToast('No hay resultados para exportar', 'error');
        return;
    }

    try {
        setLoading(true);
        const charts = [];

        if (type === 'ab_test') {
            const img = await Plotly.toImage('plotlyChart', { format: 'png', width: 800, height: 500 });
            charts.push(img);
        } else if (type === 'scm') {
            const img1 = await Plotly.toImage('scmTimeSeriesChart', { format: 'png', width: 800, height: 500 });
            const img2 = await Plotly.toImage('scmWeightsChart', { format: 'png', width: 800, height: 500 });
            charts.push(img1, img2);
        } else if (type === 'regression') {
            const img = await Plotly.toImage('regressionPlotlyChart', { format: 'png', width: 800, height: 500 });
            charts.push(img);
        }

        await exportResultsToExcel(type, data, charts);
        showToast('Excel generado exitosamente', 'success');
    } catch (error) {
        showToast('Error al exportar: ' + error.message, 'error');
        console.error('Export error:', error);
    } finally {
        setLoading(false);
    }
}

/**
 * Envía los datos y capturas de pantalla al backend para generar el Excel
 */
async function exportResultsToExcel(type, data, charts) {
    const response = await fetch(`${API_BASE_URL}/export/excel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            analysis_type: type,
            data: data,
            charts: charts
        })
    });

    if (!response.ok) {
        throw new Error('Error en el servidor al generar el Excel');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    let filename = 'Report.xlsx';
    if (type === 'ab_test') {
        filename = 'AB_Test_Report.xlsx';
    } else if (type === 'scm') {
        filename = 'SCM_Report.xlsx';
    } else if (type === 'regression') {
        filename = 'Regression_Report.xlsx';
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// =============================================
// Regresión / Curve Fitting
// =============================================

/**
 * Inicializa el formulario de regresión
 */
async function initRegressionForm() {
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
            xColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
            yColumnSelect.innerHTML = '<option value="">Selecciona columna...</option>';
        }
    });

    // Mostrar fórmula cuando se selecciona una función
    functionSelect.addEventListener('change', () => {
        const funcName = functionSelect.value;
        const func = appState.availableFunctions.find(f => f.name === funcName);
        if (func) {
            functionFormula.textContent = `Fórmula: ${func.formula}`;
        } else {
            functionFormula.textContent = 'Selecciona una función para ver su fórmula';
        }
    });

    // Submit del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleRegressionSubmit();
    });
}

/**
 * Puebla los selects de columnas para regresión
 */
function populateRegressionColumnSelects(columns) {
    const xColumnSelect = document.getElementById('xColumn');
    const yColumnSelect = document.getElementById('yColumn');

    [xColumnSelect, yColumnSelect].forEach(select => {
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
function populateFunctionSelect() {
    const functionSelect = document.getElementById('functionSelect');
    if (!functionSelect) return;

    functionSelect.innerHTML = '<option value="">Selecciona una función...</option>';

    // Agrupar funciones por prefijo
    const groups = {};
    appState.availableFunctions.forEach(func => {
        const parts = func.name.split('_');
        const prefix = parts[0];
        if (!groups[prefix]) {
            groups[prefix] = [];
        }
        groups[prefix].push(func);
    });

    // Crear optgroups
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
async function handleRegressionSubmit() {
    const config = {
        dataset_id: document.getElementById('regressionDataset').value,
        x_column: document.getElementById('xColumn').value,
        y_column: document.getElementById('yColumn').value,
        function_name: document.getElementById('functionSelect').value,
        engine_type: document.getElementById('engineSelect').value
    };

    // Validar
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
            document.getElementById('regressionResultsSection').classList.remove('hidden');

            // Scroll to results
            document.getElementById('regressionResultsSection').scrollIntoView({
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
function renderRegressionResults(result) {
    const container = document.getElementById('regressionResultsContent');

    const r2Class = result.r_squared >= 0.85 ? 'positive' : result.r_squared >= 0.70 ? '' : 'negative';

    container.innerHTML = `
        <div class="results-metrics">
            <div class="metric-card">
                <div class="metric-label">R² (Coef. Determinación)</div>
                <div class="metric-value ${r2Class}">${result.r_squared.toFixed(4)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">RMSE</div>
                <div class="metric-value">${result.rmse.toFixed(4)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Función</div>
                <div class="metric-value" style="font-size: 1rem;">${result.function_name}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Motor</div>
                <div class="metric-value" style="font-size: 1rem;">${result.engine_used}</div>
            </div>
        </div>

        <div class="interpretation-box ${result.r_squared >= 0.85 ? 'significant' : 'not-significant'}">
            <p>${result.interpretation}</p>
        </div>

        <div class="results-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); margin-top: var(--spacing-md);">
            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📊 Parámetros Ajustados</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: var(--spacing-xs);">Parámetro</th>
                            <th style="text-align: right; padding: var(--spacing-xs);">Valor</th>
                            <th style="text-align: right; padding: var(--spacing-xs);">Error</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(result.parameters).map(([name, value]) => `
                            <tr>
                                <td style="padding: var(--spacing-xs); color: var(--text-muted);">${name}</td>
                                <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${value.toFixed(6)}</td>
                                <td style="padding: var(--spacing-xs); text-align: right; color: var(--text-muted);">±${(result.errors[name] || 0).toFixed(6)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>

            <div class="glass-card" style="padding: var(--spacing-md);">
                <h3 style="margin-bottom: var(--spacing-md);">📈 Estadísticas</h3>
                <table style="width: 100%; font-size: 0.9rem;">
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">Puntos de datos</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.original_x.length}</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">R²</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${(result.r_squared * 100).toFixed(2)}%</td>
                    </tr>
                    <tr>
                        <td style="padding: var(--spacing-xs); color: var(--text-muted);">RMSE</td>
                        <td style="padding: var(--spacing-xs); text-align: right; font-weight: 600;">${result.rmse.toFixed(4)}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div id="regressionPlotlyChart" style="width: 100%; height: 450px; margin-top: var(--spacing-md);"></div>
    `;

    // Renderizar gráfico de la curva ajustada
    renderRegressionPlotlyChart(result);
}

/**
 * Renderiza el gráfico de Plotly para la regresión
 */
function renderRegressionPlotlyChart(result) {
    const scatterTrace = {
        x: result.original_x,
        y: result.original_y,
        mode: 'markers',
        type: 'scatter',
        name: 'Datos Originales',
        marker: {
            color: 'rgba(99, 102, 241, 0.7)',
            size: 8,
            line: {
                color: 'rgba(99, 102, 241, 1)',
                width: 1
            }
        }
    };

    const fittedTrace = {
        x: result.fitted_x,
        y: result.fitted_y,
        mode: 'lines',
        type: 'scatter',
        name: `Ajuste: ${result.function_name}`,
        line: {
            color: 'rgba(236, 72, 153, 1)',
            width: 3
        }
    };

    const layout = {
        title: {
            text: `Regresión: ${result.function_name} (R² = ${result.r_squared.toFixed(4)})`,
            font: { color: '#f3f4f6', size: 16 }
        },
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0.1)',
        xaxis: {
            title: 'X',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            zerolinecolor: 'rgba(255, 255, 255, 0.2)',
            tickfont: { color: '#9ca3af' },
            titlefont: { color: '#f3f4f6' }
        },
        yaxis: {
            title: 'Y',
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            zerolinecolor: 'rgba(255, 255, 255, 0.2)',
            tickfont: { color: '#9ca3af' },
            titlefont: { color: '#f3f4f6' }
        },
        legend: {
            font: { color: '#f3f4f6' },
            bgcolor: 'rgba(0, 0, 0, 0.3)'
        },
        margin: { t: 50, l: 60, r: 30, b: 50 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    Plotly.newPlot('regressionPlotlyChart', [scatterTrace, fittedTrace], layout, config);
}

/**
 * Actualiza la sección de regresión cuando hay datasets cargados
 */
function updateRegressionSection() {
    const regressionSection = document.getElementById('regressionSection');
    const regressionDatasetSelect = document.getElementById('regressionDataset');

    if (!regressionSection || !regressionDatasetSelect) return;

    if (appState.datasets.length > 0) {
        regressionSection.classList.remove('hidden');

        // Actualizar selector de datasets
        regressionDatasetSelect.innerHTML = '<option value="">Selecciona un dataset...</option>';
        appState.datasets.forEach(dataset => {
            regressionDatasetSelect.innerHTML += `<option value="${dataset.id}">${dataset.name}</option>`;
        });
    }
}

