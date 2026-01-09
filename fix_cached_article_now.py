#!/usr/bin/env python3
"""
Directly fix the cached article by applying the LaTeX normalization.
"""
import json
import os
import re

def _validate_and_fix_latex_delimiters(article: str) -> str:
    """Fix LaTeX delimiters - comprehensive version."""
    # Fix malformed delimiters
    article = article.replace("\\left$", "\\left(")
    article = article.replace("\\right$", "\\right)")
    article = article.replace("$\\left(", "\\left(")
    article = article.replace("\\right)$", "\\right)")
    article = article.replace("\\left\\frac", "\\left(\\frac")
    
    # Apply regex fixes
    for _ in range(15):
        before = article
        article = re.sub(r"\\left\$", r"\\left(", article)
        article = re.sub(r"\\right\$", r"\\right)", article)
        article = re.sub(r"\$\\left\(", r"\\left(", article)
        article = re.sub(r"\\right\)\$(?!\$)", r"\\right)", article)
        article = re.sub(r"\\left\\frac", r"\\left(\\frac", article)
        article = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", article)
        if article == before:
            break
    
    # Final safety net
    article = article.replace("\\left$", "\\left(")
    article = article.replace("\\right$", "\\right)")
    article = article.replace("$\\left(", "\\left(")
    
    return article

def fix_unclosed_delimiters(text: str) -> str:
    """Fix unclosed $ delimiters in lines."""
    lines = text.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Count $ in the line
        dollar_count = line.count('$')
        
        # If odd number of $, there's an unclosed $
        if dollar_count % 2 == 1:
            if '$' in line:
                # Find the first $ position
                first_dollar_pos = line.find('$')
                after_dollar = line[first_dollar_pos+1:]
                
                # Check if there's LaTeX after it
                if re.search(r'\\(?:left|right|mathbf|mathcal)', after_dollar):
                    # Find \right) followed by comma or punctuation
                    match = re.search(r'(\\right[)\]])(\s*[,;.])', after_dollar)
                    if match:
                        # Insert $ right after \right) and before punctuation
                        insert_pos = first_dollar_pos + 1 + match.start(2)
                        line = line[:insert_pos] + '$' + line[insert_pos:]
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# Load cache
cache_path = ".ui_cache/ui_state.json"
if not os.path.exists(cache_path):
    print("❌ Cache file not found")
    exit(1)

with open(cache_path, 'r') as f:
    cache = json.load(f)

article = cache.get('generated_article', '')
if not article:
    print("❌ No article in cache")
    exit(1)

print("="*70)
print("FIXING CACHED ARTICLE")
print("="*70)

# Check for the problematic pattern
if '$q\\left(\\mathbf{x}_t' in article:
    idx = article.find('$q\\left(\\mathbf{x}_t')
    context_before = article[max(0,idx-50):min(len(article),idx+150)]
    print(f"\nBEFORE fix:")
    print(context_before)
    
    # Apply fixes
    print(f"\nApplying LaTeX delimiter fixes...")
    fixed = _validate_and_fix_latex_delimiters(article)
    
    print(f"Applying unclosed delimiter fixes...")
    fixed = fix_unclosed_delimiters(fixed)
    
    # Check after
    if '$q\\left(\\mathbf{x}_t' in fixed:
        idx2 = fixed.find('$q\\left(\\mathbf{x}_t')
        context_after = fixed[max(0,idx2-50):min(len(fixed),idx2+150)]
        print(f"\nAFTER fix:")
        print(context_after)
        
        # Count changes
        changes = sum(1 for a, b in zip(article, fixed) if a != b)
        if changes > 0:
            print(f"\n✅ Applied {changes} character corrections")
            
            # Update cache
            cache['generated_article'] = fixed
            if cache.get('base_generated_article') == article:
                cache['base_generated_article'] = fixed
            
            # Save
            with open(cache_path, 'w') as f:
                json.dump(cache, f, indent=2)
            
            print(f"💾 Saved fixed article to cache")
            print(f"\n⚠️  IMPORTANT: Refresh your browser and download PDF again")
        else:
            print(f"\n⚠️  No changes made - pattern might already be fixed")
    else:
        print(f"\n✅ Pattern no longer found - article is fixed")
        
        # Save anyway
        cache['generated_article'] = fixed
        if cache.get('base_generated_article') == article:
            cache['base_generated_article'] = fixed
        
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
        
        print(f"💾 Saved to cache")
        print(f"\n⚠️  IMPORTANT: Refresh your browser and download PDF again")
else:
    print(f"\n⚠️  Problematic pattern not found in article")
    print(f"   Searching for any unclosed delimiters...")
    
    # Apply fixes anyway
    fixed = _validate_and_fix_latex_delimiters(article)
    fixed = fix_unclosed_delimiters(fixed)
    
    changes = sum(1 for a, b in zip(article, fixed) if a != b)
    if changes > 0:
        print(f"✅ Applied {changes} corrections")
        cache['generated_article'] = fixed
        if cache.get('base_generated_article') == article:
            cache['base_generated_article'] = fixed
        
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
        
        print(f"💾 Saved to cache")
        print(f"\n⚠️  Refresh browser and download PDF again")
    else:
        print(f"✅ No changes needed")
