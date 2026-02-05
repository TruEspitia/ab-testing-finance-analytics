import matplotlib.pyplot as plt
import io
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
import zipfile
from datetime import datetime
from scipy import stats
from scipy.interpolate import make_interp_spline
import warnings

warnings.filterwarnings('ignore')

# Activar modo interactivo de matplotlib
plt.ion()

def cargar_y_preparar_datos(ruta_excel):
    try:
        print("Cargando datos desde el archivo Excel...")
        df = pd.read_excel(ruta_excel)
        df_trabajo = pd.DataFrame()
        df_trabajo['curp'] = df.iloc[:, 4].astype(str).str.strip()
        df_trabajo['marca'] = df.iloc[:, 6].astype(str).str.strip()
        df_trabajo['fecha_marcado'] = pd.to_datetime(df.iloc[:, 7], errors='coerce')
        df_trabajo.dropna(inplace=True)
        df_trabajo = df_trabajo[(df_trabajo['curp'] != '') & (df_trabajo['marca'] != '')]
        df_trabajo['curp_anonimo'] = df_trabajo['curp'].str[-6:]
        df_trabajo['año'] = df_trabajo['fecha_marcado'].dt.year
        df_trabajo['mes'] = df_trabajo['fecha_marcado'].dt.month
        df_trabajo['dia'] = df_trabajo['fecha_marcado'].dt.day
        df_trabajo['dia_semana'] = df_trabajo['fecha_marcado'].dt.dayofweek
        df_trabajo['dia_año'] = df_trabajo['fecha_marcado'].dt.dayofyear
        df_trabajo['trimestre'] = df_trabajo['fecha_marcado'].dt.quarter

        label_encoder = LabelEncoder()
        df_trabajo['marca_encoded'] = label_encoder.fit_transform(df_trabajo['marca'])

        print(f"Datos preparados con {len(df_trabajo)} registros y {df_trabajo['marca'].nunique()} marcas únicas")
        return df_trabajo, label_encoder
    except Exception as e:
        print(f"ERROR al cargar y preparar datos: {str(e)}")
        return None, None

def ejecutar_clustering(df_trabajo):
    try:
        n_clusters = min(df_trabajo['marca'].nunique(), 10)
        
        # Agregar métricas adicionales
        df_trabajo['frecuencia'] = df_trabajo.groupby(['curp_anonimo', 'marca'])['curp_anonimo'].transform('count')
        df_trabajo['dias_activo'] = df_trabajo.groupby(['curp_anonimo', 'marca'])['fecha_marcado'].transform(
            lambda x: (x.max() - x.min()).days if len(x) > 1 else 1
        )
        
        # Agregar mes y día más frecuente
        df_trabajo['mes_frecuente'] = df_trabajo.groupby(['curp_anonimo', 'marca'])['mes'].transform(
            lambda x: x.mode()[0] if len(x) > 0 else x.iloc[0]
        )
        df_trabajo['dia_semana_frecuente'] = df_trabajo.groupby(['curp_anonimo', 'marca'])['dia_semana'].transform(
            lambda x: x.mode()[0] if len(x) > 0 else x.iloc[0]
        )
        
        features_persona = df_trabajo.copy()
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features_persona[['marca_encoded', 'mes', 'dia', 'dia_semana', 'trimestre']])
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        features_persona['cluster'] = clusters
        
        silhouette = silhouette_score(X_scaled, clusters)
        print(f"Silhouette Score: {silhouette:.3f}")

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], hue=clusters, palette='viridis')
        plt.title('Clustering K-Means')
        plt.xlabel('Componente Principal 1')
        plt.ylabel('Componente Principal 2')
        plt.draw()
        plt.pause(0.001)
        
        return features_persona, kmeans, scaler
    except Exception as e:
        print(f"ERROR en clustering: {str(e)}")
        return None, None, None

