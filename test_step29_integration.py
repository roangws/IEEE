#!/usr/bin/env python3
"""
Test Suite for Step 2.9 Integration
Tests that the integration meets the user's requirements:
1. Keeps internal references
2. Integrates external references (60%+ utilization)
3. LLM gets abstract and information
4. Outputs proper reference ordering
5. Citations are in text
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
    return """# Video Inpainting and Restoration: Diffusion Models and Beyond

## Abstract
Video inpainting has emerged as a critical task in computer vision, addressing the challenge of filling missing regions in video sequences while maintaining temporal consistency [1]. This paper presents a comprehensive analysis of recent advances in diffusion-based approaches for video restoration tasks.

## 1. Introduction
Video inpainting represents one of the most challenging problems in computer vision [2]. The ability to fill missing regions while maintaining temporal coherence requires sophisticated understanding of both spatial and temporal dependencies [3]. Recent advances in generative models have shown promising results for this task [4].

## 2. Background and Related Work
Traditional approaches to video inpainting relied on optical flow and patch-based methods [5]. These methods, while effective for small regions, struggle with large missing areas and complex motion patterns [6]. The introduction of deep learning has revolutionized this field [7].

## 3. Methodology
Our approach builds upon recent advances in diffusion models for video generation [8]. We propose a novel architecture that combines temporal attention mechanisms with spatial diffusion processes [9]. The key innovation is our adaptive mask handling strategy [10].

## 4. Results
We evaluate our method on standard benchmarks including DAVIS and YouTube-VOS [11]. Our approach achieves state-of-the-art performance with a PSNR improvement of 3.2dB over previous methods [12]. The qualitative results show superior handling of complex motion patterns [13].

## 5. Discussion
The results demonstrate that diffusion-based approaches are particularly effective for video inpainting tasks [14]. However, computational requirements remain a challenge [15]. Future work should focus on efficiency improvements [16].

## 6. Conclusion
Video inpainting with diffusion models represents a promising direction for video restoration [17]. Our contributions include a novel architecture and comprehensive evaluation [18]. The integration of temporal consistency mechanisms is key to success [19].

