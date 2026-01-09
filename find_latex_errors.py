#!/usr/bin/env python3
"""
Search for the specific LaTeX error patterns in the cached article
"""
import json
import os
import re

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        print("="*70)
        print("SEARCHING FOR LATEX ERRORS IN ARTICLE")
        print("="*70)
        
        # Search for the specific patterns you're seeing
        patterns = [
            (r"\\left\$", "\\left$"),
            (r"\\right\$", "\\right$"),
            (r"\$\\left\(", "$\\left("),
            (r"L_\{\\text\{hybrid\}\}", "L_{\\text{hybrid}}"),
            (r"L_\{\\text\{diffusion\}\}", "L_{\\text{diffusion}}"),
        ]
        
        found_any = False
        for pattern, display in patterns:
            matches = list(re.finditer(pattern, article))
            if matches:
                found_any = True
                print(f"\n❌ Found {len(matches)} occurrence(s) of: {display}")
                for i, match in enumerate(matches[:3]):  # Show first 3
                    start = max(0, match.start() - 80)
                    end = min(len(article), match.end() + 80)
                    context = article[start:end]
                    print(f"\n  Occurrence {i+1} at position {match.start()}:")
                    print(f"  ...{context}...")
        
        if not found_any:
            print("\n✅ No LaTeX error patterns found in article")
            
        # Also search for the specific formula you showed
        search_terms = [
            "L_{\\text{hybrid}}",
            "L_{\\text{diffusion}}",
            "\\mathbf{x}_t",
        ]
        
        print("\n" + "="*70)
        print("SEARCHING FOR SPECIFIC FORMULAS")
        print("="*70)
        
        for term in search_terms:
            if term in article:
                idx = article.find(term)
                start = max(0, idx - 100)
                end = min(len(article), idx + 200)
                print(f"\nFound '{term}' at position {idx}:")
                print(f"{article[start:end]}")
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
