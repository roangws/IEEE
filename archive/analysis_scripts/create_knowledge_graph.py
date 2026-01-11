#!/usr/bin/env python3
"""
Knowledge Graph Creator for Vector Database
Creates interactive network graphs showing relationships between documents.
"""

import argparse
import numpy as np
from qdrant_client import QdrantClient
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import plotly.graph_objects as go
from collections import defaultdict
import pandas as pd


class KnowledgeGraphBuilder:
    """Builds knowledge graphs from vector embeddings."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "academic_papers_test"
    ):
        """
        Initialize the graph builder.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
    def fetch_document_embeddings(self):
        """
        Fetch all vectors and aggregate by document.
        
        Returns:
            Dictionary mapping filenames to their averaged embeddings
        """
        print(f"Fetching vectors from collection '{self.collection_name}'...")
        
        # Get collection info
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        total_points = collection_info.points_count
        
        print(f"Total vectors in collection: {total_points}")
        
        # Fetch all vectors
        doc_vectors = defaultdict(list)
        doc_chunks = defaultdict(int)
        
        offset = None
        fetched = 0
        
        while True:
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_vectors=True,
                with_payload=True
            )
            
            points, offset = result
            
            if not points:
                break
            
            for point in points:
                filename = point.payload.get('filename', 'unknown')
                doc_vectors[filename].append(point.vector)
                doc_chunks[filename] += 1
                fetched += 1
            
            if offset is None:
                break
        
        print(f"Fetched {fetched} vectors from {len(doc_vectors)} documents")
        
        # Average vectors for each document
        doc_embeddings = {}
        for filename, vectors in doc_vectors.items():
            doc_embeddings[filename] = np.mean(vectors, axis=0)
        
        return doc_embeddings, doc_chunks
    
    def compute_similarity_matrix(self, doc_embeddings):
        """
        Compute pairwise cosine similarity between documents.
        
        Args:
            doc_embeddings: Dictionary of document embeddings
            
        Returns:
            Similarity matrix and list of document names
        """
        print("Computing similarity matrix...")
        
        doc_names = list(doc_embeddings.keys())
        embeddings_matrix = np.array([doc_embeddings[name] for name in doc_names])
        
        similarity_matrix = cosine_similarity(embeddings_matrix)
        
        print(f"Computed similarities for {len(doc_names)} documents")
        
        return similarity_matrix, doc_names
    
    def build_graph(self, similarity_matrix, doc_names, threshold=0.5, top_k=3):
        """
        Build a NetworkX graph from similarity matrix.
        
        Args:
            similarity_matrix: Pairwise similarity matrix
            doc_names: List of document names
            threshold: Minimum similarity to create an edge
            top_k: Connect each node to its top-k most similar nodes
            
        Returns:
            NetworkX graph
        """
        print(f"Building graph (threshold={threshold}, top_k={top_k})...")
        
        G = nx.Graph()
        
        # Add nodes
        for doc_name in doc_names:
            G.add_node(doc_name)
        
        # Add edges based on similarity
        n = len(doc_names)
        edges_added = 0
        
        for i in range(n):
            # Get top-k most similar documents (excluding self)
            similarities = similarity_matrix[i].copy()
            similarities[i] = -1  # Exclude self
            
            # Get indices of top-k similar documents
            top_indices = np.argsort(similarities)[-top_k:]
            
            for j in top_indices:
                sim = similarity_matrix[i, j]
                if sim >= threshold and i < j:  # Avoid duplicate edges
                    G.add_edge(
                        doc_names[i],
                        doc_names[j],
                        weight=float(sim),
                        similarity=float(sim)
                    )
                    edges_added += 1
        
        print(f"Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        return G
    
    def detect_communities(self, G):
        """
        Detect communities in the graph.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary mapping nodes to community IDs
        """
        print("Detecting communities...")
        
        if G.number_of_edges() == 0:
            # No edges, each node is its own community
            return {node: i for i, node in enumerate(G.nodes())}
        
        # Use Louvain community detection
        communities = nx.community.louvain_communities(G, seed=42)
        
        # Create node to community mapping
        node_to_community = {}
        for comm_id, community in enumerate(communities):
            for node in community:
                node_to_community[node] = comm_id
        
        print(f"Found {len(communities)} communities")
        
        return node_to_community
    
    def calculate_graph_metrics(self, G):
        """
        Calculate graph metrics for each node.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of metrics
        """
        print("Calculating graph metrics...")
        
        metrics = {
            'degree_centrality': nx.degree_centrality(G),
            'betweenness_centrality': nx.betweenness_centrality(G) if G.number_of_edges() > 0 else {},
            'closeness_centrality': nx.closeness_centrality(G) if nx.is_connected(G) else {},
            'clustering_coefficient': nx.clustering(G)
        }
        
        return metrics
    
    def create_interactive_graph(
        self,
        G,
        doc_chunks,
        node_to_community,
        metrics,
        layout='spring'
    ):
        """
        Create interactive Plotly visualization of the graph.
        
        Args:
            G: NetworkX graph
            doc_chunks: Dictionary of chunk counts per document
            node_to_community: Community assignments
            metrics: Graph metrics
            layout: Layout algorithm ('spring', 'circular', 'kamada_kawai')
            
        Returns:
            Plotly figure
        """
        print(f"Creating interactive visualization with {layout} layout...")
        
        # Compute layout
        if layout == 'spring':
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            similarity = edge[2].get('similarity', 0)
            
            # Color and width based on similarity
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(
                    width=similarity * 3,
                    color=f'rgba(150, 150, 150, {similarity * 0.8})'
                ),
                hoverinfo='text',
                text=f"Similarity: {similarity:.3f}",
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Get metrics
            degree = metrics['degree_centrality'].get(node, 0)
            betweenness = metrics['betweenness_centrality'].get(node, 0)
            clustering = metrics['clustering_coefficient'].get(node, 0)
            chunks = doc_chunks.get(node, 0)
            community = node_to_community.get(node, 0)
            
            # Node info
            node_text.append(
                f"<b>{node}</b><br>"
                f"Community: {community}<br>"
                f"Chunks: {chunks}<br>"
                f"Connections: {G.degree(node)}<br>"
                f"Degree Centrality: {degree:.3f}<br>"
                f"Betweenness: {betweenness:.3f}<br>"
                f"Clustering: {clustering:.3f}"
            )
            
            node_color.append(community)
            node_size.append(20 + degree * 30)  # Size based on centrality
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=[node.replace('.pdf', '') for node in G.nodes()],
            textposition='top center',
            textfont=dict(size=10),
            hovertext=node_text,
            hoverinfo='text',
            marker=dict(
                size=node_size,
                color=node_color,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Community",
                    thickness=15,
                    len=0.7
                ),
                line=dict(width=2, color='white')
            )
        )
        
        # Create figure
        fig = go.Figure(
            data=edge_traces + [node_trace],
            layout=go.Layout(
                title=dict(
                    text=f"Document Knowledge Graph<br>"
                         f"<sub>{G.number_of_nodes()} documents, "
                         f"{G.number_of_edges()} relationships, "
                         f"{len(set(node_to_community.values()))} communities</sub>",
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=80),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                width=1400,
                height=900,
                plot_bgcolor='rgba(240, 240, 240, 0.9)'
            )
        )
        
        return fig
    
    def generate_graph_report(self, G, node_to_community, metrics):
        """
        Generate a text report about the graph.
        
        Args:
            G: NetworkX graph
            node_to_community: Community assignments
            metrics: Graph metrics
            
        Returns:
            Report string
        """
        report = []
        report.append("=" * 70)
        report.append("KNOWLEDGE GRAPH ANALYSIS")
        report.append("=" * 70)
        
        # Basic stats
        report.append(f"\n📊 Graph Statistics:")
        report.append(f"  Nodes (documents): {G.number_of_nodes()}")
        report.append(f"  Edges (relationships): {G.number_of_edges()}")
        report.append(f"  Communities detected: {len(set(node_to_community.values()))}")
        report.append(f"  Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
        report.append(f"  Graph density: {nx.density(G):.3f}")
        
        # Most central documents
        report.append(f"\n🌟 Most Central Documents (by degree centrality):")
        degree_cent = metrics['degree_centrality']
        top_central = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (doc, score) in enumerate(top_central, 1):
            report.append(f"  {i}. {doc}: {score:.3f}")
        
        # Most connected documents
        report.append(f"\n🔗 Most Connected Documents:")
        degrees = dict(G.degree())
        top_connected = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (doc, connections) in enumerate(top_connected, 1):
            report.append(f"  {i}. {doc}: {connections} connections")
        
        # Communities
        report.append(f"\n👥 Communities:")
        communities = defaultdict(list)
        for node, comm in node_to_community.items():
            communities[comm].append(node)
        
        for comm_id, members in sorted(communities.items()):
            report.append(f"  Community {comm_id} ({len(members)} documents):")
            for member in members[:3]:  # Show first 3
                report.append(f"    - {member}")
            if len(members) > 3:
                report.append(f"    ... and {len(members) - 3} more")
        
        # Strongest relationships
        report.append(f"\n💪 Strongest Relationships:")
        edges_with_sim = [(u, v, data['similarity']) for u, v, data in G.edges(data=True)]
        top_edges = sorted(edges_with_sim, key=lambda x: x[2], reverse=True)[:5]
        for i, (u, v, sim) in enumerate(top_edges, 1):
            report.append(f"  {i}. {u} ↔ {v}: {sim:.3f}")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create knowledge graph from vector database"
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='academic_papers_test',
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum similarity threshold for edges (0-1)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='Connect each document to its top-k most similar documents'
    )
    parser.add_argument(
        '--layout',
        type=str,
        choices=['spring', 'circular', 'kamada_kawai'],
        default='spring',
        help='Graph layout algorithm'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='knowledge_graph.html',
        help='Output HTML file path'
    )
    
    args = parser.parse_args()
    
    # Initialize builder
    builder = KnowledgeGraphBuilder(collection_name=args.collection)
    
    # Fetch document embeddings
    doc_embeddings, doc_chunks = builder.fetch_document_embeddings()
    
    # Compute similarity matrix
    similarity_matrix, doc_names = builder.compute_similarity_matrix(doc_embeddings)
    
    # Build graph
    G = builder.build_graph(
        similarity_matrix,
        doc_names,
        threshold=args.threshold,
        top_k=args.top_k
    )
    
    # Detect communities
    node_to_community = builder.detect_communities(G)
    
    # Calculate metrics
    metrics = builder.calculate_graph_metrics(G)
    
    # Generate report
    report = builder.generate_graph_report(G, node_to_community, metrics)
    print("\n" + report)
    
    # Create visualization
    fig = builder.create_interactive_graph(
        G,
        doc_chunks,
        node_to_community,
        metrics,
        layout=args.layout
    )
    
    # Save to file
    print(f"\nSaving knowledge graph to {args.output}...")
    fig.write_html(args.output)
    print(f"✓ Knowledge graph saved!")
    print(f"\nOpen {args.output} in your browser to explore the interactive graph.")


if __name__ == '__main__':
    main()
