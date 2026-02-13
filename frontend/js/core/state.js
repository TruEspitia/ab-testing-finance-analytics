// =============================================
// Estado Global de la Aplicación
// =============================================

export const appState = {
    datasets: [],
    selectedDataset: null,
    currentPreview: null,
    lastResults: null,
    lastSCMResults: null,
    lastRegressionResults: null,
    lastClusteringResults: null,
    lastMonteCarloResults: null,
    lastRiskResults: null,
    availableFunctions: [],
    currentView: 'ab-testing', // Por defecto
    theme: localStorage.getItem('theme') || 'dark'
};
