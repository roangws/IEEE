"""
Default Article Template Module
Contains the default template for academic article generation.
"""

DEFAULT_TEMPLATE = """# {topic}

## Abstract
Based on an analysis of {num_sources} academic papers, this {tone} article synthesizes key findings and insights related to {topic}. The following sections provide a comprehensive overview of the current state of research, methodologies, and future directions in this field.

**CRITICAL STRUCTURAL REQUIREMENTS** (Based on analysis of 200 IEEE papers):
- Abstract: REQUIRED (100% of papers) - 100-150 words summarizing key contributions
- Introduction: REQUIRED (100% of papers) - Establish context, motivation, and scope
- Results: REQUIRED (99.5% of papers) - Present findings with data and evidence
- Method/Approach: REQUIRED (93-95% of papers) - Detail methodologies and techniques
- Conclusion: REQUIRED (81% of papers) - Synthesize insights and implications
- References: REQUIRED (100% of papers) - Properly formatted citations

## 1. Introduction
{topic} represents a significant area of research with broad implications across multiple domains. This section MUST establish clear research context, motivation, and scope.

**Required elements for Introduction:**
- Opening statement establishing the research domain and its importance
- Problem statement or research gap identification
- Overview of the current state of the field
- Clear articulation of what this synthesis covers
- Roadmap of the article structure

The analysis draws upon {num_sources} peer-reviewed papers to provide a comprehensive synthesis of:
- Core concepts and theoretical frameworks
- Methodological approaches and innovations
- Key findings and empirical results
- Emerging trends and future research directions

## 2. Background and Related Work
[Provide essential background information, historical context, and review of related work. This section should establish the foundation for understanding the topic.]

**Content requirements:**
- Historical development and evolution of the field
- Foundational concepts and terminology definitions
- Key prior work and seminal contributions
- Current research landscape and major research groups/institutions
- Identification of research gaps this synthesis addresses

## 3. Methodology and Approach
[Synthesize the various methodological approaches found in the literature. Compare and contrast different techniques, tools, frameworks, and experimental designs.]

**Content requirements:**
- Overview of common methodological frameworks
- Detailed description of prevalent techniques and algorithms
- Comparison of different approaches with their strengths/weaknesses
- Discussion of evaluation metrics and validation methods
- Analysis of datasets, benchmarks, and experimental setups used

## 4. Results and Key Findings
[Present the major findings from the analyzed papers, organizing them thematically. Highlight areas of consensus and disagreement in the literature.]

**Content requirements:**
- Quantitative results with specific metrics and performance numbers
- Qualitative findings and observations
- Comparative analysis across different studies
- Statistical significance and validation of results
- Visualization or tabular presentation of key data points

### 4.1 Primary Contributions and Breakthroughs
[Detailed discussion of the most significant contributions, innovations, and breakthroughs reported in the literature]

### 4.2 Supporting Evidence and Validation
[Analysis of empirical evidence, validation studies, ablation studies, and reproducibility results]

### 4.3 Limitations and Challenges
[Critical examination of limitations, challenges, failure cases, and areas requiring further investigation]

## 5. Discussion and Analysis
[Provide critical analysis, identifying patterns, contradictions, and gaps in the current research. Synthesize insights across multiple papers to draw broader conclusions.]

**Content requirements:**
- Cross-study synthesis identifying common themes and patterns
- Critical evaluation of conflicting findings and their explanations
- Analysis of research trends and trajectory
- Discussion of theoretical implications and contributions
- Examination of practical applications and real-world impact
- Identification of open problems and research gaps

### 5.1 Comparative Analysis
[In-depth comparison of different approaches, their relative merits, trade-offs, and applicability to different scenarios]

### 5.2 Theoretical Implications
[Discussion of theoretical contributions, conceptual frameworks, and their significance to the field]

### 5.3 Practical Applications and Impact
[Examination of real-world applications, deployment scenarios, industry adoption, and societal impact]

## 6. Future Research Directions
[Identify promising areas for future research based on gaps, limitations, and emerging trends identified in the literature.]

**Content requirements:**
- Specific open problems and unsolved challenges
- Promising research directions with justification
- Potential methodological improvements
- Emerging applications and use cases
- Cross-disciplinary opportunities
- Long-term research vision

## 7. Conclusion
[Provide a concise but comprehensive summary of the key insights, their significance, and the overall state of research in this area.]

**Content requirements:**
- Synthesis of main findings and contributions
- Assessment of the current state of the field
- Key takeaways for researchers and practitioners
- Final thoughts on the trajectory and impact of this research area

---

## References
[List all cited papers with proper IEEE academic formatting: [1] Author(s), "Title," Journal/Conference, vol., no., pp., year.]

---

**WORD COUNT DISTRIBUTION GUIDANCE** (Based on corpus analysis):
- Abstract: 100-150 words (2% of total)
- Introduction: 800-1000 words (12-15% of total)
- Background/Related Work: 600-800 words (10% of total)
- Methodology: 1000-1200 words (15-18% of total)
- Results: 1200-1500 words (18-22% of total)
- Discussion: 1000-1200 words (15-18% of total)
- Future Directions: 400-600 words (6-8% of total)
- Conclusion: 400-500 words (6% of total)

**Target Length**: {word_count} words (body only, excluding References)
**Tone**: {tone}
**Sources**: {num_sources} papers

**CRITICAL REMINDERS**:
1. Every claim MUST be supported by inline citations [Filename.pdf]
2. Synthesize across sources - do NOT just summarize individual papers
3. Include specific data, metrics, and quantitative results from papers
4. Maintain IEEE academic writing standards throughout
5. Ensure logical flow and coherence between sections
6. Meet the target word count ±15% (body only, References excluded)
"""

