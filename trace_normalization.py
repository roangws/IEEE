#!/usr/bin/env python3
"""
Trace through the normalization process step by step
"""
import json
import os
import re

def _normalize_article_for_rendering_traced(text: str) -> str:
    """Normalize LaTeX/Markdown with detailed tracing."""
    t = text or ""
    
    print(f"STEP 0 - Original length: {len(t)}")
    if r"\left(" in t[:1000]:
        print(f"  ✓ Contains \\left( in first 1000 chars")
    if r"\right)" in t[:1000]:
        print(f"  ✓ Contains \\right) in first 1000 chars")
    
    # Fix 1: Replace \left$ and \right$ with proper delimiters
    before = t
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    if t != before:
        print(f"STEP 1 - Fixed \\left$ and \\right$ (changed: {t != before})")
    
    # Fix 2: Remove $ that's incorrectly placed with \left or \right
    before = t
    t = t.replace("$\\left(", "\\left(")
    t = t.replace("\\right)$", "\\right)")
    if t != before:
        print(f"STEP 2 - Fixed $\\left( and \\right)$ (changed: {t != before})")
    
    # Fix 3: Fix \left\frac (missing opening delimiter)
    before = t
    t = t.replace("\\left\\frac", "\\left(\\frac")
    if t != before:
        print(f"STEP 3 - Fixed \\left\\frac (changed: {t != before})")
    
    # Fix 4: Apply regex-based fixes
    before = t
    for i in range(20):
        iteration_before = t
        t = re.sub(r"\\left\$", r"\\left(", t)
        t = re.sub(r"\\right\$", r"\\right)", t)
        t = re.sub(r"\$\\left\(", r"\\left(", t)
        t = re.sub(r"\\right\)\$(?!\$)", r"\\right)", t)
        t = re.sub(r"\\left\\frac", r"\\left(\\frac", t)
        t = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", t)
        if t == iteration_before:
            break
    if t != before:
        print(f"STEP 4 - Regex fixes (changed: {t != before}, iterations: {i+1})")
    
    # Fix 5: Final safety net
    before = t
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    if t != before:
        print(f"STEP 5 - Final safety net (changed: {t != before})")
    
    print(f"After LaTeX fixes - length: {len(t)}")
    
    # Now proceed with normal normalization
    before = t
    t = t.replace('\\[', '$$').replace('\\]', '$$')
    if t != before:
        print(f"STEP 6 - Replace \\[ and \\] with $$ (changed: {t != before})")
    
    # The problematic line that was commented out
    # t = t.replace('\\(', '$').replace('\\)', '$')
    print(f"STEP 7 - SKIPPED: \\( and \\) replacement (would break \\left and \\right)")
    
    print(f"Final length: {len(t)}")
    
    # Check for errors at the end
    if r"\left$" in t:
        print(f"❌ ERROR: \\left$ found in output!")
        idx = t.find(r"\left$")
        print(f"   Position {idx}: {t[max(0,idx-50):idx+50]}")
    if r"\right$" in t:
        print(f"❌ ERROR: \\right$ found in output!")
        idx = t.find(r"\right$")
        print(f"   Position {idx}: {t[max(0,idx-50):idx+50]}")
    
    return t

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        print("="*70)
        print("TRACING NORMALIZATION PROCESS")
        print("="*70)
        
        # Extract just the title to get the body
        lines = article.split('\n')
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith('# '):
                body_start = i + 1
                break
        
        article_body = '\n'.join(lines[body_start:])
        
        print(f"\nOriginal article body length: {len(article_body)}")
        
        result = _normalize_article_for_rendering_traced(article_body)
        
        print(f"\n{'='*70}")
        print("NORMALIZATION COMPLETE")
        print(f"{'='*70}")
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
