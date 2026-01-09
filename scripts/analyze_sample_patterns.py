#!/usr/bin/env python3
"""
Simplified IEEE Pattern Analyzer - Sample 200 papers
Extracts section and subsection patterns with robust PDF text extraction
"""

import os
import re
import json
import random
from collections import Counter, defaultdict
from typing import List, Dict, Optional
import pdfplumber

# Configuration
PDF_FOLDER = "downloaded_pdfs"
OUTPUT_DIR = "output"
SAMPLE_SIZE = 200

def clean_pdf_text(text: str) -> str:
    """Clean and normalize PDF text extraction issues."""
    # Add spaces after periods followed by capital letters (common PDF issue)
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    # Add spaces after lowercase followed by capital (word concatenation)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Add newlines before common section markers
    text = re.sub(r'([.!?])\s+(I+\.|[IVX]+\.|[0-9]+\.)\s+([A-Z])', r'\1\n\2 \3', text)
    return text

def extract_sections_and_subsections(text: str) -> Dict:
    """Extract section headers and subsection patterns from text."""
    sections = []
    subsections = []
    
    # More aggressive pattern matching - look anywhere in text, not just line starts
    # Pattern 1: Standard numbered sections with dot (3.1 Title, 4.2 Title)
    # Only match single-digit section numbers (1-9) to avoid DOIs and technical specs
    pattern1 = r'\b([1-9]\.[0-9](?:\.[0-9]+)?)\s+([A-Z][A-Za-z\s]{3,50}?)(?:\s|$|\.|\n)'
    matches1 = re.finditer(pattern1, text)
    for match in matches1:
        num = match.group(1)
        title = match.group(2).strip()
        
        # Skip if looks like technical specs (GHz, MHz, etc.) or DOIs
        if any(skip in title for skip in ['Hz', 'DOI', 'IEEE', 'Vol', 'pp', 'GMAC', 'Gaussian']):
            continue
        
        # Clean up title - remove trailing punctuation and extra words
        title = re.sub(r'\s+(and|the|of|in|for|with|to)\s*$', '', title, flags=re.IGNORECASE)
        
        # Must have at least one lowercase letter (not all caps abbreviation)
        if len(title) >= 3 and any(c.islower() for c in title):
            if not any(skip in title.lower() for skip in ['fig', 'table', 'equation', 'section', 'page']):
                level = num.count('.') + 1
                if level == 1:
                    sections.append({'number': num, 'title': title, 'level': 1})
                else:
                    subsections.append(f"{num}: {title}")
    
    # Pattern 2: Roman numerals (I. Title, II. Title)
    pattern2 = r'\b([IVX]+)\.\s+([A-Z][A-Za-z\s]{2,50}?)(?:\s|$|\.)'
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        title = match.group(2).strip()
        title = re.sub(r'\s+(and|the|of|in|for|with|to)\s*$', '', title, flags=re.IGNORECASE)
        if len(title) >= 3:
            sections.append({'number': match.group(1), 'title': title, 'level': 1})
    
    # Pattern 3: Look for subsection patterns in concatenated text (e.g., "4.1Introduction")
    pattern3 = r'\b([0-9]+\.[0-9]+)([A-Z][a-z]{3,}(?:[A-Z][a-z]+)*)'
    matches3 = re.finditer(pattern3, text)
    for match in matches3:
        num = match.group(1)
        title = match.group(2)
        # Add spaces before capital letters
        title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
        if len(title) >= 3:
            subsections.append(f"{num}: {title}")
    
    # Also look for common section keywords
    keyword_sections = []
    for keyword in ['Abstract', 'Introduction', 'Background', 'Related Work', 
                    'Methodology', 'Method', 'Approach', 'Experiments', 'Results',
                    'Discussion', 'Conclusion', 'References', 'Acknowledgment']:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            keyword_sections.append(keyword)
    
    # Deduplicate subsections
    subsections = list(dict.fromkeys(subsections))
    
    return {
        'sections': sections,
        'subsections': subsections,
        'keyword_sections': keyword_sections,
        'num_sections': len(sections),
        'num_subsections': len(subsections)
    }

