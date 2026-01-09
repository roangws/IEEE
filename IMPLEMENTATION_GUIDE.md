# Complete Implementation Guide

## Phase 1: Enhanced Semantic Filtering (Step 2.2)

### Files Added:
- `semantic_filter.py` - Core semantic filtering logic
- `requirements_semantic.txt` - Additional dependencies

### Integration Points:
1. Install dependencies: `pip install -r requirements_semantic.txt`
2. Modify `layer2_external_ui.py` to add semantic filtering button
3. Add progress indicators and filtering UI

### Features:
- SPECTER embeddings for academic similarity
- Method compatibility checking with local LLM
- Venue validation for top-tier conferences
- Overall scoring and ranking

---

## Phase 2: Smart Citation Integration (Step 3)

### Files Added:
- `smart_citation_integratorator.py` - Intelligent citation placement

### Integration Points:
1. Replace current external integrator in `layer2_external_ui.py`
2. Use content-aware citation matching
3. Implement type-based placement rules

### Features:
- Content categorization (methods/results/background)
- Citation type matching
- Context-aware placement
- Preserves existing citations

---

## Phase 3: OpenAI Refinement (Step 4)

### Files Added:
- `openai_refiner.py` - Citation-preserving refinement

### Integration Points:
1. Add refinement option after article generation
2. Validate citation preservation
3. Polish without losing references

### Features:
- Strict citation preservation
- Section-by-section refinement
- Citation validation
- Final quality check

---

## Installation Steps

```bash
# Install semantic filtering dependencies
pip install sentence-transformers>=2.2.2 numpy>=1.21.0

# Download SPECTER model (automatic on first use)
# Model: allenai/specter-base-v2
```

---

## Usage Flow

1. **Step 2.2**: Search → Click "🔍 Filter by Relevance" → Get high-quality papers
2. **Step 3**: Generate → Smart citation integration → Well-cited article
3. **Step 4**: Refine → OpenAI polishing → Perfect final article

---

## Expected Results

- 90%+ citation-text relevance
- All local references preserved
- 60%+ external references integrated
- Citations in correct logical positions
- Publication-ready quality
