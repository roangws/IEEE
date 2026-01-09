# Integration Issue Found

## Problem
The "Integrate External References" button:
- Shows spinner briefly
- No error message
- No integration happens

## Root Cause Analysis

Looking at the code, I see:
1. The UI defines a `progress_callback` function
2. But `SmartCitationIntegrator.integrate_citations_smart()` doesn't accept a `progress_callback` parameter
3. The integration might be failing silently

## Solution Needed

Either:
1. **Add progress_callback support to SmartCitationIntegrator**
2. **Remove progress callback from UI and handle differently**

## Quick Fix

Let's add error handling to show the actual error:

```python
try:
    integrator = SmartCitationIntegrator()
    enhanced_article = integrator.integrate_citations_smart(
        article_text=article_text,
        references=selected_refs,
        llm_type=llm_type,
        model=integration_model
    )
except Exception as e:
    st.error(f"❌ Integration error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
    return
```

This will show the actual error instead of failing silently.
