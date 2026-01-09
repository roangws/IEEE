#!/usr/bin/env python3
"""
Test the NEW simplified bare LaTeX wrapping fix.
"""
import re

def fix_bare_latex_lines(text):
    """Wrap lines containing bare LaTeX in display math."""
    lines = text.split('\n')
    fixed_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines, tables, and lines already in math mode
        if not stripped or '|' in line or stripped.startswith('$$') or stripped.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # Check if line has LaTeX commands
        has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal|text|mathrm|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|sum|int|prod|lim|infty|partial|nabla|times|cdot)', line))
        
        if has_latex:
            # Count $ in the line
            dollar_count = line.count('$')
            
            # If no $ at all, this is bare LaTeX - wrap the entire line
            if dollar_count == 0:
                # This is a standalone equation line - wrap in display math
                fixed_lines.append(f"$$\n{stripped}\n$$")
                continue
            
            # If odd number of $, there's an unclosed $ - fix it
            if dollar_count % 2 == 1:
                # Find where the $ is and try to close the math mode properly
                # Simple fix: if line starts with $ but doesn't end with $, add $ at end
                if stripped.startswith('$') and not stripped.endswith('$'):
                    # Find the end of the LaTeX expression
                    # Look for punctuation or end of line
                    match = re.search(r'(\\right[)\]]|\\right\\}|\}|\))(\s*[,.]?)', stripped)
                    if match:
                        # Insert $ after the closing delimiter
                        insert_pos = match.end()
                        fixed_line = stripped[:insert_pos] + '$' + stripped[insert_pos:]
                        fixed_lines.append(fixed_line)
                        continue
        
        # No changes needed
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

print("="*70)
print("TESTING NEW SIMPLIFIED BARE LATEX FIX")
print("="*70)

# Test the exact problematic text from the PDF
pdf_text = """The theoretical implications of employing diffusion models in video restoration are profound. At the
core, these models facilitate a probabilistic framework that can be elegantly described by the equation:
q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right) = \\mathcal{N}\\left(\\mathbf{x}_t;
\\sqrt{\\alpha_t}\\mathbf{x}_{t-1}, \\left(1-\\alpha_t\\right)\\mathbf{I}\\right)"""

print("\nOriginal:")
for i, line in enumerate(pdf_text.split('\n'), 1):
    print(f"  {i}: {line}")

fixed = fix_bare_latex_lines(pdf_text)

print("\nFixed:")
for i, line in enumerate(fixed.split('\n'), 1):
    print(f"  {i}: {line}")

# Check if bare LaTeX line is now wrapped
lines = fixed.split('\n')
has_display_math = any('$$' in line for line in lines)

if has_display_math:
    print("\n✅ SUCCESS: Bare LaTeX line is now wrapped in $$ ... $$")
else:
    print("\n❌ FAIL: Bare LaTeX line not wrapped")

# Test the other problematic case
print("\n" + "="*70)
print("TEST: Unclosed $ delimiter")
print("="*70)

unclosed_text = "denoted as $q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict a process"

print(f"\nOriginal: {unclosed_text}")

fixed2 = fix_bare_latex_lines(unclosed_text)

print(f"Fixed:    {fixed2}")

# Check if the $ is now closed
if fixed2.count('$') % 2 == 0:
    print("\n✅ SUCCESS: $ delimiter is now properly closed")
else:
    print("\n❌ FAIL: $ delimiter still unclosed")

# Show where the $ was added
if '$' in fixed2:
    first_dollar = fixed2.index('$')
    last_dollar = fixed2.rindex('$')
    print(f"\nFirst $ at position {first_dollar}")
    print(f"Last $ at position {last_dollar}")
    print(f"Content between: {fixed2[first_dollar:last_dollar+1]}")
