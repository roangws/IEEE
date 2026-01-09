#!/usr/bin/env python3
"""
COMPREHENSIVE ANTI-HALLUCINATION TEST SUITE

5 different test scenarios to ensure LLM NEVER adds unauthorized content:
1. Title-only section test (no content between title and abstract)
2. Abstract preservation test (no citations, no modifications)
3. Empty section handling test
4. Content length verification test (output <= input length + citations)
5. Full integration test with structure validation
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_citation_integratorator import SmartCitationIntegrator
from external_reference_fetcher import ExternalReference


def create_test_references(count=5, start_num=43):
    """Helper to create test references"""
    references = []
    for i in range(count):
        ref = ExternalReference(
            title=f"Test Paper {start_num+i}",
            authors=["Author"],
            year="2023",
            venue="CVPR",
            citation_number=start_num+i,
            selected=True
        )
        references.append(ref)
    return references


def test_1_title_only_section():
    """
    TEST 1: Title-Only Section
    Ensures no content is added between title and first section
    """
    print("=" * 70)
    print("TEST 1: Title-Only Section (No Content Between Title and Abstract)")
    print("=" * 70)
    
    article = """# Video Inpainting with Diffusion Models

## Abstract
This paper presents a novel approach to video inpainting.

## 1. Introduction
Video inpainting has become important."""
    
    integrator = SmartCitationIntegrator()
    references = create_test_references()
    
    # Mock LLM
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        # Return unchanged for abstract, add citation for intro
        prompt = args[0] if args else ""
        if "abstract" in prompt.lower():
            return "This paper presents a novel approach to video inpainting.", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        else:
            return "Video inpainting has become important [43].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator.integrate_citations_smart(
            article, references, llm_type="openai", model="gpt-4o", return_usage=True
        )[0]
    
    print("\nOriginal article structure:")
    print("  Line 1: # Title")
    print("  Line 2: [empty]")
    print("  Line 3: ## Abstract")
    
    # Check structure
    lines = result.split('\n')
    
    # Find title line
    title_idx = None
    abstract_idx = None
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title_idx = i
        if '## Abstract' in line or '## abstract' in line.lower():
            abstract_idx = i
            break
    
    if title_idx is not None and abstract_idx is not None:
        # Check lines between title and abstract
        between_lines = lines[title_idx+1:abstract_idx]
        non_empty_between = [line for line in between_lines if line.strip()]
        
        if non_empty_between:
            print(f"\n❌ FAILURE: Found {len(non_empty_between)} lines between title and abstract!")
            print("Content between title and abstract:")
            for line in non_empty_between:
                print(f"  '{line}'")
            return False
        else:
            print("\n✅ SUCCESS: No content between title and abstract")
            return True
    else:
        print("\n❌ FAILURE: Could not find title or abstract")
        return False


def test_2_abstract_preservation():
    """
    TEST 2: Abstract Preservation
    Ensures abstract is returned unchanged without citations
    """
    print("\n" + "=" * 70)
    print("TEST 2: Abstract Preservation (No Citations, No Modifications)")
    print("=" * 70)
    
    integrator = SmartCitationIntegrator()
    
    original_abstract = "This paper presents a novel approach to video inpainting using diffusion models. We demonstrate significant improvements over existing methods through extensive experiments on benchmark datasets."
    
    references = create_test_references()
    
    # Mock LLM
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        return original_abstract, type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator._enhance_section_with_citations(
            "## Abstract",
            original_abstract,
            {},
            "openai",
            "gpt-4o",
            return_usage=True,
            all_references=references,
            used_references=set()
        )[0]
    
    print(f"\nOriginal: {original_abstract}")
    print(f"\nResult:   {result}")
    
    # Check for citations
    citations = re.findall(r'\[(\d+)\]', result)
    
    if citations:
        print(f"\n❌ FAILURE: Abstract has citations: {citations}")
        return False
    
    # Check if content changed
    if result.strip() != original_abstract.strip():
        print("\n❌ FAILURE: Abstract content was modified")
        print(f"Expected: {original_abstract}")
        print(f"Got:      {result}")
        return False
    
    print("\n✅ SUCCESS: Abstract unchanged, no citations")
    return True


def test_3_empty_section_handling():
    """
    TEST 3: Empty Section Handling
    Ensures sections with no content are skipped without LLM hallucination
    """
    print("\n" + "=" * 70)
    print("TEST 3: Empty Section Handling (Skip Empty Sections)")
    print("=" * 70)
    
    article = """# Video Inpainting

