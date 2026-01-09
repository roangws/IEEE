#!/usr/bin/env python3
"""
Test the normalization function directly with the actual error pattern
"""
import re

def _normalize_article_for_rendering(text: str) -> str:
    """Normalize LaTeX/Markdown for reliable rendering in both webpage and PDF."""
    t = text or ""
    
    # CRITICAL PRE-PROCESSING: Fix malformed LaTeX delimiters FIRST
    # This is the last line of defense before rendering
    
    # Fix 1: Replace \left$ and \right$ with proper delimiters
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    
    # Fix 2: Remove $ that's incorrectly placed with \left or \right
    t = t.replace("$\\left(", "\\left(")
    t = t.replace("\\right)$", "\\right)")
    
    # Fix 3: Fix \left\frac (missing opening delimiter)
    t = t.replace("\\left\\frac", "\\left(\\frac")
    
    # Fix 4: Apply regex-based fixes (multiple aggressive passes)
    for _ in range(20):  # More passes for deeply nested issues
        before = t
        t = re.sub(r"\\left\$", r"\\left(", t)
        t = re.sub(r"\\right\$", r"\\right)", t)
        t = re.sub(r"\$\\left\(", r"\\left(", t)
        t = re.sub(r"\\right\)\$(?!\$)", r"\\right)", t)  # Don't break $$
        t = re.sub(r"\\left\\frac", r"\\left(\\frac", t)
        # Fix missing closing delimiter before letter (e.g., \rightV -> \right)V)
        t = re.sub(r"\\right([A-Za-z])", r"\\right)\1", t)
        if t == before:
            break  # No more changes
    
    # Fix 5: Final safety net - direct string replacements
    t = t.replace("\\left$", "\\left(")
    t = t.replace("\\right$", "\\right)")
    t = t.replace("$\\left(", "\\left(")
    
    return t

# Test with the exact error pattern from the UI
test_text = r"\text{softmax}\left$\frac{QK^T}{\sqrt{d_k}}\right$V"

print("="*70)
print("TESTING NORMALIZATION FUNCTION")
print("="*70)

print(f"\nInput text:")
print(f"  {test_text}")

# Check for errors before
errors_before = []
if r"\left$" in test_text:
    errors_before.append("\\left$")
if r"\right$" in test_text:
    errors_before.append("\\right$")

print(f"\nErrors detected: {errors_before}")

# Apply normalization
result = _normalize_article_for_rendering(test_text)

print(f"\nOutput text:")
print(f"  {result}")

# Check for errors after
errors_after = []
if r"\left$" in result:
    errors_after.append("\\left$")
if r"\right$" in result:
    errors_after.append("\\right$")

if errors_after:
    print(f"\n❌ NORMALIZATION FAILED - Errors still present: {errors_after}")
else:
    print(f"\n✅ NORMALIZATION SUCCESSFUL - All errors fixed")

# Show character-by-character comparison
print("\n" + "="*70)
print("CHARACTER COMPARISON")
print("="*70)
print(f"Input length:  {len(test_text)}")
print(f"Output length: {len(result)}")
print(f"Changed: {test_text != result}")

if test_text != result:
    print("\nDifferences:")
    for i, (a, b) in enumerate(zip(test_text, result)):
        if a != b:
            print(f"  Position {i}: '{a}' -> '{b}'")
