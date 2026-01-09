#!/usr/bin/env python3
"""
Check what's actually in the cached session state article
"""
import json
import os

cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    article = cache.get('generated_article', '')
    
    if article:
        # Search for the specific error pattern
        search_pattern = r"\text{softmax}\left$"
        
        if search_pattern in article:
            print("❌ FOUND THE ERROR IN CACHED ARTICLE!")
            idx = article.find(search_pattern)
            print(f"\nPosition: {idx}")
            print(f"Context:\n{article[idx:idx+200]}")
        else:
            print("✅ Error pattern NOT found in cached article")
            
        # Check for any \left$ or \right$ patterns
        if r"\left$" in article:
            print(f"\n❌ Found \\left$ in article ({article.count(r'\left$')} occurrences)")
            # Show first occurrence
            idx = article.find(r"\left$")
            print(f"First occurrence at position {idx}:")
            print(f"{article[max(0,idx-50):idx+100]}")
        else:
            print("\n✅ No \\left$ found in article")
            
        if r"\right$" in article:
            print(f"\n❌ Found \\right$ in article ({article.count(r'\right$')} occurrences)")
        else:
            print("✅ No \\right$ found in article")
    else:
        print("No article in cache")
else:
    print(f"Cache file not found: {cache_path}")
