# Log Cleanup Plan - Simplify Integration Logs

## Current Problems

1. **Too many technical details** - LLM type, pricing, token calculations
2. **Redundant warnings** - Processing time, reference ratio shown multiple times
3. **Debug information** - Should not be visible to users
4. **Conflicting messages** - Success and failure shown together
5. **Invalid citation errors** - Should be handled internally, not shown prominently

## What Users Actually Need

### Essential Information:
- ✅ Integration started
- ✅ Progress (X/Y sections processed)
- ✅ Citations added count
- ✅ Total processing time
- ✅ Success/failure status

### Remove:
- ❌ LLM type details
- ❌ Pricing calculations
- ❌ Article length
- ❌ Reference ratio warnings (move to expandable section)
- ❌ Processing time estimates (move to single info box)
- ❌ Debug data sources
- ❌ Invalid citation errors (handle silently or log only)
- ❌ Non-integrated references list (move to expandable section)

## Simplified Log Structure

```
=== INTEGRATION STARTED ===
Processing 22 sections with 20 external references...

[Section 1/22] Introduction - Processing...
[Section 1/22] Complete - 2 citations added

[Section 2/22] Background - Processing...
[Section 2/22] Complete - 3 citations added

...

=== INTEGRATION COMPLETE ===
✅ Added 39 citations in 245 seconds
Total tokens: 15,234 | Cost: $0.23
```

## Implementation Changes

1. **Remove verbose logging** - Keep only essential progress
2. **Move warnings to expandable sections** - Don't clutter main view
3. **Consolidate success messages** - One clear message at end
4. **Hide debug info** - Remove "Debug: Data Sources" section
5. **Simplify error messages** - Show only actionable errors