def entrenar_red_neuronal(df_trabajo):
    try:
        all_features = ['año', 'mes', 'dia', 'dia_semana', 'dia_año', 'trimestre', 'marca_encoded']
        X = df_trabajo[all_features].values
        y = df_trabajo['marca_encoded'].values
        
        label_encoder_nn = LabelEncoder()
        y_encoded_cleaned = label_encoder_nn.fit_transform(y)
        n_clases = len(label_encoder_nn.classes_)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded_cleaned, test_size=0.2, random_state=42, stratify=y_encoded_cleaned)
        scaler_nn = StandardScaler()
        X_train_scaled = scaler_nn.fit_transform(X_train)
        X_test_scaled = scaler_nn.transform(X_test)
        
        y_train_cat = keras.utils.to_categorical(y_train, num_classes=n_clases)
        y_test_cat = keras.utils.to_categorical(y_test, num_classes=n_clases)
        
        model = keras.Sequential([
            layers.Dense(256, activation='relu', input_shape=(len(all_features),)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(n_clases, activation='softmax')
        ])
        
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        
        early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        history = model.fit(X_train_scaled, y_train_cat, epochs=50, batch_size=128, validation_split=0.2, callbacks=[early_stopping], verbose=0)
        
        plt.figure(figsize=(14, 5))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Loss Entrenamiento')
        plt.plot(history.history['val_loss'], label='Loss Validación')
        plt.title('Loss durante el Entrenamiento')
        plt.legend()
        plt.subplot(1, 2, 2)
        plt.plot(history.history['accuracy'], label='Accuracy Entrenamiento')
        plt.plot(history.history['val_accuracy'], label='Accuracy Validación')
        plt.title('Accuracy durante el Entrenamiento')
        plt.legend()
        plt.draw()
        plt.pause(0.001)
        print("\nRed neuronal entrenada con éxito")
        
        return model, scaler_nn
    except Exception as e:
        print(f"ERROR en entrenamiento de red neuronal: {str(e)}")
        return None, None

def analizar_distribuciones_completas(features_clustered):
    print("\nANALISIS DE DISTRIBUCIONES POR CLUSTER - TODAS LAS MARCAS")
    print("-" * 70)
    
    # Función para plotear PDF
    def plot_pdf(mu, sigma, label, color=None, alpha=0.7):
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 1000)
        y = stats.norm.pdf(x, mu, sigma)
        plt.plot(x, y, label=label, color=color, linewidth=2, alpha=alpha)
        plt.fill_between(x, y, alpha=0.3, color=color)
    
    # ANÁLISIS 1: Distribuciones generales por variable
    print("\nANALISIS 1: Distribuciones por Variable")
    variables_analizar = ['frecuencia', 'dias_activo', 'mes_frecuente']
    
    for variable in variables_analizar:
        print(f"\n   Analizando: {variable}")
        plt.figure(figsize=(14, 8))
        
        n_clusters = features_clustered['cluster'].nunique()
        colors = plt.cm.Set3(np.linspace(0, 1, n_clusters))
        
        # Subplot 1: PDFs por cluster
        plt.subplot(2, 2, 1)
        parametros = []
        for cluster in sorted(features_clustered['cluster'].unique()):
            datos_cluster = features_clustered[features_clustered['cluster'] == cluster][variable]
            if len(datos_cluster) > 0:
                mu = datos_cluster.mean()
                sigma = datos_cluster.std()
                if sigma > 0:
                    plot_pdf(mu, sigma,
                            label=f"Cluster {cluster}: μ={mu:.2f}, σ={sigma:.2f}",
                            color=colors[cluster])
                    parametros.append({'cluster': cluster, 'mu': mu, 'sigma': sigma})
        
        plt.title(f"Distribuciones PDF - {variable}")
        plt.xlabel(variable)
        plt.ylabel('Densidad')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Histogramas superpuestos
        plt.subplot(2, 2, 2)
        for cluster in sorted(features_clustered['cluster'].unique()):
            datos = features_clustered[features_clustered['cluster'] == cluster][variable]
            plt.hist(datos, bins=30, alpha=0.5, density=True,
                    label=f'Cluster {cluster}', color=colors[cluster])
        
        plt.title(f"Histogramas Normalizados - {variable}")
        plt.xlabel(variable)
        plt.ylabel('Densidad')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Subplot 3: Violin plots
        plt.subplot(2, 2, 3)
        data_violin = []
        positions = []
        for i, cluster in enumerate(sorted(features_clustered['cluster'].unique())):
            datos = features_clustered[features_clustered['cluster'] == cluster][variable].values
            data_violin.append(datos)
            positions.append(i)
        
        parts = plt.violinplot(data_violin, positions=positions, showmeans=True, showmedians=True)
        
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i])
            pc.set_alpha(0.7)
        
        plt.xticks(positions, [f'C{c}' for c in sorted(features_clustered['cluster'].unique())])
        plt.title(f"Violin Plots - {variable}")
        plt.xlabel('Cluster')
        plt.ylabel(variable)
        plt.grid(True, alpha=0.3)
        
        # Subplot 4: QQ plots
        plt.subplot(2, 2, 4)
        for cluster in sorted(features_clustered['cluster'].unique()):
            datos = features_clustered[features_clustered['cluster'] == cluster][variable]
            if len(datos) > 0:
                stats.probplot(datos, dist="norm", plot=plt)
        
        plt.title(f"Q-Q Plots (Normalidad) - {variable}")
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)
    
    # ANÁLISIS 2: Distribución de TODAS las marcas por cluster
    print("\nANALISIS 2: Distribución de TODAS las Marcas")
    todas_marcas = sorted(features_clustered['marca'].unique())
    n_marcas = len(todas_marcas)
    print(f"   Total de marcas únicas: {n_marcas}")
    
    # Crear matriz de distribución marca-cluster
    marca_cluster_dist = np.zeros((n_marcas, n_clusters))
    for i, marca in enumerate(todas_marcas):
        for j, cluster in enumerate(sorted(features_clustered['cluster'].unique())):
            count = len(features_clustered[
                (features_clustered['marca'] == marca) &
                (features_clustered['cluster'] == cluster)
            ])
            marca_cluster_dist[i, j] = count
    
    # Normalizar por cluster
    marca_cluster_norm = marca_cluster_dist / (marca_cluster_dist.sum(axis=0) + 1e-10)
    
    # Visualización: Heatmap
    plt.figure(figsize=(12, max(8, n_marcas * 0.3)))
    sns.heatmap(marca_cluster_norm,
                xticklabels=[f'Cluster {c}' for c in range(n_clusters)],
                yticklabels=todas_marcas,
                cmap='YlOrRd',
                cbar_kws={'label': 'Proporción'})
    plt.title(f'Distribución de TODAS las Marcas ({n_marcas}) por Cluster')
    plt.xlabel('Cluster')
    plt.ylabel('Marca')
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)
    
    # ANÁLISIS 3: PDFs para frecuencia por marca
    print("\nANALISIS 3: Distribuciones de Frecuencia para CADA Marca")
    marcas_por_grafico = 6
    n_graficos = int(np.ceil(n_marcas / marcas_por_grafico))
    
    for grupo in range(min(n_graficos, 3)):  # Limitar a 3 gráficos para no saturar
        inicio = grupo * marcas_por_grafico
        fin = min((grupo + 1) * marcas_por_grafico, n_marcas)
        marcas_grupo = todas_marcas[inicio:fin]
        
        if len(marcas_grupo) == 0:
            continue
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for idx, marca in enumerate(marcas_grupo):
            ax = axes[idx]
            
            for cluster in sorted(features_clustered['cluster'].unique()):
                datos_marca_cluster = features_clustered[
                    (features_clustered['marca'] == marca) &
                    (features_clustered['cluster'] == cluster)
                ]['frecuencia']
                
                if len(datos_marca_cluster) > 1:
                    mu = datos_marca_cluster.mean()
                    sigma = datos_marca_cluster.std()
                    if sigma > 0:
                        x = np.linspace(max(0, mu - 3*sigma), mu + 3*sigma, 100)
                        y = stats.norm.pdf(x, mu, sigma)
                        ax.plot(x, y,
                               label=f"C{cluster}: μ={mu:.1f}, σ={sigma:.1f}",
                               color=colors[cluster],
                               linewidth=2,
                               alpha=0.7)
                        ax.fill_between(x, y, alpha=0.3, color=colors[cluster])
            
            ax.set_title(f'Marca: {marca}', fontsize=10)
            ax.set_xlabel('Frecuencia')
            ax.set_ylabel('Densidad')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)
        
        for idx in range(len(marcas_grupo), len(axes)):
            axes[idx].set_visible(False)
        
        plt.suptitle(f'Distribuciones de Frecuencia - Grupo {grupo + 1}/{n_graficos}', fontsize=14)
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)
    
    # ANÁLISIS 4: Resumen estadístico
    print("\nRESUMEN ESTADISTICO GLOBAL")
    print("-" * 100)
    print(f"{'Marca':<20} {'Cluster':<10} {'N':<10} {'Media Frec':<12} {'Std Frec':<12} {'Media Días':<12}")
    print("-" * 100)
    
    for marca in todas_marcas[:20]:
        for cluster in sorted(features_clustered['cluster'].unique()):
            datos = features_clustered[
                (features_clustered['marca'] == marca) &
                (features_clustered['cluster'] == cluster)
            ]
            if len(datos) > 0:
                print(f"{marca:<20} {cluster:<10} {len(datos):<10} "
                      f"{datos['frecuencia'].mean():<12.2f} {datos['frecuencia'].std():<12.2f} "
                      f"{datos['dias_activo'].mean():<12.2f}")
    
    if n_marcas > 20:
        print(f"\n... y {n_marcas - 20} marcas más")
    
    # ANÁLISIS 5: Distribución temporal
    print("\nANALISIS 5: Distribución Temporal Global")
    plt.figure(figsize=(14, 8))
    
    marca_por_cluster = features_clustered.groupby('cluster')['marca'].agg(
        lambda x: x.mode()[0] if not x.empty else 'N/A'
    ).to_dict()
    
    # Subplot 1: Distribución por mes
    plt.subplot(2, 1, 1)
    for cluster in sorted(features_clustered['cluster'].unique()):
        meses_cluster = features_clustered[features_clustered['cluster'] == cluster]['mes_frecuente']
        marca_label = marca_por_cluster.get(cluster, f'Cluster {cluster}')
        
        if len(meses_cluster) > 0:
            counts, bins = np.histogram(meses_cluster, bins=12, range=(1, 13))
            centers = (bins[:-1] + bins[1:]) / 2
            
            x_smooth = np.linspace(1, 12, 300)
            spl = make_interp_spline(centers, counts, k=3)
            y_smooth = spl(x_smooth)
            
            plt.plot(x_smooth, y_smooth, 
                    label=f'Cluster {cluster}: {marca_label}',
                    color=colors[cluster], linewidth=2, alpha=0.8)
            plt.fill_between(x_smooth, y_smooth, alpha=0.3, color=colors[cluster])
    
    plt.xlabel('Mes')
    plt.ylabel('Frecuencia')
    plt.title('Distribución Temporal por Mes - Todas las Marcas')
    plt.xticks(range(1, 13), ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                               'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Subplot 2: Distribución por día de la semana
    plt.subplot(2, 1, 2)
    for cluster in sorted(features_clustered['cluster'].unique()):
        dias_cluster = features_clustered[features_clustered['cluster'] == cluster]['dia_semana_frecuente']
        marca_label = marca_por_cluster.get(cluster, f'Cluster {cluster}')
        
        if len(dias_cluster) > 0:
            mu = dias_cluster.mean()
            sigma = dias_cluster.std()
            if sigma > 0:
                plot_pdf(mu, sigma,
                        label=f"Cluster {cluster} ({marca_label}): μ={mu:.2f}, σ={sigma:.2f}",
                        color=colors[cluster])
    
    plt.xlabel('Día de la Semana (0=Lunes, 6=Domingo)')
    plt.ylabel('Densidad')
    plt.title('Distribución por Día de la Semana - Todas las Marcas')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)
    
    print("\nAnálisis de distribuciones completado para TODAS las marcas")

