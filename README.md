# A/B Testing en Finance Analytics 🧪💳

Este proyecto demuestra cómo diseñar y evaluar pruebas A/B para campañas de marketing en finanzas, con una aplicación web moderna que permite cargar datos dinámicamente en múltiples formatos.

---

## 🚀 Características Principales

✨ **Frontend Moderno**
- Interfaz web profesional con diseño glassmorphism
- Drag & drop para subir archivos
- Visualizaciones interactivas con Plotly
- Diseño responsive y dark mode

📊 **Data Loader Multi-formato**
- Soporte para CSV, XLSX y JSON
- Detección automática de encoding y delimitadores
- Validación de datos y manejo de errores

🧪 **Análisis A/B Testing**
- Pruebas estadísticas (Chi-cuadrado, t-test)
- Cálculo automático de métricas
- Interpretación en lenguaje natural
- Visualización de resultados

🔧 **Backend API RESTful**
- FastAPI con endpoints documentados
- Gestión de datasets en memoria
- Análisis en tiempo real

---

## 📁 Estructura del Proyecto

```
ab-testing-finance-analytics/
│
├── backend/                    # Backend FastAPI
│   ├── main.py                 # Aplicación principal
│   ├── routes.py               # API endpoints
│   ├── models.py               # Modelos Pydantic
│   ├── data_loader.py          # Cargador multi-formato
│   ├── dataset_manager.py      # Gestor de datasets
│   └── ab_testing.py           # Lógica de análisis
│
├── frontend/                   # Frontend web
│   ├── index.html              # Página principal
│   ├── styles.css              # Estilos glassmorphism
│   └── app.js                  # Lógica JavaScript
│
├── streamlit_app/              # App Streamlit (alternativa)
│   └── app.py
│
├── data/                       # Datos de ejemplo
│   └── customers.csv
│
├── notebooks/                  # Jupyter notebooks
├── requirements.txt            # Dependencias
└── README.md
```

---

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Terraspace009/ab-testing-finance-analytics.git
cd ab-testing-finance-analytics
```

### 2. Crear entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 🚀 Uso

### Opción 1: Aplicación Web (Recomendado)

Inicia el servidor FastAPI:

```bash
cd backend
uvicorn main:app --reload
```

Abre tu navegador en: **http://localhost:8000**

#### Flujo de trabajo:

1. **Cargar datos**: Arrastra un archivo CSV, XLSX o JSON
2. **Ver preview**: Visualiza las primeras filas del dataset
3. **Configurar análisis**: Selecciona columnas y grupos
4. **Ejecutar análisis**: Obtén resultados estadísticos
5. **Visualizar**: Gráficos interactivos de resultados

### Opción 2: Streamlit (Interfaz Simple)

```bash
streamlit run streamlit_app/app.py
```

---

## 📊 Formatos Soportados

### CSV
- Detección automática de delimitador (`,` `;` `\t` `|`)
- Detección de encoding (UTF-8, ISO-8859-1, etc.)
- Validación de columnas duplicadas

### XLSX
- Archivos Excel (.xlsx, .xls)
- Lectura de hojas específicas
- Soporte para múltiples hojas

### JSON
- Orientación: records, index, columns
- Arrays de objetos
- Objetos con estructura de tabla

---

## 🧪 Análisis A/B Testing

El sistema realiza automáticamente:

### Métricas Calculadas
- **Tasas de conversión** por grupo (control vs treatment)
- **Lift absoluto y porcentual**
- **Chi-cuadrado** para variables categóricas
- **T-test** para variables continuas
- **P-value** y nivel de significancia

### Interpretación
- Resultados en lenguaje natural (español)
- Recomendaciones basadas en significancia estadística
- Tabla de contingencia detallada
- Gráficos de barras comparativos

---

## 🌐 API Endpoints

### Cargar archivo
```http
POST /api/upload
Content-Type: multipart/form-data

file: <archivo.csv|xlsx|json>
```

### Listar datasets
```http
GET /api/datasets
```

### Preview de dataset
```http
GET /api/dataset/{dataset_id}/preview?n_rows=100
```

### Ejecutar análisis
```http
POST /api/analyze
Content-Type: application/json

{
  "dataset_id": "uuid",
  "group_column": "received_bonus_offer",
  "target_column": "signed_up",
  "control_value": "No",
  "treatment_value": "Yes",
  "alpha": 0.05
}
```

Documentación completa: **http://localhost:8000/docs**

---

## 🧰 Tech Stack

**Backend**:
- FastAPI - Framework web moderno
- Pandas - Procesamiento de datos
- SciPy - Análisis estadístico
- Pydantic - Validación de datos
- Uvicorn - Servidor ASGI

**Frontend**:
- HTML5, CSS3, JavaScript (Vanilla)
- Plotly.js - Visualizaciones interactivas
- Glassmorphism - Diseño moderno

**Data Processing**:
- openpyxl - Lectura de Excel
- chardet - Detección de encoding
- NumPy - Operaciones numéricas

---

## 📌 Ejemplo de Uso

### Datos de Entrada (customers.csv)

```csv
customer_id,received_bonus_offer,signed_up,age,income
1,Yes,Yes,35,75000
2,No,No,42,65000
3,Yes,Yes,28,80000
...
```

### Configuración del Análisis

- **Grupo**: `received_bonus_offer`
- **Target**: `signed_up`
- **Control**: `No`
- **Treatment**: `Yes`
- **Alpha**: `0.05`

### Resultados

```
✅ Resultado significativo
Control: 12.5%
Treatment: 18.7%
Lift: +6.2% (+49.6%)
P-value: 0.0023 (< 0.05)
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

---

## 👨‍💻 Autor

**Miguel Espitia**

Proyecto de portafolio en Data Science y Análisis A/B Testing

---

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en GitHub.
