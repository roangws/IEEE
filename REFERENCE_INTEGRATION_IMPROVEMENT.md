# Reference Integration Improvements

## Problem Identified

The system was losing local references when integrating external ones:
- Expected: 40 local + ~30 external = ~70 total references
- Actual: 36 local + 0 external = 36 total references

## Root Cause

1. **Weak prompt**: Not explicitly preserving local citations
2. **Low limit**: Only 5 external refs per section
3. **Unclear instructions**: LLM wasn't told to add most external refs

## Fixes Applied

### 1. Stronger Prompt
- Emphasizes PRESERVING ALL existing citations
- Sets target of 60% external reference integration
- Provides clear examples of how to combine citations
- Explicitly mentions local citation ranges [1-40]

### 2. Increased Reference Limit
- Changed from 5 to 10 external refs per section
- Allows more external citations to be added

### 3. Clearer Instructions
- Step-by-step numbering
- Example showing how to combine citations
- Warning not to renumber or remove existing citations

## Expected Behavior Now

1. **Step 1**: 40 local references found
2. **Step 2**: 50 external references selected
3. **Step 3**: Integration preserves all 40 local + adds ~30 external
4. **Step 4**: Shows ~70 total references

## Testing

After these changes:
1. Clear cache and restart Streamlit
2. Generate new article
3. Select external references
4. Run integration
5. Verify count in Step 4.1

The system should now keep ALL local references and add most external ones.
