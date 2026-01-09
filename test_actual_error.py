#!/usr/bin/env python3
"""
Test normalization with the ACTUAL error from the UI
"""
import re

def _normalize_article_for_rendering(text: str) -> str:
    """Normalize LaTeX/Markdown for reliable rendering in both webpage and PDF."""
    t = text or ""
    
    print(f"INPUT: {repr(t[:200])}")
    
    # CRITICAL PRE-PROCESSING: Fix malformed LaTeX delimiters FIRST
    # This is the last line of defense before rendering
    
    # Fix 1: Replace \left$ and \right$ with proper delimiters
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    print(f"After Fix 1: {repr(t[:200])}")
    
    # Fix 2: Remove $ that's incorrectly placed with \left or \right
    t = t.replace("$\\left(", "\\left(")
    t = t.replace("\\right)$", "\\right)")
    
    # Fix 3: Fix \left\frac (missing opening delimiter)
    t = t.replace("\\left\\frac", "\\left(\\frac")
    
    # Fix 4: Apply regex-based fixes (multiple aggressive passes)
    for i in range(20):  # More passes for deeply nested issues
        before = t
        t = re.sub(r"\\left\$", r"\\left(", t)
        t = re.sub(r"\\right\$", r"\\right)", t)
        t = re.sub(r"\$\\left\(", r"\\left(", t)
        t = re.sub(r"\\right\)\$(?!\$)", r"\\right)", t)  # Don't break $$
        t = re.sub(r"\\left\\frac", r"\\left(\\frac", t)
        # Fix missing closing delimiter before letter (e.g., \rightV -> \right)V)
        t = re.sub(r"\\right([A-Za-z])", r"\\right)\\1", t)
        if t == before:
            print(f"Regex loop stopped at iteration {i}")
            break  # No more changes
    
    print(f"After Fix 4: {repr(t[:200])}")
    
    # Fix 5: Final safety net - direct string replacements
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    
    print(f"FINAL: {repr(t[:200])}")
    
    return t

# Test with the EXACT error from the UI
test_formula = r"L_{\text{diffusion}}\left$\mathbf{x}_t, \mathbf{x}_{t-1}\right$"

print("="*70)
print("TESTING WITH ACTUAL ERROR FROM UI")
print("="*70)
print(f"\nOriginal: {test_formula}")

# Check for errors
if r"\left$" in test_formula:
    print("✓ Contains \\left$ error")
if r"\right$" in test_formula:
    print("✓ Contains \\right$ error")

print("\n" + "="*70)
print("RUNNING NORMALIZATION")
print("="*70)

result = _normalize_article_for_rendering(test_formula)

print("\n" + "="*70)
print("RESULT")
print("="*70)
print(f"Output: {result}")

# Check if fixed
if r"\left$" in result or r"\right$" in result:
    print("\n❌ FAILED - Errors still present")
else:
    print("\n✅ SUCCESS - Errors fixed")
