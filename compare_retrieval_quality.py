#!/usr/bin/env python3
"""
Retrieval Quality Comparison Tool
Compare old SPECTER vs new SPECTER2 retrieval quality.
"""

import os

# CRITICAL: Set up cache BEFORE importing any HF libraries
HF_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hf_cache")
os.makedirs(HF_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_CACHE_DIR, "transformers")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(HF_CACHE_DIR, "sentence_transformers")
os.environ["HF_TOKEN_PATH"] = os.path.join(HF_CACHE_DIR, "token")
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import json

class RetrievalComparator:
    """Compare retrieval quality between two collections."""
    
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        
        # Old model (SPECTER v1)
        print("Loading old model (allenai-specter)...")
        self.old_model = SentenceTransformer('sentence-transformers/allenai-specter')
        
        # New model (SPECTER2)
        print("Loading new model (specter2_base)...")
        self.new_model = SentenceTransformer('allenai/specter2_base')
        
        print("Models loaded!\n")
    
    def search_collection(self, collection_name: str, query: str, model, top_k: int = 10):
        """Search a collection with given model."""
        # Encode query
        query_vector = model.encode(query).tolist()
        
        # Search using correct Qdrant API
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k
        ).points
        
        return results
    
    def compare_retrieval(self, query: str, old_collection: str, new_collection: str, top_k: int = 10):
        """Compare retrieval results for a query."""
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        # Search old collection
        print(f"Searching OLD collection ({old_collection})...")
        old_results = self.search_collection(old_collection, query, self.old_model, top_k)
        
        # Search new collection
        print(f"Searching NEW collection ({new_collection})...")
        new_results = self.search_collection(new_collection, query, self.new_model, top_k)
        
        # Display results
        print(f"\n{'OLD MODEL RESULTS (SPECTER v1)':-^80}")
        for i, result in enumerate(old_results, 1):
            filename = result.payload.get('filename', 'Unknown')
            score = result.score
            chunk_preview = result.payload.get('chunk_text', '')[:100]
            print(f"{i}. [{score:.4f}] {filename}")
            print(f"   Preview: {chunk_preview}...")
            print()
        
        print(f"\n{'NEW MODEL RESULTS (SPECTER2)':-^80}")
        for i, result in enumerate(new_results, 1):
            filename = result.payload.get('filename', 'Unknown')
            score = result.score
            chunk_preview = result.payload.get('chunk_text', '')[:100]
            print(f"{i}. [{score:.4f}] {filename}")
            print(f"   Preview: {chunk_preview}...")
            print()
        
        # Calculate metrics
        old_filenames = [r.payload.get('filename') for r in old_results]
        new_filenames = [r.payload.get('filename') for r in new_results]
        
        overlap = len(set(old_filenames) & set(new_filenames))
        unique_to_new = len(set(new_filenames) - set(old_filenames))
        
        old_avg_score = np.mean([r.score for r in old_results])
        new_avg_score = np.mean([r.score for r in new_results])
        
        print(f"\n{'COMPARISON METRICS':-^80}")
        print(f"Papers in both results: {overlap}/{top_k}")
        print(f"New papers found by SPECTER2: {unique_to_new}")
        print(f"Old model avg score: {old_avg_score:.4f}")
        print(f"New model avg score: {new_avg_score:.4f}")
        print(f"Score improvement: {((new_avg_score - old_avg_score) / old_avg_score * 100):.2f}%")
        
        return {
            'query': query,
            'overlap': overlap,
            'unique_to_new': unique_to_new,
            'old_avg_score': old_avg_score,
            'new_avg_score': new_avg_score,
            'improvement_pct': (new_avg_score - old_avg_score) / old_avg_score * 100
        }

def main():
    """Run comparison tests."""
    print("="*80)
    print("RETRIEVAL QUALITY COMPARISON: SPECTER v1 vs SPECTER2")
    print("="*80)
    
    comparator = RetrievalComparator()
    
    # Test queries (academic paper topics)
    test_queries = [
        "transformer architectures for natural language processing",
        "graph neural networks for program analysis",
        "deep learning approaches to code similarity detection",
        "attention mechanisms in neural machine translation",
        "convolutional neural networks for image classification"
    ]
    
    # Collections to compare
    old_collection = "academic_papers_100_specter"
    new_collection = "academic_papers_100_specter2_v2"
    
    # Check if collections exist
    collections = comparator.client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if old_collection not in collection_names:
        print(f"\n❌ Old collection '{old_collection}' not found!")
        print(f"Available collections: {collection_names}")
        return
    
    if new_collection not in collection_names:
        print(f"\n❌ New collection '{new_collection}' not found!")
        print(f"Available collections: {collection_names}")
        print("\nPlease wait for re-ingestion to complete.")
        return
    
    # Run comparisons
    results = []
    for query in test_queries:
        result = comparator.compare_retrieval(query, old_collection, new_collection, top_k=10)
        results.append(result)
    
    # Overall summary
    print(f"\n\n{'OVERALL SUMMARY':-^80}")
    avg_improvement = np.mean([r['improvement_pct'] for r in results])
    avg_overlap = np.mean([r['overlap'] for r in results])
    avg_new_papers = np.mean([r['unique_to_new'] for r in results])
    
    print(f"Average score improvement: {avg_improvement:.2f}%")
    print(f"Average paper overlap: {avg_overlap:.1f}/10")
    print(f"Average new papers found: {avg_new_papers:.1f}/10")
    
    print("\n" + "="*80)
    if avg_improvement > 5:
        print("✅ SPECTER2 shows significant improvement!")
    elif avg_improvement > 0:
        print("✅ SPECTER2 shows modest improvement")
    else:
        print("⚠️ Results are similar - may need more testing")
    print("="*80)
    
    # Save results
    with open('retrieval_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: retrieval_comparison_results.json")

if __name__ == "__main__":
    main()
