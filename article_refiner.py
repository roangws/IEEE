"""
Article Refiner - Hybrid LLM Refinement System Layer 2

This module implements a refinement layer that enhances base-generated articles
by adding more citations, integrating unused sources, and making corrections
while preserving structure. Based on IEEE patterns research from 5,671 papers.

IEEE Citation Targets (from corpus analysis):
- Mean references: 47 papers
- Mean in-text citations: 135
- Target refs per 1k words: 7.1
- Min in-text citations: 67
"""

import re
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# Import LaTeX validation from app module
try:
    from app import _validate_and_fix_latex_delimiters
except ImportError:
    # Fallback if import fails - define a minimal version
    def _validate_and_fix_latex_delimiters(article: str, log_fn=None) -> str:
        """Minimal LaTeX delimiter fixer."""
        article = article.replace("\\left$", "\\left(")
        article = article.replace("\\right$", "\\right)")
        article = article.replace("$\\left(", "\\left(")
        article = article.replace("\\right)$", "\\right)")
        article = article.replace("\\left\\frac", "\\left(\\frac")
        for _ in range(10):
            article = re.sub(r"\\left\$", r"\\left(", article)
            article = re.sub(r"\\right\$", r"\\right)", article)
            article = re.sub(r"\$\\left\(", r"\\left(", article)
            article = re.sub(r"\\right\)\$(?!\$)", r"\\right)", article)
            article = re.sub(r"\\left\\frac", r"\\left(\\frac", article)
            article = re.sub(r"\\right([A-Za-z])", r"\\right)\1", article)
        return article


# IEEE section citation targets based on research
IEEE_SECTION_CITATION_TARGETS = {
    'introduction': {'min': 8, 'target': 12, 'max': 20},
    'literature review': {'min': 20, 'target': 30, 'max': 50},
    'related work': {'min': 15, 'target': 25, 'max': 40},
    'methodology': {'min': 12, 'target': 18, 'max': 25},
    'methods': {'min': 10, 'target': 15, 'max': 20},
    'experiments': {'min': 8, 'target': 12, 'max': 18},
    'results': {'min': 6, 'target': 10, 'max': 15},
    'discussion': {'min': 4, 'target': 8, 'max': 12},
    'conclusion': {'min': 0, 'target': 2, 'max': 5},
    'abstract': {'min': 0, 'target': 0, 'max': 0}
}

# Load IEEE patterns if available
IEEE_PATTERNS_FILE = "output/ieee_patterns_summary.json"


@dataclass
class ArticleCoverageAnalysis:
    """Analysis of article citation coverage and gaps."""
    total_citations: int = 0
    unique_citations: List[int] = field(default_factory=list)
    citations_per_section: Dict[str, int] = field(default_factory=dict)
    section_gaps: Dict[str, int] = field(default_factory=dict)  # How many more citations needed
    unused_sources: List[int] = field(default_factory=list)
    word_count: int = 0
    refs_per_1k_words: float = 0.0
    meets_ieee_minimum: bool = False
    target_additional_citations: int = 0


@dataclass
class RefinementReport:
    """Report on refinement results."""
    original_citations: int = 0
    refined_citations: int = 0
    citations_added: int = 0
    unused_sources_integrated: int = 0
    sections_enhanced: List[str] = field(default_factory=list)
    validation_passed: bool = True
    hallucinated_citations: List[int] = field(default_factory=list)
    word_count_before: int = 0
    word_count_after: int = 0
    structure_preserved: bool = True
    refinement_notes: List[str] = field(default_factory=list)