SYNTHESIS_SYSTEM_PROMPT = """You are an expert academic writer and researcher specializing in IEEE-style publications. Your task is to write a comprehensive, well-structured article based on the provided academic paper excerpts.

**CRITICAL STRUCTURAL REQUIREMENTS** (Based on analysis of 200 IEEE papers):
- Abstract (100% required): 100-150 words summarizing key contributions
- Introduction (100% required): Establish context, motivation, problem statement, and scope
- Results (99.5% required): Present findings with specific data, metrics, and evidence
- Methodology/Approach (93-95% required): Detail techniques, algorithms, and frameworks
- Conclusion (81% required): Synthesize insights, implications, and future directions
- References (100% required): Properly formatted IEEE citations

**Content Quality Guidelines:**
1. **Use the provided template structure** - expand each section with detailed, substantive content following the specified requirements
2. **Cite sources inline** using [Filename.pdf] format - every claim must be supported by citations
3. **Synthesize information** across multiple sources - identify patterns, compare approaches, analyze trends
4. **Maintain IEEE academic rigor** - precise language, logical argumentation, technical accuracy
5. **Include quantitative data** - specific metrics, performance numbers, statistical results from papers
6. **Be critical and analytical** - don't just report findings, evaluate their significance and limitations
7. **Target the specified word count** - distribute words according to the guidance (±15% tolerance)
8. **Match the requested tone** while maintaining IEEE publication standards
9. **Ensure coherence** - logical flow between sections, unified narrative, clear transitions
10. **Provide specific examples** - algorithms, datasets, experimental setups, case studies from papers

**Word Count Distribution** (strictly follow):
- Abstract: 100-150 words (2%)
- Introduction: 800-1000 words (12-15%)
- Background: 600-800 words (10%)
- Methodology: 1000-1200 words (15-18%)
- Results: 1200-1500 words (18-22%)
- Discussion: 1000-1200 words (15-18%)
- Future Directions: 400-600 words (6-8%)
- Conclusion: 400-500 words (6%)

**Quality Standards:**
- Every section must have substantive content with proper depth
- Include comparative analysis across multiple papers
- Present specific data points, metrics, and quantitative results
- Discuss methodological details, not just high-level concepts
- Identify research gaps and limitations critically
- Ensure proper IEEE citation format throughout

Remember: This must read like a professional IEEE publication, not a blog post or summary. Every paragraph should demonstrate deep understanding and synthesis of the source material."""

def get_article_prompt(topic: str, sources: str, word_count: int, tone: str, template: str = None) -> str:
    """
    Generate the complete prompt for article generation.
    
    Args:
        topic: The article topic/title
        sources: Retrieved context from papers
        word_count: Target word count
        tone: Writing tone (Academic, Technical, Survey, Opinion)
        template: Custom template (uses DEFAULT_TEMPLATE if None)
        
    Returns:
        Complete prompt for LLM
    """
    if template is None:
        template = DEFAULT_TEMPLATE
    
    # Count number of unique sources
    num_sources = len(set([line.split(']')[0].replace('[', '') 
                           for line in sources.split('\n') 
                           if line.startswith('[')]))
    
    # Fill in template variables
    filled_template = template.format(
        topic=topic,
        num_sources=num_sources,
        word_count=word_count,
        tone=tone,
        sources=sources
    )
    
    # Construct full prompt
    prompt = f"""{SYNTHESIS_SYSTEM_PROMPT}

---

## ARTICLE TOPIC
{topic}

---

## TONE
{tone}

---

## TARGET WORD COUNT
{word_count} words

---

## SOURCE MATERIAL
The following excerpts are from academic papers relevant to this topic. Use these as the foundation for your article:

{sources}

---

## TEMPLATE TO FOLLOW
{filled_template}

---

Now, write the complete article following the template structure above. Expand each section with detailed analysis and synthesis of the source material. Include inline citations and ensure the article meets the target word count while maintaining high academic quality.
"""
    
    return prompt
