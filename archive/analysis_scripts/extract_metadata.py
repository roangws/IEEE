#!/usr/bin/env python3
"""
PDF Metadata Extractor
Extracts titles, authors, and other metadata from PDFs for proper citations.
"""

import argparse
import fitz
import os
import json
import re
from pathlib import Path


def extract_pdf_metadata(pdf_path):
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with metadata
    """
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        
        # Get first page text to extract title if not in metadata
        first_page = doc[0].get_text()
        
        # Extract title (first non-empty line, usually the title)
        title = metadata.get('title', '')
        if not title or len(title) < 10:
            # Try to extract from first page
            lines = [line.strip() for line in first_page.split('\n') if line.strip()]
            if lines:
                # Title is usually the first substantial line
                for line in lines[:5]:
                    if len(line) > 20 and not line.startswith('http'):
                        title = line
                        break
        
        # Extract authors
        authors = metadata.get('author', '')
        
        # Try to extract year from text or filename
        year = None
        # Check metadata
        if metadata.get('creationDate'):
            year_match = re.search(r'(\d{4})', metadata['creationDate'])
            if year_match:
                year = year_match.group(1)
        
        # Check first page for year
        if not year:
            year_match = re.search(r'\b(19|20)\d{2}\b', first_page[:1000])
            if year_match:
                year = year_match.group(0)
        
        # Extract DOI if present
        doi = None
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', first_page[:2000])
        if doi_match:
            doi = doi_match.group(0)
        
        filename = os.path.basename(pdf_path)
        
        doc.close()
        
        return {
            'filename': filename,
            'title': title or f"Document {filename}",
            'authors': authors or "Unknown Authors",
            'year': year or "n.d.",
            'doi': doi,
            'path': str(pdf_path)
        }
        
    except Exception as e:
        filename = os.path.basename(pdf_path)
        return {
            'filename': filename,
            'title': f"Document {filename}",
            'authors': "Unknown Authors",
            'year': "n.d.",
            'doi': None,
            'path': str(pdf_path),
            'error': str(e)
        }


def extract_all_metadata(pdf_dir):
    """
    Extract metadata from all PDFs in a directory.
    
    Args:
        pdf_dir: Directory containing PDFs
        
    Returns:
        Dictionary mapping filenames to metadata
    """
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files")
    print("Extracting metadata...\n")
    
    metadata_dict = {}
    
    for i, pdf_path in enumerate(pdf_files, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(pdf_files)} PDFs...")
        
        metadata = extract_pdf_metadata(pdf_path)
        metadata_dict[metadata['filename']] = metadata
    
    print(f"\n✓ Extracted metadata from {len(metadata_dict)} PDFs")
    
    return metadata_dict


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract metadata from PDFs for citations"
    )
    parser.add_argument(
        '--pdf-dir',
        type=str,
        default='test_pdfs_100',
        help='Directory containing PDFs'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='pdf_metadata.json',
        help='Output JSON file'
    )
    
    args = parser.parse_args()
    
    # Extract metadata
    metadata = extract_all_metadata(args.pdf_dir)
    
    # Save to JSON
    with open(args.output, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Metadata saved to {args.output}")
    
    # Show sample
    print("\n" + "="*70)
    print("SAMPLE METADATA")
    print("="*70)
    
    for i, (filename, meta) in enumerate(list(metadata.items())[:3], 1):
        print(f"\n{i}. {filename}")
        print(f"   Title: {meta['title'][:80]}...")
        print(f"   Authors: {meta['authors']}")
        print(f"   Year: {meta['year']}")
        if meta.get('doi'):
            print(f"   DOI: {meta['doi']}")


if __name__ == '__main__':
    main()
