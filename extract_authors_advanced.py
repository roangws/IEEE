#!/usr/bin/env python3
"""
Advanced Author Extraction from PDFs
Extracts authors from IEEE papers by analyzing the first page content.
"""

import fitz
import re
import json
from pathlib import Path


def extract_authors_from_ieee_paper(pdf_path):
    """
    Extract authors from IEEE paper by analyzing first page.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of author names
    """
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0].get_text()
        doc.close()
        
        # IEEE papers typically have authors on first page after title
        # Look for patterns like:
        # - Names followed by affiliations
        # - Names in ALL CAPS or Title Case
        # - Names before "Abstract" section
        
        # Split into lines
        lines = [line.strip() for line in first_page.split('\n') if line.strip()]
        
        authors = []
        
        # Find the abstract section
        abstract_idx = None
        for i, line in enumerate(lines):
            if 'abstract' in line.lower() and len(line) < 50:
                abstract_idx = i
                break
        
        # Look for author names in first 20 lines or before abstract
        search_end = min(abstract_idx if abstract_idx else 20, 20)
        
        # Pattern 1: Names with potential middle initials (e.g., "John A. Smith")
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\b'
        
        # Pattern 2: Names in format "FIRSTNAME LASTNAME" or "Firstname Lastname"
        for i in range(1, search_end):
            line = lines[i]
            
            # Skip lines that are clearly not author names
            if any(skip in line.lower() for skip in ['ieee', 'access', 'volume', 'doi', 'received', 'accepted', 'published', 'http', 'www', 'index terms', 'manuscript']):
                continue
            
            # Skip very long lines (likely not just names)
            if len(line) > 100:
                continue
            
            # Skip lines with numbers or special characters
            if re.search(r'\d|[@#$%^&*()]', line):
                continue
            
            # Look for name patterns
            potential_names = re.findall(name_pattern, line)
            
            # Filter out common false positives
            false_positives = {'The', 'And', 'For', 'With', 'This', 'That', 'From', 'Digital', 'Member'}
            
            for name in potential_names:
                if name not in false_positives and len(name.split()) >= 2:
                    # Check if it looks like a real name (has at least 2 words)
                    if name not in authors:
                        authors.append(name)
        
        # If we found multiple authors, return them
        if len(authors) > 0:
            return authors[:10]  # Limit to 10 authors max
        
        # Fallback: try to find names in a different way
        # Look for lines with commas (author lists often separated by commas)
        for i in range(1, search_end):
            line = lines[i]
            if ',' in line and not any(skip in line.lower() for skip in ['ieee', 'doi', 'http', 'abstract']):
                # Split by comma and extract names
                parts = [p.strip() for p in line.split(',')]
                for part in parts:
                    if re.match(r'^[A-Z][a-z]+\s+[A-Z]', part) and len(part) < 50:
                        if part not in authors:
                            authors.append(part)
        
        return authors if authors else None
        
    except Exception as e:
        print(f"Error extracting authors from {pdf_path}: {e}")
        return None


def format_authors_ieee(authors):
    """
    Format authors in IEEE citation style.
    
    Args:
        authors: List of author names
        
    Returns:
        Formatted author string
    """
    if not authors or len(authors) == 0:
        return "Unknown Authors"
    
    if len(authors) == 1:
        return authors[0]
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    elif len(authors) <= 6:
        return ", ".join(authors[:-1]) + f", and {authors[-1]}"
    else:
        # More than 6 authors: list first 3 and use "et al."
        return f"{authors[0]}, {authors[1]}, {authors[2]}, et al."


def update_metadata_with_authors(metadata_file="pdf_metadata.json", pdf_dir="test_pdfs_100"):
    """
    Update existing metadata file with extracted authors.
    
    Args:
        metadata_file: Path to metadata JSON file
        pdf_dir: Directory containing PDFs
    """
    # Load existing metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"Extracting authors from {len(metadata)} PDFs...")
    print("This may take a few minutes...\n")
    
    updated_count = 0
    
    for i, (filename, meta) in enumerate(metadata.items(), 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(metadata)} PDFs...")
        
        pdf_path = Path(pdf_dir) / filename
        
        if not pdf_path.exists():
            continue
        
        # Extract authors
        authors = extract_authors_from_ieee_paper(pdf_path)
        
        if authors:
            # Format authors
            formatted_authors = format_authors_ieee(authors)
            metadata[filename]['authors'] = formatted_authors
            metadata[filename]['author_list'] = authors
            updated_count += 1
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Updated {updated_count}/{len(metadata)} papers with author information")
    print(f"✓ Saved to {metadata_file}")
    
    # Show sample
    print("\n" + "="*70)
    print("SAMPLE UPDATED METADATA")
    print("="*70)
    
    sample_count = 0
    for filename, meta in metadata.items():
        if meta.get('authors') != "Unknown Authors" and sample_count < 5:
            print(f"\n{filename}")
            print(f"  Title: {meta['title'][:60]}...")
            print(f"  Authors: {meta['authors']}")
            sample_count += 1


if __name__ == '__main__':
    update_metadata_with_authors()
