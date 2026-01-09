#!/usr/bin/env python3
"""
Find the actual malformed LaTeX in the cached article
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
        print("SEARCHING FOR MALFORMED LATEX PATTERNS")
        print("="*70)
        
        # Search for the specific error pattern from the UI
        patterns = [
            (r"q\\left\\mathbf", "q\\left without opening paren"),
            (r"\\left(?![(\[])", "\\left not followed by ( or ["),
            (r"\\right(?![)\]])", "\\right not followed by ) or ]"),
            (r"\\left\s+\\mathbf", "\\left with space before \\mathbf"),
        ]
        
        for pattern, desc in patterns:
            matches = list(re.finditer(pattern, article))
            if matches:
                print(f"\n❌ Found {len(matches)} occurrence(s) of: {desc}")
                for i, match in enumerate(matches[:3]):
                    start = max(0, match.start() - 100)
                    end = min(len(article), match.end() + 100)
                    context = article[start:end]
                    print(f"\n  Match {i+1} at position {match.start()}:")
                    print(f"  {repr(context)}")
        
        # Search for the specific text from the error message
        search_text = "q\\left\\mathbf{x}_t"
        if search_text in article:
            idx = article.find(search_text)
            print(f"\n\n{'='*70}")
            print(f"FOUND EXACT ERROR PATTERN at position {idx}")
            print(f"{'='*70}")
            start = max(0, idx - 150)
            end = min(len(article), idx + 200)
            print(article[start:end])
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
