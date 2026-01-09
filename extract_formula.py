#!/usr/bin/env python3
"""
Extract the exact formula causing the error
"""
import json
import os

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        # Find the formula
        idx = article.find("L_{\\text{hybrid}}")
        if idx >= 0:
            # Extract the full formula (from $$ to $$)
            start = article.rfind("$$", 0, idx)
            end = article.find("$$", idx) + 2
            
            formula = article[start:end]
            
            print("="*70)
            print("EXTRACTED FORMULA")
            print("="*70)
            print(formula)
            print("="*70)
            
            # Check for errors
            if "\\left$" in formula:
                print("\n❌ Contains \\left$")
            if "\\right$" in formula:
                print("\n❌ Contains \\right$")
            if "\\left(" in formula and "\\right)" in formula:
                print("\n✅ Uses proper \\left( and \\right)")
                
            # Show byte representation to check for hidden characters
            print("\n" + "="*70)
            print("BYTE REPRESENTATION (first 200 chars)")
            print("="*70)
            print(repr(formula[:200]))
        else:
            print("Formula not found")
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
