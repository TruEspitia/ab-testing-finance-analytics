# Guía de Usuario - A/B Testing Finance Analytics

## 📚 Índice

1. [Introducción](#introducción)
2. [Cómo Iniciar la Aplicación](#cómo-iniciar-la-aplicación)
3. [Cargar Datasets](#cargar-datasets)
4. [Configurar Análisis A/B](#configurar-análisis-ab)
5. [Interpretar Resultados](#interpretar-resultados)
6. [Casos de Uso Comunes](#casos-de-uso-comunes)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Introducción

**A/B Testing Finance Analytics** es una herramienta profesional para analizar campañas de marketing financiero mediante pruebas A/B estadísticamente rigurosas.

### ¿Qué puedes hacer?

- ✅ Cargar datasets en múltiples formatos (CSV, XLSX, JSON)
- ✅ Analizar tasas de conversión entre grupos control y treatment
- ✅ Obtener métricas estadísticas (Chi-cuadrado, p-value, lift)
- ✅ Visualizar resultados de forma interactiva
- ✅ Interpretar resultados en lenguaje natural

---

## 🚀 Cómo Iniciar la Aplicación

### Método Simple (Recomendado)

1. Abre una terminal en la carpeta del proyecto
2. Ejecuta:
   ```bash
   python run.py
   ```
3. **El navegador se abrirá automáticamente** en http://127.0.0.1:8000

### Detalles Técnicos

- El servidor se ejecuta en `http://127.0.0.1:8000`
- La documentación de la API está en `http://127.0.0.1:8000/docs`
- Para detener el servidor, presiona `Ctrl+C` en la terminal

---

## 📤 Cargar Datasets

### Formatos Soportados

| Formato | Extensiones | Características |
|---------|-------------|-----------------|
| **CSV** | `.csv`, `.txt` | Detección automática de delimitador y encoding |
| **Excel** | `.xlsx`, `.xls` | Soporte para hojas múltiples |
| **JSON** | `.json` | Orientaciones: records, index, columns |

### Métodos de Carga

#### 1. Arrastrar y Soltar (Drag & Drop)

1. Arrastra uno o múltiples archivos desde tu explorador de archivos
2. Suéltalos en la zona de carga
3. ✨ **Nuevo:** Puedes cargar múltiples archivos a la vez

#### 2. Seleccionar Archivos

1. Haz clic en la zona de carga
2. Selecciona uno o múltiples archivos
3. Haz clic en "Abrir"

### Límites y Validaciones

- **Tamaño máximo por archivo:** 50 MB
- **Número máximo de datasets en memoria:** 10
- **Validaciones automáticas:**
  - Formato de archivo válido
  - Encoding detectado automáticamente
  - Columnas duplicadas eliminadas
  - Datos vacíos validados

### Estructura de Datos Recomendada

Tu dataset debe tener:

- **Columna de grupo:** Identifica control vs treatment (ej: `received_bonus_offer`)
  - Valores: "No" (control), "Yes" (treatment)
  
- **Columna objetivo:** Variable a medir (ej: `signed_up`)
  - Valores: "No", "Yes" (para variables categóricas)
  
- **Columnas adicionales** (opcionales): edad, ingreso, etc.

#### Ejemplo de Dataset

```csv
customer_id,received_bonus_offer,signed_up,age,income
1,Yes,Yes,35,75000
2,No,No,42,65000
3,Yes,Yes,28,80000
4,No,Yes,31,68000
5,Yes,No,45,92000
```

---

## ⚙️ Configurar Análisis A/B

### Paso 1: Seleccionar Dataset

1. Después de cargar archivos, ve a la sección "Configuración del Análisis A/B"
2. Selecciona el dataset que deseas analizar

### Paso 2: Configurar Parámetros

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| **Dataset** | Dataset a analizar | `customers.csv (5000 filas)` |
| **Columna de Grupo** | Columna que separa control/treatment | `received_bonus_offer` |
| **Columna Objetivo** | Variable que mides | `signed_up` |
| **Valor Control** | Valor que identifica el grupo control | `No` |
| **Valor Treatment** | Valor que identifica el grupo treatment | `Yes` |
| **Nivel de Significancia (α)** | Típicamente 0.05 (95% confianza) | `0.05` |

### Paso 3: Ejecutar Análisis

1. Verifica que todos los campos estén completos
2. Haz clic en "🚀 Ejecutar Análisis"
3. Espera a que se procese (típicamente < 5 segundos)
4. Los resultados aparecerán automáticamente

---

## 📊 Interpretar Resultados

### Métricas Principales

#### Tasas de Conversión

- **Control:** Tasa de conversión del grupo control (%)
- **Treatment:** Tasa de conversión del grupo treatment (%)
- **Lift:** Diferencia entre treatment y control (puntos porcentuales)
- **Lift %:** Mejora porcentual relativa

#### Estadísticas

- **Chi-cuadrado (χ²):** Estadístico de la prueba
- **P-value:** Probabilidad de que el resultado sea por azar
- **Grados de libertad:** Parámetro de la distribución chi-cuadrado
- **¿Significativo?:** Resultado de la prueba

### Interpretación del P-value

| P-value | Interpretación |
|---------|----------------|
| < 0.01 | ⭐⭐⭐ Muy significativo (99% confianza) |
| < 0.05 | ⭐⭐ Significativo (95% confianza) |
| < 0.10 | ⭐ Marginalmente significativo (90% confianza) |
| ≥ 0.10 | ❌ No significativo |

### Ejemplo de Resultado

```
✅ Resultado significativo

Control:     12.5%
Treatment:   18.7%
Lift:        +6.2% (+49.6%)
P-value:     0.0023 (< 0.05)

Interpretación:
El grupo de tratamiento incrementó la tasa de conversión en 49.6% 
(de 12.5% a 18.7%). Esta diferencia es estadísticamente significativa 
(p-value = 0.0023 < 0.05).
```

### Gráficos

La aplicación genera automáticamente:

- **Gráfico de barras:** Compara tasas de conversión
- **Tabla de contingencia:** Muestra conteos por grupo
- **Métricas visuales:** Tarjetas con las métricas clave

---

## 💼 Casos de Uso Comunes

### 1. Campaña de Email Marketing

**Escenario:** Quieres saber si enviar un email promocional aumenta las suscripciones.

**Configuración:**
- Dataset: `email_campaign.csv`
- Grupo: `email_sent` (Yes/No)
- Objetivo: `subscribed` (Yes/No)
- Control: `No`
- Treatment: `Yes`

**Análisis:** La herramienta te dirá si el email tuvo un efecto significativo.

### 2. Precio de Producto

**Escenario:** Probaste dos precios diferentes para un producto.

**Configuración:**
- Dataset: `pricing_test.csv`
- Grupo: `price_variant` (standard/discount)
- Objetivo: `purchased` (Yes/No)
- Control: `standard`
- Treatment: `discount`

**Análisis:** Determina si el descuento incrementó las compras significativamente.

### 3. Diseño de Landing Page

**Escenario:** Comparas dos diseños de landing page.

**Configuración:**
- Dataset: `landing_page_test.csv`
- Grupo: `page_version` (A/B)
- Objetivo: `converted` (Yes/No)
- Control: `A`
- Treatment: `B`

**Análisis:** Identifica qué diseño genera más conversiones.

---

## 🔧 Solución de Problemas

### Problema: "Formato no soportado"

**Causa:** El archivo no es CSV, XLSX o JSON
**Solución:** Convierte tu archivo a uno de los formatos soportados

### Problema: "Archivo demasiado grande"

**Causa:** El archivo excede 50 MB
**Solución:** 
- Filtra o muestrea tus datos
- Divide el archivo en partes más pequeñas

### Problema: "Error al cargar el archivo"

**Causas posibles:**
- Encoding incorrecto
- Columnas duplicadas
- Archivo corrupto

**Solución:**
- Abre el archivo en Excel/editor de texto
- Verifica que no haya caracteres extraños
- Asegúrate de que las columnas tengan nombres únicos

### Problema: "Columna no encontrada"

**Causa:** El nombre de la columna no existe en el dataset
**Solución:** 
- Verifica los nombres de las columnas en la vista previa
- Asegúrate de escribir el nombre exactamente como aparece

### Problema: "No hay datos suficientes"

**Causa:** Tu dataset es demasiado pequeño
**Solución:** 
- Se recomienda un mínimo de 100 observaciones por grupo
- Para resultados confiables, 1000+ observaciones por grupo

### Problema: "Resultado no significativo"

**Causa:** La diferencia entre grupos es pequeña o hay mucha variabilidad
**Solución:**
- Aumenta el tamaño de la muestra
- Verifica que los grupos estén bien balanceados
- Considera si el tratamiento realmente tiene efecto

### Problema: "Servidor no arranca"

**Causa:** Puerto 8000 ocupado o dependencias faltantes
**Solución:**
```bash
# Verificar dependencias
pip install -r requirements.txt

# Si el puerto está ocupado, cambiar en run.py
# port=8000  →  port=8080
```

---

## 📞 Soporte

Si tienes problemas adicionales:

1. Verifica la consola del navegador (F12) para errores
2. Revisa la terminal del servidor para mensajes de error
3. Consulta la documentación de la API: `http://127.0.0.1:8000/docs`

---

## 📝 Notas Finales

- **Interpretación:** Siempre lee la interpretación en lenguaje natural
- **Contexto:** Los resultados estadísticos deben interpretarse en el contexto del negocio
- **Causalidad:** Significancia estadística ≠ Causalidad (requiere diseño experimental adecuado)
- **Múltiples pruebas:** Si haces múltiples análisis, considera el ajuste Bonferroni

¡Buena suerte con tus análisis! 🚀
