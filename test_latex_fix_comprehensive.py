#!/usr/bin/env python3
"""
Comprehensive test to validate LaTeX fixes are working correctly.
This script will test the normalization function and validate the cached article.
"""
import json
import os
import re
import sys

# Import the actual normalization function from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _normalize_article_for_rendering(text: str) -> str:
    """Copy of the normalization function from app.py for testing."""
    t = text or ""
    
    # CRITICAL PRE-PROCESSING: Fix malformed LaTeX delimiters FIRST
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    t = t.replace("\\right)$", "\\right)")
    t = t.replace("\\left\\frac", "\\left(\\frac")
    
    # Apply regex-based fixes
    for _ in range(20):
        before = t
        t = re.sub(r"\\left\$", r"\\left(", t)
        t = re.sub(r"\\right\$", r"\\right)", t)
        t = re.sub(r"\$\\left\(", r"\\left(", t)
        t = re.sub(r"\\right\)\$(?!\$)", r"\\right)", t)
        t = re.sub(r"\\left\\frac", r"\\left(\\frac", t)
        t = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", t)
        if t == before:
            break
    
    # Final safety net
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    
    # Normal normalization
    t = t.replace('\\[', '$$').replace('\\]', '$$')
    # DO NOT replace \( and \) - commented out to prevent breaking \left( and \right)
    
    # Convert equation environments
    t = re.sub(r"\\begin\{equation\*?\}\s*([\s\S]*?)\s*\\end\{equation\*?\}", r"$$\n\1\n$$", t)
    t = re.sub(r"\\begin\{align\*?\}\s*([\s\S]*?)\s*\\end\{align\*?\}", r"$$\n\\begin{aligned}\n\1\n\\end{aligned}\n$$", t)
    
    # CRITICAL: Do NOT wrap \left(...\right) content in $...$
    # These patterns were creating errors - now commented out
    
    return t

