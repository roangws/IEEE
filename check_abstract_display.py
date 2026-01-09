#!/usr/bin/env python3
"""
Check if the abstract is present in the article and how it's being extracted
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
        print("CHECKING ABSTRACT IN ARTICLE")
        print("="*70)
        
        lines = article.split('\n')
        
        # Show first 20 lines
        print("\nFirst 20 lines of article:")
        print("-"*70)
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:3d}: {line}")
        
        # Check for abstract section
        print("\n" + "="*70)
        print("SEARCHING FOR ABSTRACT")
        print("="*70)
        
        abstract_found = False
        for i, line in enumerate(lines):
            if 'abstract' in line.lower():
                print(f"\nFound 'abstract' at line {i+1}: {line}")
                # Show context
                start = max(0, i-2)
                end = min(len(lines), i+10)
                print("\nContext:")
                for j in range(start, end):
                    marker = ">>>" if j == i else "   "
                    print(f"{marker} {j+1:3d}: {lines[j]}")
                abstract_found = True
                break
        
        if not abstract_found:
            print("\n❌ No abstract section found in article")
        
        # Simulate title extraction
        print("\n" + "="*70)
        print("SIMULATING TITLE EXTRACTION")
        print("="*70)
        
        for i, line in enumerate(lines[:10]):
            stripped = line.strip()
            if not stripped:
                continue
            
            if stripped.startswith('# '):
                title = stripped[2:].strip()
                remaining_lines = lines[:i] + lines[i+1:]
                article_body = '\n'.join(remaining_lines)
                
                print(f"\nTitle found at line {i+1}: {title}")
                print(f"\nArticle body starts with:")
                print("-"*70)
                body_lines = article_body.split('\n')
                for j, bline in enumerate(body_lines[:15], 1):
                    print(f"{j:3d}: {bline}")
                break
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
