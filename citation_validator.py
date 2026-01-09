#!/usr/bin/env python3
"""
Citation Validator - Prevents invalid citations in articles
"""

import re
from typing import List, Dict, Tuple


class CitationValidator:
    """Validates and fixes citation numbers in articles."""
    
    def __init__(self):
        self.invalid_citations = []
        self.valid_citations = set()
    
    def extract_citations_from_text(self, text: str) -> List[int]:
        """Extract all citation numbers from article text."""
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, text)
        return [int(m) for m in matches]
    
    def validate_citations(
        self,
        article_text: str,
        local_citations: List[int],
        external_citations: List[int]
    ) -> Dict:
        """
        Validate all citations in article text.
        
        Returns:
            Dict with validation results
        """
        all_valid = set(local_citations + external_citations)
        article_citations = self.extract_citations_from_text(article_text)
        unique_citations = set(article_citations)
        
        # Find invalid citations
        invalid = [c for c in unique_citations if c not in all_valid]
        
        # Count occurrences
        citation_counts = {}
        for c in article_citations:
            citation_counts[c] = citation_counts.get(c, 0) + 1
        
        return {
            'total_citations': len(article_citations),
            'unique_citations': len(unique_citations),
            'valid_citations': len(all_valid),
            'invalid_citations': invalid,
            'invalid_count': len(invalid),
            'citation_counts': citation_counts,
            'validation_passed': len(invalid) == 0
        }
    
    def fix_invalid_citations(
        self,
        article_text: str,
        local_citations: List[int],
        external_citations: List[int]
    ) -> Tuple[str, List[str]]:
        """
        Remove invalid citations from article text.
        
        Returns:
            Tuple of (fixed_text, removed_citations)
        """
        all_valid = set(local_citations + external_citations)
        removed = []
        
        # Replace invalid citations with empty string
        def replace_invalid(match):
            num = int(match.group(1))
            if num not in all_valid:
                removed.append(str(num))
                return ''
            return match.group(0)
        
        fixed_text = re.sub(r'\[(\d+)\]', replace_invalid, article_text)
        
        # Clean up double spaces and extra brackets
        fixed_text = re.sub(r'\s+', ' ', fixed_text)
        fixed_text = re.sub(r'\[\s*\]', '', fixed_text)
        
        return fixed_text, removed


def check_external_reference_ratio(
    local_count: int,
    external_count: int,
    target_ratio: float = 0.4
) -> Dict:
    """
    Check if external reference ratio meets target.
    
    Args:
        local_count: Number of local references
        external_count: Number of external references
        target_ratio: Target ratio of external/(local+external)
    
    Returns:
        Dict with ratio analysis
    """
    total = local_count + external_count
    
    if total == 0:
        return {
            'ratio': 0.0,
            'meets_target': False,
            'message': 'No references found'
        }
    
    actual_ratio = external_count / total
    
    return {
        'ratio': actual_ratio,
        'target_ratio': target_ratio,
        'meets_target': actual_ratio >= target_ratio,
        'message': f'External ratio: {actual_ratio:.1%} (target: {target_ratio:.1%})',
        'need_more_external': actual_ratio < target_ratio
    }
