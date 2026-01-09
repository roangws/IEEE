#!/usr/bin/env python3
"""
Extract metadata from all PDFs in downloaded_pdfs folder.
Creates comprehensive metadata file for citation formatting.
"""

import fitz
import re
import json
from pathlib import Path
from tqdm import tqdm
import concurrent.futures

def extract_ieee_metadata(pdf_path):
    """
    Extract metadata from IEEE paper.
    Returns: dict with title, authors, year, doi
    """
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0].get_text()
        doc.close()
        
        lines = first_page.split('\n')
        
        metadata = {
            'filename': pdf_path.name,
            'title': None,
            'authors': 'Unknown Authors',
            'author_list': [],
            'year': 'n.d.',
            'doi': None,
            'path': str(pdf_path)
        }
        
        # Extract DOI
        for line in lines[:30]:
            if 'DOI' in line or 'doi' in line.lower():
                doi_match = re.search(r'10\.\d{4,}/[^\s]+', line)
                if doi_match:
                    metadata['doi'] = doi_match.group(0)
                    break
        
        # Extract year from date line
        for line in lines[:10]:
            if 'date of current version' in line.lower() or 'date of publication' in line.lower():
                year_match = re.search(r'\b(20\d{2})\b', line)
                if year_match:
                    metadata['year'] = year_match.group(1)
                    break
        
        # Extract title (usually after DOI, before authors)
        title_candidates = []
        in_title_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if 'Digital Object Identifier' in line or 'DOI' in line:
                in_title_section = True
                continue
            
            if in_title_section:
                # Stop at authors (ALL CAPS line)
                if len(line) > 10 and line.isupper():
                    break
                
                # Stop at department/affiliation
                if any(x in line for x in ['Department', 'Faculty', 'University', 'Institute']):
                    break
                
                # Collect title lines
                if len(line) > 10 and not line.isupper():
                    title_candidates.append(line)
                
                if len(title_candidates) >= 5:
                    break
        
        if title_candidates:
            metadata['title'] = ' '.join(title_candidates[:3])  # Take first 3 lines
        
        # Extract authors (ALL CAPS after title)
        authors = []
        in_author_section = False
        
        for line in lines:
            line = line.strip()
            
            if metadata['title'] and metadata['title'][:30] in line:
                in_author_section = True
                continue
            
            if in_author_section:
                # Stop at department/affiliation
                if any(x in line for x in ['Department', 'Faculty', 'School', 'University', 'Institute']):
                    break
                
                # Stop at abstract
                if 'ABSTRACT' in line:
                    break
                
                if line and re.search(r'[A-Z]{2,}', line):
                    # Remove numbers
                    line = re.sub(r'\d+', '', line)
                    parts = re.split(r',|\s+AND\s+', line)
                    
                    for part in parts:
                        part = part.strip()
                        if len(part) > 5 and len(part) < 50:
                            uppercase_ratio = sum(1 for c in part if c.isupper()) / len(part.replace(' ', ''))
                            if uppercase_ratio > 0.7:
                                name = part.title()
                                if name not in authors:
                                    authors.append(name)
        
        # Format authors
        if authors:
            cleaned_authors = []
            for author in authors:
                author = ' '.join(author.split())
                words = author.split()
                if len(words) >= 2 and len(words) <= 5:
                    if all(len(w) >= 2 for w in words):
                        cleaned_authors.append(author)
            
            if cleaned_authors:
                metadata['author_list'] = cleaned_authors[:10]
                
                if len(cleaned_authors) == 1:
                    metadata['authors'] = cleaned_authors[0]
                elif len(cleaned_authors) == 2:
                    metadata['authors'] = f"{cleaned_authors[0]} and {cleaned_authors[1]}"
                elif len(cleaned_authors) <= 6:
                    metadata['authors'] = ", ".join(cleaned_authors[:-1]) + f", and {cleaned_authors[-1]}"
                else:
                    metadata['authors'] = f"{cleaned_authors[0]}, {cleaned_authors[1]}, {cleaned_authors[2]}, et al."
        
        return metadata
        
    except Exception as e:
        return {
            'filename': pdf_path.name,
            'title': f'Document {pdf_path.name}',
            'authors': 'Unknown Authors',
            'author_list': [],
            'year': 'n.d.',
            'doi': None,
            'path': str(pdf_path)
        }

def main():
    pdf_dir = Path('downloaded_pdfs')
    output_file = 'pdf_metadata.json'
    
    # Get all PDFs
    pdf_files = list(pdf_dir.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDFs in {pdf_dir}")
    
    # Load existing metadata if available
    existing_metadata = {}
    if Path(output_file).exists():
        with open(output_file, 'r') as f:
            existing_metadata = json.load(f)
        print(f"Loaded {len(existing_metadata)} existing entries")
    
    # Process PDFs in parallel
    metadata = {}
    
    print("\nExtracting metadata from PDFs...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_pdf = {executor.submit(extract_ieee_metadata, pdf): pdf for pdf in pdf_files}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=len(pdf_files)):
            pdf = future_to_pdf[future]
            try:
                result = future.result()
                metadata[result['filename']] = result
            except Exception as e:
                print(f"\nError processing {pdf.name}: {e}")
    
    # Save metadata
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved metadata for {len(metadata)} PDFs to {output_file}")
    
    # Statistics
    with_authors = sum(1 for m in metadata.values() if m['authors'] != 'Unknown Authors')
    with_doi = sum(1 for m in metadata.values() if m['doi'])
    with_year = sum(1 for m in metadata.values() if m['year'] != 'n.d.')
    
    print(f"\nStatistics:")
    print(f"  PDFs with authors: {with_authors}/{len(metadata)} ({with_authors/len(metadata)*100:.1f}%)")
    print(f"  PDFs with DOI: {with_doi}/{len(metadata)} ({with_doi/len(metadata)*100:.1f}%)")
    print(f"  PDFs with year: {with_year}/{len(metadata)} ({with_year/len(metadata)*100:.1f}%)")
    
    # Show samples
    print("\n" + "="*70)
    print("SAMPLE METADATA")
    print("="*70)
    
    sample_count = 0
    for filename, meta in metadata.items():
        if meta['authors'] != 'Unknown Authors' and sample_count < 5:
            print(f"\n{filename}")
            print(f"  Title: {meta['title'][:60]}...")
            print(f"  Authors: {meta['authors']}")
            print(f"  Year: {meta['year']}")
            print(f"  DOI: {meta['doi']}")
            sample_count += 1

if __name__ == '__main__':
    main()
