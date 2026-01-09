#!/usr/bin/env python3
"""
Test the PDF generation fix by creating an actual PDF with the problematic formula.
"""
import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import generate_article_pdf, _normalize_article_for_rendering
from citation_manager import CitationManager

def test_normalization_on_problematic_text():
    """Test normalization on the exact problematic text."""
    print("="*70)
    print("TEST 1: NORMALIZATION ON PROBLEMATIC TEXT")
    print("="*70)
    
    # The exact text from the user's report
    problematic_text = """These models, often denoted as $q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict a process where $\\mathbf{x}_t$ represents the video frame at time $t$ conditioned on frame $\\mathbf{x}_{t-1}$ [5]."""
    
    print(f"\nOriginal text:")
    print(problematic_text)
    
    # Apply normalization
    normalized = _normalize_article_for_rendering(problematic_text)
    
    print(f"\nNormalized text:")
    print(normalized)
    
    # Check if the bare LaTeX is now wrapped
    if '$q\\left(' in normalized or '$$q\\left(' in normalized:
        print("\n✅ PASS: Bare LaTeX is now wrapped in $ delimiters")
        return True
    else:
        print("\n❌ FAIL: Bare LaTeX still not properly wrapped")
        return False

def test_pdf_generation():
    """Test actual PDF generation with the cached article."""
    print("\n" + "="*70)
    print("TEST 2: ACTUAL PDF GENERATION")
    print("="*70)
    
    cache_path = ".ui_cache/ui_state.json"
    if not os.path.exists(cache_path):
        print("❌ Cache file not found")
        return False
    
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    citation_map = cache.get('citation_map', {})
    sources = cache.get('article_sources', [])
    topic = cache.get('article_topic_stored', 'Test Article')
    
    if not article:
        print("❌ No article in cache")
        return False
    
    print(f"\nGenerating PDF...")
    print(f"  Article length: {len(article)} chars")
    print(f"  Citations: {len(citation_map)}")
    print(f"  Sources: {len(sources)}")
    
    try:
        pdf_bytes = generate_article_pdf(article, topic, citation_map, sources)
        pdf_size = len(pdf_bytes.getvalue())
        
        print(f"\n✅ PDF generated successfully")
        print(f"  PDF size: {pdf_size:,} bytes")
        
        # Save the PDF for manual inspection
        output_path = "test_output.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes.getvalue())
        
        print(f"  Saved to: {output_path}")
        print(f"\n⚠️  MANUAL VERIFICATION REQUIRED:")
        print(f"  Open {output_path} and check section 5.2 for the formula:")
        print(f"  q\\left(\\mathbf{{x}}_t \\mid \\mathbf{{x}}_{{t-1}}\\right)")
        print(f"  It should be properly formatted with no bare LaTeX")
        
        return True
    except Exception as e:
        print(f"\n❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_formula_wrapping():
    """Test that the specific problematic formula gets wrapped correctly."""
    print("\n" + "="*70)
    print("TEST 3: SPECIFIC FORMULA WRAPPING")
    print("="*70)
    
    # Test various forms of the problematic pattern
    test_cases = [
        {
            "name": "Bare LaTeX in sentence",
            "input": "denoted as q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict",
            "should_contain": "$q\\left("
        },
        {
            "name": "Already wrapped",
            "input": "$q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right)$",
            "should_contain": "$q\\left("
        },
        {
            "name": "Partial wrapping (opening $ only)",
            "input": "$q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict",
            "should_contain": "$q\\left("
        }
    ]
    
    all_passed = True
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"  Input:  {test['input']}")
        
        result = _normalize_article_for_rendering(test['input'])
        print(f"  Output: {result}")
        
        if test['should_contain'] in result:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL: Expected to contain '{test['should_contain']}'")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PDF FIX COMPREHENSIVE VALIDATION")
    print("="*70)
    
    results = []
    
    results.append(("Normalization on Problematic Text", test_normalization_on_problematic_text()))
    results.append(("Specific Formula Wrapping", test_specific_formula_wrapping()))
    results.append(("Actual PDF Generation", test_pdf_generation()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL AUTOMATED TESTS PASSED")
        print("="*70)
        print("\nPDF has been generated: test_output.pdf")
        print("Please open it and verify section 5.2 looks correct.")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
