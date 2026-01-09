#!/usr/bin/env python3
"""
Comprehensive PDF Generation Diagnostic Script
Tests each potential failure point systematically.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

print("="*70)
print("PDF GENERATION DIAGNOSTIC REPORT")
print("="*70)

results = []

# TEST 1: Check if Pandoc is installed and in PATH
print("\n[TEST 1] Checking Pandoc installation...")
try:
    result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version = result.stdout.split('\n')[0]
        print(f"✅ PASS: {version}")
        results.append(("Pandoc installed", True, version))
    else:
        print(f"❌ FAIL: Pandoc returned error code {result.returncode}")
        results.append(("Pandoc installed", False, "Error code"))
except FileNotFoundError:
    print("❌ FAIL: Pandoc not found in PATH")
    results.append(("Pandoc installed", False, "Not in PATH"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Pandoc installed", False, str(e)))

# TEST 2: Check if pdflatex is installed and in PATH
print("\n[TEST 2] Checking pdflatex installation...")
try:
    env = os.environ.copy()
    env['PATH'] = '/Library/TeX/texbin:' + env.get('PATH', '')
    result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True, timeout=5, env=env)
    if result.returncode == 0:
        version = result.stdout.split('\n')[0]
        print(f"✅ PASS: {version}")
        results.append(("pdflatex installed", True, version))
    else:
        print(f"❌ FAIL: pdflatex returned error code {result.returncode}")
        results.append(("pdflatex installed", False, "Error code"))
except FileNotFoundError:
    print("❌ FAIL: pdflatex not found in PATH")
    results.append(("pdflatex installed", False, "Not in PATH"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("pdflatex installed", False, str(e)))

# TEST 3: Check if pandoc_pdf_generator.py exists and can be imported
print("\n[TEST 3] Checking pandoc_pdf_generator.py import...")
try:
    from pandoc_pdf_generator import PandocPDFGenerator
    print("✅ PASS: PandocPDFGenerator imported successfully")
    results.append(("Pandoc generator import", True, "Success"))
except ImportError as e:
    print(f"❌ FAIL: Import error - {e}")
    results.append(("Pandoc generator import", False, str(e)))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Pandoc generator import", False, str(e)))

# TEST 4: Check if article cache exists and has content
print("\n[TEST 4] Checking article cache...")
cache_path = ".ui_cache/ui_state.json"
if os.path.exists(cache_path):
    try:
        with open(cache_path, 'r') as f:
            cache = json.load(f)
        article = cache.get('generated_article', '')
        if article:
            print(f"✅ PASS: Article found ({len(article)} characters)")
            results.append(("Article cache", True, f"{len(article)} chars"))
        else:
            print("❌ FAIL: Article is empty")
            results.append(("Article cache", False, "Empty"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append(("Article cache", False, str(e)))
else:
    print("❌ FAIL: Cache file not found")
    results.append(("Article cache", False, "Not found"))

# TEST 5: Check for bare LaTeX in article
print("\n[TEST 5] Checking for bare LaTeX in article...")
try:
    import re
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    article = cache.get('generated_article', '')
    lines = article.split('\n')
    
    bare_latex_count = 0
    for line in lines:
        has_latex = bool(re.search(r'\\(?:left|right|frac|sqrt|mathbf|mathcal)', line))
        if has_latex and '$' not in line and '$$' not in line.strip():
            bare_latex_count += 1
    
    if bare_latex_count == 0:
        print("✅ PASS: No bare LaTeX found")
        results.append(("Bare LaTeX check", True, "None found"))
    else:
        print(f"❌ FAIL: Found {bare_latex_count} lines with bare LaTeX")
        results.append(("Bare LaTeX check", False, f"{bare_latex_count} lines"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Bare LaTeX check", False, str(e)))

# TEST 6: Check for unclosed $ delimiters
print("\n[TEST 6] Checking for unclosed $ delimiters...")
try:
    unclosed_count = 0
    for i, line in enumerate(lines):
        if '$' in line:
            dollar_count = line.count('$')
            if dollar_count % 2 == 1:
                unclosed_count += 1
    
    if unclosed_count == 0:
        print("✅ PASS: All $ delimiters are properly closed")
        results.append(("Unclosed delimiters", True, "All closed"))
    else:
        print(f"❌ FAIL: Found {unclosed_count} lines with unclosed $ delimiters")
        results.append(("Unclosed delimiters", False, f"{unclosed_count} lines"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Unclosed delimiters", False, str(e)))

# TEST 7: Check if Python cache exists
print("\n[TEST 7] Checking for Python bytecode cache...")
pycache_dirs = list(Path('.').rglob('__pycache__'))
if pycache_dirs:
    print(f"⚠️  WARNING: Found {len(pycache_dirs)} __pycache__ directories")
    print("   These may contain old compiled code")
    results.append(("Python cache", False, f"{len(pycache_dirs)} dirs"))
else:
    print("✅ PASS: No __pycache__ directories found")
    results.append(("Python cache", True, "Clean"))

# TEST 8: Test Pandoc with simple markdown
print("\n[TEST 8] Testing Pandoc with simple markdown...")
try:
    test_md = """# Test
    
