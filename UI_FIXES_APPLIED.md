# UI Fixes Applied

## 1. JSON Expanders Collapsed by Default

### Fixed:
- **Debug: Data Sources for Metrics** - Now collapsed (was expanded)
- **Citation Data** - Now collapsed in its own expander

### Before:
- JSON objects were expanded by default, taking up lots of screen space
- Made the UI cluttered and hard to navigate

### After:
- Clean, collapsed UI
- Users can expand only what they need to see
- Much better user experience

## 2. LaTeX Formula Display Issue

The issue with `q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right)` showing underscores as italics is a Streamlit markdown rendering issue. 

### Current Status:
- The formulas render correctly in the PDF (with MathJax)
- In the Streamlit UI, underscores in math mode sometimes render as italics
- This is a known limitation of Streamlit's markdown renderer

### Possible Solutions:
1. Use `st.latex()` for individual formulas
2. Replace underscores with `\\_` in display mode
3. Accept the limitation (formulas work in PDF)

### Recommendation:
Since the PDF generation works perfectly with MathJax, this UI display issue is minor and doesn't affect the final output.

## Summary

✅ JSON objects now collapsed by default  
⚠️ LaTeX underscore issue in UI (PDF works perfectly)  

The UI is now much cleaner and more user-friendly!
