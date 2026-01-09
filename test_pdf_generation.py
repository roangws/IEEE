#!/usr/bin/env python3
"""
Test PDF generation with the problematic formula to identify the exact issue.
"""
import json
import os
import sys

# Test the exact formula from the user's report
test_formula = r"q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{\alpha_t}\mathbf{x}_{t-1}, \left(1-\alpha_t\right)\mathbf{I}\right)"

print("="*70)
print("ANALYZING PROBLEMATIC FORMULA")
print("="*70)

print(f"\nFormula: {test_formula}")

# Check if it has proper math delimiters
has_opening_dollar = test_formula.startswith('$')
has_closing_dollar = test_formula.endswith('$')
has_double_dollar = '$$' in test_formula

print(f"\nMath delimiter analysis:")
print(f"  Starts with $: {has_opening_dollar}")
print(f"  Ends with $: {has_closing_dollar}")
print(f"  Contains $$: {has_double_dollar}")

if not has_opening_dollar and not has_double_dollar:
    print("\n❌ PROBLEM: Formula has NO math delimiters!")
    print("   This is bare LaTeX that won't render correctly")
    print("   It should be wrapped in $ ... $ or $$ ... $$")

# Check the cached article for this pattern
cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        # Search for this pattern
        if 'q\\left(\\mathbf{x}_t' in article:
            idx = article.find('q\\left(\\mathbf{x}_t')
            start = max(0, idx - 100)
            end = min(len(article), idx + 200)
            
            print("\n" + "="*70)
            print("FOUND IN CACHED ARTICLE")
            print("="*70)
            print(f"\nContext around position {idx}:")
            print(article[start:end])
            
            # Check if it has $ delimiters in the article
            context = article[max(0, idx-10):min(len(article), idx+300)]
            if context.startswith('$') or '$$' in context[:20]:
                print("\n✅ Formula HAS math delimiters in article")
            else:
                print("\n❌ Formula MISSING math delimiters in article")
                print("   This is the root cause - LLM generated bare LaTeX")
        else:
            print("\n⚠️  Exact pattern not found in cached article")
            # Try a broader search
            if 'mathbf{x}_t' in article:
                print("   But found mathbf{x}_t - searching...")
                idx = article.find('mathbf{x}_t')
                start = max(0, idx - 150)
                end = min(len(article), idx + 150)
                print(f"\nContext:")
                print(article[start:end])
else:
    print(f"\n❌ Cache file not found: {cache_path}")

print("\n" + "="*70)
print("SOLUTION")
print("="*70)
print("\nThe issue is that the LLM is generating bare LaTeX formulas")
print("without proper $ delimiters. The normalization function needs to:")
print("1. Detect bare LaTeX patterns (\\left, \\mathbf, \\mathcal, etc.)")
print("2. Wrap them in $ ... $ for inline math")
print("3. Or wrap in $$ ... $$ for display math")
