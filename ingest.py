#!/usr/bin/env python3
"""
PDF Ingestion and Vector Store Module
Processes academic PDFs and stores embeddings in Qdrant for RAG retrieval.
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

import argparse
from pathlib import Path
from typing import List, Dict
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import uuid


class PDFIngestor:
    """Handles PDF processing and vector store ingestion."""
    
    def __init__(
        self,
        pdf_dir: str = "downloaded_pdfs",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "academic_papers",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 100
    ):
        """
        Initialize the PDF ingestor.
        
        Args:
            pdf_dir: Directory containing PDF files
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of the Qdrant collection
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
            batch_size: Batch size for upserts
        """
        self.pdf_dir = Path(pdf_dir)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        
        # Cache for embeddings to speed up processing
        self._embedding_cache = {}
        
        # Initialize embedding model - SPECTER2 base (better than original SPECTER)
        print("Loading embedding model (allenai/specter2_base)...")
        import torch
        # Use MPS (Metal Performance Shaders) for M1/M2/M3/M4 Macs
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        print(f"Using device: {device}")
        self.embedder = SentenceTransformer('allenai/specter2_base', device=device)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        print(f"Model loaded: {self.embedding_dim}-dimensional embeddings on {device}")
        
        # Initialize Qdrant client
        print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Create or recreate collection
        self._setup_collection()
    
    def _setup_collection(self):
        """Create or recreate the Qdrant collection."""
        # Check if collection exists
        collections = self.qdrant_client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)
        
        if collection_exists:
            print(f"Collection '{self.collection_name}' already exists.")
            response = input("Do you want to recreate it? (y/n): ").strip().lower()
            if response == 'y':
                print(f"Deleting existing collection '{self.collection_name}'...")
                self.qdrant_client.delete_collection(self.collection_name)
                collection_exists = False
        
        if not collection_exists:
            print(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print(f"Collection created with dimension {self.embedding_dim}")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            Exception: If PDF cannot be read
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from {pdf_path.name}: {str(e)}")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks with overlap.
        Simple and reliable chunking strategy.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or len(text) == 0:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # Get chunk
            chunk = text[start:end]
            
            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk)
            
            # Move start position with overlap
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def create_embeddings(self, texts: List[str], prefix: str = "search_document: ") -> List[List[float]]:
        """
        Create embeddings for a list of texts with batching for speed.
        
        Args:
            texts: List of text strings
            prefix: Prefix to add to each text
            
        Returns:
            List of embeddings
        """
        # Add prefix to texts for better retrieval
        prefixed_texts = [prefix + text for text in texts]
        
        # Generate embeddings with larger batch size for speed
        # Use larger batch size for GPU (MPS/CUDA) acceleration
        embeddings = self.embedder.encode(
            prefixed_texts, 
            show_progress_bar=False,
            batch_size=64,  # Increased for GPU acceleration
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for better similarity
        )
        return embeddings.tolist()
    
    def process_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Process a single PDF file into chunks with metadata.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with chunk data
        """
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        # Skip if no text extracted
        if not text.strip():
            return []
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Create chunk data
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                'filename': pdf_path.name,
                'chunk_text': chunk,
                'chunk_id': i,
                'total_chunks': len(chunks)
            })
        
        return chunk_data
    
    def ingest_pdfs(self):
        """
        Process all PDFs and ingest into Qdrant.
        
        Returns:
            Tuple of (total_vectors, successful_pdfs, failed_pdfs)
        """
        # Get all PDF files
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.pdf_dir}")
            return 0, 0, 0
        
        print(f"\nFound {len(pdf_files)} PDF files to process")
        print(f"Chunk size: {self.chunk_size} characters")
        print(f"Chunk overlap: {self.chunk_overlap} characters")
        print(f"Batch size: {self.batch_size}\n")
        
        total_vectors = 0
        successful_pdfs = 0
        failed_pdfs = 0
        batch_points = []
        
        # Process each PDF with progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                # Process PDF into chunks
                chunk_data = self.process_pdf(pdf_path)
                
                if not chunk_data:
                    failed_pdfs += 1
                    continue
                
                # Create embeddings for chunks
                chunk_texts = [c['chunk_text'] for c in chunk_data]
                embeddings = self.create_embeddings(chunk_texts)
                
                # Create points for Qdrant
                for chunk_info, embedding in zip(chunk_data, embeddings):
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            'filename': chunk_info['filename'],
                            'chunk_text': chunk_info['chunk_text'],
                            'chunk_id': chunk_info['chunk_id'],
                            'total_chunks': chunk_info['total_chunks']
                        }
                    )
                    batch_points.append(point)
                
                # Batch upsert when batch is full
                if len(batch_points) >= self.batch_size:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=batch_points
                    )
                    total_vectors += len(batch_points)
                    batch_points = []
                
                successful_pdfs += 1
                
            except Exception as e:
                print(f"\n⚠ Error processing {pdf_path.name}: {str(e)}")
                failed_pdfs += 1
                continue
        
        # Upsert remaining points
        if batch_points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch_points
            )
            total_vectors += len(batch_points)
        
        return total_vectors, successful_pdfs, failed_pdfs
    
    def print_stats(self):
        """Print collection statistics."""
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        print("\n" + "="*70)
        print("COLLECTION STATISTICS")
        print("="*70)
        print(f"Collection name: {self.collection_name}")
        print(f"Total vectors: {collection_info.points_count}")
        print(f"Vector dimension: {self.embedding_dim}")
        print("Distance metric: COSINE")
        print("="*70 + "\n")


def main():
    """Main entry point for PDF ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest academic PDFs into Qdrant vector store"
    )
    parser.add_argument(
        '--skip-ingest',
        action='store_true',
        help='Skip PDF ingestion (useful for testing other components)'
    )
    parser.add_argument(
        '--pdf-dir',
        type=str,
        default='downloaded_pdfs',
        help='Directory containing PDF files (default: downloaded_pdfs)'
    )
    parser.add_argument(
        '--qdrant-host',
        type=str,
        default='localhost',
        help='Qdrant host (default: localhost)'
    )
    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant port (default: 6333)'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='academic_papers',
        help='Qdrant collection name (default: academic_papers)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Chunk size in characters (default: 1000)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=100,
        help='Chunk overlap in characters (default: 100)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for upserts (default: 100)'
    )
    
    args = parser.parse_args()
    
    if args.skip_ingest:
        print("Skipping PDF ingestion (--skip-ingest flag set)")
        print("You can now use query.py or app.py to interact with existing data")
        return
    
    # Initialize ingestor
    ingestor = PDFIngestor(
        pdf_dir=args.pdf_dir,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size
    )
    
    # Ingest PDFs
    print("\nStarting PDF ingestion...\n")
    total_vectors, successful_pdfs, failed_pdfs = ingestor.ingest_pdfs()
    
    # Print results
    print("\n" + "="*70)
    print("INGESTION COMPLETE")
    print("="*70)
    print(f"✓ Successfully processed: {successful_pdfs} PDFs")
    print(f"✗ Failed to process: {failed_pdfs} PDFs")
    print(f"📊 Total vectors stored: {total_vectors}")
    print("="*70)
    
    # Print collection stats
    ingestor.print_stats()
    
    print("Ready to use! Run 'streamlit run app.py' to start the web interface")


if __name__ == '__main__':
    main()