def analizar_distribuciones_por_cluster(features_clustered):
    try:
        plt.figure(figsize=(12, 8))
        sns.violinplot(x='cluster', y='marca_encoded', data=features_clustered, palette='muted')
        plt.title('Distribución de la Frecuencia por Cluster')
        plt.draw()
        plt.pause(0.001)
        print("\nAnálisis de distribuciones realizado correctamente")
    except Exception as e:
        print(f"Error en el análisis de distribuciones: {str(e)}")

def analizar_valores_p(features_clustered):
    print("\nANALISIS DE VALORES P PARA CADA MARCA")
    print("=" * 80)
    
    resultados = []
    todas_marcas = sorted(features_clustered['marca'].unique())
    print(f"\nAnalizando {len(todas_marcas)} marcas...\n")
    
    for i, marca in enumerate(todas_marcas):
        if i % 50 == 0:
            print(f"   Procesando marca {i+1}/{len(todas_marcas)}...")
        
        datos_marca = features_clustered[features_clustered['marca'] == marca]
        if len(datos_marca) < 2:
            continue
        
        resultado = {
            'marca': marca,
            'n_registros': len(datos_marca),
            'n_clusters': datos_marca['cluster'].nunique()
        }
        
        # Test ANOVA entre clusters para frecuencia
        try:
            grupos_frecuencia = []
            for cluster in sorted(features_clustered['cluster'].unique()):
                grupo = datos_marca[datos_marca['cluster'] == cluster]['frecuencia'].values
                if len(grupo) > 0:
                    grupos_frecuencia.append(grupo)
            
            if len(grupos_frecuencia) >= 2:
                all_values = np.concatenate(grupos_frecuencia)
                if len(np.unique(all_values)) > 1:
                    _, p_anova_freq = stats.f_oneway(*grupos_frecuencia)
                    resultado['p_anova_frecuencia'] = p_anova_freq
                else:
                    resultado['p_anova_frecuencia'] = 1.0
            else:
                resultado['p_anova_frecuencia'] = np.nan
        except:
            resultado['p_anova_frecuencia'] = np.nan
        
        # Test Chi-cuadrado para distribución entre clusters
        try:
            obs_freq = []
            for cluster in sorted(features_clustered['cluster'].unique()):
                count = len(datos_marca[datos_marca['cluster'] == cluster])
                obs_freq.append(count)
            
            if sum(obs_freq) > 0 and len([x for x in obs_freq if x > 0]) > 1:
                obs_freq_filtered = [x for x in obs_freq if x > 0]
                expected = [sum(obs_freq_filtered) / len(obs_freq_filtered)] * len(obs_freq_filtered)
                if min(expected) >= 5:
                    _, p_chi2 = stats.chisquare(obs_freq_filtered, expected)
                    resultado['p_chi2_distribucion'] = p_chi2
                else:
                    resultado['p_chi2_distribucion'] = np.nan
            else:
                resultado['p_chi2_distribucion'] = np.nan
        except:
            resultado['p_chi2_distribucion'] = np.nan
        
        resultados.append(resultado)
    
    df_valores_p = pd.DataFrame(resultados)
    
    # Imprimir resultados
    print("\nVALORES P POR MARCA")
    print("=" * 100)
    print(f"{'Marca':<30} {'N':<10} {'Clusters':<10} {'ANOVA Frec':<15} {'Chi2 Dist':<15}")
    print("-" * 100)
    
    for _, row in df_valores_p.head(50).iterrows():  # Mostrar solo las primeras 50
        print(f"{row['marca']:<30} {row['n_registros']:<10} {row['n_clusters']:<10} ", end="")
        
        # Formatear valor ANOVA
        valor = row['p_anova_frecuencia']
        if pd.isna(valor):
            print(f"{'N/A':<15} ", end="")
        elif valor == 1.0:
            print(f"{'No var.':<15} ", end="")
        else:
            sig = "***" if valor < 0.001 else "**" if valor < 0.01 else "*" if valor < 0.05 else ""
            print(f"{valor:>10.4f}{sig:<5} ", end="")
        
        # Formatear valor Chi2
        valor = row['p_chi2_distribucion']
        if pd.isna(valor):
            print(f"{'N/A':<15}")
        else:
            sig = "***" if valor < 0.001 else "**" if valor < 0.01 else "*" if valor < 0.05 else ""
            print(f"{valor:>10.4f}{sig:<5}")
    
    # Resumen
    print("\nRESUMEN DE SIGNIFICANCIA ESTADISTICA")
    print("=" * 80)
    print("Niveles de significancia: * p<0.05, ** p<0.01, *** p<0.001")
    
    # Top marcas significativas
    print("\nTOP 10 MARCAS CON DIFERENCIAS MAS SIGNIFICATIVAS")
    print("-" * 60)
    df_validos = df_valores_p[df_valores_p['p_anova_frecuencia'].notna() & 
                              (df_valores_p['p_anova_frecuencia'] < 1.0)]
    if len(df_validos) > 0:
        top_marcas = df_validos.nsmallest(min(10, len(df_validos)), 'p_anova_frecuencia')
        for i, (_, row) in enumerate(top_marcas.iterrows(), 1):
            print(f"{i:2d}. {row['marca']:<30} p = {row['p_anova_frecuencia']:.6f}")
    
    # Guardar resultados
    df_valores_p.to_csv('valores_p_marcas.csv', index=False)
    print("\nResultados guardados en 'valores_p_marcas.csv'")
    
    return df_valores_p