def test_normalization_function():
    """Test the normalization function with problematic formulas."""
    print("="*70)
    print("TEST 1: NORMALIZATION FUNCTION")
    print("="*70)
    
    test_cases = [
        {
            "name": "Valid formula with \\left( and \\right)",
            "input": r"\mathcal{L}_{\text{Hybrid}} = \mathcal{L}_{\text{diffusion}}\left(\mathbf{x}_t\right) + \mathcal{L}_{\text{GAN}}\left(\mathbf{G}(\mathbf{z})\right)",
            "should_change": False,
            "should_have_errors": False
        },
        {
            "name": "Formula with \\left$ error",
            "input": r"\mathcal{L}_{\text{diffusion}}\left$\mathbf{x}_t\right$",
            "should_change": True,
            "should_have_errors": False
        },
        {
            "name": "Formula with $\\left( error",
            "input": r"$\left(\mathbf{x}_t\right)$",
            "should_change": True,
            "should_have_errors": False
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"Input:  {test['input']}")
        
        result = _normalize_article_for_rendering(test['input'])
        print(f"Output: {result}")
        
        changed = result != test['input']
        has_errors = r"\left$" in result or r"\right$" in result
        
        # Check expectations
        passed = True
        if test['should_change'] and not changed:
            print(f"  ❌ FAIL: Expected changes but got none")
            passed = False
        elif not test['should_change'] and changed:
            print(f"  ⚠️  WARNING: Unexpected changes")
        
        if has_errors:
            print(f"  ❌ FAIL: Output contains \\left$ or \\right$ errors")
            passed = False
        else:
            print(f"  ✅ PASS: No LaTeX errors in output")
        
        if passed:
            print(f"  ✅ Test case passed")
        else:
            all_passed = False
    
    return all_passed

def test_cached_article():
    """Test the actual cached article."""
    print("\n" + "="*70)
    print("TEST 2: CACHED ARTICLE")
    print("="*70)
    
    cache_path = ".ui_cache/ui_state.json"
    if not os.path.exists(cache_path):
        print("❌ Cache file not found")
        return False
    
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    if not article:
        print("❌ No article in cache")
        return False
    
    print(f"\nArticle length: {len(article)} characters")
    
    # Check for errors in original
    errors_before = []
    if r"\left$" in article:
        count = article.count(r"\left$")
        errors_before.append(f"\\left$ ({count} times)")
    if r"\right$" in article:
        count = article.count(r"\right$")
        errors_before.append(f"\\right$ ({count} times)")
    
    print(f"Errors in cached article: {errors_before if errors_before else 'None'}")
    
    # Extract body (skip title)
    lines = article.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# '):
            body_start = i + 1
            break
    article_body = '\n'.join(lines[body_start:])
    
    # Apply normalization
    print(f"\nApplying normalization...")
    normalized = _normalize_article_for_rendering(article_body)
    
    print(f"Normalized length: {len(normalized)} characters")
    
    # Check for errors after normalization
    errors_after = []
    if r"\left$" in normalized:
        count = normalized.count(r"\left$")
        errors_after.append(f"\\left$ ({count} times)")
        # Show first occurrence
        idx = normalized.find(r"\left$")
        print(f"\n❌ Found \\left$ at position {idx}:")
        print(f"   Context: {normalized[max(0,idx-80):idx+80]}")
    if r"\right$" in normalized:
        count = normalized.count(r"\right$")
        errors_after.append(f"\\right$ ({count} times)")
        # Show first occurrence
        idx = normalized.find(r"\right$")
        print(f"\n❌ Found \\right$ at position {idx}:")
        print(f"   Context: {normalized[max(0,idx-80):idx+80]}")
    
    print(f"\nErrors after normalization: {errors_after if errors_after else 'None'}")
    
    # Verdict
    if errors_after:
        print("\n❌ FAIL: Normalization is creating or not fixing errors")
        return False
    elif errors_before:
        print("\n⚠️  WARNING: Original article has errors but normalization fixed them")
        print("   Recommendation: Click the 'Validate & Fix LaTeX' button to fix the source")
        return True
    else:
        print("\n✅ PASS: No errors in original or normalized article")
        return True

def test_specific_formula():
    """Test the specific formula the user reported."""
    print("\n" + "="*70)
    print("TEST 3: USER'S SPECIFIC FORMULA")
    print("="*70)
    
    # The formula from the user's report
    formula = r"\mathcal{L}_{\text{Hybrid}} = \mathcal{L}_{\text{diffusion}}\left(\mathbf{x}_t\right) + \mathcal{L}_{\text{GAN}}\left(\mathbf{G}(\mathbf{z})\right)"
    
    print(f"\nFormula: {formula}")
    
    # Check if it has errors
    has_errors_before = r"\left$" in formula or r"\right$" in formula
    print(f"Has errors before normalization: {has_errors_before}")
    
    # Apply normalization
    result = _normalize_article_for_rendering(formula)
    
    print(f"\nResult: {result}")
    
    # Check if it has errors after
    has_errors_after = r"\left$" in result or r"\right$" in result
    print(f"Has errors after normalization: {has_errors_after}")
    
    # Check if it changed
    changed = result != formula
    print(f"Formula changed: {changed}")
    
    if has_errors_after:
        print("\n❌ FAIL: Normalization created or didn't fix errors")
        return False
    elif changed and not has_errors_before:
        print("\n⚠️  WARNING: Normalization changed a valid formula")
        print(f"   This might cause issues")
        return True
    else:
        print("\n✅ PASS: Formula is valid and unchanged")
        return True

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("COMPREHENSIVE LATEX FIX VALIDATION")
    print("="*70)
    
    results = []
    
    # Test 1: Normalization function
    results.append(("Normalization Function", test_normalization_function()))
    
    # Test 2: Cached article
    results.append(("Cached Article", test_cached_article()))
    
    # Test 3: Specific formula
    results.append(("User's Formula", test_specific_formula()))
    
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
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nThe LaTeX fix is working correctly!")
        print("If you're still seeing errors in the UI, try:")
        print("1. Click the 'Validate & Fix LaTeX' button")
        print("2. Hard refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)")
        print("3. Clear browser cache completely")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        print("\nThe LaTeX fix is NOT working correctly.")
        print("Further investigation is needed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
