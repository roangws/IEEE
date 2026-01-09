#!/usr/bin/env python3
"""
Bench test for Step 3 integration to verify OpenAI API is working correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/roan-aparavi/aparavi-repo/Roan-IEEE')

from external_integrator import ExternalIntegrator
from external_reference_fetcher import ExternalReference
from config import call_openai

# Test article text (simplified)
TEST_ARTICLE = """# Machine Learning in Healthcare

## Abstract
This article explores the applications of machine learning in healthcare.

## Introduction
Machine learning has revolutionized healthcare by enabling predictive analytics and personalized treatment plans. Recent advances in deep learning have shown promising results in medical imaging and diagnosis.

## Methodology
Various machine learning algorithms including neural networks, decision trees, and support vector machines have been applied to healthcare datasets. These methods process patient data to identify patterns and make predictions.

## Results
Studies have shown that machine learning models can achieve high accuracy in disease prediction and diagnosis. Performance metrics indicate significant improvements over traditional statistical methods.

## Conclusion
Machine learning continues to transform healthcare delivery and patient outcomes.
"""

# Test external reference
TEST_EXTERNAL_REF = ExternalReference(
    citation_number=63,
    title="Deep Learning for Medical Image Analysis",
    authors=["Smith, J.", "Johnson, A."],
    year=2023,
    venue="IEEE Transactions on Medical Imaging",
    journal="IEEE Trans. Med. Imaging",
    publisher="IEEE",
    abstract="This paper presents a comprehensive survey of deep learning techniques applied to medical image analysis, including segmentation, classification, and detection tasks.",
    doi="10.1109/TMI.2023.12345",
    url="https://ieeexplore.ieee.org/document/12345",
    relevance_score=0.95,
    selected=True
)

def test_openai_api():
    """Test basic OpenAI API call."""
    print("=" * 60)
    print("TEST 1: Basic OpenAI API Call")
    print("=" * 60)
    
    try:
        response = call_openai(
            "Say 'API test successful' if you can read this.",
            model="gpt-4o-mini",
            max_tokens=50
        )
        print(f"✅ SUCCESS: {response}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_section_parsing():
    """Test section parsing."""
    print("\n" + "=" * 60)
    print("TEST 2: Section Parsing")
    print("=" * 60)
    
    integrator = ExternalIntegrator()
    sections = integrator.parse_sections(TEST_ARTICLE)
    
    print(f"Found {len(sections)} sections:")
    for i, (heading, heading_text, content) in enumerate(sections, 1):
        content_preview = content[:100] + "..." if len(content) > 100 else content
        print(f"  {i}. {heading} {heading_text}")
        print(f"     Content: {content_preview}")
    
    return len(sections) > 0

def test_section_integration():
    """Test integrating external refs into a single section."""
    print("\n" + "=" * 60)
    print("TEST 3: Section Integration with OpenAI")
    print("=" * 60)
    
    integrator = ExternalIntegrator()
    
    # Test on Introduction section
    test_heading = "##"
    test_heading_text = "Introduction"
    test_content = """Machine learning has revolutionized healthcare by enabling predictive analytics and personalized treatment plans. Recent advances in deep learning have shown promising results in medical imaging and diagnosis."""
    
    print(f"Integrating external ref [63] into '{test_heading_text}' section...")
    print(f"Using OpenAI model: gpt-4o-mini")
    
    try:
        enhanced = integrator.integrate_section(
            heading=test_heading,
            heading_text=test_heading_text,
            section_content=test_content,
            relevant_refs=[TEST_EXTERNAL_REF],
            llm_type="openai",
            model="gpt-4o-mini"
        )
        
        print(f"\n✅ SUCCESS: Section enhanced")
        print(f"\nOriginal length: {len(test_content)} chars")
        print(f"Enhanced length: {len(enhanced)} chars")
        print(f"\nEnhanced section preview:")
        print("-" * 60)
        print(enhanced[:500])
        print("-" * 60)
        
        # Check if citation was added
        if "[63]" in enhanced:
            print("\n✅ Citation [63] successfully added to section")
        else:
            print("\n⚠️ WARNING: Citation [63] not found in enhanced section")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_full_integration():
    """Test full article integration."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Article Integration")
    print("=" * 60)
    
    integrator = ExternalIntegrator()
    
    def progress_callback(section_num, total_sections, section_name):
        print(f"  [{section_num}/{total_sections}] Processing: {section_name}")
    
    try:
        enhanced_article = integrator.integrate_external_refs(
            article_text=TEST_ARTICLE,
            external_refs=[TEST_EXTERNAL_REF],
            llm_type="openai",
            model="gpt-4o-mini",
            progress_callback=progress_callback
        )
        
        print(f"\n✅ SUCCESS: Full integration complete")
        print(f"\nOriginal length: {len(TEST_ARTICLE)} chars")
        print(f"Enhanced length: {len(enhanced_article)} chars")
        
        if enhanced_article == TEST_ARTICLE:
            print("\n⚠️ WARNING: Article unchanged after integration")
            return False
        else:
            print("\n✅ Article was modified during integration")
            
            # Count citations added
            citation_count = enhanced_article.count("[63]")
            print(f"✅ Citation [63] appears {citation_count} time(s) in enhanced article")
            
            return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("STEP 3 INTEGRATION BENCH TEST")
    print("=" * 60)
    print(f"Testing OpenAI API integration for external references")
    print(f"Model: gpt-4o-mini")
    print("=" * 60)
    
    results = {
        "Basic API Call": test_openai_api(),
        "Section Parsing": test_section_parsing(),
        "Section Integration": test_section_integration(),
        "Full Integration": test_full_integration()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - OpenAI API is working correctly")
        print("Step 3 integration should work in the Streamlit app.")
    else:
        print("❌ SOME TESTS FAILED - There is an issue with the integration")
        print("Check the error messages above for details.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
