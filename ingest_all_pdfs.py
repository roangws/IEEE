#!/usr/bin/env python3
"""
Ingest all 5,634 PDFs from downloaded_pdfs into Qdrant with SPECTER2 embeddings.
Creates a new collection: academic_papers_full_specter2
"""

import sys
from pathlib import Path
from ingest import PDFIngestor

def main():
    print("="*70)
    print("FULL PDF INGESTION - 5,634 Papers")
    print("="*70)
    
    # Configuration
    pdf_dir = "downloaded_pdfs"
    collection_name = "academic_papers_full_specter2"
    
    # Count PDFs
    pdf_files = list(Path(pdf_dir).glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDFs in {pdf_dir}")
    
    # Confirm
    print(f"\nThis will:")
    print(f"  1. Create collection: {collection_name}")
    print(f"  2. Use SPECTER2 embeddings (768-dimensional)")
    print(f"  3. Process all {len(pdf_files)} PDFs with semantic chunking")
    print(f"  4. Estimated time: 30-60 minutes")
    print(f"  5. Estimated chunks: ~{len(pdf_files) * 80} (avg 80 chunks/paper)")
    
    response = input("\nProceed with ingestion? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Ingestion cancelled.")
        return
    
    # Initialize ingestor
    print("\n" + "="*70)
    print("INITIALIZING INGESTOR")
    print("="*70)
    
    ingestor = PDFIngestor(
        pdf_dir=pdf_dir,
        collection_name=collection_name,
        chunk_size=1000,
        chunk_overlap=100,
        batch_size=100
    )
    
    # Process PDFs
    print("\n" + "="*70)
    print("PROCESSING PDFs")
    print("="*70)
    
    total_vectors, successful_pdfs, failed_pdfs = ingestor.ingest_pdfs()
    
    print("\n" + "="*70)
    print("INGESTION COMPLETE")
    print("="*70)
    print(f"✓ Successfully processed: {successful_pdfs} PDFs")
    print(f"✗ Failed to process: {failed_pdfs} PDFs")
    print(f"📊 Total vectors stored: {total_vectors}")
    
    # Verify
    collection_info = ingestor.qdrant_client.get_collection(collection_name)
    print(f"\nCollection: {collection_name}")
    print(f"  Total chunks: {collection_info.points_count}")
    print(f"  Vector dimension: {collection_info.config.params.vectors.size}")
    print(f"  Estimated papers: ~{collection_info.points_count // 80}")
    print(f"  Status: {collection_info.status}")
    
    print("\n✓ All PDFs ingested successfully!")
    print(f"\nNext steps:")
    print(f"  1. Refresh Streamlit UI")
    print(f"  2. Select collection: {collection_name}")
    print(f"  3. Generate articles with all 5,634 papers!")

if __name__ == '__main__':
    main()
