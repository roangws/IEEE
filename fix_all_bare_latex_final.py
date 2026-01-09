#!/usr/bin/env python3
"""
Comprehensive fix for ALL bare LaTeX in the article.
"""
import json
import re

def comprehensive_latex_fix(text: str) -> str:
    """Apply all LaTeX fixes comprehensively."""
    lines = text.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines, headers, tables
        if not stripped or stripped.startswith('#') or '|' in line or stripped.startswith('$$'):
            fixed_lines.append(line)
            i += 1
            continue
        
        # Check if line has LaTeX
        has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|text|alpha|beta|gamma|theta|lambda|mu|sigma)', line))
        
        if has_latex:
            dollar_count = line.count('$')
            
            # Case 1: NO $ at all - bare LaTeX
            if dollar_count == 0:
                # Check if it's a standalone formula line (entire line is formula)
                if re.match(r'^[a-z_]\\left\(|^\\mathcal|^\\sqrt', stripped):
                    # This is a standalone formula - wrap in display math
                    # Check if next lines are also part of the formula
                    formula_lines = [stripped]
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            break
                        # Check if continuation of formula
                        if re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|alpha|beta|gamma)', next_line) and '$' not in next_line:
                            formula_lines.append(next_line)
                            j += 1
                        else:
                            break
                    
                    # Wrap entire formula
                    formula = '\n'.join(formula_lines)
                    fixed_lines.append(f"$$\n{formula}\n$$")
                    i = j
                    continue
                else:
                    # LaTeX embedded in text - wrap inline
                    # Find LaTeX expressions and wrap them
                    fixed_line = line
                    # Simple approach: wrap entire line if it has significant LaTeX
                    if re.search(r'\\left\(.*\\right\)', line):
                        # Find the LaTeX expression
                        match = re.search(r'([a-z_]+\\left\(.*?\\right\))', line)
                        if match:
                            latex_expr = match.group(1)
                            fixed_line = line.replace(latex_expr, f"${latex_expr}$")
                    fixed_lines.append(fixed_line)
                    i += 1
                    continue
            
            # Case 2: Odd number of $ - unclosed delimiter
            elif dollar_count % 2 == 1:
                # Find first $ and check if LaTeX after it
                first_dollar = line.find('$')
                if first_dollar >= 0:
                    after_dollar = line[first_dollar+1:]
                    if re.search(r'\\(?:left|right|mathbf|mathcal)', after_dollar):
                        # Find \right) followed by punctuation
                        match = re.search(r'(\\right[)\]])(\s*[,;.])', after_dollar)
                        if match:
                            insert_pos = first_dollar + 1 + match.start(2)
                            line = line[:insert_pos] + '$' + line[insert_pos:]
                
                fixed_lines.append(line)
                i += 1
                continue
        
        # No LaTeX or already properly formatted
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

# Load and fix
cache_path = ".ui_cache/ui_state.json"
with open(cache_path, 'r') as f:
    cache = json.load(f)

article = cache.get('generated_article', '')

print("="*70)
print("COMPREHENSIVE LATEX FIX")
print("="*70)

# Show problematic line 63 before
lines = article.split('\n')
if len(lines) > 63:
    print(f"\nLine 63 BEFORE:")
    print(f"  {lines[62]}")

# Apply fix
print(f"\nApplying comprehensive fix...")
fixed = comprehensive_latex_fix(article)

# Show after
fixed_lines = fixed.split('\n')
if len(fixed_lines) > 63:
    print(f"\nLine 63 AFTER:")
    for i in range(max(0, 62), min(len(fixed_lines), 67)):
        print(f"  {i+1}: {fixed_lines[i][:100]}")

# Count changes
changes = sum(1 for a, b in zip(article, fixed) if a != b)
print(f"\n✅ Applied {changes} character corrections")

# Save
cache['generated_article'] = fixed
if cache.get('base_generated_article') == article:
    cache['base_generated_article'] = fixed

with open(cache_path, 'w') as f:
    json.dump(cache, f, indent=2)

print(f"💾 Saved to cache")
print(f"\n⚠️  CRITICAL: Refresh browser and download PDF again")
