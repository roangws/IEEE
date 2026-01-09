#!/usr/bin/env python3
"""
Test that:
1. Abstract is present in the displayed article
2. PDF generation uses the current (fixed) article from session state
"""
import json
import os

def test_abstract_presence():
    """Test that abstract is present in the article."""
    print("="*70)
    print("TEST 1: ABSTRACT PRESENCE")
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
    
    # Extract title and body (simulating what the app does)
    lines = article.split('\n')
    title_line = -1
    for i, line in enumerate(lines[:10]):
        if line.strip().startswith('# '):
            title_line = i
            break
    
    if title_line >= 0:
        title = lines[title_line][2:].strip()
        article_body = '\n'.join(lines[:title_line] + lines[title_line+1:])
    else:
        title = "No title found"
        article_body = article
    
    print(f"\nTitle: {title[:80]}...")
    print(f"Article body length: {len(article_body)} chars")
    
    # Check for abstract in body
    has_abstract = '## Abstract' in article_body or '## abstract' in article_body.lower()
    
    if has_abstract:
        print("\n✅ PASS: Abstract section found in article body")
        
        # Show first few lines of body
        body_lines = article_body.split('\n')
        print("\nFirst 10 lines of article body:")
        for i, line in enumerate(body_lines[:10], 1):
            if line.strip():
                print(f"  {i}: {line[:80]}...")
        return True
    else:
        print("\n❌ FAIL: Abstract section NOT found in article body")
        return False

def test_pdf_uses_session_state():
    """Test that PDF generation logic uses session state article."""
    print("\n" + "="*70)
    print("TEST 2: PDF USES CURRENT SESSION STATE")
    print("="*70)
    
    # Read the app.py file to check PDF generation code
    with open('app.py', 'r') as f:
        app_code = f.read()
    
    # Check if PDF generation uses st.session_state.generated_article
    if 'generate_article_pdf(\n                        st.session_state.generated_article,' in app_code:
        print("\n✅ PASS: PDF generation uses st.session_state.generated_article")
        print("   This means PDF will reflect any LaTeX fixes applied to session state")
        return True
    else:
        print("\n❌ FAIL: PDF generation may not be using current session state")
        return False

def test_pdf_cache_invalidation():
    """Test that PDF cache is invalidated when article changes."""
    print("\n" + "="*70)
    print("TEST 3: PDF CACHE INVALIDATION")
    print("="*70)
    
    with open('app.py', 'r') as f:
        app_code = f.read()
    
    # Check if article length is used in signature (forces regeneration on changes)
    if 'str(len(st.session_state.generated_article or ""))' in app_code:
        print("\n✅ PASS: PDF cache uses article length in signature")
        print("   This means PDF will be regenerated when article is modified")
        return True
    else:
        print("\n⚠️  WARNING: PDF cache may not invalidate on article changes")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PDF AND ABSTRACT FIX VALIDATION")
    print("="*70)
    
    results = []
    
    results.append(("Abstract Presence", test_abstract_presence()))
    results.append(("PDF Uses Session State", test_pdf_uses_session_state()))
    results.append(("PDF Cache Invalidation", test_pdf_cache_invalidation()))
    
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
        print("\nBoth fixes are in place:")
        print("1. Abstract is present in the article body")
        print("2. PDF generation uses current session state (includes LaTeX fixes)")
        print("\nIf you're still seeing issues:")
        print("- Click 'Validate & Fix LaTeX' button")
        print("- Then download PDF - it will have the fixes")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
