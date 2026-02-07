// =============================================
// Navegación y Manejo de Vistas
// =============================================

import { appState } from '../core/state.js';
import { showToast } from './notifications.js';

/**
 * Cambia la vista activa del sistema
 */
export function switchView(viewId) {
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
        'regression': 'Regresión / Curve Fitting',
        'clustering': 'Análisis de Clustering',
        'quick-stats': 'Quick Stats',
        'monte-carlo': 'Simulación Monte Carlo',
        'risk-calculator': 'Risk Calculator (VaR)'
    };
    document.getElementById('currentViewTitle').textContent = titleMap[viewId] || 'Análisis';

    showToast(`Cambiado a ${titleMap[viewId]}`, 'info');
}

/**
 * Inicializa los eventos del sidebar y navegación
 */
export function initNavigation() {
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
