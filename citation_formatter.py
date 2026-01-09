#!/usr/bin/env python3
"""
Citation Formatter
Creates proper academic citations and reference lists.
"""

import json
import os


class CitationFormatter:
    """Handles citation formatting for academic articles."""
    
    def __init__(self, metadata_file="pdf_metadata.json"):
        """
        Initialize citation formatter.
        
        Args:
            metadata_file: Path to JSON file with PDF metadata
        """
        self.metadata = {}
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
    
    def format_in_text_citation(self, filename, citation_number):
        """
        Format in-text citation.
        
        Args:
            filename: PDF filename
            citation_number: Citation number
            
        Returns:
            Formatted in-text citation
        """
        meta = self.metadata.get(filename, {})
        authors = meta.get('authors', 'Unknown')
        year = meta.get('year', 'n.d.')
        
        # Format: [1] or [Author, Year]
        return f"[{citation_number}]"
    
    def format_reference(self, filename, citation_number):
        """
        Format full reference entry.
        
        Args:
            filename: PDF filename
            citation_number: Citation number
            
        Returns:
            Formatted reference entry
        """
        meta = self.metadata.get(filename, {})
        
        title = meta.get('title', f'Document {filename}')
        authors = meta.get('authors', 'Unknown Authors')
        year = meta.get('year', 'n.d.')
        doi = meta.get('doi', None)
        
        # IEEE citation style
        reference = f"[{citation_number}] {authors}, \"{title},\" {year}."
        
        if doi:
            reference += f" DOI: {doi}"
        
        return reference
    
    def create_reference_list(self, sources):
        """
        Create a complete reference list from sources.
        
        Args:
            sources: List of source dictionaries with 'filename' key
            
        Returns:
            Formatted reference list string
        """
        # Get unique sources
        unique_sources = {}
        for source in sources:
            filename = source['filename']
            if filename not in unique_sources:
                unique_sources[filename] = source
        
        # Sort by filename for consistency
        sorted_sources = sorted(unique_sources.items())
        
        # Create reference list
        references = []
        references.append("\n## References\n")
        
        for i, (filename, source) in enumerate(sorted_sources, 1):
            ref = self.format_reference(filename, i)
            references.append(f"{ref}\n")
        
        return "\n".join(references)
    
    def create_citation_mapping(self, sources):
        """
        Create mapping of filenames to citation numbers.
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            Dictionary mapping filename to citation number
        """
        unique_sources = {}
        for source in sources:
            filename = source['filename']
            if filename not in unique_sources:
                unique_sources[filename] = len(unique_sources) + 1
        
        return unique_sources
    
    def get_source_info(self, filename):
        """
        Get formatted source information for display.
        
        Args:
            filename: PDF filename
            
        Returns:
            Formatted source info string
        """
        meta = self.metadata.get(filename, {})
        
        title = meta.get('title', filename)
        authors = meta.get('authors', 'Unknown')
        year = meta.get('year', 'n.d.')
        
        return f"{title} ({authors}, {year})"


def test_formatter():
    """Test the citation formatter."""
    formatter = CitationFormatter()
    
    print("="*70)
    print("CITATION FORMATTER TEST")
    print("="*70)
    
    # Test with sample sources
    sample_sources = [
        {'filename': '10937696.pdf'},
        {'filename': '10934994.pdf'},
        {'filename': '10934995.pdf'}
    ]
    
    print("\n### In-text Citations:")
    citation_map = formatter.create_citation_mapping(sample_sources)
    for filename, num in citation_map.items():
        print(f"{filename} -> {formatter.format_in_text_citation(filename, num)}")
    
    print("\n### Reference List:")
    ref_list = formatter.create_reference_list(sample_sources)
    print(ref_list)
    
    print("\n### Source Info:")
    for filename in citation_map.keys():
        print(f"- {formatter.get_source_info(filename)}")


if __name__ == '__main__':
    test_formatter()
