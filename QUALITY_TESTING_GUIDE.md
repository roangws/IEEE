# Quality Testing Guide: SPECTER v1 vs SPECTER2

## Overview
This guide helps you systematically test and compare retrieval quality between the old SPECTER v1 and new SPECTER2 models.

---

## Collections

### Old Collection
- **Name**: `academic_papers_100_specter`
- **Model**: allenai-specter (2020)
- **Dimension**: 768
- **Training Data**: 684K papers

### New Collection
- **Name**: `academic_papers_100_specter2_v2`
- **Model**: allenai/specter2_base (2023)
- **Dimension**: 768
- **Training Data**: 6M+ papers
- **Chunking**: Semantic (paragraph-aware)

---

## Test 1: Automated Retrieval Comparison

**Run the comparison script:**
```bash
cd /Users/roan-aparavi/aparavi-repo/Roan-IEEE
HF_HOME=$(pwd)/.cache/huggingface venv/bin/python compare_retrieval_quality.py
```

**What it tests:**
- 5 academic queries across different domains
- Top 10 results from each collection
- Score improvements
- Paper overlap
- New papers discovered

**Expected results:**
- Score improvement: 10-20%
- Some overlap in top results
- New relevant papers found by SPECTER2

---

## Test 2: Manual Query Testing in UI

**Steps:**
1. Open Streamlit app: http://localhost:8501
2. Go to "Q&A with Papers" tab
3. Test same query with both collections

**Test Queries:**
```
1. "transformer architectures for natural language processing"
2. "graph neural networks for program analysis"
3. "deep learning approaches to code similarity detection"
4. "attention mechanisms in neural machine translation"
5. "convolutional neural networks for image classification"
```

**For each query:**
1. Select OLD collection (`academic_papers_100_specter`)
2. Run query, note top 5 papers
3. Select NEW collection (`academic_papers_100_specter2_v2`)
4. Run same query, note top 5 papers
5. Compare:
   - Are results more relevant?
   - Are scores higher?
   - Are different (potentially better) papers found?

---

## Test 3: Article Generation Quality

**Generate articles with both collections:**

### Test Article 1: Technical Survey
**Topic**: "A comprehensive survey of transformer architectures in natural language processing"

**Settings:**
- Word Count: 3000
- Papers: 30
- Rigor Level: 4 (Advanced)

**Generate with:**
1. OLD collection
2. NEW collection

**Compare:**
- Number of papers cited
- Technical depth
- Relevance of citations
- Quality of synthesis

### Test Article 2: Specific Domain
**Topic**: "Graph neural networks for code similarity detection and program analysis"

**Settings:**
- Word Count: 2000
- Papers: 20
- Rigor Level: 5 (Maximum)

**Compare:**
- Citation accuracy
- Technical precision
- Relevant papers found

---

## Test 4: Citation Quality Analysis

**For generated articles, check:**

1. **Citation Relevance**
   - Are cited papers actually relevant to the topic?
   - Do citations support the claims made?

2. **Citation Diversity**
   - How many unique papers cited?
   - Are citations distributed across sections?

3. **Technical Accuracy**
   - Do cited metrics/results match the papers?
   - Are algorithms/methods correctly described?

4. **Source Quality**
   - Are the most important papers in the field cited?
   - Are recent advances included?

---

## Metrics to Track

### Retrieval Metrics
```
Old Collection:
- Average Score: _______
- Top 10 Relevance: _______/10
- Unique Papers: _______

New Collection:
- Average Score: _______
- Top 10 Relevance: _______/10
- Unique Papers: _______

Improvement: _______%
```

### Article Generation Metrics
```
Old Collection:
- Papers Cited: _______
- Citation Utilization: _______%
- Technical Depth (1-5): _______
- Relevance Score (1-5): _______

New Collection:
- Papers Cited: _______
- Citation Utilization: _______%
- Technical Depth (1-5): _______
- Relevance Score (1-5): _______
```

---

## Expected Improvements

### SPECTER2 Should Show:
✅ **Better Semantic Understanding**
- More relevant papers for complex queries
- Better handling of technical terminology
- Improved understanding of research context

✅ **Higher Quality Citations**
- More appropriate papers cited
- Better match between query and results
- Improved diversity in results

✅ **Better Chunking**
- Context preserved across paragraphs
- Citations stay with relevant text
- More coherent retrieval units

### Potential Issues to Watch:
⚠️ **Different Results ≠ Better Results**
- Validate that new results are actually more relevant
- Check if important papers are still found

⚠️ **Score Calibration**
- Scores may be on different scales
- Focus on relative ranking, not absolute scores

---

## Decision Criteria

### Use SPECTER2 if:
- ✅ Retrieval scores improve by >10%
- ✅ Article quality is noticeably better
- ✅ More relevant papers are cited
- ✅ Technical depth improves

### Further Investigation if:
- ⚠️ Results are mixed (some better, some worse)
- ⚠️ Improvement is marginal (<5%)
- ⚠️ Different but not clearly better

### Revert to SPECTER v1 if:
- ❌ Quality degrades
- ❌ Important papers are missed
- ❌ Results are less relevant

---

## Next Steps After Testing

### If SPECTER2 is Better:
1. ✅ Make `academic_papers_100_specter2_v2` the default
2. ✅ Update documentation
3. ✅ Consider Phase 2 optimizations (Hybrid Retrieval)
4. ✅ Archive old collection

### If Results are Mixed:
1. 🔄 Keep both collections available
2. 🔄 Test on more diverse queries
3. 🔄 Gather user feedback
4. 🔄 Consider hybrid approach

### If Implementing Phase 2:
1. 🚀 Add BM25 sparse retrieval
2. 🚀 Implement hybrid scoring
3. 🚀 Add cross-encoder reranking
4. 🚀 Expected +30-40% total improvement

---

## Troubleshooting

### Issue: New collection not showing in UI
**Solution**: Refresh the Streamlit app, check Qdrant connection

### Issue: Scores seem lower with SPECTER2
**Solution**: Compare relative rankings, not absolute scores

### Issue: Different papers but unclear if better
**Solution**: Manually review top 10 results for relevance

### Issue: Ingestion taking too long
**Solution**: Normal for 5,634 PDFs, ~15 minutes expected

---

## Documentation

Save your test results in:
- `retrieval_comparison_results.json` (automated tests)
- Manual notes in this file
- Screenshots of article comparisons

This will help with:
- Future optimization decisions
- Understanding model behavior
- Justifying model choice
