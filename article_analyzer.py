#!/usr/bin/env python3
"""
Article Analyzer for IEEE Access Submission Evaluation
Scores manuscripts (1-100) against IEEE Access standards using LLM evaluation.
"""

import os
import re
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import PyPDF2
from config import call_claude, call_openai, call_ollama


@dataclass
class ArticleMetrics:
    """Extracted metrics from the article"""
    # Basic structure
    word_count: int
    abstract_length: int
    num_sections: int
    num_references: int
    num_figures: int
    num_tables: int
    
    # Content analysis
    has_abstract: bool
    has_introduction: bool
    has_methodology: bool
    has_experiments: bool
    has_results: bool
    has_discussion: bool
    has_conclusion: bool
    has_references: bool
    
    # Citation analysis
    in_text_citations: int
    refs_per_1k_words: float
    
    # Quality indicators
    math_density: int
    code_mentions: int
    dataset_mentions: int
    comparison_mentions: int
    
    # Readability
    avg_sentence_length: float
    avg_paragraph_length: float


@dataclass
class EvaluationResult:
    """Complete evaluation result"""
    overall_score: int  # 1-100
    decision: str  # "Strong Accept", "Accept", "Borderline", "Reject", "Desk Reject"
    confidence: str  # "High", "Medium", "Low"
    
    # Detailed scores (each 1-100)
    technical_soundness: int
    novelty: int
    comprehensiveness: int
    reference_quality: int
    structure_quality: int
    writing_quality: int
    
    # Comparisons to IEEE Access standards
    metrics_comparison: Dict[str, Dict[str, any]]
    
    # Recommendations
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    # Desk rejection triggers (if any)
    desk_rejection_reasons: List[str]