def analizar_patrones_temporales(df_trabajo):
    print("\nANALISIS DE PATRONES TEMPORALES")
    print("=" * 80)
    
    plt.figure(figsize=(15, 5))
    
    # Análisis por día de la semana
    plt.subplot(1, 3, 1)
    conteo_dia_semana = df_trabajo['dia_semana'].value_counts().sort_index()
    dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    plt.bar(range(7), conteo_dia_semana.values)
    plt.xticks(range(7), dias)
    plt.title('Distribución por Día de la Semana')
    plt.xlabel('Día')
    plt.ylabel('Cantidad de Registros')
    
    # Análisis por mes
    plt.subplot(1, 3, 2)
    conteo_mes = df_trabajo['mes'].value_counts().sort_index()
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    plt.bar(range(1, 13), conteo_mes.values)
    plt.xticks(range(1, 13), meses, rotation=45)
    plt.title('Distribución por Mes')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad de Registros')
    
    # Análisis por trimestre
    plt.subplot(1, 3, 3)
    conteo_trimestre = df_trabajo['trimestre'].value_counts().sort_index()
    plt.bar(range(1, 5), conteo_trimestre.values)
    plt.xticks(range(1, 5), ['Q1', 'Q2', 'Q3', 'Q4'])
    plt.title('Distribución por Trimestre')
    plt.xlabel('Trimestre')
    plt.ylabel('Cantidad de Registros')
    
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)
    
    # Estadísticas temporales
    print("\nESTADISTICAS TEMPORALES:")
    print(f"Día más activo: {dias[conteo_dia_semana.idxmax()]} ({conteo_dia_semana.max()} registros)")
    print(f"Mes más activo: {meses[conteo_mes.idxmax()-1]} ({conteo_mes.max()} registros)")
    print(f"Trimestre más activo: Q{conteo_trimestre.idxmax()} ({conteo_trimestre.max()} registros)")

