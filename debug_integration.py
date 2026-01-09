#!/usr/bin/env python3
"""
Debug script to test SmartCitationIntegrator
"""

from smart_citation_integratorator import SmartCitationIntegrator
from external_reference_fetcher import ExternalReference

# Create test data
test_refs = [
    ExternalReference(
        citation_number=40,
        title="Video Inpainting with Deep Learning",
        authors=["Smith, J."],
        year=2024,
        venue="CVPR",
        abstract="We propose a novel method for video inpainting..."
    )
]

test_article = """
## Methods
Our approach uses deep learning for video inpainting.

## Results
We achieve state-of-the-art performance.

## Background
Video inpainting is an important problem.
"""

print("Testing SmartCitationIntegrator...")
print("="*50)

try:
    integrator = SmartCitationIntegrator()
    
    # Test the integrate_citations_smart method
    result = integrator.integrate_citations_smart(
        article_text=test_article,
        references=test_refs,
        llm_type="openai",
        model="gpt-4o-mini"
    )
    
    print("✅ Integration successful!")
    print("\nResult:")
    print(result[:500] + "..." if len(result) > 500 else result)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
