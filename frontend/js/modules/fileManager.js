// =============================================
// File Manager - Gestión de subida de archivos
// =============================================

import { showToast } from '../ui/notifications.js';
import { uploadFile, uploadBatchFiles } from '../api/client.js';
import { loadDatasets, runHealthCheck } from './datasetManager.js';

/**
 * Inicializa los eventos de carga de archivos
 */
export function initFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) return;

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
            if (files.length > 1) {
                await handleBatchUpload(files);
            } else {
                await handleFileUpload(files[0]);
            }
        }
    });
}

/**
 * Maneja la subida de un solo archivo
 */
export async function handleFileUpload(file) {
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Archivo demasiado grande. Máximo 50MB', 'error');
        return;
    }

    const validExtensions = ['csv', 'xlsx', 'xls', 'json'];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(extension)) {
        showToast('Formato no soportado. Use CSV, XLSX o JSON', 'error');
        return;
    }

    const uploadProgress = document.getElementById('uploadProgress');
    const uploadArea = document.getElementById('uploadArea');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    progressFill.style.width = '30%';
    progressText.textContent = 'Subiendo archivo...';

    try {
        const result = await uploadFile(file);

        progressFill.style.width = '100%';
        progressText.textContent = 'Archivo cargado exitosamente';

        if (result.success) {
            showToast(result.message, 'success');

            await loadDatasets();

            document.getElementById('previewSection').classList.remove('hidden');
            document.getElementById('analysisSection').classList.remove('hidden');

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
export async function handleBatchUpload(files) {
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

    if (invalidFiles.length > 0) {
        const errorMsg = invalidFiles.map(f => `${f.name}: ${f.reason}`).join('\n');
        showToast(`${invalidFiles.length} archivo(s) inválido(s):\n${errorMsg}`, 'error');
    }

    if (validFiles.length === 0) return;

    const uploadProgress = document.getElementById('uploadProgress');
    const uploadArea = document.getElementById('uploadArea');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    progressFill.style.width = '30%';
    progressText.textContent = `Subiendo ${validFiles.length} archivo(s)...`;

    try {
        const result = await uploadBatchFiles(validFiles);

        progressFill.style.width = '100%';
        progressText.textContent = `${result.successful} archivo(s) cargado(s) exitosamente`;

        if (result.successful > 0) {
            showToast(`${result.successful} archivo(s) cargado(s) exitosamente`, 'success');

            await loadDatasets();

            document.getElementById('previewSection').classList.remove('hidden');
            document.getElementById('analysisSection').classList.remove('hidden');

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
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            uploadArea.classList.remove('hidden');
            progressFill.style.width = '0%';
            document.getElementById('fileInput').value = '';
        }, 3000);
    }
}
