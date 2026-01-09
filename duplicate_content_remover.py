#!/usr/bin/env python3
"""
Duplicate Content Remover - Detects and removes duplicate sections
"""

import re
from typing import List, Tuple, Dict


class DuplicateContentRemover:
    """Detects and removes duplicate content in articles."""
    
    def __init__(self):
        self.duplicates_found = []
    
    def find_duplicate_sections(self, text: str) -> List[Dict]:
        """
        Find duplicate sections in article text.
        
        Returns:
            List of duplicate sections with positions
        """
        lines = text.split('\n')
        duplicates = []
        
        # Track seen sections
        seen_sections = {}
        
        for i, line in enumerate(lines):
            # Skip empty lines and citations
            if not line.strip() or line.strip().startswith('['):
                continue
            
            # Check for headers
            if line.startswith('#'):
                # Extract header content
                header_content = line.strip()
                
                if header_content in seen_sections:
                    # Found duplicate
                    original_pos = seen_sections[header_content]
                    duplicates.append({
                        'type': 'duplicate_header',
                        'content': header_content,
                        'original_line': original_pos,
                        'duplicate_line': i,
                        'original_text': lines[original_pos],
                        'duplicate_text': line
                    })
                else:
                    seen_sections[header_content] = i
            
            # Check for duplicate paragraphs (non-header lines)
            elif len(line.strip()) > 20:  # Only check substantial lines
                # Normalize for comparison
                normalized = re.sub(r'\s+', ' ', line.strip().lower())
                
                # Check against seen paragraphs
                for seen_line, seen_pos in seen_sections.items():
                    if not seen_line.startswith('#'):
                        seen_normalized = re.sub(r'\s+', ' ', seen_line.strip().lower())
                        if normalized == seen_normalized:
                            duplicates.append({
                                'type': 'duplicate_paragraph',
                                'content': line[:100] + '...',
                                'original_line': seen_pos,
                                'duplicate_line': i,
                                'original_text': seen_line,
                                'duplicate_text': line
                            })
                            break
                else:
                    seen_sections[line] = i
        
        self.duplicates_found = duplicates
        return duplicates
    
    def remove_duplicates(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Remove duplicate content from text.
        
        Returns:
            Tuple of (cleaned_text, removed_duplicates)
        """
        duplicates = self.find_duplicate_sections(text)
        lines = text.split('\n')
        lines_to_remove = set()
        
        # Mark duplicates for removal (keep first occurrence)
        for dup in duplicates:
            lines_to_remove.add(dup['duplicate_line'])
        
        # Build cleaned text
        cleaned_lines = []
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Clean up extra whitespace
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
        
        return cleaned_text, duplicates
    
    def analyze_article_structure(self, text: str) -> Dict:
        """
        Analyze article structure for issues.
        
        Returns:
            Dict with structure analysis
        """
        lines = text.split('\n')
        
        # Count different elements
        headers = [line for line in lines if line.strip().startswith('#')]
        paragraphs = [line for line in lines if line.strip() and not line.strip().startswith('#') and len(line.strip()) > 10]
        citations = re.findall(r'\[\d+\]', text)
        
        # Check for multiple titles
        titles = [h for h in headers if h.startswith('# ')]
        
        return {
            'total_lines': len(lines),
            'header_count': len(headers),
            'paragraph_count': len(paragraphs),
            'citation_count': len(citations),
            'multiple_titles': len(titles) > 1,
            'title_count': len(titles),
            'titles': titles
        }
