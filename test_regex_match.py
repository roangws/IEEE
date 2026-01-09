#!/usr/bin/env python3
"""
Test if the regex pattern matches the actual text.
"""
import re

# The actual text from the article
text = r"$q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right), depict a process"

# Extract after the $
first_dollar = text.find('$')
after_dollar = text[first_dollar+1:]

print(f"Text: {text}")
print(f"After $: {after_dollar}")

# Test the regex pattern
pattern = r'(\\right[)\]])(\\s*[,;.])'
match = re.search(pattern, after_dollar)

if match:
    print(f"\n✅ Pattern matched!")
    print(f"Match: {match.group()}")
    print(f"Group 1 (\\right): {match.group(1)}")
    print(f"Group 2 (whitespace + punct): {match.group(2)}")
    print(f"Start of group 2: {match.start(2)}")
    
    # Calculate insert position
    insert_pos = first_dollar + 1 + match.start(2)
    fixed = text[:insert_pos] + '$' + text[insert_pos:]
    print(f"\nFixed: {fixed}")
else:
    print(f"\n❌ Pattern did NOT match")
    
    # Try without the whitespace requirement
    pattern2 = r'(\\right[)\]])([,;.])'
    match2 = re.search(pattern2, after_dollar)
    if match2:
        print(f"\n✅ Pattern WITHOUT \\s* matched!")
        print(f"Match: {match2.group()}")
        insert_pos = first_dollar + 1 + match2.start(2)
        fixed = text[:insert_pos] + '$' + text[insert_pos:]
        print(f"Fixed: {fixed}")
