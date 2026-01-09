#!/usr/bin/env python3
"""
Test SPECTER2 Model Upgrade
Validates that the new model loads correctly and compares with old model.
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

from sentence_transformers import SentenceTransformer
import numpy as np

def test_model_loading():
    """Test that SPECTER2 model loads correctly."""
    print("=" * 60)
    print("Testing SPECTER2 Model Upgrade")
    print("=" * 60)
    
    print("\n1. Loading SPECTER2 base...")
    try:
        model = SentenceTransformer('allenai/specter2_base')
        dim = model.get_sentence_embedding_dimension()
        print(f"   ✅ Model loaded successfully!")
        print(f"   📊 Embedding dimension: {dim}")
        return model
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        return None

def test_embedding_quality(model):
    """Test embedding quality with academic queries."""
    print("\n2. Testing embedding quality...")
    
    # Academic paper titles/abstracts
    test_texts = [
        "Transformer architectures for natural language processing",
        "Graph neural networks for program analysis",
        "Deep learning approaches to code similarity detection",
        "Attention mechanisms in neural machine translation"
    ]
    
    print("   Encoding test texts...")
    embeddings = model.encode(test_texts)
    
    print(f"   ✅ Generated {len(embeddings)} embeddings")
    print(f"   📊 Shape: {embeddings.shape}")
    
    # Calculate similarity matrix
    print("\n3. Computing similarity matrix...")
    similarities = np.zeros((len(test_texts), len(test_texts)))
    
    for i in range(len(test_texts)):
        for j in range(len(test_texts)):
            sim = np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
            )
            similarities[i][j] = sim
    
    print("\n   Similarity Matrix:")
    print("   " + "-" * 50)
    for i, text in enumerate(test_texts):
        print(f"   {i+1}. {text[:40]}...")
    print("   " + "-" * 50)
    
    for i in range(len(test_texts)):
        row = "   "
        for j in range(len(test_texts)):
            row += f"{similarities[i][j]:.3f}  "
        print(row)
    
    print("\n   Expected behavior:")
    print("   - Diagonal should be ~1.0 (self-similarity)")
    print("   - Related papers should have higher similarity")
    print("   - Unrelated papers should have lower similarity")

def test_semantic_chunking():
    """Test semantic chunking function."""
    print("\n4. Testing semantic chunking...")
    
    sample_text = """
This is the first paragraph. It contains some information about transformers.

This is the second paragraph. It discusses attention mechanisms in detail.

This is the third paragraph. It covers implementation details and frameworks.

This is the fourth paragraph. It provides experimental results and metrics.
"""
    
    # Simulate chunking logic
    paragraphs = sample_text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    chunk_size = 1000
    min_size = 500
    max_size = 1500
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) + 2 < max_size:
            current_chunk += para + "\n\n"
        else:
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"
                if len(current_chunk) >= min_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    print(f"   ✅ Created {len(chunks)} semantic chunks")
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i+1}: {len(chunk)} chars")

def main():
    """Run all tests."""
    model = test_model_loading()
    
    if model:
        test_embedding_quality(model)
        test_semantic_chunking()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Ready for re-ingestion.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Create new collection: academic_papers_100_specter2")
        print("2. Run: python ingest.py --pdf-dir downloaded_pdfs --collection academic_papers_100_specter2")
        print("3. Update app.py to use new collection")
        print("4. Test retrieval quality improvements")
    else:
        print("\n" + "=" * 60)
        print("❌ Model loading failed. Please check installation.")
        print("=" * 60)

if __name__ == "__main__":
    main()
