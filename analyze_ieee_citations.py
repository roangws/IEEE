#!/usr/bin/env python3
"""
IEEE Citation Format Analyzer
Extracts and analyzes citation patterns from IEEE papers to replicate exact format.
"""

import fitz
import re
from pathlib import Path
import json


def extract_citations_from_ieee_paper(pdf_path):
    """
    Extract citation patterns from an IEEE paper.
    
    Args:
        pdf_path: Path to IEEE PDF
        
    Returns:
        Dictionary with citation analysis
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        # Extract text from all pages
        for page in doc:
            full_text += page.get_text()
        
        doc.close()
        
        # Find in-text citations
        # IEEE uses [1], [2], [3] or [1]-[3] or [1], [2]
        in_text_citations = re.findall(r'\[(\d+(?:[-,]\s*\d+)*)\]', full_text)
        
        # Find References section
        ref_match = re.search(r'(?:REFERENCES|References)\s*\n(.*?)(?:\n\n\n|\Z)', full_text, re.DOTALL | re.IGNORECASE)
        
        references = []
        if ref_match:
            ref_section = ref_match.group(1)
            
            # IEEE reference format: [1] Author(s), "Title," Journal/Conference, details.
            ref_pattern = r'\[(\d+)\]\s*([^\n]+(?:\n(?!\[\d+\])[^\n]+)*)'
            ref_matches = re.findall(ref_pattern, ref_section)
            
            for num, ref_text in ref_matches:
                references.append({
                    'number': int(num),
                    'text': ref_text.strip()
                })
        
        return {
            'filename': Path(pdf_path).name,
            'in_text_citations': in_text_citations[:20],  # Sample
            'total_citations': len(set(in_text_citations)),
            'references': references[:10],  # Sample first 10
            'total_references': len(references)
        }
        
    except Exception as e:
        return {
            'filename': Path(pdf_path).name,
            'error': str(e)
        }


def analyze_ieee_citation_patterns(pdf_dir="test_pdfs_100", num_samples=10):
    """
    Analyze citation patterns from multiple IEEE papers.
    
    Args:
        pdf_dir: Directory with IEEE PDFs
        num_samples: Number of papers to analyze
        
    Returns:
        Analysis results
    """
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))[:num_samples]
    
    print(f"Analyzing {len(pdf_files)} IEEE papers for citation patterns...")
    print("="*70)
    
    results = []
    
    for pdf_path in pdf_files:
        print(f"\nAnalyzing: {pdf_path.name}")
        result = extract_citations_from_ieee_paper(pdf_path)
        results.append(result)
        
        if 'error' not in result:
            print(f"  In-text citations: {result['total_citations']}")
            print(f"  References: {result['total_references']}")
    
    return results


def document_ieee_format(results):
    """
    Document the IEEE citation format based on analysis.
    
    Args:
        results: Analysis results from multiple papers
    """
    print("\n" + "="*70)
    print("IEEE CITATION FORMAT DOCUMENTATION")
    print("="*70)
    
    print("\n## IN-TEXT CITATION FORMAT")
    print("-"*70)
    print("IEEE uses NUMBERED citations in square brackets:")
    print("  - Single citation: [1]")
    print("  - Multiple citations: [1], [2], [5]")
    print("  - Range: [1]-[5]")
    print("  - Mixed: [1], [3]-[5], [7]")
    print("\nExamples from papers:")
    
    for result in results[:3]:
        if 'error' not in result and result['in_text_citations']:
            print(f"\n  {result['filename']}:")
            for cite in result['in_text_citations'][:5]:
                print(f"    [{cite}]")
    
    print("\n## REFERENCE LIST FORMAT")
    print("-"*70)
    print("IEEE reference format:")
    print("  [Number] Author(s), \"Title,\" Publication, vol., no., pp., Month Year.")
    print("\nExamples from papers:")
    
    for result in results[:3]:
        if 'error' not in result and result['references']:
            print(f"\n  {result['filename']}:")
            for ref in result['references'][:3]:
                print(f"    [{ref['number']}] {ref['text'][:100]}...")
    
    print("\n## KEY OBSERVATIONS")
    print("-"*70)
    print("1. Citations are ALWAYS in square brackets [1]")
    print("2. Citations appear AFTER the sentence/clause, before punctuation")
    print("3. Multiple citations are comma-separated: [1], [2], [3]")
    print("4. References are numbered in ORDER OF APPEARANCE in text")
    print("5. Reference format: [N] Authors, \"Title,\" Publication, details.")
    print("6. NO author names in in-text citations (only numbers)")
    print("7. NO year in in-text citations (only in reference list)")
    
    print("\n## INCORRECT FORMATS TO AVOID")
    print("-"*70)
    print("❌ (Author, Year) - This is APA, not IEEE")
    print("❌ Author [1] - IEEE puts citation after, not with author name")
    print("❌ [Source 1] - Use numbers only, not 'Source'")
    print("❌ Notes like '(Note: This article cites...)' - Never add these")


def create_ieee_citation_template():
    """Create a template for proper IEEE citations."""
    template = """
# IEEE CITATION FORMAT TEMPLATE

## In-Text Citation Rules:
1. Use square brackets with numbers: [1]
2. Place AFTER the relevant text, BEFORE punctuation
3. Multiple citations: [1], [2], [5]
4. Ranges: [1]-[5]
5. NO author names in text (only in reference list)

## Reference List Format:
[1] A. Author, B. Author, and C. Author, "Article title," Journal Name, 
    vol. X, no. Y, pp. ZZ-ZZ, Month Year, doi: XX.XXXX/XXXXX.

[2] A. Author and B. Author, "Conference paper title," in Proc. Conference 
    Name, City, Country, Year, pp. ZZ-ZZ.

[3] A. Author, Book Title. City: Publisher, Year.

## Example Article Structure:

Recent advances in machine learning [1] have enabled new approaches to 
code analysis [2], [3]. Various techniques have been proposed [4]-[7], 
with deep learning methods showing particular promise [8].

## References

[1] J. Smith and A. Jones, "Machine learning for code analysis," IEEE 
    Trans. Software Eng., vol. 45, no. 3, pp. 234-245, Mar. 2023.

[2] B. Chen et al., "Deep learning approaches to program understanding," 
    in Proc. Int. Conf. Software Eng., 2023, pp. 123-134.
"""
    
    with open("ieee_citation_template.txt", "w") as f:
        f.write(template)
    
    print("\n✓ IEEE citation template saved to: ieee_citation_template.txt")


def main():
    """Main analysis function."""
    print("="*70)
    print("IEEE CITATION FORMAT ANALYZER")
    print("="*70)
    
    # Analyze papers
    results = analyze_ieee_citation_patterns(num_samples=10)
    
    # Document format
    document_ieee_format(results)
    
    # Create template
    create_ieee_citation_template()
    
    # Save results
    with open("ieee_citation_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✓ Analysis saved to: ieee_citation_analysis.json")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nIEEE uses a SIMPLE numbered citation system:")
    print("  - In-text: [1], [2], [3]")
    print("  - References: [1] Author, \"Title,\" Publication, details.")
    print("  - Order: Citations numbered by first appearance")
    print("  - NO author names or years in text")
    print("  - NO explanatory notes about citation counts")


if __name__ == '__main__':
    main()
