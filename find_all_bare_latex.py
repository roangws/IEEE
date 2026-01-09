#!/usr/bin/env python3
"""
Find ALL bare LaTeX formulas in the article.
"""
import json
import re

cache_path = ".ui_cache/ui_state.json"
with open(cache_path, 'r') as f:
    cache = json.load(f)

article = cache.get('generated_article', '')

print("="*70)
print("FINDING ALL BARE LATEX FORMULAS")
print("="*70)

lines = article.split('\n')

# Find all lines with bare LaTeX (LaTeX commands but no $ or $$)
bare_latex_lines = []

for i, line in enumerate(lines, 1):
    # Check if line has LaTeX commands
    has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|text|alpha|beta|gamma|theta)', line))
    
    if has_latex:
        # Check if it has $ delimiters
        dollar_count = line.count('$')
        
        # If no $ at all, it's bare LaTeX
        if dollar_count == 0:
            bare_latex_lines.append((i, line))
            print(f"\nLine {i} (NO $):")
            print(f"  {line[:150]}")
        
        # If odd number of $, unclosed delimiter
        elif dollar_count % 2 == 1:
            bare_latex_lines.append((i, line))
            print(f"\nLine {i} (UNCLOSED $, count={dollar_count}):")
            print(f"  {line[:150]}")

print(f"\n{'='*70}")
print(f"SUMMARY: Found {len(bare_latex_lines)} lines with bare/unclosed LaTeX")
print(f"{'='*70}")

# Show specific problematic patterns
print(f"\nSearching for specific patterns...")

# Pattern 1: q\left without opening $
if 'q\\left(' in article:
    count = article.count('q\\left(')
    print(f"  - 'q\\left(' appears {count} times")
    
# Pattern 2: p_{\theta}\left without proper delimiters  
if 'p_{\\theta}\\left(' in article:
    count = article.count('p_{\\theta}\\left(')
    print(f"  - 'p_{{\\theta}}\\left(' appears {count} times")

# Pattern 3: Standalone formulas on their own lines
standalone_formulas = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped and not stripped.startswith('#') and '|' not in stripped:
        # Check if entire line is a formula (starts with LaTeX command)
        if re.match(r'^[a-z_]\\left\(', stripped) or re.match(r'^\\mathcal', stripped):
            standalone_formulas.append((i, stripped))

if standalone_formulas:
    print(f"\n  - {len(standalone_formulas)} standalone formula lines:")
    for i, formula in standalone_formulas[:5]:
        print(f"    Line {i}: {formula[:100]}")