def analyze_paper(pdf_path: str) -> Optional[Dict]:
    """Analyze a single paper and extract patterns."""
    try:
        paper_id = os.path.basename(pdf_path).replace('.pdf', '')
        
        # Extract text with pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
        
        if not text or len(text) < 500:
            return None
        
        # Clean text
        text = clean_pdf_text(text)
        
        # Extract patterns
        patterns = extract_sections_and_subsections(text)
        
        # Count words
        word_count = len(text.split())
        
        return {
            'paper_id': paper_id,
            'word_count': word_count,
            'sections': patterns['sections'],
            'subsections': patterns['subsections'],
            'keyword_sections': patterns['keyword_sections'],
            'num_sections': patterns['num_sections'],
            'num_subsections': patterns['num_subsections']
        }
    
    except Exception as e:
        print(f"  Error processing {pdf_path}: {str(e)[:100]}")
        return None

def main():
    print("=" * 60)
    print("IEEE Pattern Analyzer - Sample Analysis")
    print("=" * 60)
    
    # Get all PDF files
    pdf_files = [os.path.join(PDF_FOLDER, f) for f in os.listdir(PDF_FOLDER) 
                 if f.endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} total PDFs")
    
    # Sample random papers
    sample_size = min(SAMPLE_SIZE, len(pdf_files))
    sampled_pdfs = random.sample(pdf_files, sample_size)
    print(f"Analyzing {sample_size} random papers...\n")
    
    # Analyze papers
    results = []
    for i, pdf_path in enumerate(sampled_pdfs, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{sample_size}")
        
        result = analyze_paper(pdf_path)
        if result:
            results.append(result)
    
    print(f"\nSuccessfully analyzed {len(results)} papers")
    
    # Aggregate statistics
    subsection_counter = Counter()
    section_keyword_counter = Counter()
    total_subsections = 0
    
    for r in results:
        for subsec in r['subsections']:
            subsection_counter[subsec] += 1
            total_subsections += 1
        for keyword in r['keyword_sections']:
            section_keyword_counter[keyword] += 1
    
    # Generate summary
    summary = {
        'sample_info': {
            'total_pdfs_available': len(pdf_files),
            'sample_size': sample_size,
            'successfully_analyzed': len(results)
        },
        'statistics': {
            'avg_word_count': sum(r['word_count'] for r in results) / len(results) if results else 0,
            'avg_sections': sum(r['num_sections'] for r in results) / len(results) if results else 0,
            'avg_subsections': sum(r['num_subsections'] for r in results) / len(results) if results else 0,
            'total_unique_subsections': len(subsection_counter)
        },
        'common_section_keywords': [
            {
                'keyword': keyword,
                'frequency': count,
                'percentage': round(count / len(results) * 100, 1)
            }
            for keyword, count in section_keyword_counter.most_common(20)
        ],
        'common_subsection_patterns': [
            {
                'subsection': pattern,
                'frequency': count,
                'percentage': round(count / len(results) * 100, 1)
            }
            for pattern, count in subsection_counter.most_common(100)
        ]
    }
    
    # Write outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Write detailed results
    with open(os.path.join(OUTPUT_DIR, 'sample_analysis_details.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    # Write summary
    summary_path = os.path.join(OUTPUT_DIR, 'sample_analysis_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print("=" * 60)
    print(f"\nAnalyzed {len(results)} papers")
    print(f"Average word count: {summary['statistics']['avg_word_count']:.0f}")
    print(f"Average sections: {summary['statistics']['avg_sections']:.1f}")
    print(f"Average subsections: {summary['statistics']['avg_subsections']:.1f}")
    print(f"Total unique subsection patterns: {summary['statistics']['total_unique_subsections']}")
    
    print(f"\nTop 10 Section Keywords:")
    for item in summary['common_section_keywords'][:10]:
        print(f"  {item['keyword']}: {item['frequency']} papers ({item['percentage']}%)")
    
    print(f"\nTop 20 Subsection Patterns:")
    for item in summary['common_subsection_patterns'][:20]:
        print(f"  {item['subsection']}: {item['frequency']} papers ({item['percentage']}%)")
    
    print(f"\nOutputs written to:")
    print(f"  - {summary_path}")
    print(f"  - {os.path.join(OUTPUT_DIR, 'sample_analysis_details.json')}")
    print("=" * 60)

if __name__ == '__main__':
    main()
