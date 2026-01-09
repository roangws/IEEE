# External References Feature Request

## Overview
Add capability to include external references (papers/sources outside the local corpus) in generated articles alongside internal citations.

## Current State
- System only cites papers from the local corpus (5,671 IEEE papers)
- All citations [1], [2], etc. map to files in the local database
- No mechanism to add external scholarly references

## Requested Feature
Allow the system to:
1. Accept external paper references (DOI, arXiv, URLs, or manual entries)
2. Integrate external references into the article alongside corpus citations
3. Format external references in IEEE style in the References section
4. Distinguish between internal corpus citations and external references

## Implementation Approach (Future)

### Option 1: Manual External References
- Add UI section to manually input external papers (title, authors, year, DOI/URL)
- Store external refs in a separate list
- Assign citation numbers starting after corpus citations
- Merge both lists in final References section

### Option 2: Automatic External Reference Discovery
- Use semantic scholar API or similar to find related papers
- LLM suggests relevant external papers based on topic
- User approves/rejects suggestions
- System integrates approved external refs

### Option 3: Hybrid Approach
- Start with manual entry (Option 1)
- Add automatic discovery later (Option 2)
- Allow users to search external databases and add to article

## Technical Considerations
- Citation numbering: corpus papers [1]-[N], external papers [N+1]-[M]
- Metadata format: need consistent schema for external refs
- Validation: ensure external refs are properly formatted
- PDF export: include both internal and external references

## Priority
- Medium-High (user explicitly requested)
- Implement after core refinement system is stable
- Start with manual entry (simplest path)

## Related Files
- `citation_manager.py` - handles citation extraction and reference building
- `citation_formatter.py` - formats references in IEEE style
- `app.py` - UI for article generation
- `article_refiner.py` - refinement system (could suggest external refs)

## Next Steps
1. Design UI mockup for external reference input
2. Extend citation_map to support external references
3. Update CitationManager to merge internal + external refs
4. Test with mixed citation types
5. Add to Layer 1 or Layer 2 (TBD based on UX)
