#!/usr/bin/env python3
"""
Utilities for filtering external references
"""

import re
from typing import List
from external_reference_fetcher import ExternalReference


def is_generic_title(title: str) -> bool:
    """Check if title is too generic to be useful."""
    generic_patterns = [
        r'\b(concepts|introduction|overview|review|survey|advances|recent|new|novel)\b',
        r'\b(studies|research|analysis|investigation|exploration)\b',
        r'\b(systems|methods|techniques|approaches|frameworks)\b',
        r'\b(intelligent|smart|advanced|modern|contemporary)\b',
        r'\b(computer|vision|image|video|processing|analysis)\b'
    ]
    
    title_lower = title.lower()
    
    # Check if title is too short
    if len(title.split()) < 4:
        return True
    
    # Check for generic patterns
    for pattern in generic_patterns:
        if re.search(pattern, title_lower):
            # Only consider generic if not combined with specific terms
            specific_terms = ['inpainting', 'restoration', 'enhancement', 'super-resolution', 'denoising']
            if not any(term in title_lower for term in specific_terms):
                return True
    
    return False


def apply_dynamic_filters(
    references: List[ExternalReference],
    min_relevance: float = 0.3,
    require_abstract: bool = True,
    exclude_generic: bool = True,
    min_year: int = 2018,
    venue_types: List[str] = None
) -> List[ExternalReference]:
    """
    Apply dynamic filters to reference list.
    
    Returns:
        Filtered list and filter log
    """
    if venue_types is None:
        venue_types = ["Conference", "Journal"]
    
    original_count = len(references)
    filtered_refs = []
    filter_log = {
        'original_count': original_count,
        'filters_applied': {
            'min_relevance': 0,
            'no_abstract': 0,
            'generic_title': 0,
            'too_old': 0,
            'wrong_venue_type': 0
        }
    }
    
    for ref in references:
        # Check relevance score
        if ref.relevance_score < min_relevance:
            filter_log['filters_applied']['min_relevance'] += 1
            continue
        
        # Check abstract
        if require_abstract and not ref.abstract:
            filter_log['filters_applied']['no_abstract'] += 1
            continue
        
        # Check generic title
        if exclude_generic and is_generic_title(ref.title or ""):
            filter_log['filters_applied']['generic_title'] += 1
            continue
        
        # Check year
        if ref.year and ref.year < min_year:
            filter_log['filters_applied']['too_old'] += 1
            continue
        
        # Check venue type
        if venue_types:
            venue = (ref.venue or "").lower()
            venue_match = False
            for vtype in venue_types:
                if vtype.lower() in venue:
                    venue_match = True
                    break
            if not venue_match:
                filter_log['filters_applied']['wrong_venue_type'] += 1
                continue
        
        # Passed all filters
        filtered_refs.append(ref)
    
    filter_log['final_count'] = len(filtered_refs)
    filter_log['retained_percentage'] = (len(filtered_refs) / original_count * 100) if original_count > 0 else 0
    
    return filtered_refs, filter_log
