#!/usr/bin/env python3
"""
MMR (Maximal Marginal Relevance) Retrieval
Ensures diverse paper selection instead of redundant chunks from same papers.
"""

import os

# Set up cache BEFORE importing any HF libraries
HF_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".hf_cache")
os.makedirs(HF_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_CACHE_DIR, "transformers")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(HF_CACHE_DIR, "sentence_transformers")
os.environ["HF_TOKEN_PATH"] = os.path.join(HF_CACHE_DIR, "token")
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")

# NOTE: Imports are placed after cache setup to ensure HF libraries use local cache
# This is intentional and necessary to avoid permission errors with system cache
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class MMRRetriever:
    """Retrieves diverse chunks using MMR algorithm."""
    
    def __init__(self, collection_name="academic_papers_100", lambda_param=0.5):
        """
        Initialize MMR retriever.
        
        Args:
            collection_name: Qdrant collection name
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
                         0.5 = balanced, 0.7 = more relevance, 0.3 = more diversity
        """
        self.collection_name = collection_name
        self.lambda_param = lambda_param
        self.client = QdrantClient(host="localhost", port=6333)
        # Upgraded to SPECTER2 base for better academic paper understanding
        self.model = SentenceTransformer('allenai/specter2_base', cache_folder=HF_CACHE_DIR)
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def mmr_retrieval(self, query: str, top_k: int = 50, target_papers: int = None,
                     initial_candidates: int = 200):
        """
        Retrieve chunks using MMR for diversity.
        
        Args:
            query: Search query
            top_k: Number of chunks to return
            target_papers: Target number of unique papers (enforces diversity)
            initial_candidates: Number of candidates to consider
            
        Returns:
            List of diverse chunks
        """
        # Get query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Retrieve initial candidates (more than needed)
        candidates = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=initial_candidates,
            with_vectors=True
        ).points
        
        if not candidates:
            return []
        
        # Extract vectors and metadata
        candidate_data = []
        for hit in candidates:
            # Calculate score from query similarity
            score = self.cosine_similarity(
                np.array(query_embedding),
                np.array(hit.vector)
            )
            candidate_data.append({
                'vector': hit.vector,
                'payload': hit.payload,
                'score': score,
                'filename': hit.payload['filename']
            })
        
        # MMR selection
        selected = []
        selected_filenames = set()
        candidate_indices = list(range(len(candidate_data)))
        
        # Select first item (most relevant)
        first_idx = 0
        selected.append(candidate_data[first_idx])
        selected_filenames.add(candidate_data[first_idx]['filename'])
        candidate_indices.remove(first_idx)
        
        # Select remaining items using MMR
        while len(selected) < top_k and candidate_indices:
            best_score = -float('inf')
            best_idx = None
            
            for idx in candidate_indices:
                candidate = candidate_data[idx]
                
                # Relevance to query
                relevance = self.cosine_similarity(
                    np.array(query_embedding),
                    np.array(candidate['vector'])
                )
                
                # Diversity: max similarity to already selected items
                max_similarity = max(
                    self.cosine_similarity(
                        np.array(candidate['vector']),
                        np.array(sel['vector'])
                    )
                    for sel in selected
                )
                
                # Paper diversity bonus
                paper_bonus = 0
                if target_papers and candidate['filename'] not in selected_filenames:
                    # Bonus for new papers if we haven't reached target
                    if len(selected_filenames) < target_papers:
                        paper_bonus = 0.3
                
                # MMR score: balance relevance and diversity
                mmr_score = (
                    self.lambda_param * relevance - 
                    (1 - self.lambda_param) * max_similarity +
                    paper_bonus
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            
            if best_idx is not None:
                selected.append(candidate_data[best_idx])
                selected_filenames.add(candidate_data[best_idx]['filename'])
                candidate_indices.remove(best_idx)
            else:
                break
        
        # Convert to result format
        results = []
        for item in selected:
            results.append({
                'filename': item['payload']['filename'],
                'chunk_text': item['payload']['chunk_text'],
                'chunk_id': item['payload']['chunk_id'],
                'score': item['score']
            })
        
        return results
    
    def diverse_paper_retrieval(self, query: str, num_papers: int = 30, 
                               chunks_per_paper: int = 3):
        """
        Retrieve chunks ensuring diversity across papers.
        
        Args:
            query: Search query
            num_papers: Number of unique papers to retrieve from
            chunks_per_paper: Average chunks per paper
            
        Returns:
            List of chunks from diverse papers
        """
        # Get query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Retrieve many candidates
        candidates = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=500,  # Get many candidates
            with_vectors=True
        ).points
        
        # Group by paper
        papers = {}
        for hit in candidates:
            filename = hit.payload['filename']
            # Calculate score
            score = self.cosine_similarity(
                np.array(query_embedding),
                np.array(hit.vector)
            )
            if filename not in papers:
                papers[filename] = []
            papers[filename].append({
                'filename': filename,
                'chunk_text': hit.payload['chunk_text'],
                'chunk_id': hit.payload['chunk_id'],
                'score': score,
                'vector': hit.vector
            })
        
        # Select top papers by best chunk score
        paper_scores = {
            filename: max(chunk['score'] for chunk in chunks)
            for filename, chunks in papers.items()
        }
        
        top_papers = sorted(paper_scores.items(), key=lambda x: x[1], reverse=True)[:num_papers]
        
        # Select chunks from each paper
        selected_chunks = []
        for filename, _ in top_papers:
            # Get top chunks from this paper
            paper_chunks = sorted(papers[filename], key=lambda x: x['score'], reverse=True)
            selected_chunks.extend(paper_chunks[:chunks_per_paper])
        
        print(f"✓ Retrieved {len(selected_chunks)} chunks from {len(top_papers)} unique papers")
        
        return selected_chunks


