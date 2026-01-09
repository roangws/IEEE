# Step 4 Issues Analysis & Solutions

## Problem 1: LaTeX Formula Not Rendering

### Issue:
LaTeX formulas like `q\left(\mathbf{x}_t \mid \mathbf{x}_{t-1}\right) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{\alpha_t}\mathbf{x}_{t-1}, \left(1-\alpha_t\right)\mathbf{I}\right)` are displayed as plain text instead of rendered math.

### Root Cause:
Streamlit's `st.markdown()` with `unsafe_allow_html=True` doesn't automatically render LaTeX. It needs either:
- MathJax/KaTeX JavaScript libraries loaded
- Or conversion to Streamlit's native LaTeX format using `$...$` or `$$...$$`

### Solution:
Add LaTeX rendering support by converting LaTeX expressions before display:
```python
# Convert LaTeX expressions to Streamlit format
import re
def render_latex(text):
    # Convert inline math: \(...\) or $...$ to Streamlit format
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text)
    # Convert display math: \[...\] or $$...$$ to Streamlit format  
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text)
    return text

article_body = render_latex(article_body)
st.markdown(article_body, unsafe_allow_html=True)
```

---

## Problem 2: Download Enhanced Article (PDF) Button Uses Wrong Article

### Issue:
The "Download Enhanced Article (PDF)" button at line 1338 should use the enhanced article with external references, but it's unclear which article variable it's using.

### Root Cause:
Looking at line 1266: `full_article = enhanced_article + "\n\n## References\n\n" + "\n".join(all_refs)`
This is correct, but we need to verify it's using the `external_enhanced_article` not the original.

### Solution:
Ensure the PDF download uses the correct article:
```python
# Line 1336 should use full_article which includes enhanced_article + references
pdf_bytes = _build_pdf_from_markdown(full_article)
```

This appears correct, but we should verify `enhanced_article` is actually `external_enhanced_article`.

---

## Problem 3: Preview Article Button Doesn't Make Sense

### Issue:
The "📄 Preview Article" button at line 1250 shows a text area with truncated article, which is redundant since the full article is already displayed above.

### Solution:
**Option 1:** Remove the button entirely (RECOMMENDED)
**Option 2:** Change it to "📄 Download PDF" to match the other download button
**Option 3:** Make it show a formatted preview in a modal/expander

Recommendation: Remove it since the article is already fully visible on the page.

---

## Problem 4: External References Not Appearing in Article Body

### Issue:
External references like [40] are listed in the "External References (verification links)" section but don't appear in the article text itself.

### Root Cause Analysis:
This is the CRITICAL issue. The integration process should have added citations like [40], [41], etc. to the article body, but they're missing.

**Possible causes:**
1. Integration failed silently
2. LLM didn't add the citations despite instructions
3. Citations were added but then stripped during processing
4. Wrong article is being displayed (showing pre-integration version)

### Investigation Needed:
Check:
1. Is `enhanced_article` actually the integrated version from `st.session_state.external_enhanced_article`?
2. Did the integration process complete successfully?
3. Are external citation numbers present in the enhanced article?

### Solution:
```python
# Verify we're using the correct article
enhanced_article = st.session_state.get('external_enhanced_article')

# Debug: Check if external citations exist
import re
all_citations = set(re.findall(r'\[(\d+)\]', enhanced_article))
external_citation_numbers = {ref.citation_number for ref in external_refs_formatted}

# Log which external citations are missing
missing = external_citation_numbers - all_citations
if missing:
    st.warning(f"⚠️ {len(missing)} external citations not found in article: {sorted(missing)}")
```

---

## Priority Order:

1. **Problem 4** (HIGH) - External references not in body - this defeats the purpose of integration
2. **Problem 1** (MEDIUM) - LaTeX rendering - affects readability
3. **Problem 3** (LOW) - Remove redundant preview button - UX cleanup
4. **Problem 2** (LOW) - Verify PDF uses correct article - likely already correct

---

## Implementation Plan:

1. First, investigate Problem 4 to understand why external references aren't in the article
2. Fix Problem 1 by adding LaTeX rendering support
3. Remove Problem 3's redundant button
4. Verify Problem 2's PDF download is correct
