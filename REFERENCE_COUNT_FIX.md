# Reference Count Discrepancy Analysis

## The Problem

The warning messages and total count show different numbers because:

### Warning Messages (lines 743, 753)
- **"11 external references not cited"** - Count of SELECTED references that weren't cited in article
- **"42 local references not cited"** - Count of AVAILABLE references that weren't cited in article

### Total Count (line 876)
- **"Showing 65 total references"** - Count of references ACTUALLY CITED in article

## Why This Happens

1. **Selection vs Citation**: Users might select 50 external references, but only cite 39 in the article
2. **Available vs Used**: The system has 42 local references available, but only uses some in the article
3. **Different reference points**:
   - Warnings = "What you had available/selected vs what you used"
   - Total = "What actually appears in the final article"

## Current Logic

```python
# Warning counts (uncited references)
missing_local = set(citation_map.values()) - set([ref[2] for ref in cited_refs if ref[1] == 'local'])
missing_external = selected_external_nums - cited_external_nums

# Total counts (cited references)
for old_num, ref_type, ref_data in cited_refs:
    if ref_type == 'local':
        local_count += 1
    else:
        external_count += 1
```

## Solution Options

### Option 1: Make Warnings Clearer
Change warning text to be more explicit:
- "⚠️ 11 external references were selected but not cited in article"
- "⚠️ 42 local references were available but not cited in article"

### Option 2: Show Both Numbers
Display both selected/available and cited counts:
- "Selected: 50 external, 42 local | Cited: 39 external, 26 local"

### Option 3: Align the Counts
Change warnings to show the same as total (cited references)

## Recommendation

Option 1 is best - just clarify the warning text to avoid confusion.
