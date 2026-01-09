#!/usr/bin/env python3
"""
Research Landscape Analyzer
Provides meaningful analysis of academic paper collections:
- Theme detection with descriptive labels
- Influential paper identification
- Research gap analysis
- Temporal trends
- Keyword extraction
"""

import argparse
import json
import numpy as np
from collections import defaultdict, Counter
from qdrant_client import QdrantClient
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
import os


class ResearchAnalyzer:
    """Analyzes research paper collections for meaningful insights."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "academic_papers_full_specter2",
        metadata_file: str = "pdf_metadata.json"
    ):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.metadata = self._load_metadata(metadata_file)
        
    def _load_metadata(self, metadata_file):
        """Load paper metadata."""
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def fetch_papers(self, limit=None, focus_keywords=None):
        """Fetch all papers with embeddings and metadata."""
        print(f"Fetching papers from '{self.collection_name}'...")
        if focus_keywords:
            print(f"Filtering for keywords: {', '.join(focus_keywords)}")
        
        doc_vectors = defaultdict(list)
        doc_texts = defaultdict(list)
        
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
                
                # Filter by keywords if provided
                if focus_keywords:
                    chunk_text = point.payload.get('chunk_text', '') or ''
                    title = self.metadata.get(filename, {}).get('title') or ''
                    abstract = self.metadata.get(filename, {}).get('abstract') or ''
                    combined_text = f"{title} {abstract} {chunk_text}".lower()
                    
                    # Check if any keyword matches
                    if not any(kw.lower() in combined_text for kw in focus_keywords):
                        continue
                
                doc_vectors[filename].append(point.vector)
                chunk_text = point.payload.get('chunk_text', '')
                doc_texts[filename].append(chunk_text)
                fetched += 1
            
            if offset is None:
                break
            
            if limit and len(doc_vectors) >= limit:
                break
        
        # Average embeddings per document
        papers = {}
        for filename in doc_vectors:
            meta = self.metadata.get(filename, {})
            papers[filename] = {
                'embedding': np.mean(doc_vectors[filename], axis=0),
                'title': meta.get('title', filename.replace('.pdf', '')),
                'authors': meta.get('authors', 'Unknown'),
                'year': meta.get('year', 'Unknown'),
                'abstract': meta.get('abstract', ''),
                'text': ' '.join(doc_texts[filename][:3]),  # First 3 chunks
                'num_chunks': len(doc_vectors[filename])
            }
        
        print(f"Loaded {len(papers)} papers")
        return papers
    
    def detect_themes(self, papers, num_themes=5):
        """
        Detect research themes using clustering and keyword extraction.
        
        Returns themes with:
        - Descriptive label (auto-generated from keywords)
        - Key papers in each theme
        - Theme size and characteristics
        """
        print(f"Detecting {num_themes} research themes...")
        
        # Get embeddings matrix
        filenames = list(papers.keys())
        embeddings = np.array([papers[f]['embedding'] for f in filenames])
        
        # Cluster papers
        kmeans = KMeans(n_clusters=num_themes, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(embeddings)
        
        # Extract keywords for each cluster using TF-IDF
        cluster_texts = defaultdict(list)
        cluster_papers = defaultdict(list)
        
        for i, filename in enumerate(filenames):
            cluster_id = clusters[i]
            cluster_texts[cluster_id].append(papers[filename]['title'] + ' ' + papers[filename].get('abstract', ''))
            cluster_papers[cluster_id].append({
                'filename': filename,
                'title': papers[filename]['title'],
                'year': papers[filename]['year'],
                'authors': papers[filename]['authors']
            })
        
        # Generate theme labels using TF-IDF
        themes = {}
        for cluster_id in range(num_themes):
            texts = cluster_texts[cluster_id]
            if not texts:
                continue
            
            # TF-IDF on cluster texts
            try:
                vectorizer = TfidfVectorizer(
                    max_features=20,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                tfidf = vectorizer.fit_transform(texts)
                
                # Get top keywords
                feature_names = vectorizer.get_feature_names_out()
                scores = np.array(tfidf.sum(axis=0)).flatten()
                top_indices = scores.argsort()[-5:][::-1]
                keywords = [feature_names[i] for i in top_indices]
                
                # Generate descriptive label
                label = self._generate_theme_label(keywords)
            except:
                keywords = ['research', 'papers']
                label = f"Theme {cluster_id + 1}"
            
            themes[cluster_id] = {
                'label': label,
                'keywords': keywords,
                'papers': cluster_papers[cluster_id],
                'size': len(cluster_papers[cluster_id]),
                'percentage': len(cluster_papers[cluster_id]) / len(filenames) * 100
            }
        
        # Assign cluster to each paper
        for i, filename in enumerate(filenames):
            papers[filename]['theme_id'] = clusters[i]
            papers[filename]['theme_label'] = themes[clusters[i]]['label']
        
        return themes, papers
    
    def _generate_theme_label(self, keywords):
        """Generate a human-readable theme label from keywords."""
        # Common academic terms to filter
        stopwords = {'based', 'using', 'novel', 'approach', 'method', 'analysis', 
                    'system', 'data', 'model', 'new', 'proposed', 'study'}
        
        # Filter and clean keywords
        clean_keywords = []
        for kw in keywords[:3]:
            words = kw.split()
            clean = [w for w in words if w.lower() not in stopwords and len(w) > 2]
            if clean:
                clean_keywords.append(' '.join(clean).title())
        
        if clean_keywords:
            return ' & '.join(clean_keywords[:2])
        return keywords[0].title() if keywords else "Research Theme"
    
    def identify_influential_papers(self, papers, themes, top_n=10):
        """
        Identify most influential papers based on:
        - Centrality in embedding space (representative of cluster)
        - Number of chunks (indicates paper length/depth)
        """
        print("Identifying influential papers...")
        
        influential = []
        
        # Get embeddings and cluster centers
        filenames = list(papers.keys())
        embeddings = np.array([papers[f]['embedding'] for f in filenames])
        
        # Calculate distance to cluster center for each paper
        for i, filename in enumerate(filenames):
            theme_id = papers[filename]['theme_id']
            
            # Get papers in same cluster
            cluster_embeddings = [papers[f]['embedding'] for f in filenames 
                                 if papers[f]['theme_id'] == theme_id]
            cluster_center = np.mean(cluster_embeddings, axis=0)
            
            # Distance to center (lower = more representative)
            dist_to_center = np.linalg.norm(papers[filename]['embedding'] - cluster_center)
            
            influential.append({
                'filename': filename,
                'title': papers[filename]['title'],
                'authors': papers[filename]['authors'],
                'year': papers[filename]['year'],
                'theme': papers[filename]['theme_label'],
                'representativeness': 1 / (1 + dist_to_center),  # Higher = more representative
                'depth': papers[filename]['num_chunks']
            })
        
        # Sort by representativeness
        influential.sort(key=lambda x: x['representativeness'], reverse=True)
        
        return influential[:top_n]
    
    def analyze_temporal_trends(self, papers, themes):
        """Analyze how research themes evolved over time."""
        print("Analyzing temporal trends...")
        
        # Group papers by year and theme
        year_theme_counts = defaultdict(lambda: defaultdict(int))
        
        for filename, paper in papers.items():
            year = paper['year']
            if year and year != 'Unknown':
                try:
                    year = int(str(year)[:4])  # Extract year
                    theme_label = paper['theme_label']
                    year_theme_counts[year][theme_label] += 1
                except:
                    pass
        
        # Create trend data
        trends = {
            'years': sorted(year_theme_counts.keys()),
            'themes': {}
        }
        
        all_themes = set()
        for year_data in year_theme_counts.values():
            all_themes.update(year_data.keys())
        
        for theme in all_themes:
            trends['themes'][theme] = [
                year_theme_counts[year].get(theme, 0) 
                for year in trends['years']
            ]
        
        return trends
    
    def find_research_gaps(self, papers, themes):
        """
        Identify potential research gaps:
        - Themes with declining publication counts
        - Under-explored intersections between themes
        - Topics mentioned but with few dedicated papers
        """
        print("Identifying research gaps...")
        
        gaps = []
        
        # Find smallest themes (potentially under-explored)
        sorted_themes = sorted(themes.items(), key=lambda x: x[1]['size'])
        for theme_id, theme_data in sorted_themes[:3]:
            if theme_data['size'] < len(papers) * 0.1:  # Less than 10% of papers
                gaps.append({
                    'type': 'Under-explored Area',
                    'description': f"'{theme_data['label']}' has only {theme_data['size']} papers ({theme_data['percentage']:.1f}%)",
                    'keywords': theme_data['keywords'],
                    'suggestion': f"Consider exploring {', '.join(theme_data['keywords'][:3])}"
                })
        
        # Find themes with older papers (potentially stagnant)
        for theme_id, theme_data in themes.items():
            years = []
            for paper in theme_data['papers']:
                try:
                    year = int(str(paper['year'])[:4])
                    years.append(year)
                except:
                    pass
            
            if years:
                avg_year = np.mean(years)
                if avg_year < 2020:  # Older research area
                    gaps.append({
                        'type': 'Potentially Stagnant Area',
                        'description': f"'{theme_data['label']}' has average publication year of {avg_year:.0f}",
                        'keywords': theme_data['keywords'],
                        'suggestion': "This area may benefit from fresh perspectives"
                    })
        
        return gaps
    
    def create_landscape_visualization(self, papers, themes, output_file="research_landscape.html"):
        """Create interactive 3D network visualization with connections between similar papers."""
        print("Creating 3D network visualization with connections...")
        
        filenames = list(papers.keys())
        embeddings = np.array([papers[f]['embedding'] for f in filenames])
        n_papers = len(filenames)
        
        # Reduce to 3D using PCA
        print(f"Reducing {n_papers} papers to 3D...")
        pca = PCA(n_components=3)
        coords = pca.fit_transform(embeddings)
        
        x = coords[:, 0]
        y = coords[:, 1]
        z = coords[:, 2]
        
        # Compute similarity matrix for connections (sample if too many papers)
        print("Computing paper similarities for connections...")
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Sample papers if too many for performance
        max_papers_for_edges = 500
        if n_papers > max_papers_for_edges:
            sample_indices = np.random.choice(n_papers, max_papers_for_edges, replace=False)
        else:
            sample_indices = np.arange(n_papers)
        
        sample_embeddings = embeddings[sample_indices]
        similarity_matrix = cosine_similarity(sample_embeddings)
        
        # Build edges for highly similar papers (threshold 0.7)
        edge_x, edge_y, edge_z = [], [], []
        threshold = 0.7
        
        for i in range(len(sample_indices)):
            for j in range(i + 1, len(sample_indices)):
                if similarity_matrix[i, j] > threshold:
                    idx_i = sample_indices[i]
                    idx_j = sample_indices[j]
                    # Add line from paper i to paper j
                    edge_x.extend([x[idx_i], x[idx_j], None])
                    edge_y.extend([y[idx_i], y[idx_j], None])
                    edge_z.extend([z[idx_i], z[idx_j], None])
        
        print(f"Created {len(edge_x) // 3} connections between similar papers")
        
        # Prepare node data
        titles = [papers[f]['title'][:60] + '...' if len(papers[f]['title']) > 60 
                 else papers[f]['title'] for f in filenames]
        theme_labels = [papers[f]['theme_label'] for f in filenames]
        theme_ids = [papers[f]['theme_id'] for f in filenames]
        years = [papers[f]['year'] for f in filenames]
        authors = [papers[f]['authors'][:40] + '...' if len(str(papers[f]['authors'])) > 40 
                  else papers[f]['authors'] for f in filenames]
        
        # Color mapping for themes
        unique_themes = sorted(set(theme_ids))
        color_map = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
        theme_colors = {tid: color_map[i % len(color_map)] for i, tid in enumerate(unique_themes)}
        node_colors = [theme_colors[tid] for tid in theme_ids]
        
        # Create 3D figure
        fig = go.Figure()
        
        # Add edges (connections between similar papers)
        fig.add_trace(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='rgba(150,150,150,0.3)', width=1),
            hoverinfo='none',
            name='Similarity Connections'
        ))
        
        # Add nodes (papers) grouped by theme
        for theme_id in unique_themes:
            mask = [tid == theme_id for tid in theme_ids]
            theme_label = themes[theme_id]['label']
            
            hover_texts = [
                f"<b>{titles[i]}</b><br>" +
                f"Authors: {authors[i]}<br>" +
                f"Year: {years[i]}<br>" +
                f"Theme: {theme_labels[i]}"
                for i in range(n_papers) if mask[i]
            ]
            
            fig.add_trace(go.Scatter3d(
                x=[x[i] for i in range(n_papers) if mask[i]],
                y=[y[i] for i in range(n_papers) if mask[i]],
                z=[z[i] for i in range(n_papers) if mask[i]],
                mode='markers',
                name=theme_label,
                text=hover_texts,
                hoverinfo='text',
                marker=dict(
                    size=6,
                    color=theme_colors[theme_id],
                    opacity=0.8,
                    line=dict(width=0.5, color='white')
                )
            ))
        
        # Update layout for 3D
        fig.update_layout(
            title=dict(
                text="🔬 3D Research Network - Papers Connected by Similarity",
                font=dict(size=20)
            ),
            scene=dict(
                xaxis_title='Dimension 1',
                yaxis_title='Dimension 2',
                zaxis_title='Dimension 3',
                bgcolor='rgba(240,240,240,0.9)'
            ),
            showlegend=True,
            legend=dict(
                title="Research Themes",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=800,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        fig.write_html(output_file)
        print(f"Saved 3D visualization to {output_file}")
        
        return fig
    
    def create_trends_visualization(self, trends, output_file="research_trends.html"):
        """Create temporal trends visualization."""
        print("Creating trends visualization...")
        
        fig = go.Figure()
        
        for theme, counts in trends['themes'].items():
            fig.add_trace(go.Scatter(
                x=trends['years'],
                y=counts,
                mode='lines+markers',
                name=theme,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="📈 Research Theme Trends Over Time",
            xaxis_title="Year",
            yaxis_title="Number of Papers",
            template="plotly_white",
            height=500,
            hovermode='x unified'
        )
        
        fig.write_html(output_file)
        print(f"Saved trends to {output_file}")
        
        return fig
    
    def generate_insights_report(self, papers, themes, influential, gaps, trends):
        """Generate a text report of insights."""
        report = []
        report.append("=" * 60)
        report.append("RESEARCH LANDSCAPE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Papers Analyzed: {len(papers)}")
        report.append(f"Number of Research Themes: {len(themes)}")
        
        report.append("\n" + "-" * 40)
        report.append("RESEARCH THEMES")
        report.append("-" * 40)
        
        for theme_id in sorted(themes.keys()):
            theme = themes[theme_id]
            report.append(f"\n🔹 {theme['label']}")
            report.append(f"   Papers: {theme['size']} ({theme['percentage']:.1f}%)")
            report.append(f"   Keywords: {', '.join(theme['keywords'][:5])}")
        
        report.append("\n" + "-" * 40)
        report.append("TOP INFLUENTIAL PAPERS")
        report.append("-" * 40)
        
        for i, paper in enumerate(influential[:5], 1):
            report.append(f"\n{i}. {paper['title'][:60]}...")
            report.append(f"   Authors: {paper['authors'][:50]}")
            report.append(f"   Theme: {paper['theme']}")
        
        report.append("\n" + "-" * 40)
        report.append("RESEARCH GAPS & OPPORTUNITIES")
        report.append("-" * 40)
        
        for gap in gaps:
            report.append(f"\n⚠️ {gap['type']}")
            report.append(f"   {gap['description']}")
            report.append(f"   💡 {gap['suggestion']}")
        
        return "\n".join(report)
    
    def run_full_analysis(self, num_themes=5, output_prefix="analysis", max_papers=None, focus_keywords=None):
        """Run complete analysis pipeline."""
        print("\n🔬 Starting Research Landscape Analysis...\n")
        
        # Fetch papers
        papers = self.fetch_papers(limit=max_papers, focus_keywords=focus_keywords)
        
        print(f"Fetched {len(papers)} papers for analysis")
        
        if len(papers) < 3:
            print(f"Not enough papers for meaningful analysis (need at least 3, got {len(papers)})")
            return None
        
        # Detect themes
        num_themes = min(num_themes, len(papers) // 2)  # Don't have more themes than papers/2
        themes, papers = self.detect_themes(papers, num_themes)
        
        # Find influential papers
        influential = self.identify_influential_papers(papers, themes)
        
        # Analyze trends
        trends = self.analyze_temporal_trends(papers, themes)
        
        # Find research gaps
        gaps = self.find_research_gaps(papers, themes)
        
        # Create visualizations
        self.create_landscape_visualization(papers, themes, f"{output_prefix}_landscape.html")
        
        if len(trends['years']) > 1:
            self.create_trends_visualization(trends, f"{output_prefix}_trends.html")
        
        # Generate report
        report = self.generate_insights_report(papers, themes, influential, gaps, trends)
        
        # Save report
        with open(f"{output_prefix}_report.txt", 'w') as f:
            f.write(report)
        
        print(report)
        
        return {
            'papers': papers,
            'themes': themes,
            'influential': influential,
            'trends': trends,
            'gaps': gaps,
            'report': report
        }


def main():
    parser = argparse.ArgumentParser(description="Analyze research paper collection")
    parser.add_argument("--collection", default="academic_papers_full_specter2",
                       help="Qdrant collection name")
    parser.add_argument("--themes", type=int, default=5,
                       help="Number of themes to detect")
    parser.add_argument("--output", default="analysis",
                       help="Output file prefix")
    parser.add_argument("--host", default="localhost",
                       help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333,
                       help="Qdrant port")
    
    args = parser.parse_args()
    
    analyzer = ResearchAnalyzer(
        qdrant_host=args.host,
        qdrant_port=args.port,
        collection_name=args.collection
    )
    
    results = analyzer.run_full_analysis(
        num_themes=args.themes,
        output_prefix=args.output
    )
    
    if results:
        print(f"\n✅ Analysis complete!")
        print(f"   - Landscape: {args.output}_landscape.html")
        print(f"   - Trends: {args.output}_trends.html")
        print(f"   - Report: {args.output}_report.txt")


if __name__ == "__main__":
    main()