This is a test with a formula: $E = mc^2$

$$
x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
$$
"""
    with open('test_simple.md', 'w') as f:
        f.write(test_md)
    
    env = os.environ.copy()
    env['PATH'] = '/Library/TeX/texbin:' + env.get('PATH', '')
    
    result = subprocess.run(
        ['pandoc', 'test_simple.md', '-o', 'test_simple.pdf', '--pdf-engine=pdflatex'],
        capture_output=True,
        text=True,
        timeout=30,
        env=env
    )
    
    if result.returncode == 0 and os.path.exists('test_simple.pdf'):
        size = os.path.getsize('test_simple.pdf')
        print(f"✅ PASS: Simple PDF generated ({size} bytes)")
        results.append(("Pandoc simple test", True, f"{size} bytes"))
        os.remove('test_simple.pdf')
    else:
        print(f"❌ FAIL: {result.stderr[:200]}")
        results.append(("Pandoc simple test", False, result.stderr[:100]))
    
    os.remove('test_simple.md')
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Pandoc simple test", False, str(e)))

# TEST 9: Check if app.py has Pandoc integration
print("\n[TEST 9] Checking app.py for Pandoc integration...")
try:
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    has_import = 'from pandoc_pdf_generator import PandocPDFGenerator' in app_content
    has_check = 'PANDOC_PDF_AVAILABLE' in app_content
    has_usage = 'PandocPDFGenerator()' in app_content
    
    if has_import and has_check and has_usage:
        print("✅ PASS: Pandoc integration found in app.py")
        results.append(("app.py integration", True, "Complete"))
    else:
        missing = []
        if not has_import: missing.append("import")
        if not has_check: missing.append("availability check")
        if not has_usage: missing.append("usage")
        print(f"❌ FAIL: Missing {', '.join(missing)}")
        results.append(("app.py integration", False, f"Missing {', '.join(missing)}"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("app.py integration", False, str(e)))

# TEST 10: Test PandocPDFGenerator with actual article
print("\n[TEST 10] Testing PandocPDFGenerator with actual article...")
try:
    from pandoc_pdf_generator import PandocPDFGenerator
    
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    article = cache.get('generated_article', '')
    
    generator = PandocPDFGenerator()
    pdf_buffer = generator.generate_pdf(article, "Test Article", "diagnostic_test.pdf")
    
    if os.path.exists('diagnostic_test.pdf'):
        size = os.path.getsize('diagnostic_test.pdf')
        print(f"✅ PASS: PDF generated from actual article ({size} bytes)")
        results.append(("Actual article PDF", True, f"{size} bytes"))
    else:
        print("❌ FAIL: PDF file not created")
        results.append(("Actual article PDF", False, "No file"))
except Exception as e:
    print(f"❌ FAIL: {e}")
    results.append(("Actual article PDF", False, str(e)[:100]))

# SUMMARY
print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)

passed = sum(1 for _, status, _ in results if status)
failed = len(results) - passed

print(f"\nTests Passed: {passed}/{len(results)}")
print(f"Tests Failed: {failed}/{len(results)}")

print("\nDetailed Results:")
for test_name, status, detail in results:
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {test_name:30s} - {detail}")

# RECOMMENDATIONS
print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

if not results[0][1]:  # Pandoc not installed
    print("\n1. Install Pandoc: brew install pandoc")

if not results[1][1]:  # pdflatex not installed
    print("\n2. Install BasicTeX: brew install --cask basictex")

if not results[4][1] or not results[5][1]:  # Bare LaTeX or unclosed delimiters
    print("\n3. Fix article LaTeX:")
    print("   - Run: ./venv/bin/python3 test_pdf_complete.py")
    print("   - Or click 'Validate & Fix LaTeX' button in Streamlit")

if not results[6][1]:  # Python cache exists
    print("\n4. Clear Python cache:")
    print("   - Run: find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null")

if not results[8][1]:  # app.py integration incomplete
    print("\n5. Verify app.py integration is complete")

if results[9][1]:  # Actual article PDF succeeded
    print("\n✅ GOOD NEWS: Pandoc CAN generate PDF from your article!")
    print("   The issue is likely in the Streamlit integration.")
    print("   Check that:")
    print("   - Python cache is cleared")
    print("   - Streamlit is restarted")
    print("   - The correct code path is being executed")

print("\n" + "="*70)
