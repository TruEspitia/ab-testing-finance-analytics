# Guía de Mantenimiento - Arquitectura Modular

## Estructura de Archivos

```
frontend/
├── js/
│   ├── core/              # Configuración y estado
│   │   ├── config.js      # Constantes (API_BASE_URL, etc.)
│   │   ├── state.js       # Estado global (appState)
│   │   └── utils.js       # Utilidades (formatBytes, formatDate, setLoading)
│   │
│   ├── api/               # Cliente API
│   │   └── client.js      # TODAS las llamadas al backend
│   │
│   ├── ui/                # Componentes UI
│   │   ├── navigation.js  # Navegación entre vistas
│   │   └── notifications.js # Sistema de toasts
│   │
│   ├── modules/           # Módulos de análisis (futuro)
│   │   └── (vacío - para migración futura)
│   │
│   └── main.js            # Entry point
│
├── app.js                 # LEGACY - código original
├── quick_stats.js         # Módulo existente
└── index.html             # Carga main.js + app.js
```

## Rutas de Imports

### En main.js
```javascript
// Rutas relativas desde main.js
import { API_BASE_URL } from './core/config.js';
import { appState } from './core/state.js';
import { formatBytes, formatDate, setLoading } from './core/utils.js';
import { showToast } from './ui/notifications.js';
import { initNavigation, switchView } from './ui/navigation.js';
import * as API from './api/client.js';
```

### En navigation.js
```javascript
// Rutas relativas desde ui/navigation.js
import { appState } from '../core/state.js';
import { showToast } from './notifications.js';
```

### En client.js
```javascript
// Rutas relativas desde api/client.js
import { API_BASE_URL } from '../core/config.js';
```

## Cómo Agregar un Nuevo Servicio

### 1. Agregar endpoint en `api/client.js`

```javascript
/**
 * Ejecuta nuevo servicio
 */
export async function runNewService(config) {
    const response = await fetch(`${API_BASE_URL}/new-service`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    });
    return await response.json();
}
```

### 2. Exportar en `main.js`

```javascript
// En la sección de exports de API
window.runNewService = API.runNewService;
```

### 3. Usar desde app.js o nuevo módulo

```javascript
const result = await runNewService({
    dataset_id: datasetId,
    parameter: value
});
```

## Migración Gradual de app.js (Opcional)

Para migrar un módulo de análisis específico:

### 1. Crear nuevo archivo en `modules/`

```javascript
// modules/newAnalysis.js
import { appState } from '../core/state.js';
import { showToast } from '../ui/notifications.js';
import { setLoading } from '../core/utils.js';
import { runNewService } from '../api/client.js';

export function initNewAnalysisForm() {
    const form = document.getElementById('newAnalysisForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleNewAnalysisSubmit();
    });
}

async function handleNewAnalysisSubmit() {
    setLoading(true);
    try {
        const result = await runNewService(config);
        renderNewAnalysisResults(result);
        showToast('Análisis completado', 'success');
    } catch (error) {
        showToast('Error en análisis', 'error');
    } finally {
        setLoading(false);
    }
}

function renderNewAnalysisResults(results) {
    // Renderizar resultados
}
```

### 2. Importar en `main.js`

```javascript
import { initNewAnalysisForm } from './modules/newAnalysis.js';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initNewAnalysisForm(); // Nueva inicialización
});
```

### 3. Exportar a window (si es necesario)

```javascript
window.initNewAnalysisForm = initNewAnalysisForm;
```

## Reglas de Mantenimiento

### ✅ DO

1. **Agregar nuevos endpoints en `api/client.js`**
   - Mantén todas las llamadas API en un solo lugar
   - Usa async/await
   - Incluye JSDoc

2. **Crear módulos pequeños y específicos**
   - Un archivo por funcionalidad
   - No más de 300 líneas por archivo
   - Responsabilidad única

3. **Usar imports explícitos**
   ```javascript
   import { funcionEspecifica } from './modulo.js';
   ```

4. **Exportar solo lo necesario**
   ```javascript
   export function funcionPublica() { }
   function funcionPrivada() { } // No exportada
   ```

### ❌ DON'T

1. **No crear dependencias circulares**
   ```javascript
   // ❌ MAL
   // a.js importa b.js
   // b.js importa a.js
   ```

2. **No duplicar código**
   - Si una función se usa en varios lugares, móvela a `core/utils.js`

3. **No hardcodear URLs**
   - Usa `API_BASE_URL` from `config.js`

4. **No mezclar lógica de vista y lógica de negocio**
   - API calls → `api/client.js`
   - DOM manipulation → módulos específicos
   - Estado → `core/state.js`

## Verificación

### Checklist antes de commit

- [ ] Todas las rutas de import son relativas y correctas
- [ ] No hay código duplicado
- [ ] Funciones están documentadas con JSDoc
- [ ] Módulos tienen responsabilidad única
- [ ] Archivos tienen menos de 300 líneas
- [ ] App carga sin errores en consola

### Verificación manual

1. Abrir http://localhost:8080
2. Abrir consola (F12)
3. Buscar:
   ```
   ✅ Módulos core cargados correctamente
   🚀 Inicializando aplicación modular...
   ✅ Navegación inicializada
   ```
4. Verificar que no hay errores
5. Probar navegación entre vistas
6. Probar una funcionalidad (upload, análisis, etc.)

## Troubleshooting

### Error: "Failed to load module"

**Causa**: Ruta de import incorrecta

**Solución**: Verificar que las rutas sean relativas al archivo que hace el import
```javascript
// Desde js/main.js
import { config } from './core/config.js'; // ✅

// Desde js/ui/navigation.js  
import { config } from '../core/config.js'; // ✅
```

### Error: "X is not defined"

**Causa**: Función no exportada a window

**Solución**: Agregar export en `main.js`
```javascript
window.miFuncion = miFuncion;
```

### Módulos no cargan

**Causa**: Script tag incorrecto

**Solución**: Verificar en index.html
```html
<script type="module" src="js/main.js"></script>
```

## Beneficios de esta Arquitectura

✅ **Mantenibilidad**: Código organizado y fácil de encontrar
✅ **Escalabilidad**: Fácil agregar nuevos servicios
✅ **Separación de responsabilidades**: Cada módulo tiene un propósito claro
✅ **Reutilización**: Funciones compartidas en un solo lugar
✅ **Testing**: Módulos pequeños son fáciles de probar
✅ **Colaboración**: Múltiples desarrolladores pueden trabajar sin conflictos

## Recursos

- [Módulos ES6 - MDN](https://developer.mozilla.org/es/docs/Web/JavaScript/Guide/Modules)
- [Import/Export - JavaScript.info](https://javascript.info/modules-intro)