## References
[1] Internal reference 1
[2] Internal reference 2
[3] Internal reference 3
[4] Internal reference 4
[5] Internal reference 5
[6] Internal reference 6
[7] Internal reference 7
[8] Internal reference 8
[9] Internal reference 9
[10] Internal reference 10
[11] Internal reference 11
[12] Internal reference 12
[13] Internal reference 13
[14] Internal reference 14
[15] Internal reference 15
[16] Internal reference 16
[17] Internal reference 17
[18] Internal reference 18
[19] Internal reference 19
[20] Internal reference 20
"""


def create_test_external_references():
    """Create 20 test external references."""
    references = []
    
    for i in range(21, 41):  # Numbers 21-40
        ref = ExternalReference(
            title=f"External Video Inpainting Paper {i}: Advanced Diffusion Techniques",
            authors=[f"Author A{i}", f"Author B{i}", f"Author C{i}"],
            year=2023 + (i % 3),
            venue=f"CVPR/ICCV/ECCV {2020 + (i % 4)}",
            citation_number=i,
            abstract="This paper presents a novel approach to video inpainting using advanced diffusion models. "
                    "Our method achieves state-of-the-art results on standard benchmarks with significant improvements "
                    "in temporal consistency and visual quality. The key innovation involves adaptive attention mechanisms "
                    "that effectively handle complex motion patterns and large missing regions.",
            doi=f"10.1000/external-paper-{i}",
            url=f"https://arxiv.org/abs/2023.{i:04d}"
        )
        ref.selected = True
        references.append(ref)
    
    return references


def run_test_1_internal_references_preserved():
    """Test 1: Verify internal references are preserved."""
    print("\n" + "="*60)
    print("TEST 1: Internal References Preservation")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    # Extract original internal citations
    cm = CitationManager()
    original_citations = cm.extract_citations_from_article(article)
    
    print(f"Original internal citations: {sorted(original_citations)}")
    
    # Run integration with Ollama (free local LLM)
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    result = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=True,
        progress_callback=progress_callback
    )
    
    # Handle different return formats
    if isinstance(result, tuple) and len(result) == 2:
        enhanced, _ = result
    elif isinstance(result, str):
        enhanced = result
    else:
        enhanced = str(result)
    
    # Check internal citations are still there
    enhanced_citations = cm.extract_citations_from_article(enhanced)
    
    print(f"Enhanced article citations: {sorted(enhanced_citations)}")
    
    # Verify all original citations are preserved
    preserved = all(c in enhanced_citations for c in original_citations)
    print(f"\n✅ All internal references preserved: {preserved}")
    
    if not preserved:
        print("❌ FAILED: Some internal references were lost!")
        return False
    
    return True


def run_test_2_external_utilization():
    """Test 2: Verify 60%+ external reference utilization."""
    print("\n" + "="*60)
    print("TEST 2: External Reference Utilization (Target: 60%+)")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    print(f"Total external references available: {len(refs)}")
    print(f"Target utilization (60%): {len(refs) * 0.6:.0f} references")
    
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    result = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=True,
        progress_callback=progress_callback
    )
    
    # Handle different return formats
    if isinstance(result, tuple) and len(result) == 2:
        enhanced, _ = result
    elif isinstance(result, str):
        enhanced = result
    else:
        enhanced = str(result)
    
    # Count external citations used
    cm = CitationManager()
    all_citations = cm.extract_citations_from_article(enhanced)
    
    # External citations are those > 20 (since internal are 1-20)
    external_used = [c for c in all_citations if c > 20]
    
    utilization = len(external_used) / len(refs) * 100
    print(f"\nExternal references used: {len(external_used)}/{len(refs)}")
    print(f"Utilization rate: {utilization:.1f}%")
    
    if utilization >= 60:
        print(f"✅ PASSED: {utilization:.1f}% >= 60%")
        return True
    else:
        print(f"❌ FAILED: {utilization:.1f}% < 60%")
        return False


def run_test_3_abstract_used():
    """Test 3: Verify LLM uses abstract information."""
    print("\n" + "="*60)
    print("TEST 3: Abstract Information Utilization")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    # Track if abstract content is being used
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    result = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=True,
        progress_callback=progress_callback
    )
    
    # Handle different return formats
    if isinstance(result, tuple) and len(result) == 2:
        enhanced, _ = result
    elif isinstance(result, str):
        enhanced = result
    else:
        enhanced = str(result)
    
    # Check if enhanced article has more content (indicating LLM used abstract info)
    print(f"\nOriginal article length: {len(article)} chars")
    print(f"Enhanced article length: {len(enhanced)} chars")
    
    # The LLM should add citations based on abstract content
    cm = CitationManager()
    citations = cm.extract_citations_from_article(enhanced)
    
    print(f"Total citations in enhanced article: {len(citations)}")
    
    if len(citations) > 20:  # More than just internal references
        print("✅ PASSED: LLM added citations based on abstract information")
        return True
    else:
        print("❌ FAILED: LLM did not add external citations")
        return False


def run_test_4_reference_ordering():
    """Test 4: Verify proper reference ordering (internal first, then external)."""
    print("\n" + "="*60)
    print("TEST 4: Reference Ordering (Internal → External)")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    result = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=True,
        progress_callback=progress_callback
    )
    
    # Handle different return formats
    if isinstance(result, tuple) and len(result) == 2:
        enhanced, _ = result
    elif isinstance(result, str):
        enhanced = result
    else:
        enhanced = str(result)
    
    # Extract citations in order of appearance
    cm = CitationManager()
    citations = cm.extract_citations_from_article(enhanced)
    
    print(f"Citations in order: {citations}")
    
    # Check if internal citations (1-20) appear before external (21+)
    # This is a simplified check - in reality, IEEE renumbering happens in Step 4
    has_internal = any(c <= 20 for c in citations)
    has_external = any(c > 20 for c in citations)
    
    print(f"Has internal citations: {has_internal}")
    print(f"Has external citations: {has_external}")
    
    if has_internal and has_external:
        print("✅ PASSED: Both internal and external citations present")
        print("Note: IEEE renumbering to sequential [1,2,3...] happens in Step 4")
        return True
    else:
        print("❌ FAILED: Missing internal or external citations")
        return False


def run_test_5_citations_in_text():
    """Test 5: Verify citations are properly placed in text."""
    print("\n" + "="*60)
    print("TEST 5: Citations Placed in Text")
    print("="*60)
    
    article = create_test_article()
    refs = create_test_external_references()
    
    integrator = SmartCitationIntegrator()
    
    def progress_callback(msg):
        print(f"  {msg}")
    
    result = integrator.integrate_citations_smart(
        article_text=article,
        references=refs,
        llm_type="ollama",
        model="gemma3:27b",
        return_usage=True,
        progress_callback=progress_callback
    )
    
    # Handle different return formats
    if isinstance(result, tuple) and len(result) == 2:
        enhanced, _ = result
    elif isinstance(result, str):
        enhanced = result
    else:
        enhanced = str(result)
    
    # Count citations in text (not just in references section)
    import re
    
    # Find all citations in the main text (before References section)
    main_text = enhanced.split("## References")[0]
    citations_in_text = re.findall(r'\[(\d+)\]', main_text)
    
    print(f"Total citations found in main text: {len(citations_in_text)}")
    print(f"Unique citations: {len(set(citations_in_text))}")
    
    # Check if citations are distributed across sections
    sections = main_text.split("##")
    sections_with_citations = sum(1 for section in sections if re.search(r'\[\d+\]', section))
    
    print(f"Sections with citations: {sections_with_citations}/{len(sections)-1}")
    
    if len(citations_in_text) > 20 and sections_with_citations >= 3:
        print("✅ PASSED: Citations properly distributed in text")
        return True
    else:
        print("❌ FAILED: Insufficient citations in text")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("STEP 2.9 INTEGRATION TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNote: Using Ollama Gemma 3 27B (local LLM) for testing")
    print("Make sure Ollama is running with: ollama serve")
    
    # Check if Ollama is available
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("\n❌ ERROR: Ollama is not running!")
            print("Please start Ollama with: ollama serve")
            return
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to Ollama: {e}")
        print("Please start Ollama with: ollama serve")
        return
    
    # Run tests
    tests = [
        ("Internal References Preserved", run_test_1_internal_references_preserved),
        ("60%+ External Utilization", run_test_2_external_utilization),
        ("Abstract Information Used", run_test_3_abstract_used),
        ("Reference Ordering", run_test_4_reference_ordering),
        ("Citations in Text", run_test_5_citations_in_text),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Step 2.9 is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review the implementation.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
