#!/usr/bin/env python3
"""
Test the bare LaTeX wrapping fix without importing the full app.
"""
import re

def _normalize_article_for_rendering(text: str) -> str:
    """Simplified version of normalization focusing on bare LaTeX wrapping."""
    t = text or ""
    
    # Pattern to detect bare LaTeX commands that should be in math mode
    latex_commands = r'\\(?:left|right|frac|sqrt|mathbf|mathcal|text|mathrm|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|sum|int|prod|lim|infty|partial|nabla)'
    
    # Fix inline bare LaTeX: wrap in $ ... $
    def wrap_bare_latex(text):
        """Wrap bare LaTeX commands in $ delimiters."""
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip lines that are already in display math or tables
            if line.strip().startswith('$$') or '|' in line:
                fixed_lines.append(line)
                continue
            
            modified_line = line
            
            # Find all positions of LaTeX commands
            matches = list(re.finditer(latex_commands, line))
            
            if matches:
                # Process from right to left to preserve positions
                for match in reversed(matches):
                    pos = match.start()
                    
                    # Check if already in math mode
                    # Count $ before this position
                    dollars_before = line[:pos].count('$')
                    
                    # If odd number of $, we're already in math mode
                    if dollars_before % 2 == 1:
                        continue
                    
                    # Find the extent of the LaTeX expression
                    start = pos
                    end = pos
                    
                    # Extend backwards to catch full expression
                    while start > 0 and line[start-1] not in [' ', '\n', '\t', ',', '.', ';']:
                        start -= 1
                    
                    # Extend forwards to catch full expression
                    brace_depth = 0
                    paren_depth = 0
                    while end < len(line):
                        char = line[end]
                        if char == '{':
                            brace_depth += 1
                        elif char == '}':
                            brace_depth -= 1
                        elif char == '(':
                            paren_depth += 1
                        elif char == ')':
                            paren_depth -= 1
                            if paren_depth == 0 and brace_depth == 0:
                                end += 1
                                break
                        elif char in [' ', ',', '.', ';', '\n'] and brace_depth == 0 and paren_depth == 0:
                            break
                        elif char == '\\':
                            # Continue through LaTeX commands
                            end += 1
                            continue
                        end += 1
                    
                    # Extract the LaTeX expression
                    latex_expr = line[start:end].strip()
                    
                    # Only wrap if it's substantial LaTeX (not just a single command)
                    if len(latex_expr) > 3 and '\\' in latex_expr:
                        # Wrap in $ ... $
                        wrapped = f"${latex_expr}$"
                        modified_line = line[:start] + wrapped + line[end:]
                        line = modified_line  # Update for next iteration
            
            fixed_lines.append(modified_line)
        
        return '\n'.join(fixed_lines)
    
    t = wrap_bare_latex(t)
    return t

# Test cases
print("="*70)
print("TESTING BARE LATEX WRAPPING")
print("="*70)

test_cases = [
    {
        "name": "User's exact problematic text",
        "input": "denoted as $q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict a process",
        "expected_fix": "wrap the bare LaTeX after the comma"
    },
    {
        "name": "Bare LaTeX in middle of sentence",
        "input": "These models, often denoted as q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right), depict a process",
        "expected_fix": "wrap q\\left(...\\right)"
    },
    {
        "name": "Already properly wrapped",
        "input": "$q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right)$",
        "expected_fix": "no change needed"
    },
    {
        "name": "Multiple bare LaTeX expressions",
        "input": "where \\mathbf{x}_t represents frame at time t and \\alpha_t is the noise",
        "expected_fix": "wrap both expressions"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['name']}")
    print(f"Input:  {test['input']}")
    
    result = _normalize_article_for_rendering(test['input'])
    print(f"Output: {result}")
    
    # Check if bare LaTeX was wrapped
    if result != test['input']:
        print(f"✅ Modified (expected: {test['expected_fix']})")
    else:
        print(f"⚠️  No change")
    
    # Check for bare LaTeX remaining
    # Simple check: LaTeX command not in $ ... $
    has_bare_latex = False
    for match in re.finditer(r'\\(?:left|mathbf|mathcal|alpha)', result):
        pos = match.start()
        dollars_before = result[:pos].count('$')
        if dollars_before % 2 == 0:  # Even number = not in math mode
            has_bare_latex = True
            print(f"❌ Still has bare LaTeX at position {pos}: {result[max(0,pos-20):pos+40]}")
            break
    
    if not has_bare_latex:
        print(f"✅ No bare LaTeX remaining")

print("\n" + "="*70)
print("SPECIFIC TEST: User's PDF Error")
print("="*70)

# The exact text from the PDF error
pdf_text = """The theoretical implications of employing diffusion models in video restoration are profound. At the
core, these models facilitate a probabilistic framework that can be elegantly described by the equation:
q\\left(\\mathbf{x}_t \\mid \\mathbf{x}_{t-1}\\right) = \\mathcal{N}\\left(\\mathbf{x}_t;
\\sqrt{\\alpha_t}\\mathbf{x}_{t-1}, \\left(1-\\alpha_t\\right)\\mathbf{I}\\right)"""

print("\nOriginal:")
print(pdf_text)

fixed = _normalize_article_for_rendering(pdf_text)

print("\nFixed:")
print(fixed)

# Check if the bare q\left is now wrapped
if '$q\\left(' in fixed or '$$q\\left(' in fixed:
    print("\n✅ SUCCESS: Bare LaTeX is now wrapped in $ delimiters")
else:
    print("\n❌ FAIL: Bare LaTeX still not wrapped")
    print("\nDEBUG: Looking for LaTeX commands...")
    for match in re.finditer(r'\\(?:left|mathcal|sqrt|alpha)', fixed):
        pos = match.start()
        context = fixed[max(0,pos-30):min(len(fixed),pos+50)]
        dollars_before = fixed[:pos].count('$')
        print(f"  Found at {pos} (${dollars_before} before): ...{context}...")
