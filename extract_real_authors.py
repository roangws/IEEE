#!/usr/bin/env python3
"""
Extract Real Author Names from IEEE PDFs
Focuses on extracting individual author names, not institutions.
"""

import fitz
import re
import json
from pathlib import Path


def extract_ieee_authors(pdf_path):
    """
    Extract author names from IEEE paper first page.
    IEEE format: Authors appear in ALL CAPS after title, before affiliations.
    
    Args:
        pdf_path: Path to PDF
        
    Returns:
        List of author names or None
    """
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0].get_text()
        doc.close()
        
        # IEEE papers have authors in ALL CAPS with superscript numbers
        # Example: "JAVAD ANSARI1, MOHAMADREZA HOMAYOUNZADE2, AND ALI REZA ABBASI3"
        
        # Look for all-caps names with optional numbers
        # Pattern: ALL CAPS NAME followed by optional digit(s)
        author_pattern = r'([A-Z][A-Z\s]{3,40}?)(?:\d+)?(?:,|\s+AND\s+|$)'
        
        # Find the section with authors (after DOI, before department/affiliation)
        lines = first_page.split('\n')
        
        authors = []
        in_author_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Start looking after DOI line
            if 'Digital Object Identifier' in line or 'DOI' in line:
                in_author_section = True
                continue
            
            # Stop at department/affiliation lines
            if any(x in line for x in ['Department', 'Faculty', 'School', 'University', 'Institute']):
                break
            
            # Stop at abstract
            if 'ABSTRACT' in line:
                break
            
            if in_author_section and line:
                # Check if line has all-caps names
                if re.search(r'[A-Z]{2,}', line):
                    # Extract names from this line
                    # Split by AND and commas
                    line = re.sub(r'\d+', '', line)  # Remove numbers
                    parts = re.split(r',|\s+AND\s+', line)
                    
                    for part in parts:
                        part = part.strip()
                        # Must be mostly uppercase and reasonable length
                        if len(part) > 5 and len(part) < 50:
                            uppercase_ratio = sum(1 for c in part if c.isupper()) / len(part.replace(' ', ''))
                            if uppercase_ratio > 0.7:  # At least 70% uppercase
                                # Convert to title case
                                name = part.title()
                                if name not in authors:
                                    authors.append(name)
        
        # Clean up and validate
        cleaned_authors = []
        for author in authors:
            # Remove extra spaces
            author = ' '.join(author.split())
            # Must have at least 2 words (first and last name)
            words = author.split()
            if len(words) >= 2 and len(words) <= 5:
                # Each word should be at least 2 chars
                if all(len(w) >= 2 for w in words):
                    cleaned_authors.append(author)
        
        return cleaned_authors[:10] if cleaned_authors else None
        
    except Exception as e:
        return None


def format_authors_ieee(authors):
    """Format authors in IEEE style."""
    if not authors or len(authors) == 0:
        return "Unknown Authors"
    
    if len(authors) == 1:
        return authors[0]
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    elif len(authors) <= 6:
        return ", ".join(authors[:-1]) + f", and {authors[-1]}"
    else:
        return f"{authors[0]}, {authors[1]}, {authors[2]}, et al."


def update_metadata_with_real_authors(metadata_file="pdf_metadata.json", pdf_dir="downloaded_pdfs"):
    """Update metadata with real author names."""
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"Extracting real author names from {len(metadata)} PDFs...")
    print("Focusing on individual names, not institutions...\n")
    
    updated_count = 0
    
    for i, (filename, meta) in enumerate(metadata.items(), 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(metadata)} PDFs...")
        
        pdf_path = Path(pdf_dir) / filename
        
        if not pdf_path.exists():
            continue
        
        authors = extract_ieee_authors(pdf_path)
        
        if authors and len(authors) > 0:
            formatted = format_authors_ieee(authors)
            metadata[filename]['authors'] = formatted
            metadata[filename]['author_list'] = authors
            updated_count += 1
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Updated {updated_count}/{len(metadata)} papers with author names")
    print(f"✓ Saved to {metadata_file}")
    
    # Show samples with real names
    print("\n" + "="*70)
    print("SAMPLE AUTHOR EXTRACTIONS")
    print("="*70)
    
    sample_count = 0
    for filename, meta in metadata.items():
        if meta.get('author_list') and len(meta.get('author_list', [])) > 0:
            if sample_count < 10:
                print(f"\n{filename}")
                print(f"  Title: {meta['title'][:60]}...")
                print(f"  Authors: {meta['authors']}")
                print(f"  Author list: {meta['author_list']}")
                sample_count += 1


if __name__ == '__main__':
    update_metadata_with_real_authors()