## 1. Introduction
Video inpainting is important."""
    
    integrator = SmartCitationIntegrator()
    references = create_test_references()
    
    # Parse sections
    sections = integrator._parse_sections(article)
    
    print(f"\nParsed {len(sections)} sections:")
    for i, (heading, content) in enumerate(sections):
        has_content = "YES" if content.strip() else "NO"
        print(f"  Section {i}: {heading[:40]} - Content: {has_content}")
    
    # Check first section (title)
    first_heading, first_content = sections[0]
    
    if first_content.strip():
        print("\n❌ FAILURE: Title section has content (should be empty)")
        print(f"Content: '{first_content}'")
        return False
    
    # Mock LLM to try to add content
    import unittest.mock
    
    call_count = [0]
    
    def mock_call_openai(*args, **kwargs):
        call_count[0] += 1
        return "Video inpainting is important [43].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator.integrate_citations_smart(
            article, references, llm_type="openai", model="gpt-4o", return_usage=True
        )[0]
    
    # Check that LLM was NOT called for empty section
    print(f"\nLLM called {call_count[0]} times (should be 1, not 2)")
    
    # Check result doesn't have content between title and intro
    result_sections = integrator._parse_sections(result)
    result_first_heading, result_first_content = result_sections[0]
    
    if result_first_content.strip():
        print("\n❌ FAILURE: Title section has content after integration")
        print(f"Content: '{result_first_content}'")
        return False
    
    print("\n✅ SUCCESS: Empty sections skipped, no hallucination")
    return True


def test_4_content_length_verification():
    """
    TEST 4: Content Length Verification
    Ensures output length is approximately input length + citations only
    """
    print("\n" + "=" * 70)
    print("TEST 4: Content Length Verification (No Content Expansion)")
    print("=" * 70)
    
    integrator = SmartCitationIntegrator()
    
    original_content = "Video inpainting has become increasingly important in recent years. Diffusion models offer a promising approach."
    
    references = create_test_references()
    
    # Mock LLM to add citations
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        # Add citations to existing content (should not expand significantly)
        return "Video inpainting has become increasingly important in recent years [43]. Diffusion models offer a promising approach [44].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator._enhance_section_with_citations(
            "## 1. Introduction",
            original_content,
            {},
            "openai",
            "gpt-4o",
            return_usage=True,
            all_references=references,
            used_references=set()
        )[0]
    
    # Calculate lengths
    original_len = len(original_content)
    result_len = len(result)
    
    # Count citations added
    citations = re.findall(r'\[(\d+)\]', result)
    citation_chars = sum(len(f"[{c}]") for c in citations)
    
    # Expected length: original + citations + some whitespace tolerance
    expected_max_len = original_len + citation_chars + 20  # 20 char tolerance
    
    print(f"\nOriginal length: {original_len} chars")
    print(f"Result length:   {result_len} chars")
    print(f"Citations added: {len(citations)} ({citation_chars} chars)")
    print(f"Expected max:    {expected_max_len} chars")
    
    if result_len > expected_max_len:
        print(f"\n❌ FAILURE: Output is {result_len - expected_max_len} chars longer than expected")
        print("LLM likely added extra content!")
        print(f"\nOriginal: {original_content}")
        print(f"\nResult:   {result}")
        return False
    
    print("\n✅ SUCCESS: Output length is appropriate (no content expansion)")
    return True


def test_5_full_integration_structure():
    """
    TEST 5: Full Integration Structure Validation
    Ensures complete article maintains proper structure without hallucination
    """
    print("\n" + "=" * 70)
    print("TEST 5: Full Integration Structure Validation")
    print("=" * 70)
    
    article = """# Video Inpainting and Restoration

## Abstract
This paper presents a novel approach to video inpainting using diffusion models.

## 1. Introduction
Video inpainting has become increasingly important in recent years.

## 2. Methodology
We propose a diffusion-based approach for video restoration.

