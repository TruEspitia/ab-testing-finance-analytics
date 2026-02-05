"""
Clustering Service
Provides K-means and DBSCAN clustering functionality based on analizer.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
import io
import base64
from typing import List, Dict, Optional, Tuple, Any
import warnings

warnings.filterwarnings('ignore')


class ClusteringService:
    """
    Service for performing clustering analysis on datasets
    Supports K-means and DBSCAN algorithms
    Based on the clustering logic from analizer.py
    """
    
    @staticmethod
    def prepare_features(df: pd.DataFrame, feature_columns: List[str]) -> Tuple[np.ndarray, StandardScaler]:
        """
        Prepara las features para clustering con normalización
        
        Args:
            df: DataFrame con los datos
            feature_columns: Lista de columnas a usar como features
            
        Returns:
            Tupla (features_scaled, scaler)
        """
        # Validar que todas las columnas existen
        missing_cols = [col for col in feature_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Columnas no encontradas: {missing_cols}")
        
        # Extraer features
        X = df[feature_columns].values
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, scaler
    
    @staticmethod
    def kmeans_clustering(
        df: pd.DataFrame,
        feature_columns: List[str],
        n_clusters: int = None,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Ejecuta clustering K-means
        Basado en ejecutar_clustering() de analizer.py
        
        Args:
            df: DataFrame con los datos
            feature_columns: Columnas a usar como features
            n_clusters: Número de clusters (si None, se calcula automáticamente)
            random_state: Semilla para reproducibilidad
            
        Returns:
            Diccionario con resultados del clustering
        """
        try:
            # Preparar features
            X_scaled, scaler = ClusteringService.prepare_features(df, feature_columns)
            
            # Calcular n_clusters si no se especifica
            if n_clusters is None:
                # Regla heurística: raíz cuadrada del número de muestras, máximo 10
                n_clusters = min(int(np.sqrt(len(df))), 10)
                n_clusters = max(2, n_clusters)  # Mínimo 2 clusters
            
            # Validar n_clusters
            if n_clusters < 2:
                raise ValueError("n_clusters debe ser al menos 2")
            if n_clusters > len(df):
                raise ValueError(f"n_clusters ({n_clusters}) no puede ser mayor que el número de muestras ({len(df)})")
            
            # Ejecutar K-means
            kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Calcular métricas
            silhouette = silhouette_score(X_scaled, clusters) if len(set(clusters)) > 1 else 0.0
            davies_bouldin = davies_bouldin_score(X_scaled, clusters) if len(set(clusters)) > 1 else 0.0
            
            # Reducción dimensional para visualización
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Generar visualización
            fig, ax = plt.subplots(figsize=(10, 6))
            scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', alpha=0.6)
            plt.colorbar(scatter, ax=ax, label='Cluster')
            ax.set_title(f'K-Means Clustering (k={n_clusters})\nSilhouette Score: {silhouette:.3f}')
            ax.set_xlabel('Componente Principal 1')
            ax.set_ylabel('Componente Principal 2')
            ax.grid(True, alpha=0.3)
            
            # Convertir a base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            # Estadísticas por cluster
            cluster_stats = []
            for i in range(n_clusters):
                mask = clusters == i
                cluster_stats.append({
                    'cluster_id': int(i),
                    'size': int(mask.sum()),
                    'percentage': float(mask.sum() / len(df) * 100),
                    'centroid': kmeans.cluster_centers_[i].tolist()
                })
            
            return {
                'success': True,
                'algorithm': 'kmeans',
                'n_clusters': n_clusters,
                'labels': clusters.tolist(),
                'silhouette_score': float(silhouette),
                'davies_bouldin_score': float(davies_bouldin),
                'cluster_stats': cluster_stats,
                'pca_coordinates': X_pca.tolist(),
                'plot_base64': plot_base64,
                'inertia': float(kmeans.inertia_)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def dbscan_clustering(
        df: pd.DataFrame,
        feature_columns: List[str],
        eps: float = 0.5,
        min_samples: int = 5
    ) -> Dict[str, Any]:
        """
        Ejecuta clustering DBSCAN
        
        Args:
            df: DataFrame con los datos
            feature_columns: Columnas a usar como features
            eps: Radio máximo de vecindad
            min_samples: Número mínimo de muestras en vecindad para formar un cluster
            
        Returns:
            Diccionario con resultados del clustering
        """
        try:
            # Preparar features
            X_scaled, scaler = ClusteringService.prepare_features(df, feature_columns)
            
            # Ejecutar DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            clusters = dbscan.fit_predict(X_scaled)
            
            # Contar clusters (excluyendo ruido = -1)
            unique_clusters = set(clusters)
            n_clusters = len(unique_clusters - {-1})
            n_noise = list(clusters).count(-1)
            
            # Calcular métricas (solo si hay al menos 2 clusters válidos)
            valid_mask = clusters != -1
            if n_clusters >= 2 and valid_mask.sum() > 1:
                silhouette = silhouette_score(X_scaled[valid_mask], clusters[valid_mask])
                davies_bouldin = davies_bouldin_score(X_scaled[valid_mask], clusters[valid_mask])
            else:
                silhouette = 0.0
                davies_bouldin = 0.0
            
            # Reducción dimensional para visualización
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Generar visualización
            fig, ax = plt.subplots(figsize=(10, 6))
            scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', alpha=0.6)
            plt.colorbar(scatter, ax=ax, label='Cluster')
            ax.set_title(f'DBSCAN Clustering\nClusters: {n_clusters}, Noise: {n_noise}, Silhouette: {silhouette:.3f}')
            ax.set_xlabel('Componente Principal 1')
            ax.set_ylabel('Componente Principal 2')
            ax.grid(True, alpha=0.3)
            
            # Convertir a base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            # Estadísticas por cluster
            cluster_stats = []
            for cluster_id in sorted(unique_clusters):
                mask = clusters == cluster_id
                cluster_stats.append({
                    'cluster_id': int(cluster_id),
                    'size': int(mask.sum()),
                    'percentage': float(mask.sum() / len(df) * 100),
                    'is_noise': cluster_id == -1
                })
            
            return {
                'success': True,
                'algorithm': 'dbscan',
                'n_clusters': n_clusters,
                'n_noise': n_noise,
                'labels': clusters.tolist(),
                'silhouette_score': float(silhouette),
                'davies_bouldin_score': float(davies_bouldin),
                'cluster_stats': cluster_stats,
                'pca_coordinates': X_pca.tolist(),
                'plot_base64': plot_base64,
                'eps': eps,
                'min_samples': min_samples
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_elbow_plot(
        df: pd.DataFrame,
        feature_columns: List[str],
        max_k: int = 10
    ) -> str:
        """
        Genera el gráfico del codo para ayudar a elegir k en K-means
        
        Args:
            df: DataFrame con los datos
            feature_columns: Columnas a usar como features
            max_k: Máximo número de clusters a probar
            
        Returns:
            Plot en base64
        """
        try:
            X_scaled, _ = ClusteringService.prepare_features(df, feature_columns)
            
            max_k = min(max_k, len(df) - 1)
            if max_k < 2:
                max_k = 2
            
            inertias = []
            silhouettes = []
            k_range = range(2, max_k + 1)
            
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(X_scaled)
                inertias.append(kmeans.inertia_)
                if len(set(clusters)) > 1:
                    silhouettes.append(silhouette_score(X_scaled, clusters))
                else:
                    silhouettes.append(0.0)
            
            # Crear gráfico dual
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Gráfico del codo
            ax1.plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
            ax1.set_xlabel('Número de Clusters (k)', fontsize=12)
            ax1.set_ylabel('Inercia', fontsize=12)
            ax1.set_title('Método del Codo', fontsize=14)
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de silhouette
            ax2.plot(k_range, silhouettes, 'go-', linewidth=2, markersize=8)
            ax2.set_xlabel('Número de Clusters (k)', fontsize=12)
            ax2.set_ylabel('Silhouette Score', fontsize=12)
            ax2.set_title('Silhouette Score vs k', fontsize=14)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convertir a base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return plot_base64
            
        except Exception as e:
            raise ValueError(f"Error generando gráfico del codo: {str(e)}")
    
    @staticmethod
    def add_cluster_labels_to_dataframe(
        df: pd.DataFrame,
        labels: List[int]
    ) -> pd.DataFrame:
        """
        Agrega las etiquetas de cluster al DataFrame
        
        Args:
            df: DataFrame original
            labels: Lista de etiquetas de cluster
            
        Returns:
            DataFrame con columna 'cluster' agregada
        """
        df_copy = df.copy()
        df_copy['cluster'] = labels
        return df_copy
