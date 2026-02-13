/**
 * Finance Analytics - Entry Point
 * Orchestrates the modularized application components.
 */

// Core imports
import { appState } from './core/state.js';
import { initNavigation } from './ui/navigation.js';
import { initThemeToggle } from './core/theme.js';
import { showToast } from './ui/notifications.js';

// Module imports
import { initFileUpload } from './modules/fileManager.js';
import { loadDatasets, updateStats } from './modules/datasetManager.js';
import { initPreviewControls } from './modules/dataPreview.js';
import { initAnalysisForm } from './modules/abTesting.js';
import { initMonteCarloForm, updateMonteCarloSection } from './modules/monteCarlo.js';
import { initRiskForm, updateRiskSection } from './modules/riskCalculator.js';
import { initQuickStats, updateQuickStatsSection } from './modules/quickStats.js';
import { updateSCMSection, initSCMForm } from './modules/scm.js';
import { updateRegressionSection, initRegressionForm } from './modules/regression.js';
import { updateClusteringSection, initClusteringForm } from './modules/clustering.js';
import { Guide } from './ui/guide.js';

// Global Event Listeners for Export (handled by individual modules where necessary, 
// or centralized if common buttons are in static HTML)
import { handleExportExcel } from './modules/exportManager.js';

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Starting Finance Analytics Modular System...');

    try {
        // Expose update functions to window for datasetManager
        window.updateSCMSection = updateSCMSection;
        window.updateRegressionSection = updateRegressionSection;
        window.updateClusteringSection = updateClusteringSection;
        window.updateQuickStatsSection = updateQuickStatsSection;
        window.updateMonteCarloSection = updateMonteCarloSection;
        window.updateRiskSection = updateRiskSection;

        // 1. Initialize Core UI & Common Components
        initNavigation();
        initThemeToggle();
        initFileUpload();
        initPreviewControls();

        // 2. Initialize Analysis Forms
        initAnalysisForm();
        initSCMForm();
        await initRegressionForm(); // Some might need async init
        initClusteringForm();
        initMonteCarloForm();
        initRiskForm();
        initQuickStats();

        // 3. Load Initial Data
        await loadDatasets();
        await updateStats();

        // 4. Set up Centralized Export Listeners (if buttons exist in index.html)
        setupExportListeners();

        // 5. Initialize Onboarding Guide
        initAppTour();

        console.log('✅ Application ready and modularized!');

    } catch (error) {
        console.error('❌ Error during application initialization:', error);
        showToast('Error al iniciar la aplicación', 'error');
    }
});

/**
 * Centrally manages export button listeners from index.html
 */
function setupExportListeners() {
    document.getElementById('exportABExcel')?.addEventListener('click', () => handleExportExcel('ab_test'));
    document.getElementById('exportSCMExcel')?.addEventListener('click', () => handleExportExcel('scm'));
    document.getElementById('exportRegressionExcel')?.addEventListener('click', () => handleExportExcel('regression'));
    document.getElementById('exportClusteringExcel')?.addEventListener('click', () => handleExportExcel('clustering'));
    document.getElementById('exportMonteCarloExcel')?.addEventListener('click', () => handleExportExcel('monte_carlo'));
}

/**
 * Configures and starts the application tour
 */
function initAppTour() {
    const startTourBtn = document.getElementById('startTourBtn');
    if (!startTourBtn) return;

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
            content: "Cambia entre A/B Testing, Control Sintético, Regresión, Riesgo y más usando el menú lateral.",
            target: ".sidebar-nav"
        }
    ]);

    startTourBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.appGuide.start();
    });
}