def analizar_marcas_principales(df_trabajo, top_n=20):
    print(f"\nANALISIS DE TOP {top_n} MARCAS")
    print("=" * 80)
    
    # Contar frecuencia de marcas
    conteo_marcas = df_trabajo['marca'].value_counts().head(top_n)
    
    # Visualización
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(conteo_marcas)), conteo_marcas.values)
    plt.yticks(range(len(conteo_marcas)), conteo_marcas.index)
    plt.xlabel('Cantidad de Registros')
    plt.title(f'Top {top_n} Marcas por Frecuencia')
    plt.gca().invert_yaxis()
    
    # Agregar valores en las barras
    for i, v in enumerate(conteo_marcas.values):
        plt.text(v + 10, i, str(v), va='center')
    
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)
    
    # Estadísticas
    print(f"\nMarca más frecuente: {conteo_marcas.index[0]} ({conteo_marcas.values[0]} registros)")
    print(f"Total de marcas únicas: {df_trabajo['marca'].nunique()}")
    print(f"Promedio de registros por marca: {len(df_trabajo) / df_trabajo['marca'].nunique():.2f}")

def crear_matriz_correlacion(features_clustered):
    print("\nMATRIZ DE CORRELACION")
    print("=" * 80)
    
    # Seleccionar solo columnas numéricas relevantes
    columnas_numericas = ['marca_encoded', 'año', 'mes', 'dia', 'dia_semana', 
                         'trimestre', 'cluster', 'frecuencia', 'dias_activo']
    
    # Filtrar columnas que existen
    columnas_disponibles = [col for col in columnas_numericas if col in features_clustered.columns]
    
    correlacion = features_clustered[columnas_disponibles].corr()
    
    # Visualización
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlacion, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title('Matriz de Correlación entre Variables')
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)
    
    # Correlaciones más fuertes
    print("\nCORRELACIONES MAS FUERTES (|r| > 0.3):")
    for i in range(len(correlacion)):
        for j in range(i+1, len(correlacion)):
            valor = correlacion.iloc[i, j]
            if abs(valor) > 0.3:
                print(f"{correlacion.index[i]} - {correlacion.columns[j]}: {valor:.3f}")