class ArticleRefiner:
    """
    Hybrid LLM Refinement System - Layer 2
    
    Refines generated articles by adding more citations while preserving structure.
    """
    
    def __init__(self, llm_provider: str = "openai", model: str = None):
        """
        Initialize the article refiner.
        
        Args:
            llm_provider: LLM to use for refinement ("claude" or "openai")
            model: Optional model name (e.g., "gpt-4o", "gpt-4-turbo")
        """
        self.llm_provider = llm_provider
        self.model = model
        self.ieee_patterns = self._load_ieee_patterns()
        
    def _load_ieee_patterns(self) -> Dict:
        """Load IEEE patterns from research output."""
        if os.path.exists(IEEE_PATTERNS_FILE):
            try:
                with open(IEEE_PATTERNS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load IEEE patterns: {e}")
        return {}
    
    def analyze_article_coverage(
        self, 
        article_text: str, 
        citation_map: Dict[str, int],
        sources_list: List[Dict]
    ) -> ArticleCoverageAnalysis:
        """
        Analyze article to identify citation coverage and gaps.
        
        Args:
            article_text: The generated article text
            citation_map: Mapping of filenames to citation numbers
            sources_list: List of source chunks retrieved
            
        Returns:
            ArticleCoverageAnalysis with detailed metrics
        """
        analysis = ArticleCoverageAnalysis()
        
        # Extract citations from article (supports ranges like [1]-[5])
        unique_citations, citation_instances = self._extract_citation_numbers_and_instances(article_text)
        analysis.total_citations = citation_instances
        analysis.unique_citations = sorted(unique_citations)
        
        # Calculate word count
        analysis.word_count = len(article_text.split())
        
        # Calculate refs per 1k words
        if analysis.word_count > 0:
            analysis.refs_per_1k_words = (len(analysis.unique_citations) / analysis.word_count) * 1000
        
        # Identify unused sources
        used_citation_nums = set(analysis.unique_citations)
        all_citation_nums = set(citation_map.values())
        analysis.unused_sources = sorted(all_citation_nums - used_citation_nums)
        
        # Analyze citations per section
        sections = self._extract_sections(article_text)
        
        for section_name, section_text in sections.items():
            _, section_instances = self._extract_citation_numbers_and_instances(section_text)
            analysis.citations_per_section[section_name] = section_instances
            
            # Calculate gap based on IEEE targets
            section_key = section_name.lower()
            for target_key, targets in IEEE_SECTION_CITATION_TARGETS.items():
                if target_key in section_key:
                    gap = targets['target'] - section_instances
                    if gap > 0:
                        analysis.section_gaps[section_name] = gap
                    break
        
        # Check if meets IEEE minimum (67 citations)
        ieee_min = self.ieee_patterns.get('recommended_constraints', {}).get('in_text_citations', {}).get('min', 67)
        analysis.meets_ieee_minimum = analysis.total_citations >= ieee_min
        
        # Calculate target additional citations
        ieee_target = self.ieee_patterns.get('recommended_constraints', {}).get('in_text_citations', {}).get('target', 135)
        analysis.target_additional_citations = max(0, ieee_target - analysis.total_citations)
        
        return analysis
    
    def _extract_sections(self, article_text: str) -> Dict[str, str]:
        """Extract sections from article text."""
        sections = {}
        
        # Pattern for markdown headers
        section_pattern = r'^##\s+(.+?)$'
        lines = article_text.split('\n')
        
        current_section = "Preamble"
        current_content = []
        
        for line in lines:
            match = re.match(section_pattern, line, re.MULTILINE)
            if match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections

    def _extract_citation_numbers_and_instances(self, text: str) -> Tuple[set, int]:
        """Extract citation numbers and count citation instances, expanding ranges like [1]-[5]."""
        if not text:
            return set(), 0

        nums = set()
        instances = 0

        # Either a range ([a]-[b]) or a single ([n])
        pattern = re.compile(r'\[(\d+)\]\s*-\s*\[(\d+)\]|\[(\d+)\]')
        for m in pattern.finditer(text):
            if m.group(1) and m.group(2):
                try:
                    a = int(m.group(1))
                    b = int(m.group(2))
                except Exception:
                    continue

                lo, hi = (a, b) if a <= b else (b, a)
                nums.update(range(lo, hi + 1))
                instances += (hi - lo + 1)
            else:
                try:
                    n = int(m.group(3))
                except Exception:
                    continue
                nums.add(n)
                instances += 1

        return nums, instances
    
    def refine_article(
        self,
        article_text: str,
        citation_map: Dict[str, int],
        sources_list: List[Dict],
        target_additional_refs: int = 15,
        metadata: Optional[Dict] = None,
        user_instructions: Optional[str] = None,
        external_refs: Optional[List] = None
    ) -> Tuple[str, RefinementReport]:
        """
        Main orchestrator for article refinement.
        
        Args:
            article_text: Base generated article
            citation_map: Mapping of filenames to citation numbers
            sources_list: List of source chunks
            target_additional_refs: Target number of additional citations to add
            metadata: Optional paper metadata
            user_instructions: Optional custom refinement instructions
            external_refs: Optional list of ExternalReference objects from web search
            
        Returns:
            Tuple of (refined_article, refinement_report)
        """
        # Step 1: Analyze current coverage
        analysis = self.analyze_article_coverage(article_text, citation_map, sources_list)
        
        # Step 2: Build refinement prompt
        prompt = self._build_refinement_prompt(
            article_text=article_text,
            analysis=analysis,
            citation_map=citation_map,
            sources_list=sources_list,
            target_additional=target_additional_refs,
            metadata=metadata,
            user_instructions=user_instructions,
            external_refs=external_refs
        )
        
        # Step 3: Call LLM for refinement
        refined_article = self._call_llm(prompt)
        
        # Step 3.5: Validate and fix LaTeX delimiters
        if refined_article:
            refined_article = _validate_and_fix_latex_delimiters(refined_article)
        
        if not refined_article:
            # Return original if refinement fails
            report = RefinementReport(
                original_citations=analysis.total_citations,
                refined_citations=analysis.total_citations,
                validation_passed=False,
                refinement_notes=["Refinement failed - LLM returned empty response"]
            )
            return article_text, report

        # Guardrail: reject obviously truncated/title-only outputs
        if len(refined_article.split()) < max(300, int(analysis.word_count * 0.5)):
            report = RefinementReport(
                original_citations=analysis.total_citations,
                refined_citations=analysis.total_citations,
                validation_passed=False,
                refinement_notes=[
                    "Refinement output appears truncated (too short). Keeping original article.",
                    f"Original words: {analysis.word_count}, Refined words: {len(refined_article.split())}"
                ]
            )
            return article_text, report
        
        # Step 4: Validate refinement
        is_valid, validation_notes, hallucinated = self._validate_refinement(
            refined_article, citation_map, article_text
        )
        
        # Step 5: Create report
        refined_analysis = self.analyze_article_coverage(refined_article, citation_map, sources_list)
        
        report = RefinementReport(
            original_citations=analysis.total_citations,
            refined_citations=refined_analysis.total_citations,
            citations_added=refined_analysis.total_citations - analysis.total_citations,
            unused_sources_integrated=len(set(analysis.unused_sources) - set(refined_analysis.unused_sources)),
            sections_enhanced=list(analysis.section_gaps.keys()),
            validation_passed=is_valid,
            hallucinated_citations=hallucinated,
            word_count_before=analysis.word_count,
            word_count_after=refined_analysis.word_count,
            structure_preserved=self._check_structure_preserved(article_text, refined_article),
            refinement_notes=validation_notes
        )
        
        # Always remove hallucinated citations if found
        if hallucinated:
            cleaned_article = self._remove_hallucinated_citations(refined_article, hallucinated, citation_map)
            # Re-validate after cleanup
            is_valid_after, notes_after, remaining_hallucinated = self._validate_refinement(
                cleaned_article, citation_map, article_text
            )
            if len(remaining_hallucinated) < len(hallucinated):
                refined_article = cleaned_article
                report.refinement_notes.append(
                    f"Removed {len(hallucinated) - len(remaining_hallucinated)}/{len(hallucinated)} hallucinated citations"
                )
                report.hallucinated_citations = remaining_hallucinated
                if not remaining_hallucinated:
                    report.validation_passed = True
                    report.refinement_notes.append("All hallucinations successfully removed")
        
        # If validation failed due to missing citations, return original article
        if not is_valid and any("Missing citations" in note for note in validation_notes):
            return article_text, report
        
        return refined_article, report
    
    def _build_refinement_prompt(
        self,
        article_text: str,
        analysis: ArticleCoverageAnalysis,
        citation_map: Dict[str, int],
        sources_list: List[Dict],
        target_additional: int,
        metadata: Optional[Dict] = None,
        user_instructions: Optional[str] = None,
        external_refs: Optional[List] = None
    ) -> str:
        """
        Build context-aware refinement prompt based on IEEE patterns.
        
        Args:
            article_text: Current article text
            analysis: Coverage analysis results
            citation_map: Citation mapping
            sources_list: Source chunks
            target_additional: Target additional citations
            metadata: Paper metadata
            user_instructions: Custom refinement instructions
            external_refs: External references from web search
            
        Returns:
            Complete refinement prompt
        """
        # Build unused sources context
        unused_sources_text = self._format_unused_sources(
            analysis.unused_sources, 
            sources_list, 
            citation_map,
            metadata
        )
        
        # Build section gaps description
        section_gaps_text = ""
        if analysis.section_gaps:
            section_gaps_text = "**Sections needing more citations:**\n"
            for section, gap in sorted(analysis.section_gaps.items(), key=lambda x: -x[1]):
                section_gaps_text += f"- {section}: needs ~{gap} more citations\n"
        
        # IEEE targets from research
        ieee_targets = self.ieee_patterns.get('recommended_constraints', {})
        target_citations = ieee_targets.get('in_text_citations', {}).get('target', 135)
        refs_per_1k = ieee_targets.get('refs_per_1k_words', {}).get('target', 7.1)
        
        user_notes = ""
        if user_instructions and user_instructions.strip():
            user_notes = f"""\n\n## USER REFINEMENT INSTRUCTIONS (HIGHEST PRIORITY)\n{user_instructions.strip()}\n"""

        # If user requested polish-only (no new citations), use a different prompt.
        if target_additional <= 0:
            prompt = f"""You are an expert IEEE academic editor. Your task is to perform FINAL EDITORIAL POLISH on an existing article while PRESERVING its structure completely.

## POLISH TASK (NO NEW CITATIONS)

**Current Article Stats:**
- Total in-text citation INSTANCES (ranges expanded): {analysis.total_citations}
- Unique papers cited: {len(analysis.unique_citations)}
- Word count: {analysis.word_count}

## CRITICAL RULES

1. **PRESERVE STRUCTURE EXACTLY:**
   - Keep the title (# ...) unchanged
   - Keep ALL section headers (##) unchanged
   - Do NOT add, remove, or reorder sections
   - Keep the overall outline and headings identical

2. **NO CITATION CHANGES:**
   - Do NOT add new in-text citations
   - Do NOT remove existing in-text citations
   - Do NOT change citation numbers
   - Do NOT add a References section

3. **IMPROVE QUALITY ONLY:**
   - Improve clarity, flow, and academic tone (IEEE style)
   - Fix grammar, punctuation, and awkward phrasing
   - Reduce repetition and tighten sentences
   - Ensure terminology, abbreviations, and notation are consistent
   - Keep meaning and technical claims the same
   - Fix ALL paragraph formatting and structure
   - Ensure proper paragraph breaks and transitions

{user_notes}

## ORIGINAL ARTICLE TO POLISH:

{article_text}

## YOUR TASK:

Output the COMPLETE polished article. Start directly with the title (# ...) - no preamble or explanation."""

            return prompt
        
        # Build external references context
        external_refs_text = ""
        if external_refs and len(external_refs) > 0:
            external_refs_text = "\n\n**EXTERNAL REFERENCES (from Internet Search):**\n"
            external_refs_text += "These are high-quality papers from Semantic Scholar that you can cite to diversify sources:\n\n"
            for ref in external_refs:
                external_refs_text += ref.to_context_snippet() + "\n\n"
            external_refs_text += f"\n💡 TIP: Integrate these external references [{external_refs[0].citation_number}]-[{external_refs[-1].citation_number}] to add diversity beyond the corpus.\n"

        prompt = f"""You are an expert IEEE academic editor. Your task is to REFINE an existing article by adding more citations while PRESERVING its structure completely.

## REFINEMENT TASK

**Current Article Stats:**
- Total in-text citation INSTANCES (ranges expanded): {analysis.total_citations}
- Unique papers cited: {len(analysis.unique_citations)}
- Word count: {analysis.word_count}
- Refs per 1k words: {analysis.refs_per_1k_words:.1f}

**IEEE Targets (from 5,671 paper analysis):**
- Target in-text citations: {target_citations}
- Target refs per 1k words: {refs_per_1k}
- You should add approximately {target_additional} more citation instances

**Available Citation Numbers (ONLY USE THESE - DO NOT EXCEED):**
Valid range: [1] to [{max(citation_map.values()) + (len(external_refs) if external_refs else 0)}]
Corpus papers: {sorted(citation_map.values())}
{f"External papers: [{external_refs[0].citation_number}]-[{external_refs[-1].citation_number}]" if external_refs else ""}

⚠️ CRITICAL: Do NOT use any citation number higher than [{max(citation_map.values()) + (len(external_refs) if external_refs else 0)}]. Any citation outside this list will be REMOVED.

**Currently Unused Sources (PRIORITIZE THESE):**
{unused_sources_text}

{external_refs_text}

{section_gaps_text}

## CRITICAL RULES

1. **PRESERVE STRUCTURE EXACTLY:**
   - Keep ALL section headers (##) unchanged
   - Keep the title (# ...) unchanged
   - Keep paragraph structure intact
   - Do NOT add new sections

2. **ADD CITATIONS NATURALLY:**
   - Insert citations into EXISTING sentences
   - Add new sentences with citations where appropriate
   - Place citations BEFORE punctuation: "Recent work shows improvements [5]."
   - Use ranges for consecutive: [1]-[3]
   - Use commas for non-consecutive: [1], [5], [8]

3. **PRIORITIZE UNUSED SOURCES:**
   - The sources listed as "unused" above should be integrated first
   - Match source content to appropriate sections
   - **MANDATORY:** Integrate at least {min(10, max(3, len(analysis.unused_sources)))} unused sources if available

4. **NO HALLUCINATIONS:**
   - ONLY use citation numbers from the available list above
   - Maximum citation number is {max(citation_map.values())}
   - Do NOT invent [99] or any number not in the list

5. **SECTION-SPECIFIC TARGETS:**
   - Literature Review/Related Work: Add 10-15 citations (MOST)
   - Methodology: Add 5-8 citations
   - Introduction: Add 3-5 citations
   - Results/Experiments: Add 3-5 citations
   - Discussion: Add 2-3 citations

6. **PARAGRAPH AND FORMATTING REQUIREMENTS:**
   - Fix ALL paragraph formatting issues
   - Ensure proper paragraph breaks and structure
   - Each paragraph should have a clear topic sentence
   - Maintain consistent paragraph length (avoid extremely short/long paragraphs)
   - Fix any formatting inconsistencies
   - Ensure smooth transitions between paragraphs

7. **ABSTRACT REQUIREMENTS (CRITICAL):**
   - Abstract must be a clean overview of the topic
   - NO citations in the abstract
   - NO mathematical formulas or equations in the abstract
   - Abstract should be 150-250 words
   - Focus on research problem, methods, results, and conclusion
   - Keep it readable without technical notation

8. **MINIMUM ADDITIONS (MANDATORY):**
   - Add at least {max(5, target_additional)} new in-text citation instances.
   - If you cannot add that many without distortion, add as many as possible and still return the FULL article.

{user_notes}

## ORIGINAL ARTICLE TO REFINE:

{article_text}

## YOUR TASK:

Output the COMPLETE refined article with additional citations integrated naturally. 
Preserve ALL original content and structure. 
Only ADD citations, do not remove existing ones.
CRITICAL: Fix all paragraph formatting and ensure the abstract is a clean overview without citations or formulas.
Start directly with the title (# ...) - no preamble or explanation."""

        return prompt
    
    def _format_unused_sources(
        self,
        unused_nums: List[int],
        sources_list: List[Dict],
        citation_map: Dict[str, int],
        metadata: Optional[Dict] = None
    ) -> str:
        """Format unused sources for the prompt."""
        if not unused_nums:
            return "All sources have been used."
        
        # Reverse citation map
        num_to_file = {v: k for k, v in citation_map.items()}
        
        lines = []
        for num in unused_nums[:35]:  # Give the model enough options to actually integrate
            filename = num_to_file.get(num, "unknown")
            
            # Get metadata
            if metadata:
                meta = metadata.get(filename, {})
                title = meta.get('title') or filename
                title = title[:80]
            else:
                title = filename[:80]
            
            # Get sample text from sources
            sample_text = ""
            for source in sources_list:
                if source.get('filename') == filename:
                    chunk = source.get('chunk_text', '')[:200]
                    sample_text = chunk.replace('\n', ' ').strip()
                    break
            
            lines.append(f"[{num}] {title}")
            if sample_text:
                lines.append(f"    Context: {sample_text}...")
        
        if len(unused_nums) > 35:
            lines.append(f"\n... and {len(unused_nums) - 35} more unused sources")
        
        return '\n'.join(lines)
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the configured LLM for refinement."""
        try:
            from config import get_llm_response
            
            system_message = """You are an expert IEEE academic editor.
You will be given a COMPLETE draft article. Your task is to produce a COMPLETE refined version of that same article.

Hard rules:
- Preserve ALL headings and overall structure.
- Preserve ALL existing in-text citations exactly as they appear (e.g., [1], [2-5], [12,15]).
- DO NOT remove, modify, or renumber any existing citations.
- DO NOT delete any citations from the article body.
- Do NOT output only a title or outline.
- Do NOT include any commentary, preamble, or explanation.
- Output the FULL refined article starting with the title line (# ...)."""
            
            if self.llm_provider.lower() == "claude":
                response = get_llm_response(
                    prompt=prompt,
                    llm_type="claude",
                    system_message=system_message,
                    max_tokens=12000,
                    temperature=0.2,
                    timeout_seconds=180,
                    model=self.model
                )
            elif self.llm_provider.lower() == "openai":
                response = get_llm_response(
                    prompt=prompt,
                    llm_type="openai",
                    system_message=system_message,
                    max_tokens=12000,
                    temperature=0.2,
                    timeout_seconds=180,
                    model=self.model
                )
            else:
                # Default to OpenAI
                response = get_llm_response(
                    prompt=prompt,
                    llm_type="openai",
                    system_message=system_message,
                    max_tokens=12000,
                    temperature=0.2,
                    timeout_seconds=180,
                    model=self.model
                )
            
            return response
            
        except Exception:
            # Let the UI handle errors with a full traceback instead of silently failing
            raise
    
    def _validate_refinement(
        self,
        refined_article: str,
        citation_map: Dict[str, int],
        original_article: str
    ) -> Tuple[bool, List[str], List[int]]:
        """
        Validate the refined article for hallucinations and structure preservation.
        
        Args:
            refined_article: The refined article text
            citation_map: Valid citation mapping
            original_article: Original article for comparison
            
        Returns:
            Tuple of (is_valid, validation_notes, hallucinated_citations)
        """
        notes = []
        hallucinated = []
        is_valid = True
        
        # Extract all citations from refined article
        citation_pattern = r'\[(\d+)\]'
        all_citations = [int(c) for c in re.findall(citation_pattern, refined_article)]
        
        # Check for hallucinated citations
        valid_nums = set(citation_map.values())
        
        for cit in all_citations:
            if cit not in valid_nums:
                hallucinated.append(cit)
        
        if hallucinated:
            is_valid = False
            unique_hallucinated = sorted(set(hallucinated))
            notes.append(f"Found {len(unique_hallucinated)} hallucinated citation numbers: {unique_hallucinated[:10]}")
        
        # Check structure preservation
        original_sections = set(self._extract_sections(original_article).keys())
        refined_sections = set(self._extract_sections(refined_article).keys())
        
        missing_sections = original_sections - refined_sections
        if missing_sections:
            is_valid = False
            notes.append(f"Missing sections: {missing_sections}")
        
        # Check if citations are preserved
        original_citations = [int(c) for c in re.findall(citation_pattern, original_article)]
        refined_citations_set = set(all_citations)
        original_citations_set = set(original_citations)
        
        missing_citations = original_citations_set - refined_citations_set
        if missing_citations:
            is_valid = False
            notes.append(f"Missing citations that were removed: {sorted(missing_citations)[:10]}")
        
        # Check word count didn't decrease significantly
        original_words = len(original_article.split())
        refined_words = len(refined_article.split())
        
        if refined_words < original_words * 0.9:
            is_valid = False
            notes.append(f"Word count decreased significantly: {original_words} -> {refined_words}")
        
        if is_valid:
            notes.append("Validation passed - no hallucinations detected, structure preserved")
        
        return is_valid, notes, list(set(hallucinated))
    
    def _remove_hallucinated_citations(
        self,
        article: str,
        hallucinated: List[int],
        citation_map: Dict[str, int]
    ) -> str:
        """Remove hallucinated citations from the article."""
        if not hallucinated:
            return article
        
        # Sort hallucinated numbers for efficient removal
        hallucinated_set = set(hallucinated)
        
        # Remove each hallucinated citation
        for num in sorted(hallucinated_set, reverse=True):
            # Pattern 1: Remove from ranges like [30]-[35]
            article = re.sub(rf'\[{num}\]\s*-\s*\[\d+\]', '', article)
            article = re.sub(rf'\[\d+\]\s*-\s*\[{num}\]', '', article)
            
            # Pattern 2: Remove from lists like [1], [31], [5]
            article = re.sub(rf',\s*\[{num}\]', '', article)
            article = re.sub(rf'\[{num}\]\s*,', '', article)
            
            # Pattern 3: Remove standalone [31]
            article = re.sub(rf'\[{num}\]', '', article)
        
        # Cleanup pass 1: Fix broken citation lists
        article = re.sub(r'\[\s*,\s*', '[', article)  # [, 5] -> [5]
        article = re.sub(r',\s*,+', ',', article)      # [1,,,5] -> [1,5]
        article = re.sub(r',\s*\]', ']', article)      # [1, ] -> [1]
        article = re.sub(r'\[\s*\]', '', article)      # [] -> remove
        
        # Cleanup pass 2: Fix spacing
        article = re.sub(r'  +', ' ', article)         # Double spaces
        article = re.sub(r' \.', '.', article)        # Space before period
        article = re.sub(r' ,', ',', article)          # Space before comma
        
        # Cleanup pass 3: Fix broken ranges
        article = re.sub(r'-\s*\[\s*\]', '', article) # [5]-[] -> [5]
        article = re.sub(r'\[\s*\]\s*-', '', article) # []-[5] -> [5]
        
        return article
    
    def _check_structure_preserved(self, original: str, refined: str) -> bool:
        """Check if the article structure was preserved."""
        original_headers = re.findall(r'^##?\s+.+$', original, re.MULTILINE)
        refined_headers = re.findall(r'^##?\s+.+$', refined, re.MULTILINE)
        
        # Check if all original headers are present
        return set(original_headers).issubset(set(refined_headers))


def create_refinement_report(report: RefinementReport) -> str:
    """
    Create a formatted refinement report for display.
    
    Args:
        report: RefinementReport object
        
    Returns:
        Formatted string report
    """
    lines = [
        "=" * 50,
        "📊 ARTICLE REFINEMENT REPORT",
        "=" * 50,
        "",
        "## Citation Statistics",
        f"- Original citations: {report.original_citations}",
        f"- Refined citations: {report.refined_citations}",
        f"- **Citations added: +{report.citations_added}**",
        f"- Unused sources integrated: {report.unused_sources_integrated}",
        "",
        "## Word Count",
        f"- Before: {report.word_count_before:,} words",
        f"- After: {report.word_count_after:,} words",
        f"- Change: {report.word_count_after - report.word_count_before:+,} words",
        "",
        "## Validation",
        f"- Status: {'✅ PASSED' if report.validation_passed else '⚠️ ISSUES FOUND'}",
        f"- Structure preserved: {'✅ Yes' if report.structure_preserved else '❌ No'}",
    ]
    
    if report.hallucinated_citations:
        lines.append(f"- Hallucinated citations removed: {report.hallucinated_citations}")
    
    if report.sections_enhanced:
        lines.append("")
        lines.append("## Sections Enhanced")
        for section in report.sections_enhanced:
            lines.append(f"- {section}")
    
    if report.refinement_notes:
        lines.append("")
        lines.append("## Notes")
        for note in report.refinement_notes:
            lines.append(f"- {note}")
    
    lines.append("")
    lines.append("=" * 50)
    
    return '\n'.join(lines)


# Convenience function for direct usage
def refine_article_with_llm(
    article_text: str,
    citation_map: Dict[str, int],
    sources_list: List[Dict],
    llm_provider: str = "openai",
    target_additional_refs: int = 15,
    metadata: Optional[Dict] = None
) -> Tuple[str, str]:
    """
    Convenience function to refine an article with more citations.
    
    Args:
        article_text: The base generated article
        citation_map: Mapping of filenames to citation numbers
        sources_list: List of source chunks
        llm_provider: "claude" or "openai"
        target_additional_refs: Target additional citations
        metadata: Optional paper metadata
        
    Returns:
        Tuple of (refined_article, formatted_report)
    """
    refiner = ArticleRefiner(llm_provider=llm_provider)
    refined_article, report = refiner.refine_article(
        article_text=article_text,
        citation_map=citation_map,
        sources_list=sources_list,
        target_additional_refs=target_additional_refs,
        metadata=metadata
    )
    
    formatted_report = create_refinement_report(report)
    
    return refined_article, formatted_report
