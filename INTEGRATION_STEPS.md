# Integration Steps for Complete Implementation

## Step 1: Install Dependencies
```bash
cd /Users/roan-aparavi/aparavi-repo/Roan-IEEE
pip install -r requirements_semantic.txt
```

## Step 2: Update Layer 2 External UI
Add semantic filtering to `layer2_external_ui.py`:
- Import SemanticFilter
- Add filter button after search results
- Show progress with similarity scores
- Display filtered references with scores

## Step 3: Update Article Generation
Replace external integrator in `layer2_external_ui.py`:
- Import SmartCitationIntegrator
- Use smart integration instead of basic
- Keep all existing UI elements

## Step 4: Add Refinement Option
Add OpenAI refinement in `layer2_external_ui.py`:
- Import OpenAIRefiner
- Add refinement button after article generation
- Show citation validation results

## Step 5: Test Flow
1. Clear cache: `find . -name "__pycache__" -exec rm -rf {} +`
2. Restart Streamlit: `./run_streamlit.sh`
3. Test semantic filtering
4. Test smart citation integration
5. Test OpenAI refinement

## Key Integration Code Snippets

### Semantic Filter Integration:
```python
from semantic_filter import SemanticFilter

# In search results section
if st.button("🔍 Filter by Relevance"):
    with st.spinner("Analyzing paper relevance..."):
        filter = SemanticFilter()
        filtered_refs = filter.comprehensive_filter(
            query_text=article_title,
            article_text=article_abstract,
            references=search_results
        )
        # Display filtered results with scores
```

### Smart Citation Integration:
```python
from smart_citation_integratorator import SmartCitationIntegrator

# Replace external integrator call
integrator = SmartCitationIntegrator()
enhanced_article = integrator.integrate_citations_smart(
    article_text=article_text,
    references=selected_refs,
    llm_type="openai",
    model="gpt-4o"
)
```

### OpenAI Refinement:
```python
from openai_refiner import OpenAIRefiner

# Add after article generation
if st.button("✨ Refine with OpenAI"):
    refiner = OpenAIRefiner()
    refined_article = refiner.refine_article(
        article_text=enhanced_article,
        llm_model="gpt-4o",
        preserve_citations=True
    )
```
