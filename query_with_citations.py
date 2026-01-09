#!/usr/bin/env python3
"""
Enhanced Query Module with Citation Support
Provides retrieval with proper citation formatting.
"""

from query import QueryEngine
from citation_formatter import CitationFormatter
from retrieval_mmr import MMRRetriever


def retrieve_for_synthesis_with_citations(topic: str, top_k: int = 50, target_papers: int = None, use_diverse_retrieval: bool = True):
    """
    Retrieve sources with proper citation formatting using optimized diverse retrieval.
    
    Args:
        topic: Search query
        top_k: Number of chunks to retrieve
        target_papers: Target number of unique papers (enforces diversity)
        use_diverse_retrieval: Use MMR-based diverse retrieval (recommended)
        
    Returns:
        Tuple of (formatted_sources_text, sources_list, citation_mapping, reference_list)
    """
    # Initialize query engine and citation formatter
    engine = QueryEngine()
    formatter = CitationFormatter()
    
    # Use diverse retrieval for better paper coverage
    if use_diverse_retrieval and target_papers:
        print(f"Using diverse retrieval: targeting {target_papers} unique papers...")
        mmr = MMRRetriever()
        
        # Calculate chunks per paper
        chunks_per_paper = max(2, top_k // target_papers) if target_papers > 0 else 3
        
        # Retrieve with diversity enforcement
        sources_list = mmr.diverse_paper_retrieval(
            topic,
            num_papers=target_papers,
            chunks_per_paper=chunks_per_paper
        )
    else:
        # Fallback to standard retrieval
        print("Using standard retrieval...")
        sources_text, sources_list = engine.retrieve_for_synthesis(topic, top_k)
    
    # Create citation mapping
    citation_map = formatter.create_citation_mapping(sources_list)
    
    # Reformat sources with proper citations
    formatted_chunks = []
    
    for source in sources_list:
        filename = source['filename']
        citation_num = citation_map.get(filename, 0)
        chunk_text = source['chunk_text']
        
        # Get source info
        source_info = formatter.get_source_info(filename)
        
        # Format with citation number
        formatted_chunk = f"\n---\n**Source [{citation_num}]**: {source_info}\n\n{chunk_text}\n"
        formatted_chunks.append(formatted_chunk)
    
    formatted_sources = "\n".join(formatted_chunks)
    
    # Create reference list
    reference_list = formatter.create_reference_list(sources_list)
    
    return formatted_sources, sources_list, citation_map, reference_list


def get_rigor_requirements(level: int) -> str:
    """Get technical depth requirements based on rigor level."""
    requirements = {
        1: """1. **Overview Level**: General concepts and high-level approaches
2. Minimal technical terminology
3. Focus on what methods do, not how they work
4. Few specific metrics or numbers
5. Broad comparisons without detailed analysis""",
        2: """1. **Moderate Level**: Some algorithms and key metrics
2. Basic technical terminology
3. Include major performance numbers
4. Mention frameworks and datasets used
5. General implementation approaches""",
        3: """1. **Technical Level**: Detailed algorithms, metrics, and frameworks
2. Precise technical terminology throughout
3. Exact performance metrics and comparisons
4. Implementation details (datasets, hyperparameters)
5. Quantitative analysis with specific numbers
6. Technical challenges and trade-offs""",
        4: """1. **Advanced Level**: Deep technical detail with equations
2. Mathematical formulations and complexity analysis
3. Detailed algorithmic descriptions
4. Comprehensive performance analysis
5. Implementation specifics (architectures, optimization)
6. Theoretical foundations and proofs (when relevant)
7. Advanced technical terminology""",
        5: """1. **Maximum Rigor**: Full mathematical rigor with proofs
2. Complete mathematical formulations and derivations
3. Complexity analysis (time, space, computational)
4. Detailed theoretical foundations
5. Rigorous algorithmic descriptions with pseudocode
6. Comprehensive quantitative analysis
7. Advanced mathematical concepts and notation
8. Formal definitions and lemmas""",
        6: """1. **EXTREME ACCURACY - Research-Grade Quality**:
2. EXHAUSTIVE mathematical formulations with complete derivations
3. Rigorous proofs for all theoretical claims
4. Complete algorithmic descriptions with pseudocode and complexity proofs
5. Comprehensive experimental analysis with statistical significance tests
6. Detailed error analysis and confidence intervals
7. Full implementation specifications (exact architectures, all hyperparameters)
8. Extensive quantitative comparisons with multiple baselines
9. Theoretical guarantees and convergence proofs
10. Formal problem definitions with mathematical notation
11. Complete ablation studies and sensitivity analysis
12. Research-level precision in all technical descriptions"""
    }
    return requirements.get(level, requirements[3])


def get_rigor_description(level: int) -> str:
    """Get short description of rigor level."""
    descriptions = {
        1: "Overview with minimal technical detail",
        2: "Moderate technical depth with key metrics",
        3: "Detailed algorithms, metrics, and frameworks",
        4: "Advanced technical detail with equations",
        5: "Maximum mathematical rigor with proofs",
        6: "EXTREME - Research-grade accuracy with exhaustive analysis"
    }
    return descriptions.get(level, descriptions[3])


def create_enhanced_article_prompt(topic: str, sources: str, word_count: int, 
                                   tone: str, reference_list: str, citation_map: dict,
                                   total_sources: int, rigor_level: int = 3,
                                   include_math: bool = False, include_synthetic_data: bool = False) -> str:
    """
    Create an enhanced prompt for article generation with proper citations.
    
    Args:
        topic: Article topic
        sources: Formatted source material
        word_count: Target word count
        tone: Writing tone
        reference_list: Formatted reference list
        citation_map: Mapping of filenames to citation numbers
        total_sources: Total number of source chunks provided
        rigor_level: Technical/mathematical rigor level (1-5)
        
    Returns:
        Complete prompt
    """
    
    # Create citation guide with technical focus
    citation_guide = f"**Citation Guide ({len(citation_map)} unique papers):**\n"
    citation_guide += "Extract TECHNICAL DETAILS from these papers:\n"
    citation_guide += "- Algorithms, architectures, formulas\n"
    citation_guide += "- Exact metrics, percentages, performance numbers\n"
    citation_guide += "- Datasets, frameworks, experimental setups\n"
    citation_guide += "- Implementation details and hyperparameters\n\n"
    for filename, num in sorted(citation_map.items(), key=lambda x: x[1]):
        citation_guide += f"- {filename} = [{num}]\n"
    
    system_prompt = f"""You are an expert academic writer specializing in IEEE-style research papers.

🚨 **CRITICAL REQUIREMENT - YOU MUST INCLUDE CITATIONS** 🚨

**IEEE CITATION FORMAT (MANDATORY - NOT OPTIONAL):**

1. **In-Text Citations (REQUIRED IN EVERY PARAGRAPH):**
   - Use ONLY numbered citations in square brackets: [1], [2], [3]
   - Place citations AFTER the text, BEFORE punctuation: "Recent work [1] shows..."
   - Multiple citations: [1], [2], [5] (comma-separated)
   - Ranges: [1]-[5] (for consecutive citations)
   - NO author names in text (only in reference list)
   - NO years in text (only in reference list)
   - NO explanatory notes about citation counts

2. **Citation Distribution (MANDATORY - Based on 5,671 IEEE Papers):**
   - You have {len(citation_map)} papers available: {list(citation_map.values())}
   - ⚠️ CRITICAL: ONLY use citation numbers from the list above
   - ⚠️ DO NOT invent citation numbers beyond {max(citation_map.values())}
   - ⚠️ DO NOT use citations like [99] if you only have {len(citation_map)} papers
   - TARGET: Use 135 in-text citations total (mean from full corpus)
   - MINIMUM: Use at least 68 in-text citations (50th percentile)
   - You MUST cite at least {max(len(citation_map) // 2, 10)} different papers
   - EVERY paragraph must have at least 1-2 citations
   - Introduction section: 8-12 citations
   - Literature Review section: 20-30 citations (HEAVIEST SECTION)
   - Methodology section: 12-18 citations
   - Experiments section: 8-12 citations
   - Results section: 6-10 citations
   - Discussion section: 4-8 citations
   - Conclusion section: 0-2 citations
   - REUSE citation numbers multiple times to reach target counts

3. **What NOT to do:**
   - ❌ NO notes like "(Note: This article cites X sources...)"
   - ❌ NO "Source 28" or placeholder text
   - ❌ NO author names in citations like "Smith [1]"
   - ❌ NO years in citations like "[1, 2023]"
   - ❌ NO explanatory text about citations
   - ❌ NO ARTICLE WITHOUT CITATIONS - This is unacceptable

**TECHNICAL DEPTH REQUIREMENTS (RIGOR LEVEL {rigor_level}/5):**
{get_rigor_requirements(rigor_level)}
"""

    # Add mathematical functions requirement if enabled
    if include_math:
        system_prompt += """

**📐 MATHEMATICAL FUNCTIONS REQUIREMENT (ENABLED):**

You MUST include relevant mathematical content throughout the article:

1. **Equations and Formulas:**
   - Use LaTeX notation in markdown: $inline$ or $$display$$
   - Include key equations for algorithms, models, loss functions
   - Example: $L(\\theta) = \\frac{1}{n}\\sum_{i=1}^{n} (y_i - f(x_i; \\theta))^2$
   - Provide equation numbers and references in text

2. **Mathematical Models:**
   - Define mathematical representations of concepts
   - Include probability distributions, optimization objectives
   - Example: $P(y|x) = \\text{softmax}(W^T h + b)$

3. **Algorithmic Complexity:**
   - Specify time/space complexity: O(n log n), O(n²)
   - Compare computational costs between methods
   - Example: "The algorithm runs in O(n²) time complexity [1]"

4. **Statistical Formulas:**
   - Include metrics: accuracy, precision, recall, F1-score formulas
   - Show derivations when relevant
   - Example: $F1 = 2 \\cdot \\frac{precision \\cdot recall}{precision + recall}$

5. **Placement:**
   - Methodology section: 3-5 key equations
   - Results section: 2-3 metric formulas
   - Discussion section: 1-2 complexity analyses

**MINIMUM REQUIREMENT:** Include at least 5-8 mathematical equations/formulas throughout the article.
"""

    # Add synthetic data generation requirement if enabled
    if include_synthetic_data:
        system_prompt += """

**📊 SYNTHETIC DATA GENERATION REQUIREMENT (ENABLED):**

You MUST include synthetic/fake datasets for analysis demonstrations:

1. **Sample Datasets:**
   - Create realistic example datasets relevant to the topic
   - Use markdown tables with proper formatting
   - Include 5-10 sample rows minimum
   - Example:
   
   | Model | Accuracy | F1-Score | Training Time (hrs) |
   |-------|----------|----------|---------------------|
   | BERT-base | 87.2% | 0.869 | 4.5 |
   | RoBERTa | 89.5% | 0.891 | 6.2 |
   | GPT-3 | 91.3% | 0.908 | 12.8 |

2. **Statistical Analysis Examples:**
   - Show sample statistical tests with fake data
   - Include mean, std dev, confidence intervals
   - Example: "Mean accuracy: 88.7% ± 2.3% (95% CI: [86.4%, 91.0%], n=100)"

3. **Experimental Results Tables:**
   - Create comparison tables with synthetic performance metrics
   - Include baseline vs proposed methods
   - Show ablation study results

4. **Data Distributions:**
   - Describe synthetic dataset characteristics
   - Example: "Training set: 10,000 samples (70%), Validation: 2,000 (15%), Test: 2,000 (15%)"

5. **Code Snippets (Optional):**
   - Include Python code to generate synthetic data
   - Example data generation functions
   - Data preprocessing examples

**MINIMUM REQUIREMENT:** Include at least 2-3 data tables and 1-2 statistical analysis examples with synthetic data.
"""

    system_prompt += """

**WRITING STYLE:**
1. Formal academic language (third person, passive voice for methods)
2. Structure: Abstract → Introduction → Literature Review → Methodology → Results → Discussion → Conclusion
3. Technical precision over simplification
4. Specific data and findings WITH citations [1]
5. Synthesize across sources with technical depth
6. Critical and analytical with quantitative evidence
7. Every paragraph needs citations and technical substance

**TONE MATCHING:**
- Academic: Formal, objective, research-focused
- Technical: Detailed, implementation-focused, precise
- Survey: Comprehensive, comparative, broad coverage
- Opinion: Analytical, critical, perspective-driven

**ARTICLE STRUCTURE (MANDATORY - FOLLOW EXACTLY):**

**YOU MUST START WITH:**

1. **TITLE** (First line, centered with #):
   - Format: `# [Descriptive Title Based on Topic]`
   - Make it specific and technical
   - Example: `# A Comprehensive Survey of Transformer Architectures in Natural Language Processing`

2. **ABSTRACT** (REQUIRED - 80-250 words, target 118 words):
   - Start with `## Abstract`
   - Concise summary of entire article
   - Include: problem, methods surveyed, key findings, conclusions
   - Must include key technical contributions and metrics
   - Target length: 118 words (measured mean from 5,671 IEEE papers)
   - This is MANDATORY - do not skip

**THEN CONTINUE WITH:**

3. **Introduction**: 
   * Technical context and problem formulation
   * Motivation with quantitative evidence [1]
   * Scope and technical contributions
   * Cite foundational and recent work

4. **Literature Review** (MOST TECHNICAL SECTION):
   * Survey organized by technical approaches/methodologies
   * For each approach: algorithms, architectures, performance metrics
   * Comparative tables with quantitative results
   * Technical evolution and improvements over time
   * Heavy citations with specific technical details from each paper

5. **Methodology** (MUST BE SPECIFIC):
   * For EACH method/model mentioned, specify:
     - Exact model name (e.g., "GPT-4-turbo", NOT "LLMs")
     - Version/variant (e.g., "BERT-base-uncased")
     - Key hyperparameters (learning rate, batch size, epochs)
     - Framework/library with version (PyTorch 2.0, TensorFlow 2.13)
     - Hardware specifications (A100 GPU, 40GB VRAM)
   * Example: "We employed GPT-4-turbo (OpenAI, 2024) with temperature=0.7, max_tokens=2048, using the OpenAI API v1.0 [1]."
   * Detailed technical approaches from papers
   * Algorithms, formulas, architectures with citations
   * Implementation frameworks and tools with versions
   * Experimental setups and datasets with citations
   * NO GENERIC TERMS: "LLMs", "neural networks", "deep learning" without specifics

6. **Results** (MANDATORY FORMAT):
   * For EVERY performance claim, use this structure:
     - Baseline method: [name] achieved [metric]=[value] [citation]
     - Proposed method: [name] achieved [metric]=[value] [citation]
     - Improvement: Δ=[delta] ([percentage]% relative improvement)
     - Statistical significance: p=[value], CI=[range], n=[sample size]
   * Example: "The baseline BERT model achieved 87.2% F1-score [1]. Our proposed ensemble method achieved 94.5% F1-score [2], representing a Δ=7.3% absolute improvement (8.4% relative, p<0.001, 95% CI=[6.8-7.8], n=1000)."
   * Quantitative findings with exact numbers and citations
   * Performance comparisons with baselines (accuracy, speed, efficiency)
   * Statistical significance and error analysis (p-values, confidence intervals)
   * NO IMPROVEMENT CLAIMS WITHOUT BASELINES
   * Cite results with specific metrics and statistical validation

7. **Discussion**:
   * Technical analysis of trade-offs
   * Computational complexity comparisons
   * Limitations and challenges
   * Technical implications
   * Cite supporting evidence

8. **Conclusion**:
   * Technical summary of key findings
   * Future technical directions
   * Open research problems

**CRITICAL - DO NOT WRITE REFERENCES SECTION:**
❌ ABSOLUTELY FORBIDDEN:
- DO NOT create your own References section
- DO NOT write any reference entries yourself
- DO NOT include ## References in your output
- DO NOT write bibliography entries
- DO NOT add author names, years, or titles in a reference list

✅ REQUIRED:
- The reference list will be AUTOMATICALLY GENERATED by the system
- Your article MUST END with the Conclusion section
- STOP writing immediately after Conclusion
- If you write a References section, the article will be REJECTED"""

    prompt = f"""{system_prompt}

---

## ARTICLE TOPIC
{topic}

---

## WRITING TONE
{tone}

---

## TARGET WORD COUNT (BODY ONLY) — CRITICAL
🚨 **YOU MUST WRITE EXACTLY {word_count} WORDS** 🚨

The References section is added automatically by the system and is NOT counted toward this target.

**MANDATORY SECTION WORD BUDGETS** (you MUST hit these targets):
- Abstract: {int(word_count * 0.02)} words (2%) — write exactly this many
- Introduction: {int(word_count * 0.12)} words (12%) — comprehensive background
- Literature Review: {int(word_count * 0.20)} words (20%) — LONGEST SECTION, survey prior work extensively
- Methodology: {int(word_count * 0.25)} words (25%) — detailed technical approach
- Experiments: {int(word_count * 0.15)} words (15%) — setup, datasets, metrics
- Results: {int(word_count * 0.15)} words (15%) — comprehensive findings
- Discussion: {int(word_count * 0.08)} words (8%) — implications, limitations
- Conclusion: {int(word_count * 0.03)} words (3%) — summary and future work

⚠️ **IF YOUR OUTPUT IS SHORTER THAN {int(word_count * 0.85)} WORDS, THE ARTICLE WILL BE REJECTED**
⚠️ Count your words as you write. Each section MUST meet its budget.

---

## CITATION MAPPING
{citation_guide}

---

## SOURCE MATERIAL
The following are excerpts from academic papers. Each source has a citation number. Use these numbers when citing.

{sources}

---

## ARTICLE REQUIREMENTS:

**CRITICAL - WORD COUNT ENFORCEMENT:**
- **MINIMUM**: {int(word_count * 0.85)} words
- **TARGET**: {word_count} words
- **MAXIMUM**: {int(word_count * 1.15)} words
- You MUST write a COMPLETE article meeting this word count
- Do NOT stop early - expand each section with detailed content
- If you're under the word count, add more technical details, examples, and analysis

**CRITICAL - CITATION ENFORCEMENT:**
- You have {len(citation_map)} unique papers available: {list(citation_map.values())}
- You MUST cite at least {max(len(citation_map) // 2, 10)} different papers
- Distribute citations across ALL sections (Introduction, Literature Review, Methodology, Results, Discussion)
- Every major claim, data point, and finding needs a citation
- Use multiple papers per section - aim for 5-10 citations per major section
- Literature Review should have the most citations (20-30% of total)

**OTHER REQUIREMENTS:**
1. **Tone**: {tone} (match this tone throughout)
2. **Technical Depth**: Level {rigor_level}/5 - {get_rigor_description(rigor_level)}
3. **Use IEEE citation format**: [1], [2], [3] in text
4. **DO NOT write a References section** - it will be added automatically

---

Now write the complete article.

**FINAL CRITICAL REMINDERS:**

1. **START WITH TITLE**: First line must be `# [Your Title Here]`
2. **INCLUDE ABSTRACT**: Second section must be `## Abstract` with 150-200 words
3. **WORD COUNT**: Write {word_count} words minimum - expand sections with details, examples, analysis
4. **CITATIONS**: Use at least {max(len(citation_map) // 2, 10)} different papers - cite throughout ALL sections
5. **TECHNICAL DEPTH**: Level {rigor_level}/5 - {get_rigor_description(rigor_level)}
6. **IEEE FORMAT**: [1], [2], [3] ONLY - place after text, before punctuation
7. **NO NOTES**: No explanatory text about citation counts or references
8. **COMPLETE ARTICLE**: Write ALL sections fully - do not stop early
9. **STOP AT CONCLUSION**: Do NOT write a References section - end your article after the Conclusion
10. **NO REFERENCES**: The system will automatically add the reference list - you must NOT include it

**TECHNICAL WRITING EXAMPLES WITH CITATIONS:**
✅ GOOD: "The proposed CNN architecture achieved 94.3% accuracy on ImageNet [1], outperforming ResNet-50 by 2.1% while reducing parameters by 40% [2]."
❌ BAD: "The method showed good results and was better than other approaches." (NO CITATIONS!)

✅ GOOD: "Using a transformer-based encoder with 12 attention heads and 768-dimensional embeddings [3], the model achieved a BLEU score of 41.2 on WMT14 [4]."
❌ BAD: "The transformer model performed well on translation tasks." (NO CITATIONS!)

✅ GOOD: "Recent advances in deep learning have enabled significant improvements in computer vision tasks [5], [6], with convolutional neural networks achieving state-of-the-art results on ImageNet classification [7]."
❌ BAD: "Recent advances in deep learning have enabled significant improvements in computer vision tasks." (NO CITATIONS!)

🚨 **FINAL WARNING - READ CAREFULLY:**
- If you write an article WITHOUT citations, it will be REJECTED
- You MUST include [1], [2], [3] etc. throughout your article
- Check your output before submitting - does it have [1], [2], [3]?
- If not, you have FAILED the task
- Citations are NOT optional - they are MANDATORY
"""
    
    return prompt


if __name__ == '__main__':
    # Test the enhanced retrieval
    print("Testing enhanced citation system...")
    
    topic = "Machine learning approaches in code similarity detection"
    sources, sources_list, citation_map, ref_list = retrieve_for_synthesis_with_citations(topic, top_k=10)
    
    print("\n" + "="*70)
    print("CITATION MAPPING")
    print("="*70)
    for filename, num in sorted(citation_map.items(), key=lambda x: x[1]):
        print(f"[{num}] {filename}")
    
    print("\n" + "="*70)
    print("REFERENCE LIST")
    print("="*70)
    print(ref_list)
