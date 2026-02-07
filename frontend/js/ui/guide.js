// =============================================
// Guide - Tour interactivo de la aplicación
// =============================================

import { showToast } from './notifications.js';

/**
 * Clase Guide para el Onboarding interactivo
 */
export class Guide {
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

        // Limpiar transformaciones previas
        this.tooltip.style.transform = 'none';

        // Actualizar Tooltip
        this.tooltip.innerHTML = `
            <div class="tour-header">
                <span class="tour-step-counter">Paso ${this.currentStep + 1} de ${this.steps.length}</span>
                <button class="icon-btn" onclick="window.appGuide.stop()" style="padding:0; height:24px; width:24px; background:transparent; border:none; color:var(--text-muted); cursor:pointer;">
                    <span class="material-icons" style="font-size:20px;">close</span>
                </button>
            </div>
            <div class="tour-title">${step.title}</div>
            <div class="tour-content">${step.content}</div>
            <div class="tour-footer">
                <button class="btn btn-secondary btn-small" onclick="window.appGuide.stop()">Saltar</button>
                <div class="tour-actions">
                    ${this.currentStep > 0 ? '<button class="btn btn-secondary btn-small" onclick="window.appGuide.prev()">Anterior</button>' : ''}
                    <button class="btn btn-primary btn-small" onclick="window.appGuide.next()">
                        ${this.currentStep === this.steps.length - 1 ? 'Finalizar' : 'Siguiente'}
                    </button>
                </div>
            </div>
        `;

        if (target) {
            const rect = target.getBoundingClientRect();
            const padding = 10;

            this.highlighter.style.display = 'block';
            this.highlighter.style.top = `${rect.top - padding}px`;
            this.highlighter.style.left = `${rect.left - padding}px`;
            this.highlighter.style.width = `${rect.width + (padding * 2)}px`;
            this.highlighter.style.height = `${rect.height + (padding * 2)}px`;

            // Posicionar tooltip cerca del target
            let top = rect.bottom + 20;
            let left = rect.left;

            // Ajustes para que no se salga de la pantalla
            if (top + 200 > window.innerHeight) {
                top = rect.top - 220;
            }
            if (left + 350 > window.innerWidth) {
                left = window.innerWidth - 370;
            }

            this.tooltip.style.top = `${Math.max(20, top)}px`;
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
