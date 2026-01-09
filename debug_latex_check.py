#!/usr/bin/env python3
"""
Debug script to check for LaTeX errors in cached article
"""
import json
import os

# Load the cached article
cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        print("="*70)
        print("CHECKING CACHED ARTICLE FOR LATEX ERRORS")
        print("="*70)
        
        errors = []
        
        # Check for malformed patterns
        if r"\left$" in article:
            count = article.count(r"\left$")
            errors.append(f"\\left$ found {count} times")
            
        if r"\right$" in article:
            count = article.count(r"\right$")
            errors.append(f"\\right$ found {count} times")
            
        if r"$\left(" in article:
            count = article.count(r"$\left(")
            errors.append(f"$\\left( found {count} times")
            
        if r"\left\frac" in article:
            count = article.count(r"\left\frac")
            errors.append(f"\\left\\frac found {count} times")
        
        if errors:
            print("\n❌ ERRORS FOUND:")
            for error in errors:
                print(f"  - {error}")
            
            print("\n" + "="*70)
            print("SAMPLE OCCURRENCES:")
            print("="*70)
            
            # Show first occurrence of \left$
            if r"\left$" in article:
                idx = article.find(r"\left$")
                start = max(0, idx - 50)
                end = min(len(article), idx + 100)
                print(f"\n\\left$ at position {idx}:")
                print(f"...{article[start:end]}...")
            
            # Show first occurrence of \right$
            if r"\right$" in article:
                idx = article.find(r"\right$")
                start = max(0, idx - 50)
                end = min(len(article), idx + 100)
                print(f"\n\\right$ at position {idx}:")
                print(f"...{article[start:end]}...")
        else:
            print("\n✅ NO ERRORS FOUND")
            print("Article appears to be valid")
        
        print("\n" + "="*70)
        print(f"Total article length: {len(article)} characters")
        print(f"Total article words: ~{len(article.split())} words")
        print("="*70)
    else:
        print("No article found in cache")
else:
    print(f"Cache file not found: {cache_path}")
