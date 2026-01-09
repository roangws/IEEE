#!/usr/bin/env python3
"""
Directly fix the cached article by applying LaTeX validation
"""
import json
import os
import re

def _validate_and_fix_latex_delimiters(article: str) -> str:
    """Universal LaTeX delimiter validator and fixer."""
    original = article
    
    # Fix 1: Replace \left$ and \right$ with proper delimiters
    article = article.replace("\\left$", "\\left(")
    article = article.replace("\\right$", "\\right)")
    
    # Fix 2: Remove $ that's incorrectly placed with \left or \right
    article = article.replace("$\\left(", "\\left(")
    article = article.replace("\\right)$", "\\right)")
    
    # Fix 3: Fix \left\frac (missing opening delimiter)
    article = article.replace("\\left\\frac", "\\left(\\frac")
    
    # Fix 4: Apply regex-based fixes (multiple passes for nested issues)
    for iteration in range(15):
        before = article
        article = re.sub(r"\\left\$", r"\\left(", article)
        article = re.sub(r"\\right\$", r"\\right)", article)
        article = re.sub(r"\$\\left\(", r"\\left(", article)
        article = re.sub(r"\\right\)\$(?!\$)", r"\\right)", article)
        article = re.sub(r"\\left\\frac", r"\\left(\\frac", article)
        article = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", article)
        if article == before:
            break
    
    # Fix 5: Final string replacements as safety net
    article = article.replace("\\left$", "\\left(")
    article = article.replace("\\right$", "\\right)")
    article = article.replace("$\\left(", "\\left(")
    
    return article

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    print("="*70)
    print("FIXING CACHED ARTICLE")
    print("="*70)
    
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        # Check for errors before
        errors_before = []
        if r"\left$" in article:
            errors_before.append(f"\\left$ ({article.count(r'\left$')} times)")
        if r"\right$" in article:
            errors_before.append(f"\\right$ ({article.count(r'\right$')} times)")
        
        print(f"\nErrors before: {errors_before if errors_before else 'None'}")
        
        # Apply fix
        fixed_article = _validate_and_fix_latex_delimiters(article)
        
        # Check for errors after
        errors_after = []
        if r"\left$" in fixed_article:
            errors_after.append(f"\\left$ ({fixed_article.count(r'\left$')} times)")
        if r"\right$" in fixed_article:
            errors_after.append(f"\\right$ ({fixed_article.count(r'\right$')} times)")
        
        print(f"Errors after:  {errors_after if errors_after else 'None'}")
        
        if fixed_article != article:
            changes = sum(1 for a, b in zip(article, fixed_article) if a != b)
            print(f"\n✅ Applied {changes} character corrections")
            
            # Update cache
            cache['generated_article'] = fixed_article
            if cache.get('base_generated_article') == article:
                cache['base_generated_article'] = fixed_article
            
            # Save back to cache
            with open(cache_path, 'w') as f:
                json.dump(cache, f, indent=2)
            
            print(f"💾 Saved fixed article to cache")
            print(f"\n⚠️ IMPORTANT: Refresh your Streamlit app to see the changes")
        else:
            print("\n✅ No changes needed - article is already valid")
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
