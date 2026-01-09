#!/usr/bin/env python3
"""
Debug the exact pattern that's failing.
"""
import json
import re

cache_path = ".ui_cache/ui_state.json"
with open(cache_path, 'r') as f:
    cache = json.load(f)

article = cache.get('generated_article', '')

# Find the exact problematic line
idx = article.find('$q\\left(\\mathbf{x}_t')
start = max(0, idx - 50)
end = min(len(article), idx + 300)
context = article[start:end]

print("="*70)
print("EXACT PROBLEMATIC TEXT")
print("="*70)
print(context)
print("\n" + "="*70)

# Extract just the line
lines = article.split('\n')
for i, line in enumerate(lines):
    if '$q\\left(\\mathbf{x}_t' in line:
        print(f"Line {i}: {line}")
        print(f"\nLine length: {len(line)}")
        print(f"$ count: {line.count('$')}")
        
        # Check the pattern
        if line.count('$') % 2 == 1:
            print("✓ Odd number of $ - unclosed delimiter detected")
            
            # Find the $ position
            dollar_pos = line.find('$')
            print(f"$ at position: {dollar_pos}")
            
            # What comes after?
            after = line[dollar_pos+1:]
            print(f"After $: {after[:100]}")
            
            # Look for \right)
            if '\\right)' in after:
                right_pos = after.find('\\right)')
                print(f"\\right) at position: {right_pos} (relative to $)")
                print(f"Text around \\right): {after[max(0,right_pos-20):right_pos+30]}")
                
                # What's after \right)?
                after_right = after[right_pos+7:]  # 7 = len('\right)')
                print(f"After \\right): '{after_right[:20]}'")
                
                # Check if there's a comma
                if after_right.startswith(','):
                    print("✓ Comma immediately after \\right)")
                    print("FIX: Should insert $ before the comma")
                    
                    # Apply the fix
                    insert_pos = dollar_pos + 1 + right_pos + 7
                    fixed = line[:insert_pos] + '$' + line[insert_pos:]
                    print(f"\nFixed line: {fixed}")
                    print(f"$ count after fix: {fixed.count('$')}")
        break
