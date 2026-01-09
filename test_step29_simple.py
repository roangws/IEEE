#!/usr/bin/env python3
"""
Simple test for Step 2.9 Integration without usage tracking
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_citation_integratorator import SmartCitationIntegrator
from external_reference_fetcher import ExternalReference
from citation_manager import CitationManager


def create_test_article():
    """Create a test article with internal citations."""
    return """# Video Inpainting Test

## Abstract
Video inpainting is a challenging task in computer vision [1].

## 1. Introduction
Recent advances in diffusion models have improved video inpainting [2, 3].

## 2. Method
Our approach uses temporal attention mechanisms [4, 5].

## References
[1] Internal ref 1
[2] Internal ref 2
[3] Internal ref 3
[4] Internal ref 4
[5] Internal ref 5
"""


def create_test_external_references():
    """Create 5 test external references."""
    references = []
    
    for i in range(6, 11):  # Numbers 6-10
        ref = ExternalReference(
            title=f"External Paper {i}: Video Inpainting Methods",
            authors=[f"Author {i}"],
            year=2023,
            venue="CVPR 2023",
            citation_number=i,
            abstract=f"This paper presents novel video inpainting techniques using diffusion models."
        )
        ref.selected = True
        references.append(ref)
    
    return references


def main():
    """Run simple integration test."""
    print("="*60)
    print("SIMPLE STEP 2.9 INTEGRATION TEST")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    print(f"Article has {len(article)} characters")
    print(f"External references: {len(refs)}")
    
    # Extract original citations
    cm = CitationManager()
    original_citations = cm.extract_citations_from_article(article)
    print(f"Original citations: {sorted(original_citations)}")
    
    # Run integration
    print("\nRunning integration with Ollama...")
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    # Run without usage tracking to avoid the error
    enhanced = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=False,  # Don't track usage for Ollama
        progress_callback=progress_callback
    )
    
    # Check results
    enhanced_citations = cm.extract_citations_from_article(enhanced)
    print(f"\nEnhanced citations: {sorted(enhanced_citations)}")
    
    # Check if external citations were added
    external_citations = [c for c in enhanced_citations if c > 5]
    print(f"External citations added: {len(external_citations)}")
    
    # Check utilization
    utilization = len(external_citations) / len(refs) * 100
    print(f"Utilization: {utilization:.1f}%")
    
    # Show part of enhanced article
    print("\n" + "="*60)
    print("ENHANCED ARTICLE PREVIEW:")
    print("="*60)
    print(enhanced[:500] + "..." if len(enhanced) > 500 else enhanced)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
