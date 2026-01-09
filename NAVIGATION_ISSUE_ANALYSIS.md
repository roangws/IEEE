# Navigation Links Issue Analysis

## Current Problem:
The navigation links are not working because:

1. **Sections are in different tabs** - Each section is rendered inside a different Streamlit tab
   - Section 1 (Paper Analysis & Q&A) → Tab "🔍 Q&A Analysis"
   - Section 2 (Research Landscape) → Tab "🔬 Research Analysis"
   - Section 3 (Paper Explorer) → Tab "📚 Paper Explorer"
   - Section 4 (Synthesis) → Tab "✍️ Article Generation"

2. **Streamlit tabs don't support URL fragments** - When you click an anchor link, it doesn't automatically switch to the correct tab

## Possible Solutions:

### Option 1: Use URL parameters with session state
- Modify the app to read URL parameters and switch tabs accordingly
- Example: `?tab=analysis#section1`

### Option 2: Create a single-page view
- Remove tabs and display all sections sequentially
- Navigation would work perfectly

### Option 3: Add tab switching buttons
- Each navigation link could have a button to switch tabs
- Use JavaScript to handle both tab switching and scrolling

### Option 4: Current workaround
- Keep the navigation but add instructions about which tab each section is in

## Current Anchors (verified):
- ✅ `#section1` - exists in Paper Analysis & Q&A
- ✅ `#section2` - exists in Research Landscape Analysis  
- ✅ `#section3` - exists in Paper Explorer & Similar Papers
- ✅ `#section-2-step-1-synthesis-article-generator` - exists in Article Generation
- ✅ `#step1` - exists in Article Generation
- ✅ `#step2a` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step-2-1-extract-keywords` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step-2-2-search-semantic-scholar-api` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step2b` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step3` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step-4-1-article-metrics` - exists in Article Generation (layer2_external_ui.py)
- ✅ `#step4` - exists in Article Generation

## Recommendation:
Implement Option 1 (URL parameters) for the best user experience.
