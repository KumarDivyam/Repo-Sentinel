import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import numpy as np

# Define a function for clustering and visualization
def cluster_and_visualize_data(data):
    # Select only the numerical columns (exclude the first two columns)
    numerical_data = data.iloc[:, 2:]

    # Fill missing values with zeros
    numerical_data.fillna(0, inplace=True)

    # Standardize the numerical data
    scaler = StandardScaler()
    numerical_data_scaled = scaler.fit_transform(numerical_data)

    # Choose the number of clusters (K) using the Silhouette Score
    scores = []
    k_values = range(2, 5)

    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(numerical_data_scaled)
        scores.append(silhouette_score(numerical_data_scaled, kmeans.labels_))

    # Find the optimal K based on the Silhouette Score
    optimal_k = k_values[scores.index(max(scores))]

    # Apply K-Means clustering with the optimal K
    kmeans = KMeans(n_clusters=optimal_k, random_state=0)
    data['cluster'] = kmeans.fit_predict(numerical_data_scaled)

    # Apply PCA for dimensionality reduction
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(numerical_data_scaled)
    data['PCA1'] = pca_result[:, 0]
    data['PCA2'] = pca_result[:, 1]

    # Find the centroids of each cluster
    centroids = kmeans.cluster_centers_

    # Calculate the Euclidean distance from each point to its cluster's centroid
    distances = np.linalg.norm(numerical_data_scaled - centroids[data['cluster']], axis=1)

    # Define a threshold for identifying outliers (e.g., points with distances above a certain percentile)
    outlier_threshold = np.percentile(distances, 90)

    # Mark outliers and label them with their names
    outliers = data[distances > outlier_threshold]
    outlier_names = outliers['Contributor']

    # Visualize the clusters in PCA space
    fig, ax = plt.subplots(figsize=(10, 6))
    for cluster_id in range(optimal_k):
        cluster_points = pca_result[data['cluster'] == cluster_id]
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1], label=f'Cluster {cluster_id}')

    # Add annotations for cluster numbers
    for cluster_id in range(optimal_k):
        cluster_center = np.mean(pca_result[data['cluster'] == cluster_id], axis=0)

    # Plot outliers
    ax.scatter(outliers['PCA1'], outliers['PCA2'], c='red', marker='x', s=100, label='Outliers')
    for name, x, y in zip(outlier_names, outliers['PCA1'], outliers['PCA2']):
        ax.annotate(name, (x, y), fontsize=8, color='red')

    ax.set_xlabel('PCA1')
    ax.set_ylabel('PCA2')
    ax.set_title(f'Clustering (K={optimal_k}) in PCA Space with Outliers')
    ax.legend()

    st.pyplot(fig)

# Create a Streamlit app
st.title("User Clustering")

st.sidebar.title("Upload Data")

uploaded_file = st.sidebar.file_uploader("Upload a data file (Excel format)", type=["xlsx"])

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    # Check if the uploaded file is valid
    if data is not None:
        st.sidebar.write("Data file loaded successfully.")
    else:
        st.sidebar.write("Please upload a valid Excel file.")

# Display the data table in the main page
if 'data' in locals():
    st.write("Data Table")
    st.dataframe(data.head())
    
    # Add a button to perform clustering and visualization in the main page
    if st.button("Cluster and Visualize"):
        cluster_and_visualize_data(data)
