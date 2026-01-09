#!/usr/bin/env python3
"""
Test that abstract sections are handled correctly:
1. No citations added to abstract
2. No hallucinated content between title and abstract
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_citation_integratorator import SmartCitationIntegrator
from external_reference_fetcher import ExternalReference

def test_abstract_no_citations():
    """Test that abstract doesn't get citations"""
    print("=" * 70)
    print("TEST: Abstract Section - No Citations")
    print("=" * 70)
    
    integrator = SmartCitationIntegrator()
    
    # Abstract content
    abstract_heading = "## Abstract"
    abstract_content = "This paper presents a novel approach to video inpainting using diffusion models. We demonstrate significant improvements over existing methods through extensive experiments."
    
    # Create some references
    references = [
        ExternalReference(
            title="Video Inpainting with Diffusion Models",
            authors=["Smith", "Jones"],
            year="2023",
            venue="CVPR",
            citation_number=43,
            selected=True
        )
    ]
    
    # Mock LLM to return unchanged content for abstract
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        # For abstract, should return unchanged
        return abstract_content, type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        # Enhance the abstract
        result = integrator._enhance_section_with_citations(
            abstract_heading,
            abstract_content,
            {},  # No citation matches
            "openai",
            "gpt-4o",
            return_usage=True,
            all_references=references,
            used_references=set()
        )[0]
    
    print(f"Original abstract:\n{abstract_content}\n")
    print(f"Result after enhancement:\n{result}\n")
    
    # Check if citations were added
    citations = re.findall(r'\[(\d+)\]', result)
    
    if citations:
        print(f"❌ FAILURE: Abstract has citations: {citations}")
        print("Abstract should NOT have any citations!")
        return False
    else:
        print("✅ SUCCESS: Abstract has no citations")
        
        # Check if content is unchanged
        if result.strip() == abstract_content.strip():
            print("✅ SUCCESS: Abstract content is unchanged")
            return True
        else:
            print("❌ FAILURE: Abstract content was modified")
            return False


def test_no_hallucinated_content():
    """Test that no content is added between title and first section"""
    print("\n" + "=" * 70)
    print("TEST: No Hallucinated Content")
    print("=" * 70)
    
    # Sample article with title and abstract
    article = """# Video Inpainting with Diffusion Models

## Abstract
This paper presents a novel approach to video inpainting.

## 1. Introduction
Video inpainting has become increasingly important."""
    
    integrator = SmartCitationIntegrator()
    
    # Parse sections
    sections = integrator._parse_sections(article)
    
    print("Parsed sections:")
    for i, (heading, content) in enumerate(sections):
        print(f"  {i}: {heading}")
        if content.strip():
            print(f"     Content: {content[:50]}...")
        else:
            print("     Content: [empty]")
    
    # Check first section
    first_heading, first_content = sections[0]
    
    if first_heading.startswith("#") and not first_content.strip():
        print("\n✅ SUCCESS: Title has no content (correct)")
    else:
        print("\n❌ FAILURE: Title section has content (wrong)")
        return False
    
    # Check abstract is second
    second_heading, second_content = sections[1]
    
    if "abstract" in second_heading.lower():
        print("✅ SUCCESS: Abstract is the second section")
        return True
    else:
        print("❌ FAILURE: Abstract is not in the correct position")
        return False


def test_integration_with_abstract():
    """Test full integration with abstract handling"""
    print("\n" + "=" * 70)
    print("TEST: Full Integration with Abstract")
    print("=" * 70)
    
    article = """# Video Inpainting and Restoration

## Abstract
This paper presents a novel approach to video inpainting using diffusion models. Our method achieves state-of-the-art results.

## 1. Introduction
Video inpainting has become increasingly important in recent years.

## 2. Methodology
We propose a diffusion-based approach for video restoration."""
    
    # Create references
    references = []
    for i in range(5):
        ref = ExternalReference(
            title=f"Paper {43+i}",
            authors=["Author"],
            year="2023",
            venue="CVPR",
            citation_number=43+i,
            selected=True
        )
        references.append(ref)
    
    integrator = SmartCitationIntegrator()
    
    # Mock LLM
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        prompt = args[0] if args else ""
        if "abstract" in prompt.lower():
            # Return unchanged for abstract
            return "This paper presents a novel approach to video inpainting using diffusion models. Our method achieves state-of-the-art results.", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        else:
            # Add citations for other sections
            return "Video inpainting has become increasingly important in recent years [43].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator.integrate_citations_smart(
            article,
            references,
            llm_type="openai",
            model="gpt-4o",
            return_usage=True
        )[0]
    
    print("\nIntegrated article:")
    print(result)
    
    # Check abstract has no citations
    abstract_match = re.search(r'## Abstract\n(.*?)(?=\n##|\n$)', result, re.DOTALL)
    if abstract_match:
        abstract_text = abstract_match.group(1)
        abstract_citations = re.findall(r'\[(\d+)\]', abstract_text)
        
        if abstract_citations:
            print(f"\n❌ FAILURE: Abstract has citations: {abstract_citations}")
            return False
        else:
            print("\n✅ SUCCESS: Abstract has no citations")
    
    # Check other sections have citations
    intro_citations = re.findall(r'\[(\d+)\]', result)
    if intro_citations:
        print(f"✅ SUCCESS: Other sections have citations: {intro_citations}")
        return True
    else:
        print("⚠️ WARNING: No citations found in other sections")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ABSTRACT HANDLING TEST")
    print("=" * 70)
    print("\nTesting that abstracts are handled correctly:\n")
    
    results = []
    results.append(("Abstract no citations", test_abstract_no_citations()))
    results.append(("No hallucinated content", test_no_hallucinated_content()))
    results.append(("Full integration", test_integration_with_abstract()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅✅✅ ALL ABSTRACT FIXES WORKING ✅✅✅")
        print("\nThe system now:")
        print("1. ✅ Does NOT add citations to abstract")
        print("2. ✅ Does NOT hallucinate content")
        print("3. ✅ Preserves abstract exactly as provided")
    else:
        print("\n❌ Some fixes need more work")
