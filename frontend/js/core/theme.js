// =============================================
// Theme Manager - Gestión de tema oscuro/claro
// =============================================

import { appState } from './state.js';
import { showToast } from '../ui/notifications.js';

/**
 * Inicializa el cambio de tema (Oscuro/Claro)
 */
export function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    // Aplicar tema guardado al inicio
    if (appState.theme === 'light') {
        document.body.classList.add('light-theme');
        const icon = themeToggle.querySelector('.material-icons');
        if (icon) icon.textContent = 'light_mode';
    }

    themeToggle.addEventListener('click', () => {
        const isDark = !document.body.classList.contains('light-theme');

        if (isDark) {
            document.body.classList.add('light-theme');
            appState.theme = 'light';
            const icon = themeToggle.querySelector('.material-icons');
            if (icon) icon.textContent = 'light_mode';
            showToast('Tema claro activado', 'info');
        } else {
            document.body.classList.remove('light-theme');
            appState.theme = 'dark';
            const icon = themeToggle.querySelector('.material-icons');
            if (icon) icon.textContent = 'dark_mode';
            showToast('Tema oscuro activado', 'info');
        }

        localStorage.setItem('theme', appState.theme);
    });
}