def generar_reporte_resumen(df_trabajo, features_clustered, df_valores_p):
    print("\n" + "="*80)
    print("REPORTE RESUMEN EJECUTIVO")
    print("="*80)
    
    # Información general
    print("\n1. INFORMACION GENERAL")
    print(f"   - Total de registros: {len(df_trabajo):,}")
    print(f"   - Total de marcas únicas: {df_trabajo['marca'].nunique():,}")
    print(f"   - Total de usuarios únicos: {df_trabajo['curp_anonimo'].nunique():,}")
    print(f"   - Periodo de datos: {df_trabajo['fecha_marcado'].min()} a {df_trabajo['fecha_marcado'].max()}")
    
    # Información de clustering
    print("\n2. RESULTADOS DE CLUSTERING")
    print(f"   - Número de clusters: {features_clustered['cluster'].nunique()}")
    print(f"   - Distribución de registros por cluster:")
    for cluster in sorted(features_clustered['cluster'].unique()):
        count = len(features_clustered[features_clustered['cluster'] == cluster])
        pct = count / len(features_clustered) * 100
        print(f"     * Cluster {cluster}: {count:,} registros ({pct:.1f}%)")
    
    # Información estadística
    if df_valores_p is not None and len(df_valores_p) > 0:
        print("\n3. RESULTADOS ESTADISTICOS")
        valores_validos = df_valores_p['p_anova_frecuencia'].dropna()
        valores_validos = valores_validos[valores_validos < 1.0]
        if len(valores_validos) > 0:
            sig_count = (valores_validos < 0.05).sum()
            print(f"   - Marcas con diferencias significativas entre clusters: {sig_count} ({sig_count/len(valores_validos)*100:.1f}%)")
            print(f"   - Valor p promedio: {valores_validos.mean():.4f}")
            print(f"   - Valor p mediano: {valores_validos.median():.4f}")
    
    # Recomendaciones
    print("\n4. RECOMENDACIONES")
    print("   - Las marcas con diferencias significativas entre clusters pueden requerir estrategias diferenciadas")
    print("   - Considerar análisis temporal más detallado para marcas con alta frecuencia")
    print("   - Evaluar patrones de uso por día de semana para optimización de recursos")
    
    # Guardar reporte
    with open('reporte_resumen.txt', 'w', encoding='utf-8') as f:
        f.write("REPORTE RESUMEN EJECUTIVO\n")
        f.write("="*80 + "\n")
        f.write(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\nTotal de registros: {len(df_trabajo):,}\n")
        f.write(f"Total de marcas únicas: {df_trabajo['marca'].nunique():,}\n")
        f.write(f"Número de clusters: {features_clustered['cluster'].nunique()}\n")
    
    print("\n   Reporte guardado en 'reporte_resumen.txt'")

def guardar_y_comprimir_figuras_en_memoria():
    print("\nGuardando y comprimiendo figuras en memoria...")
    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_memory:
            # Obtener todos los números de figura
            fig_nums = plt.get_fignums()
            for i, num in enumerate(fig_nums):
                # Obtener la figura por su número
                fig = plt.figure(num)
                fig_buffer = io.BytesIO()
                fig.savefig(fig_buffer, format='png', bbox_inches='tight', dpi=100)
                fig_buffer.seek(0)
                zip_memory.writestr(f'figura_{i+1}.png', fig_buffer.read())
                print(f"   Figura {i+1} guardada en memoria.")
    except Exception as e:
        print(f"Error al guardar figuras: {str(e)}")
    
    zip_buffer.seek(0)
    print("\nFiguras comprimidas exitosamente en memoria.")
    
    # Opcional: Guardar el archivo ZIP en disco
    with open('figuras_analisis.zip', 'wb') as f:
        f.write(zip_buffer.getvalue())
    print("Archivo 'figuras_analisis.zip' guardado en disco.")
    
    return zip_buffer

# Main
if __name__ == "__main__":
    print("Iniciando proceso completo...")
    ruta_excel = 'C:\\Users\\miguel.espitia\\Downloads\\localinsertk (1).xlsx'
    
    # Cargar datos
    df_trabajo, label_encoder = cargar_y_preparar_datos(ruta_excel)
    
    if df_trabajo is not None:
        # Ejecutar clustering
        features_clustered, modelo_kmeans, scaler = ejecutar_clustering(df_trabajo)
        
        if features_clustered is not None:
            # Entrenar red neuronal
            model, scaler_nn = entrenar_red_neuronal(df_trabajo)
            
            # Análisis de distribuciones básico
            analizar_distribuciones_por_cluster(features_clustered)
            
            # NUEVO: Análisis de distribuciones completo
            analizar_distribuciones_completas(features_clustered)
            
            # Análisis de valores p
            df_valores_p = analizar_valores_p(features_clustered)
            
            # Análisis temporales
            analizar_patrones_temporales(df_trabajo)
            
            # Análisis de marcas principales
            analizar_marcas_principales(df_trabajo)
            
            # Matriz de correlación
            crear_matriz_correlacion(features_clustered)
            
            # Generar reporte resumen
            generar_reporte_resumen(df_trabajo, features_clustered, df_valores_p)
            
        # Guardar figuras
        zip_figuras_memoria = guardar_y_comprimir_figuras_en_memoria()
        
        print("\n" + "="*80)
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)
        print("\nArchivos generados:")
        print("  - valores_p_marcas.csv")
        print("  - reporte_resumen.txt")
        print("  - figuras_analisis.zip")
        print("  - Figuras comprimidas en memoria")
        
        # Mantener las figuras abiertas
        print("\nPresiona Ctrl+C en la consola para cerrar todas las figuras y terminar el programa.")
        plt.ioff()  # Desactivar modo interactivo
        plt.show()  # Mostrar todas las figuras y mantenerlas abiertas