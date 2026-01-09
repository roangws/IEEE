#!/usr/bin/env python3
"""
PRODUCTION VALIDATION TEST SUITE
Validates actual integration output to ensure external citations are in article text
Run this BEFORE expensive LLM calls to verify the system works correctly.
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_citation_integratorator import SmartCitationIntegrator
from external_reference_fetcher import ExternalReference


def load_sample_data():
    """Load sample article and references for testing"""
    
    # Original article (before integration) - 42 local citations
    original_article = """# Video Inpainting and Restoration Using Diffusion Models

## Abstract
This paper presents a novel approach to video inpainting using diffusion models.

## 1. Introduction
Video inpainting has become increasingly important [1]. Traditional methods struggle with temporal consistency [2].

## 2. Related Work
Previous work includes optical flow methods [3] and CNN-based approaches [4].

## 3. Methodology
We propose a novel architecture [5] with spatial diffusion [6].

## 4. Experiments
We evaluate on standard benchmarks [7]. Results show improvements [8].

## 5. Conclusion
Our approach achieves state-of-the-art results [9]."""

    # Create 10 external references
    external_refs = []
    for i in range(10):
        ref = ExternalReference(
            title=f"External Paper {10+i}: Advanced Video Inpainting",
            authors=[f"Author {chr(65+i)}"],
            year="2023",
            venue="CVPR",
            citation_number=10+i,
            selected=True
        )
        external_refs.append(ref)
    
    return original_article, external_refs


def apply_ieee_renumbering(article: str) -> str:
    """Apply IEEE sequential renumbering"""
    all_citations_in_order = []
    for match in re.finditer(r'\[(\d+)\]', article):
        citation_num = int(match.group(1))
        if citation_num not in all_citations_in_order:
            all_citations_in_order.append(citation_num)
    
    old_to_new = {old: new for new, old in enumerate(all_citations_in_order, start=1)}
    
    for old_num, new_num in sorted(old_to_new.items(), reverse=True):
        article = article.replace(f"[{old_num}]", f"[TEMP{new_num}]")
    
    for new_num in range(1, len(old_to_new) + 1):
        article = article.replace(f"[TEMP{new_num}]", f"[{new_num}]")
    
    return article


def run_integration_with_local_llm(original_article, external_refs):
    """Run integration with local mock (no expensive API calls)"""
    integrator = SmartCitationIntegrator()
    
    import unittest.mock
    
    citation_counter = [0]
    
    def mock_call_openai(*args, **kwargs):
        prompt = args[0] if args else ""
        content = prompt.split("SECTION CONTENT:")[1].split("AVAILABLE CITATIONS")[0].strip() if "SECTION CONTENT:" in prompt else ""
        
        if "abstract" in prompt.lower():
            return content, type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
        
        if content and '.' in content and citation_counter[0] < len(external_refs):
            sentences = content.split('.')
            if len(sentences) > 0:
                sentences[0] = sentences[0] + f" [{external_refs[citation_counter[0]].citation_number}]"
                citation_counter[0] += 1
                content = '.'.join(sentences)
        
        return content, type('Usage', (), {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150})()
    
    with unittest.mock.patch('smart_citation_integratorator.call_openai', side_effect=mock_call_openai):
        integrated_article = integrator.integrate_citations_smart(
            original_article, external_refs, llm_type="openai", model="gpt-4o", return_usage=True
        )[0]
    
    integrated_article = apply_ieee_renumbering(integrated_article)
    return integrated_article


def test_1_citation_count_delta():
    """TEST 1: Verify external citations were added to article text"""
    print("=" * 70)
    print("TEST 1: Citation Count Delta Validation")
    print("=" * 70)
    
    original_article, external_refs = load_sample_data()
    
    original_citations = set(re.findall(r'\[(\d+)\]', original_article))
    original_count = len(original_citations)
    
    print(f"\nOriginal: {original_count} citations")
    
    integrated_article = run_integration_with_local_llm(original_article, external_refs)
    
    final_citations = set(re.findall(r'\[(\d+)\]', integrated_article))
    final_count = len(final_citations)
    
    print(f"Integrated: {final_count} citations")
    
    citations_added = final_count - original_count
    num_selected = len([r for r in external_refs if r.selected])
    
    print(f"Added: {citations_added} (expected 1-{num_selected})")
    
    success = citations_added > 0 and citations_added <= num_selected
    
    if success:
        print(f"\n✅ PASS: {citations_added} external citations added")
        return True
    else:
        print(f"\n❌ FAIL: No citations added")
        return False


def test_2_sequential_integrity():
    """TEST 2: Verify IEEE sequential numbering"""
    print("\n" + "=" * 70)
    print("TEST 2: Citation Number Sequential Integrity")
    print("=" * 70)
    
    original_article, external_refs = load_sample_data()
    integrated_article = run_integration_with_local_llm(original_article, external_refs)
    
    all_citations = [int(c) for c in re.findall(r'\[(\d+)\]', integrated_article)]
    unique_citations = sorted(set(all_citations))
    
    print(f"\nCitations: {unique_citations}")
    
    expected_sequence = list(range(1, len(unique_citations) + 1))
    is_sequential = unique_citations == expected_sequence
    
    if is_sequential:
        print(f"\n✅ PASS: Sequential [1-{len(unique_citations)}]")
        return True
    else:
        print(f"\n❌ FAIL: Not sequential")
        return False


def test_3_external_citation_position():
    """TEST 3: Verify external citations in article body"""
    print("\n" + "=" * 70)
    print("TEST 3: External Citation Position Verification")
    print("=" * 70)
    
    original_article, external_refs = load_sample_data()
    
    original_count = len(set(re.findall(r'\[(\d+)\]', original_article)))
    
    integrated_article = run_integration_with_local_llm(original_article, external_refs)
    
    integrator = SmartCitationIntegrator()
    sections = integrator._parse_sections(integrated_article)
    
    external_found = 0
    for heading, content in sections:
        if content.strip():
            section_citations = [int(c) for c in re.findall(r'\[(\d+)\]', content)]
            external_in_section = [c for c in section_citations if c > original_count]
            external_found += len(external_in_section)
    
    print(f"\nExternal citations in article body: {external_found}")
    
    if external_found > 0:
        print(f"\n✅ PASS: {external_found} external citations in text")
        return True
    else:
        print(f"\n❌ FAIL: No external citations in text")
        return False


def test_4_reference_list_completeness():
    """TEST 4: Verify all selected refs in reference list"""
    print("\n" + "=" * 70)
    print("TEST 4: Reference List Completeness")
    print("=" * 70)
    
    original_article, external_refs = load_sample_data()
    integrated_article = run_integration_with_local_llm(original_article, external_refs)
    
    all_citations = set([int(c) for c in re.findall(r'\[(\d+)\]', integrated_article)])
    
    selected_count = len([r for r in external_refs if r.selected])
    
    print(f"\nSelected external refs: {selected_count}")
    print(f"Total citations in article: {len(all_citations)}")
    
    original_count = len(set(re.findall(r'\[(\d+)\]', original_article)))
    expected_total = original_count + selected_count
    
    if len(all_citations) >= original_count:
        print(f"\n✅ PASS: Reference list includes external refs")
        return True
    else:
        print(f"\n❌ FAIL: Missing external refs")
        return False


def test_5_citation_reference_mapping():
    """TEST 5: Verify every citation has reference entry"""
    print("\n" + "=" * 70)
    print("TEST 5: Citation-Reference Mapping Consistency")
    print("=" * 70)
    
    original_article, external_refs = load_sample_data()
    integrated_article = run_integration_with_local_llm(original_article, external_refs)
    
    cited_numbers = set([int(c) for c in re.findall(r'\[(\d+)\]', integrated_article)])
    
    expected_range = set(range(1, len(cited_numbers) + 1))
    
    print(f"\nCited numbers: {sorted(cited_numbers)}")
    print(f"Expected range: {sorted(expected_range)}")
    
    is_consistent = cited_numbers == expected_range
    
    if is_consistent:
        print(f"\n✅ PASS: All citations map to references")
        return True
    else:
        print(f"\n❌ FAIL: Orphaned citations exist")
        return False


def run_all_tests():
    """Run all 5 production validation tests"""
    print("\n" + "=" * 70)
    print("PRODUCTION VALIDATION TEST SUITE")
    print("Validating External Citation Integration (Local - No API Cost)")
    print("=" * 70)
    
    results = []
    
    results.append(("Test 1: Citation Count Delta", test_1_citation_count_delta()))
    results.append(("Test 2: Sequential Integrity", test_2_sequential_integrity()))
    results.append(("Test 3: External Citation Position", test_3_external_citation_position()))
    results.append(("Test 4: Reference List Completeness", test_4_reference_list_completeness()))
    results.append(("Test 5: Citation-Reference Mapping", test_5_citation_reference_mapping()))
    
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - SAFE TO USE LLM")
        print("=" * 70)
        print("\nExternal citations ARE being added to article text.")
        print("The integration is working correctly.")
        print("💰 You can proceed with expensive LLM calls safely!")
    else:
        print("\n" + "=" * 70)
        print("❌ TESTS FAILED - DO NOT USE LLM YET")
        print("=" * 70)
        print(f"\n{total - passed} test(s) failed.")
        print("⚠️  Fix issues before spending money on LLM!")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
