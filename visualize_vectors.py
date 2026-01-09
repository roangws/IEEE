#!/usr/bin/env python3
"""
Vector Database Visualization Tool
Visualizes the embedding space using dimensionality reduction techniques.
"""

import argparse
import numpy as np
from qdrant_client import QdrantClient
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import pandas as pd


class VectorVisualizer:
    """Visualizes vectors from Qdrant collection."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "academic_papers_test"
    ):
        """
        Initialize the visualizer.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
    def fetch_vectors(self, limit: int = None):
        """
        Fetch vectors and metadata from Qdrant.
        
        Args:
            limit: Maximum number of vectors to fetch (None for all)
            
        Returns:
            Tuple of (vectors, filenames, chunk_ids)
        """
        print(f"Fetching vectors from collection '{self.collection_name}'...")
        
        # Get collection info
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        total_points = collection_info.points_count
        
        if limit is None:
            limit = total_points
        
        print(f"Total vectors in collection: {total_points}")
        print(f"Fetching {min(limit, total_points)} vectors...")
        
        # Scroll through all points
        vectors = []
        filenames = []
        chunk_ids = []
        chunk_texts = []
        
        offset = None
        fetched = 0
        
        while fetched < limit:
            batch_size = min(100, limit - fetched)
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                offset=offset,
                with_vectors=True,
                with_payload=True
            )
            
            points, offset = result
            
            if not points:
                break
            
            for point in points:
                vectors.append(point.vector)
                filenames.append(point.payload.get('filename', 'unknown'))
                chunk_ids.append(point.payload.get('chunk_id', 0))
                chunk_text = point.payload.get('chunk_text', '')
                chunk_texts.append(chunk_text[:100] + '...' if len(chunk_text) > 100 else chunk_text)
                fetched += 1
                
                if fetched >= limit:
                    break
            
            if offset is None:
                break
        
        print(f"Fetched {len(vectors)} vectors")
        
        return np.array(vectors), filenames, chunk_ids, chunk_texts
    
    def reduce_dimensions(self, vectors, method='tsne', n_components=2):
        """
        Reduce vector dimensions for visualization.
        
        Args:
            vectors: High-dimensional vectors
            method: Reduction method ('tsne' or 'pca')
            n_components: Number of dimensions to reduce to (2 or 3)
            
        Returns:
            Reduced vectors
        """
        print(f"Reducing dimensions using {method.upper()}...")
        
        if method == 'tsne':
            reducer = TSNE(
                n_components=n_components,
                random_state=42,
                perplexity=min(30, len(vectors) - 1),
                max_iter=1000
            )
        else:  # pca
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=n_components, random_state=42)
        
        reduced = reducer.fit_transform(vectors)
        print(f"Reduced to {n_components}D")
        
        return reduced
    
    def create_2d_plot(self, reduced_vectors, filenames, chunk_ids, chunk_texts):
        """
        Create interactive 2D scatter plot.
        
        Args:
            reduced_vectors: 2D reduced vectors
            filenames: List of filenames
            chunk_ids: List of chunk IDs
            chunk_texts: List of chunk text previews
            
        Returns:
            Plotly figure
        """
        # Create DataFrame
        df = pd.DataFrame({
            'x': reduced_vectors[:, 0],
            'y': reduced_vectors[:, 1],
            'filename': filenames,
            'chunk_id': chunk_ids,
            'text_preview': chunk_texts
        })
        
        # Count documents
        doc_counts = Counter(filenames)
        
        # Create color map for top documents
        top_docs = [doc for doc, _ in doc_counts.most_common(10)]
        color_map = {doc: i for i, doc in enumerate(top_docs)}
        df['color'] = df['filename'].apply(
            lambda x: color_map.get(x, len(color_map))
        )
        df['doc_label'] = df['filename'].apply(
            lambda x: x if x in top_docs else 'Other'
        )
        
        # Create plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='doc_label',
            hover_data={
                'filename': True,
                'chunk_id': True,
                'text_preview': True,
                'x': False,
                'y': False,
                'color': False,
                'doc_label': False
            },
            title=f'Vector Embedding Space Visualization ({len(df)} chunks from {len(doc_counts)} documents)',
            labels={'doc_label': 'Document'},
            width=1200,
            height=800
        )
        
        fig.update_traces(marker=dict(size=8, opacity=0.7))
        fig.update_layout(
            hovermode='closest',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def create_3d_plot(self, reduced_vectors, filenames, chunk_ids, chunk_texts):
        """
        Create interactive 3D scatter plot.
        
        Args:
            reduced_vectors: 3D reduced vectors
            filenames: List of filenames
            chunk_ids: List of chunk IDs
            chunk_texts: List of chunk text previews
            
        Returns:
            Plotly figure
        """
        # Create DataFrame
        df = pd.DataFrame({
            'x': reduced_vectors[:, 0],
            'y': reduced_vectors[:, 1],
            'z': reduced_vectors[:, 2],
            'filename': filenames,
            'chunk_id': chunk_ids,
            'text_preview': chunk_texts
        })
        
        # Count documents
        doc_counts = Counter(filenames)
        
        # Create color map for top documents
        top_docs = [doc for doc, _ in doc_counts.most_common(10)]
        color_map = {doc: i for i, doc in enumerate(top_docs)}
        df['color'] = df['filename'].apply(
            lambda x: color_map.get(x, len(color_map))
        )
        df['doc_label'] = df['filename'].apply(
            lambda x: x if x in top_docs else 'Other'
        )
        
        # Create plot
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color='doc_label',
            hover_data={
                'filename': True,
                'chunk_id': True,
                'text_preview': True,
                'x': False,
                'y': False,
                'z': False,
                'color': False,
                'doc_label': False
            },
            title=f'3D Vector Embedding Space ({len(df)} chunks from {len(doc_counts)} documents)',
            labels={'doc_label': 'Document'},
            width=1200,
            height=800
        )
        
        fig.update_traces(marker=dict(size=5, opacity=0.7))
        
        return fig
    
    def create_document_clusters(self, reduced_vectors, filenames):
        """
        Create visualization showing document clusters.
        
        Args:
            reduced_vectors: 2D reduced vectors
            filenames: List of filenames
            
        Returns:
            Plotly figure
        """
        df = pd.DataFrame({
            'x': reduced_vectors[:, 0],
            'y': reduced_vectors[:, 1],
            'filename': filenames
        })
        
        # Calculate centroids for each document
        centroids = df.groupby('filename')[['x', 'y']].mean().reset_index()
        centroids.columns = ['filename', 'centroid_x', 'centroid_y']
        
        # Create plot
        fig = go.Figure()
        
        # Add scatter points
        for filename in df['filename'].unique():
            doc_df = df[df['filename'] == filename]
            fig.add_trace(go.Scatter(
                x=doc_df['x'],
                y=doc_df['y'],
                mode='markers',
                name=filename,
                marker=dict(size=6, opacity=0.6),
                hovertemplate=f'<b>{filename}</b><br>x: %{{x}}<br>y: %{{y}}<extra></extra>'
            ))
        
        # Add centroids
        fig.add_trace(go.Scatter(
            x=centroids['centroid_x'],
            y=centroids['centroid_y'],
            mode='markers+text',
            name='Centroids',
            marker=dict(size=15, symbol='star', color='red'),
            text=centroids['filename'],
            textposition='top center',
            hovertemplate='<b>Centroid</b><br>%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Document Clusters with Centroids',
            width=1200,
            height=800,
            hovermode='closest'
        )
        
        return fig
    
    def generate_statistics(self, filenames):
        """
        Generate statistics about the collection.
        
        Args:
            filenames: List of filenames
            
        Returns:
            Dictionary of statistics
        """
        doc_counts = Counter(filenames)
        
        stats = {
            'total_chunks': len(filenames),
            'total_documents': len(doc_counts),
            'avg_chunks_per_doc': len(filenames) / len(doc_counts),
            'max_chunks': max(doc_counts.values()),
            'min_chunks': min(doc_counts.values()),
            'top_documents': doc_counts.most_common(5)
        }
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize vector embeddings from Qdrant"
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='academic_papers_test',
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of vectors to visualize (default: all)'
    )
    parser.add_argument(
        '--dimensions',
        type=int,
        choices=[2, 3],
        default=2,
        help='Number of dimensions for visualization (2 or 3)'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['tsne', 'pca'],
        default='tsne',
        help='Dimensionality reduction method'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='vector_visualization.html',
        help='Output HTML file path'
    )
    
    args = parser.parse_args()
    
    # Initialize visualizer
    visualizer = VectorVisualizer(collection_name=args.collection)
    
    # Fetch vectors
    vectors, filenames, chunk_ids, chunk_texts = visualizer.fetch_vectors(limit=args.limit)
    
    # Generate statistics
    stats = visualizer.generate_statistics(filenames)
    print("\n" + "="*70)
    print("COLLECTION STATISTICS")
    print("="*70)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Average chunks per document: {stats['avg_chunks_per_doc']:.1f}")
    print(f"Max chunks in a document: {stats['max_chunks']}")
    print(f"Min chunks in a document: {stats['min_chunks']}")
    print("\nTop 5 documents by chunk count:")
    for doc, count in stats['top_documents']:
        print(f"  {doc}: {count} chunks")
    print("="*70 + "\n")
    
    # Reduce dimensions
    reduced = visualizer.reduce_dimensions(
        vectors,
        method=args.method,
        n_components=args.dimensions
    )
    
    # Create visualization
    if args.dimensions == 2:
        fig = visualizer.create_2d_plot(reduced, filenames, chunk_ids, chunk_texts)
    else:
        fig = visualizer.create_3d_plot(reduced, filenames, chunk_ids, chunk_texts)
    
    # Save to file
    print(f"\nSaving visualization to {args.output}...")
    fig.write_html(args.output)
    print(f"✓ Visualization saved!")
    print(f"\nOpen {args.output} in your browser to view the interactive plot.")
    
    # Also create document clusters if 2D
    if args.dimensions == 2:
        cluster_output = args.output.replace('.html', '_clusters.html')
        cluster_fig = visualizer.create_document_clusters(reduced, filenames)
        cluster_fig.write_html(cluster_output)
        print(f"✓ Document clusters saved to {cluster_output}")


if __name__ == '__main__':
    main()