def test_mmr_vs_standard():
    """Compare MMR retrieval vs standard retrieval."""
    print("="*70)
    print("MMR vs STANDARD RETRIEVAL COMPARISON")
    print("="*70)
    
    query = "machine learning in code analysis"
    top_k = 50
    
    # Standard retrieval
    from query import QueryEngine
    engine = QueryEngine()
    standard_results = engine.search(query, top_k=top_k)
    standard_papers = set(r['filename'] for r in standard_results)
    
    print(f"\n📊 Standard Retrieval (top_k={top_k}):")
    print(f"  Unique papers: {len(standard_papers)}")
    print(f"  Diversity: {len(standard_papers)/top_k*100:.1f}%")
    
    # MMR retrieval
    mmr = MMRRetriever(lambda_param=0.5)
    mmr_results = mmr.mmr_retrieval(query, top_k=top_k, target_papers=30)
    mmr_papers = set(r['filename'] for r in mmr_results)
    
    print(f"\n📊 MMR Retrieval (top_k={top_k}, lambda=0.5):")
    print(f"  Unique papers: {len(mmr_papers)}")
    print(f"  Diversity: {len(mmr_papers)/top_k*100:.1f}%")
    print(f"  Improvement: {len(mmr_papers)/len(standard_papers):.1f}x more papers")
    
    # Diverse paper retrieval
    diverse_results = mmr.diverse_paper_retrieval(query, num_papers=30, chunks_per_paper=3)
    diverse_papers = set(r['filename'] for r in diverse_results)
    
    print("\n📊 Diverse Paper Retrieval (30 papers, 3 chunks each):")
    print(f"  Total chunks: {len(diverse_results)}")
    print(f"  Unique papers: {len(diverse_papers)}")
    print(f"  Diversity: {len(diverse_papers)/len(diverse_results)*100:.1f}%")
    print(f"  Improvement: {len(diverse_papers)/len(standard_papers):.1f}x more papers")


if __name__ == '__main__':
    import os
    os.environ['HF_HOME'] = os.path.join(os.getcwd(), '.cache/huggingface')
    
    test_mmr_vs_standard()