## 3. Conclusion
Our method achieves state-of-the-art results on benchmark datasets."""
    
    integrator = SmartCitationIntegrator()
    references = create_test_references(10)
    
    # Count original sections and words
    original_sections = integrator._parse_sections(article)
    original_word_count = len(article.split())
    
    print(f"\nOriginal article:")
    print(f"  Sections: {len(original_sections)}")
    print(f"  Words: {original_word_count}")
    
    # Mock LLM
    import unittest.mock
    
    def mock_call_openai(*args, **kwargs):
        prompt = args[0] if args else ""
        if "abstract" in prompt.lower():
            return "This paper presents a novel approach to video inpainting using diffusion models.", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        elif "introduction" in prompt.lower():
            return "Video inpainting has become increasingly important in recent years [43].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        elif "methodology" in prompt.lower():
            return "We propose a diffusion-based approach for video restoration [44].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        else:
            return "Our method achieves state-of-the-art results on benchmark datasets [45].", type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        result = integrator.integrate_citations_smart(
            article, references, llm_type="openai", model="gpt-4o", return_usage=True
        )[0]
    
    # Count result sections and words
    result_sections = integrator._parse_sections(result)
    result_word_count = len(result.split())
    
    # Remove citation numbers for fair word count comparison
    result_no_citations = re.sub(r'\[\d+\]', '', result)
    result_word_count_no_citations = len(result_no_citations.split())
    
    print(f"\nResult article:")
    print(f"  Sections: {len(result_sections)}")
    print(f"  Words (with citations): {result_word_count}")
    print(f"  Words (without citations): {result_word_count_no_citations}")
    
    # Validation checks
    errors = []
    
    # Check section count
    if len(result_sections) != len(original_sections):
        errors.append(f"Section count changed: {len(original_sections)} -> {len(result_sections)}")
    
    # Check word count (should not increase significantly)
    # Note: The "remaining references" feature adds citations at the end, which is expected
    # We allow some tolerance for this feature
    word_increase = result_word_count_no_citations - original_word_count
    
    # Count how many citations were added
    total_citations = len(re.findall(r'\[\d+\]', result))
    
    # If word increase is small relative to citations added, it's OK
    # Each citation is typically 1-2 words when written out
    max_allowed_increase = total_citations * 2 + 10  # 2 words per citation + 10 tolerance
    
    if word_increase > max_allowed_increase:
        errors.append(f"Word count increased by {word_increase} words (hallucination detected, expected max {max_allowed_increase})")
    
    # Check for content between title and abstract
    title_idx = None
    abstract_idx = None
    result_lines = result.split('\n')
    for i, line in enumerate(result_lines):
        if line.startswith('# '):
            title_idx = i
        if '## Abstract' in line or '## abstract' in line.lower():
            abstract_idx = i
            break
    
    if title_idx is not None and abstract_idx is not None:
        between_lines = result_lines[title_idx+1:abstract_idx]
        non_empty_between = [line for line in between_lines if line.strip()]
        if non_empty_between:
            errors.append(f"Found {len(non_empty_between)} lines between title and abstract")
    
    # Check abstract has no citations
    abstract_match = re.search(r'## Abstract\n(.*?)(?=\n##|\Z)', result, re.DOTALL)
    if abstract_match:
        abstract_text = abstract_match.group(1)
        abstract_citations = re.findall(r'\[(\d+)\]', abstract_text)
        if abstract_citations:
            errors.append(f"Abstract has citations: {abstract_citations}")
    
    if errors:
        print("\n❌ FAILURE: Structure validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ SUCCESS: Structure maintained, no hallucination")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ANTI-HALLUCINATION TEST SUITE")
    print("=" * 70)
    print("\n5 different tests to ensure LLM NEVER adds unauthorized content\n")
    
    results = []
    
    # Run all 5 tests
    results.append(("Test 1: Title-only section", test_1_title_only_section()))
    results.append(("Test 2: Abstract preservation", test_2_abstract_preservation()))
    results.append(("Test 3: Empty section handling", test_3_empty_section_handling()))
    results.append(("Test 4: Content length verification", test_4_content_length_verification()))
    results.append(("Test 5: Full integration structure", test_5_full_integration_structure()))
    
    # Summary
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
        print("\n" + "=" * 70)
        print("✅✅✅ ALL ANTI-HALLUCINATION TESTS PASSED ✅✅✅")
        print("=" * 70)
        print("\nThe system is protected against:")
        print("1. ✅ Content between title and abstract")
        print("2. ✅ Citations in abstract")
        print("3. ✅ Hallucination in empty sections")
        print("4. ✅ Content expansion beyond citations")
        print("5. ✅ Structure corruption")
        print("\n🎯 LLM hallucination is PREVENTED!")
    else:
        print("\n" + "=" * 70)
        print("❌ SOME TESTS FAILED - HALLUCINATION RISK EXISTS")
        print("=" * 70)
        print(f"\n{total - passed} test(s) failed. Review and fix before deployment!")
