# Test Streamlit PDF Download

## Steps to Test

1. **Start Streamlit:**
   ```bash
   ./run_streamlit.sh
   ```

2. **Check Terminal Output:**
   Look for one of these messages:
   - ✅ `MathJax PDF generator loaded successfully` = GOOD
   - ⚠️ `MathJax PDF generator not available: ...` = Problem with import

3. **Download PDF:**
   - Click "📄 Download PDF" button
   - Open the downloaded PDF

4. **Verify Formulas:**
   - Should see mathematical symbols (√, α, proper fractions)
   - Should NOT see LaTeX code like `\left`, `\mathbf`

---

## If MathJax PDF Generator Not Loading

Check terminal for error message and:

1. Verify Playwright is installed:
   ```bash
   ./venv/bin/pip show playwright
   ```

2. Verify Chromium is installed:
   ```bash
   ./venv/bin/playwright install chromium
   ```

3. Test generator directly:
   ```bash
   ./venv/bin/python3 html_mathjax_pdf_generator.py
   ```

---

## Expected Behavior

When you click "📄 Download PDF":
- PDF generation takes ~10-15 seconds (MathJax rendering time)
- Downloaded PDF has perfect formula rendering
- Formulas look exactly like in `MATHJAX_TIMING_TEST.pdf`

---

## Current Integration

- **File:** `app.py`
- **Lines 45-51:** Import MathJax PDF generator
- **Lines 1203-1220:** Use MathJax for PDF generation
- **Fallback:** ReportLab if MathJax fails

The integration is complete. Just need to verify it loads in Streamlit.
