#!/usr/bin/env python3
"""
Test if the normalization function is working correctly
"""

# Test the exact error pattern you're seeing
test_latex = r"\text{softmax}\left$\frac{QK^T}{\sqrt{d_k}}\right$V"

print("="*70)
print("TESTING NORMALIZATION FUNCTION")
print("="*70)

print(f"\nOriginal LaTeX:")
print(f"  {test_latex}")

# Check if the pattern exists
if r"\left$" in test_latex:
    print(f"\n❌ Contains \\left$ error")
if r"\right$" in test_latex:
    print(f"❌ Contains \\right$ error")

# Apply the fix manually
fixed = test_latex.replace("\\left$", "\\left(")
fixed = fixed.replace("\\right$", "\\right)")

print(f"\nFixed LaTeX:")
print(f"  {fixed}")

# Verify fix
if r"\left$" not in fixed and r"\right$" not in fixed:
    print(f"\n✅ Fix successful!")
else:
    print(f"\n❌ Fix failed!")

print("\n" + "="*70)
print("CHECKING IF THIS IS A RAW STRING ISSUE")
print("="*70)

# The issue might be that the errors are in the markdown as literal text
# not as Python raw strings
markdown_version = "\\text{softmax}\\left$\\frac{QK^T}{\\sqrt{d_k}}\\right$V"
print(f"\nMarkdown version (escaped):")
print(f"  {markdown_version}")

if "\\left$" in markdown_version:
    print("❌ Contains \\left$ in markdown")
    
fixed_md = markdown_version.replace("\\left$", "\\left(")
fixed_md = fixed_md.replace("\\right$", "\\right)")

print(f"\nFixed markdown:")
print(f"  {fixed_md}")

if "\\left$" not in fixed_md:
    print("✅ Markdown fix successful!")