class ArticleAnalyzer:
    """Analyzes manuscripts against IEEE Access standards"""
    
    def __init__(self):
        """Initialize with IEEE Access reference data"""
        self.ieee_standards = self._load_ieee_standards()
        self.reference_data = self._load_reference_data()
    
    def _load_ieee_standards(self) -> Dict:
        """Load IEEE Access standards and benchmarks"""
        return {
            "journal_info": {
                "issn": "2169-3536",
                "name": "IEEE Access",
                "acceptance_rate": 0.27,
                "impact_factor": 3.6,
                "citescore": 9.0
            },
            "submission_requirements": {
                "abstract_length": [150, 250],
                "recommended_page_limit": 20,
                "keywords_required": [3, 4]
            },
            "statistical_benchmarks": {
                "word_count": {"min": 3000, "max": 10000, "mean": 6629, "median": 6085},
                "references": {"min": 20, "max": 80, "mean": 42, "median": 38},
                "figures": {"min": 3, "max": 15, "mean": 23, "median": 20},
                "tables": {"min": 1, "max": 8, "mean": 14, "median": 12},
                "in_text_citations": {"min": 0, "max": 1590, "mean": 137, "median": 107}
            },
            "desk_rejection_triggers": [
                "out_of_scope",
                "below_technical_standards",
                "no_clear_advance",
                "plagiarism",
                "format_violations"
            ]
        }
    
    def _load_reference_data(self) -> Dict:
        """Load reference data from 5k+ analyzed papers"""
        reference_data = {}
        
        # Load quality metrics
        quality_path = "output/quality_metrics_summary_full.json"
        if os.path.exists(quality_path):
            with open(quality_path, 'r') as f:
                reference_data['quality_metrics'] = json.load(f)
        
        # Load IEEE patterns
        patterns_path = "output/ieee_patterns_summary.json"
        if os.path.exists(patterns_path):
            with open(patterns_path, 'r') as f:
                reference_data['ieee_patterns'] = json.load(f)
        
        # Load reference analysis
        refs_path = "output/references_analysis_summary.json"
        if os.path.exists(refs_path):
            with open(refs_path, 'r') as f:
                reference_data['references_analysis'] = json.load(f)
        
        # Load section stats
        sections_path = "output/ieee_section_stats_summary.json"
        if os.path.exists(sections_path):
            with open(sections_path, 'r') as f:
                reference_data['section_stats'] = json.load(f)
        
        return reference_data
    
    def parse_file(self, file_path: str, file_type: str) -> str:
        """Parse MD or PDF file to extract text"""
        if file_type == "md":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_type == "pdf":
            return self._parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _parse_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        text = []
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
        return '\n'.join(text)
    
    def extract_features(self, article_text: str) -> ArticleMetrics:
        """Extract quantitative features from article"""
        
        # Basic counts
        words = article_text.split()
        word_count = len(words)
        
        # Section detection
        sections = re.findall(r'^#{1,3}\s+(.+)$', article_text, re.MULTILINE)
        num_sections = len(sections)
        
        # Check for key sections
        text_lower = article_text.lower()
        has_abstract = bool(re.search(r'\babstract\b', text_lower))
        has_introduction = bool(re.search(r'\bintroduction\b', text_lower))
        has_methodology = bool(re.search(r'\b(methodology|method|approach)\b', text_lower))
        has_experiments = bool(re.search(r'\b(experiment|evaluation)\b', text_lower))
        has_results = bool(re.search(r'\bresults?\b', text_lower))
        has_discussion = bool(re.search(r'\bdiscussion\b', text_lower))
        has_conclusion = bool(re.search(r'\bconclusion\b', text_lower))
        has_references = bool(re.search(r'\breferences?\b', text_lower))
        
        # Abstract length
        abstract_match = re.search(r'##?\s*Abstract\s*\n(.*?)(?:\n##|\Z)', article_text, re.IGNORECASE | re.DOTALL)
        abstract_length = len(abstract_match.group(1).split()) if abstract_match else 0
        
        # References
        ref_matches = re.findall(r'\[(\d+)\]', article_text)
        in_text_citations = len(ref_matches)
        unique_refs = len(set(ref_matches))
        num_references = unique_refs
        
        # Figures and tables
        num_figures = len(re.findall(r'\b(figure|fig\.?)\s+\d+', text_lower))
        num_tables = len(re.findall(r'\btable\s+\d+', text_lower))
        
        # Quality indicators
        math_density = len(re.findall(r'\$.*?\$|\\[a-zA-Z]+', article_text))
        code_mentions = len(re.findall(r'\b(github|code|repository|implementation)\b', text_lower))
        dataset_mentions = len(re.findall(r'\b(dataset|benchmark|corpus)\b', text_lower))
        comparison_mentions = len(re.findall(r'\b(compared|comparison|baseline|outperform)\b', text_lower))
        
        # Readability
        sentences = re.split(r'[.!?]+', article_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        paragraphs = article_text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        # Calculate refs per 1k words
        refs_per_1k_words = (num_references / word_count * 1000) if word_count > 0 else 0
        
        return ArticleMetrics(
            word_count=word_count,
            abstract_length=abstract_length,
            num_sections=num_sections,
            num_references=num_references,
            num_figures=num_figures,
            num_tables=num_tables,
            has_abstract=has_abstract,
            has_introduction=has_introduction,
            has_methodology=has_methodology,
            has_experiments=has_experiments,
            has_results=has_results,
            has_discussion=has_discussion,
            has_conclusion=has_conclusion,
            has_references=has_references,
            in_text_citations=in_text_citations,
            refs_per_1k_words=refs_per_1k_words,
            math_density=math_density,
            code_mentions=code_mentions,
            dataset_mentions=dataset_mentions,
            comparison_mentions=comparison_mentions,
            avg_sentence_length=avg_sentence_length,
            avg_paragraph_length=avg_paragraph_length
        )
    
    def evaluate_with_llm(
        self,
        article_text: str,
        metrics: ArticleMetrics,
        llm_type: str = "claude"
    ) -> EvaluationResult:
        """Use LLM to evaluate article quality and provide detailed feedback"""
        
        # Build comprehensive evaluation prompt
        prompt = self._build_evaluation_prompt(article_text, metrics)
        system_msg = "You are an expert IEEE Access reviewer with deep knowledge of academic publishing standards."
        
        # Call appropriate LLM
        if llm_type == "claude_sonnet":
            response = call_claude(
                prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_msg
            )
        elif llm_type == "claude_opus":
            response = call_claude(
                prompt,
                model="claude-3-opus-20240229",
                max_tokens=4000,
                system=system_msg
            )
        elif llm_type == "openai_gpt4o":
            response = call_openai(
                prompt,
                model="gpt-4o",
                max_tokens=4000,
                system=system_msg
            )
        elif llm_type == "openai_gpt4o_mini":
            response = call_openai(
                prompt,
                model="gpt-4o-mini",
                max_tokens=4000,
                system=system_msg
            )
        elif llm_type == "ollama":
            response = call_ollama(
                prompt,
                model="llama3.1",
                system=system_msg
            )
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        
        # Parse LLM response
        return self._parse_llm_response(response, metrics)
    
    def _build_evaluation_prompt(self, article_text: str, metrics: ArticleMetrics) -> str:
        """Build comprehensive evaluation prompt for LLM"""
        
        # Get benchmarks
        benchmarks = self.ieee_standards['statistical_benchmarks']
        
        prompt = f"""# IEEE Access Manuscript Evaluation

## Your Task
Evaluate this manuscript for submission to IEEE Access (Impact Factor: 3.6, Acceptance Rate: 27%).
Provide a comprehensive review with scores and recommendations.

## Article Preview (first 3000 chars)
{article_text[:3000]}

## Extracted Metrics
{json.dumps(asdict(metrics), indent=2)}

## IEEE Access Benchmarks (from 5,634 published papers)
**Word Count**: min={benchmarks['word_count']['min']}, mean={benchmarks['word_count']['mean']}, median={benchmarks['word_count']['median']}, max={benchmarks['word_count']['max']}
**References**: min={benchmarks['references']['min']}, mean={benchmarks['references']['mean']}, median={benchmarks['references']['median']}, max={benchmarks['references']['max']}
**Figures**: mean={benchmarks['figures']['mean']}, median={benchmarks['figures']['median']}
**Tables**: mean={benchmarks['tables']['mean']}, median={benchmarks['tables']['median']}
**In-text Citations**: mean={benchmarks['in_text_citations']['mean']}, median={benchmarks['in_text_citations']['median']}

## Quality Indicators from Published Papers
- Papers with math: 99%
- Papers with statistical tests: 91%
- Papers with code availability: 20%
- Papers with comparisons: 94%
- Papers with ablation studies: 32%
- Papers with error reporting: 59%

## Evaluation Criteria

Provide scores (1-100) for each criterion:

1. **Technical Soundness** (weight: HIGH)
   - Methodology rigor
   - Experimental design
   - Statistical validity
   - Reproducibility

2. **Novelty** (weight: HIGH)
   - Clear contribution
   - Advancement over prior work
   - Innovation level

3. **Comprehensiveness** (weight: MEDIUM)
   - Literature review depth
   - Experimental coverage
   - Result analysis

4. **Reference Quality** (weight: MEDIUM)
   - Citation count and relevance
   - Recent work coverage (post-2017)
   - Key papers included

5. **Structure Quality** (weight: MEDIUM)
   - Section organization
   - Logical flow
   - IEEE format compliance

6. **Writing Quality** (weight: MEDIUM)
   - Clarity and precision
   - Grammar and style
   - Technical communication

## Output Format (JSON)

Provide your evaluation in this exact JSON format:

{{
  "overall_score": <1-100>,
  "decision": "<Strong Accept|Accept|Borderline|Reject|Desk Reject>",
  "confidence": "<High|Medium|Low>",
  "scores": {{
    "technical_soundness": <1-100>,
    "novelty": <1-100>,
    "comprehensiveness": <1-100>,
    "reference_quality": <1-100>,
    "structure_quality": <1-100>,
    "writing_quality": <1-100>
  }},
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "weaknesses": [
    "<weakness 1>",
    "<weakness 2>",
    "<weakness 3>"
  ],
  "recommendations": [
    "<recommendation 1>",
    "<recommendation 2>",
    "<recommendation 3>"
  ],
  "desk_rejection_reasons": [
    "<reason if applicable, otherwise empty array>"
  ],
  "metrics_analysis": {{
    "word_count_assessment": "<below|within|above> benchmark range",
    "reference_count_assessment": "<below|within|above> benchmark range",
    "structure_completeness": "<percentage>% of expected sections present"
  }}
}}

Be thorough, objective, and constructive in your evaluation."""

        return prompt
    
    def _parse_llm_response(self, response: str, metrics: ArticleMetrics) -> EvaluationResult:
        """Parse LLM JSON response into EvaluationResult"""
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("Could not parse JSON from LLM response")
        
        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
        
        # Build metrics comparison
        benchmarks = self.ieee_standards['statistical_benchmarks']
        metrics_comparison = {
            "word_count": {
                "value": metrics.word_count,
                "benchmark_mean": benchmarks['word_count']['mean'],
                "benchmark_median": benchmarks['word_count']['median'],
                "status": self._compare_to_benchmark(
                    metrics.word_count,
                    benchmarks['word_count']['min'],
                    benchmarks['word_count']['max']
                )
            },
            "references": {
                "value": metrics.num_references,
                "benchmark_mean": benchmarks['references']['mean'],
                "benchmark_median": benchmarks['references']['median'],
                "status": self._compare_to_benchmark(
                    metrics.num_references,
                    benchmarks['references']['min'],
                    benchmarks['references']['max']
                )
            },
            "figures": {
                "value": metrics.num_figures,
                "benchmark_mean": benchmarks['figures']['mean'],
                "status": "within_range" if metrics.num_figures >= 3 else "below_range"
            },
            "tables": {
                "value": metrics.num_tables,
                "benchmark_mean": benchmarks['tables']['mean'],
                "status": "within_range" if metrics.num_tables >= 1 else "below_range"
            }
        }
        
        return EvaluationResult(
            overall_score=data['overall_score'],
            decision=data['decision'],
            confidence=data['confidence'],
            technical_soundness=data['scores']['technical_soundness'],
            novelty=data['scores']['novelty'],
            comprehensiveness=data['scores']['comprehensiveness'],
            reference_quality=data['scores']['reference_quality'],
            structure_quality=data['scores']['structure_quality'],
            writing_quality=data['scores']['writing_quality'],
            metrics_comparison=metrics_comparison,
            strengths=data['strengths'],
            weaknesses=data['weaknesses'],
            recommendations=data['recommendations'],
            desk_rejection_reasons=data.get('desk_rejection_reasons', [])
        )
    
    def _compare_to_benchmark(self, value: float, min_val: float, max_val: float) -> str:
        """Compare value to benchmark range"""
        if value < min_val:
            return "below_range"
        elif value > max_val:
            return "above_range"
        else:
            return "within_range"
    
    def analyze_article(
        self,
        file_path: str,
        file_type: str,
        llm_type: str = "claude"
    ) -> Tuple[ArticleMetrics, EvaluationResult]:
        """Complete analysis pipeline"""
        
        # Parse file
        article_text = self.parse_file(file_path, file_type)
        
        # Extract features
        metrics = self.extract_features(article_text)
        
        # Evaluate with LLM
        evaluation = self.evaluate_with_llm(article_text, metrics, llm_type)
        
        return metrics, evaluation
