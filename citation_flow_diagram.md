# Citation Integration Flow Diagram

## Initial State
```
Article with 30 Internal Citations: [1] [2] [3] ... [30]
External References Available: 20 papers (numbers 31-50)
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    STEP 2.9 INTEGRATION                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Article Parsing                                        │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Section 1       │  │ Section 2       │  ...             │
│  │ Internal: [1,2] │  │ Internal: [3,4] │                  │
│  │ Content: ...    │  │ Content: ...    │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Citation Context Building                               │
│                                                             │
│  For EACH section, the LLM sees:                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SECTION CONTENT:                                    │   │
│  │ "Recent advances in diffusion models [3,4]..."      │   │
│  │                                                     │   │
│  │ AVAILABLE CITATIONS:                                │   │
│  │ [31] External Paper 1: "Video Restoration..."      │   │
│  │      Authors: A, B, C                              │   │
│  │      Abstract: "This paper presents..."             │   │
│  │                                                     │   │
│  │ [32] External Paper 2: "Temporal Attention..."      │   │
│  │      Authors: D, E, F                              │   │
│  │      Abstract: "Our method uses..."                 │   │
│  │                                                     │   │
│  │ ... (up to 5 per type, total 20 available)         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. LLM Processing (per section)                            │
│                                                             │
│  LLM Instructions:                                         │
│  ✓ PRESERVE all existing citations [3,4]                   │
│  ✓ ADD new citations where appropriate                     │
│  ✓ Use IEEE format: [number]                              │
│                                                             │
│  Example LLM output:                                       │
│  "Recent advances in diffusion models [3,4,31] have       │
│   shown promising results [32]. Our approach builds       │
│   on these methods [33]..."                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Result After Step 2.9                                   │
│                                                             │
│  Article contains:                                         │
│  - Internal citations: [1] to [30] (preserved)            │
│  - External citations: [31] to [50] (added)               │
│  - Total: 50 citations                                     │
│                                                             │
│  Example section:                                          │
│  "Recent advances in diffusion models [3,4,31] have       │
│   shown promising results [32,33]. Our approach [34]      │
│   builds on temporal attention [35,36]..."                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Step 4: IEEE Renumbering                                │
│                                                             │
│  BEFORE: [1-30] internal, [31-50] external                 │
│                                                             │
│  AFTER IEEE renumbering:                                   │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ [1]  Internal 1 │  │ [21] External 1 │  ← Local refs    │
│  │ [2]  Internal 2 │  │ [22] External 2 │  (first 20)     │
│  │ ...             │  │ ...             │                  │
│  │ [20] Internal 20│  │ [40] External 20│                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  Final article has sequential [1] to [40] citations        │
└─────────────────────────────────────────────────────────────┘
```

## Key Points:

1. **Internal citations are NEVER removed** - [1-30] always preserved
2. **External citations are ADDED** - [31-50] inserted where relevant
3. **LLM sees full context** - Title, authors, abstract for each external paper
4. **Section-by-section processing** - Each section gets relevant citations
5. **IEEE renumbering in Step 4** - Converts to sequential [1-40] format

## Citation Distribution Strategy:

```
Total sections: 8
External citations: 20
Average per section: 2-3 citations

Section 1 (Abstract): 0 citations (rule)
Section 2 (Intro): 2-3 citations
Section 3 (Background): 3-4 citations
Section 4 (Method): 3-4 citations
Section 5 (Results): 2-3 citations
Section 6 (Discussion): 3-4 citations
Section 7 (Conclusion): 2-3 citations
```

The system ensures ALL 20 external references are used by tracking which ones are still unused and distributing them across sections.
