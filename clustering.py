"""
clustering.py
Community clustering and PCA dimensionality reduction module.
"""

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from data_preprocessing import load_and_preprocess_data


def perform_clustering(df, features_scaled, n_clusters=5):
    """
    Perform KMeans clustering on standardized feature data.

    Parameters:
        df (pd.DataFrame): Original DataFrame containing raw indicator columns.
        features_scaled (np.ndarray): Standardized feature matrix with 4 columns.
        n_clusters (int): Number of clusters, default is 5.

    Returns:
        tuple: (df_with_cluster, kmeans_model, stats_dict)
            df_with_cluster: DataFrame with added Cluster column.
            kmeans_model: Trained KMeans model.
            stats_dict: Dictionary of original indicator means per cluster.
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(features_scaled)

    df_with_cluster = df.copy()
    df_with_cluster['Cluster'] = labels

    stats = df_with_cluster.groupby('Cluster')[['Income', 'Education', 'Employment', 'Diversity']].mean()
    stats_dict = {int(cluster): {
        'Income': round(row['Income'], 2),
        'Education': round(row['Education'], 2),
        'Employment': round(row['Employment'], 2),
        'Diversity': round(row['Diversity'], 2)
    } for cluster, row in stats.iterrows()}

    return df_with_cluster, kmeans, stats_dict


def get_pca_projection(scaled_data):
    """
    Reduce standardized features to two principal components using PCA.

    Parameters:
        scaled_data (np.ndarray or pd.DataFrame): Standardized feature matrix.

    Returns:
        pd.DataFrame: DataFrame containing PC1 and PC2.
    """
    pca = PCA(n_components=2, random_state=42)
    pca_result = pca.fit_transform(scaled_data)
    return pd.DataFrame(pca_result, columns=['PC1', 'PC2'])


if __name__ == '__main__':
    df, features = load_and_preprocess_data()
    df_clustered, kmeans_model, cluster_stats = perform_clustering(df, features, n_clusters=5)

    print("Sample count for each cluster:")
    print(df_clustered['Cluster'].value_counts().sort_index())
    print()

    print("Statistics for each cluster (means):")
    for cluster_id, stats in cluster_stats.items():
        print(f"Cluster {cluster_id}: {stats}")
    print()

    pca_df = get_pca_projection(features)
    print("PCA projection results (first 5 rows):")
    print(pca_df.head())
