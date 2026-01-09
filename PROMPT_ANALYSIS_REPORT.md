# Prompt Analysis Report: Section Duplication Issue

## Problem Statement

The integration process is creating duplicate section headings (e.g., "1. Introduction" appears twice). This indicates the LLM is not following instructions to avoid duplicating headings.

## Root Cause Analysis

### 1. **Prompt Structure Issue**

**Current Prompt:**
```python
prompt = f"""Enhance this section with smart citation placement:

{heading}

{content}

AVAILABLE CITATIONS BY TYPE:
{citation_context}

INSTRUCTIONS:
- Add citations where they naturally support the content
- Match citation type to content type
- Preserve all existing citations
- DO NOT add any titles, headings, or duplicate the section heading
- Output the complete enhanced section ONLY (no extra text before or after)"""
```

**Problem:** The prompt includes `{heading}` in the input, which shows the LLM the heading. Then it says "Output the complete enhanced section ONLY" - this is ambiguous. Does "complete section" include the heading or not?

### 2. **Conflicting Instructions**

- System message says: "DO NOT add titles, headings, or any section headers"
- Prompt says: "DO NOT add any titles, headings, or duplicate the section heading"
- But then: "Output the complete enhanced section ONLY"

The LLM interprets "complete section" as including the heading, so it outputs:
```
1. Introduction

[content with citations]
```

Then when reassembled, the heading is added again by `_reassemble_article`:
```python
def _reassemble_article(self, sections: List[Tuple[str, str]]) -> str:
    """Reassemble article from enhanced sections."""
    return "\n\n".join([f"{heading}\n\n{content}" for heading, content in sections])
```

This creates:
```
1. Introduction

1. Introduction

[content]
```

### 3. **Reassembly Logic Flaw**

The `_reassemble_article` function ALWAYS adds the heading, assuming the enhanced content doesn't include it. But the LLM is including it, causing duplication.

## Validation Findings

### Issue 1: Ambiguous Output Expectation
- ❌ Prompt shows heading to LLM
- ❌ Asks for "complete section" (unclear if heading included)
- ❌ LLM includes heading in response
- ❌ Reassembly adds heading again = DUPLICATION

### Issue 2: Instruction Clarity
- ❌ "DO NOT add titles" vs "Output complete section" - contradictory
- ❌ No explicit example of expected output format
- ❌ No clear boundary between what to include/exclude

### Issue 3: Response Parsing
- ❌ No validation that LLM didn't include heading
- ❌ No stripping of duplicate headings before reassembly
- ❌ Assumes LLM follows instructions perfectly

## Recommendations (DO NOT EXECUTE YET)

### Option 1: **Explicit Output Format** (RECOMMENDED)
```python
prompt = f"""Enhance this section with smart citation placement:

SECTION HEADING: {heading}

SECTION CONTENT:
{content}

AVAILABLE CITATIONS BY TYPE:
{citation_context}

INSTRUCTIONS:
- Add citations where they naturally support the content
- Match citation type to content type
- Preserve all existing citations
- Output ONLY the enhanced content (WITHOUT the heading)
- Do NOT include "{heading}" in your response
- Start your response directly with the content

EXAMPLE OUTPUT FORMAT:
[First paragraph of content with citations...]
[Second paragraph with citations...]
(Do NOT start with the heading)"""
```

### Option 2: **Post-Processing Cleanup**
Add validation after LLM response:
```python
enhanced_section, usage = self._enhance_section_with_citations(...)

# Remove heading if LLM included it
if enhanced_section.strip().startswith(heading.strip()):
    enhanced_section = enhanced_section[len(heading):].strip()

enhanced_sections.append((heading, enhanced_section))
```

### Option 3: **Separate Heading from Content**
Don't show heading to LLM at all:
```python
prompt = f"""Add citations to this content:

{content}

AVAILABLE CITATIONS:
{citation_context}

OUTPUT: Return the content with citations added. Do NOT add any headings."""
```

### Option 4: **Two-Step Validation**
```python
# After getting LLM response
enhanced_section = enhanced.strip()

# Check if heading was duplicated
lines = enhanced_section.split('\n')
if lines[0].strip() == heading.strip():
    # Remove first line (duplicate heading)
    enhanced_section = '\n'.join(lines[1:]).strip()
```

## Impact Analysis

### Current State:
- ✅ Citations are being added correctly
- ✅ Content is being enhanced
- ❌ Headings are duplicated
- ❌ Article structure is malformed

### After Fix:
- ✅ Citations added correctly
- ✅ Content enhanced
- ✅ Headings appear once
- ✅ Clean article structure

## Recommended Solution

**Combine Option 1 + Option 4:**

1. **Make prompt explicit** about not including heading
2. **Add validation** to strip heading if LLM includes it anyway
3. **Update reassembly** to handle both cases

This provides:
- Clear instructions to LLM
- Safety net if LLM doesn't follow instructions
- Robust handling of edge cases

## Testing Strategy

1. Test with sample section containing heading
2. Verify LLM response doesn't include heading
3. If it does, verify validation strips it
4. Confirm reassembled article has no duplicates
5. Test with multiple sections to ensure consistency

## Priority: HIGH

This issue affects article quality and user experience. Should be fixed before next integration run.
