#!/usr/bin/env python3
r"""
Analyze high-priority quality metrics across IEEE papers.

Metrics tracked:
1. Math density: $$, \begin{equation}, \[
2. Statistical keywords: p-value, confidence interval, significance, Cohen's d
3. Code availability: github.com, code available
4. Figure count: Figure, Fig.
5. Table count: Table, TABLE
6. Baseline comparisons: vs., compared to, outperforms
7. Datasets count: dataset, unique dataset names
8. Contributions list: contributions are:, bullet points in intro
9. Limitations section: limitation heading/keyword
10. Ablation: ablation
"""

import os
import re
import json
import csv
from pathlib import Path
from typing import Dict
from concurrent.futures import ProcessPoolExecutor, as_completed

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception:
        return ""

def count_math_density(text: str) -> Dict[str, int]:
    """Count math expressions - looking for equation numbers and mathematical symbols."""
    # Look for equation references like (1), (2), Eq. 1, Equation 1
    equation_refs = len(re.findall(r'\(\d+\)|\bEq\.?\s*\d+|\bEquation\s+\d+', text, re.IGNORECASE))
    
    # Greek letters commonly used in math
    greek_letters = len(re.findall(r'\b(alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|phi|psi|tau|rho)\b', text, re.IGNORECASE))
    
    # Mathematical symbols and operators
    math_symbols = len(re.findall(r'[∑∏∫∂∇≤≥≠≈±×÷√∞]|\b(sum|integral|derivative|gradient)\b', text, re.IGNORECASE))
    
    return {
        'equation_references': equation_refs,
        'greek_letters': greek_letters,
        'math_symbols': math_symbols,
        'total_math_indicators': equation_refs + greek_letters + math_symbols
    }

def count_statistical_keywords(text: str) -> Dict[str, int]:
    """Count statistical test keywords."""
    text_lower = text.lower()
    return {
        'p_value': len(re.findall(r'\bp[-\s]?value\b', text_lower)),
        'confidence_interval': len(re.findall(r'\bconfidence\s+interval\b', text_lower)),
        'significance': len(re.findall(r'\bsignificance\b|\bsignificant\b', text_lower)),
        'cohens_d': len(re.findall(r"\bcohen'?s?\s+d\b", text_lower)),
        'total_statistical': 0  # will be computed
    }

def detect_code_availability(text: str) -> Dict[str, any]:
    """Detect code availability mentions."""
    text_lower = text.lower()
    github_matches = re.findall(r'github\.com/[\w\-]+/[\w\-]+', text_lower)
    code_available = len(re.findall(r'\bcode\s+(is\s+)?(available|released|provided)', text_lower))
    
    return {
        'github_links': len(github_matches),
        'code_available_mentions': code_available,
        'has_code_link': len(github_matches) > 0 or code_available > 0
    }

def count_figures(text: str) -> Dict[str, int]:
    """Count figure references."""
    fig_pattern = re.findall(r'\b(Figure|Fig\.)\s+\d+', text, re.IGNORECASE)
    return {
        'figure_count': len(fig_pattern),
        'unique_figures': len(set([m.lower() for m in fig_pattern]))
    }

def count_tables(text: str) -> Dict[str, int]:
    """Count table references."""
    table_pattern = re.findall(r'\b(Table|TABLE)\s+\d+', text)
    return {
        'table_count': len(table_pattern),
        'unique_tables': len(set(table_pattern))
    }

def count_baseline_comparisons(text: str) -> Dict[str, int]:
    """Count baseline comparison keywords."""
    text_lower = text.lower()
    return {
        'vs_mentions': len(re.findall(r'\bvs\.?\b', text_lower)),
        'compared_to': len(re.findall(r'\bcompared\s+to\b', text_lower)),
        'outperforms': len(re.findall(r'\boutperform(s|ed|ing)?\b', text_lower)),
        'total_comparisons': 0  # will be computed
    }

def count_datasets(text: str) -> Dict[str, any]:
    """Count dataset mentions."""
    text_lower = text.lower()
    dataset_mentions = len(re.findall(r'\bdataset(s)?\b', text_lower))
    
    # Common dataset names
    common_datasets = [
        'imagenet', 'coco', 'mnist', 'cifar', 'pascal voc', 'cityscapes',
        'kitti', 'ade20k', 'places', 'openimages', 'kinetics', 'ucf',
        'glue', 'squad', 'superglue', 'wikitext', 'bookcorpus'
    ]
    
    found_datasets = []
    for ds in common_datasets:
        if ds in text_lower:
            found_datasets.append(ds)
    
    return {
        'dataset_mentions': dataset_mentions,
        'unique_known_datasets': len(found_datasets),
        'known_datasets': found_datasets
    }

def detect_contributions_list(text: str) -> Dict[str, any]:
    """Detect explicit contributions list in introduction."""
    text_lower = text.lower()
    
    # Look for "contributions are:" or similar
    contrib_pattern = re.search(r'(our\s+)?contributions?\s+(are|include)', text_lower)
    has_contrib_statement = contrib_pattern is not None
    
    # Count bullet points in first 3000 chars (intro section)
    intro_section = text[:3000]
    bullet_points = len(re.findall(r'^\s*[•\-\*]\s+', intro_section, re.MULTILINE))
    
    return {
        'has_contributions_statement': has_contrib_statement,
        'bullet_points_in_intro': bullet_points
    }

def detect_limitations_section(text: str) -> Dict[str, any]:
    """Detect limitations section or discussion."""
    text_lower = text.lower()
    
    # Look for section headers with "limitation"
    limitation_header = re.search(r'^#+\s*limitations?', text_lower, re.MULTILINE)
    limitation_mentions = len(re.findall(r'\blimitation(s)?\b', text_lower))
    
    return {
        'has_limitations_section': limitation_header is not None,
        'limitation_mentions': limitation_mentions
    }

def count_ablation(text: str) -> Dict[str, int]:
    """Count ablation study mentions."""
    text_lower = text.lower()
    return {
        'ablation_mentions': len(re.findall(r'\bablation\b', text_lower)),
        'ablation_study': len(re.findall(r'\bablation\s+study\b', text_lower))
    }

def count_multiple_runs(text: str) -> Dict[str, int]:
    """Count mentions of multiple experimental runs."""
    text_lower = text.lower()
    return {
        'runs_mentions': len(re.findall(r'\bruns?\b', text_lower)),
        'seeds_mentions': len(re.findall(r'\bseeds?\b', text_lower)),
        'averaged_over': len(re.findall(r'\baveraged\s+over\b', text_lower)),
        'total_reproducibility_indicators': 0  # computed later
    }

def count_error_reporting(text: str) -> Dict[str, int]:
    """Count error reporting and uncertainty quantification."""
    std_mentions = len(re.findall(r'\bstd\b|\bstandard\s+deviation\b', text, re.IGNORECASE))
    plus_minus = len(re.findall(r'±|\+/-|\+/−', text))
    error_bars = len(re.findall(r'\berror\s+bars?\b', text, re.IGNORECASE))
    variance = len(re.findall(r'\bvariance\b', text, re.IGNORECASE))
    
    return {
        'std_mentions': std_mentions,
        'plus_minus_symbols': plus_minus,
        'error_bars': error_bars,
        'variance_mentions': variance,
        'total_error_reporting': std_mentions + plus_minus + error_bars + variance
    }

def calculate_readability(text: str) -> Dict[str, float]:
    """Calculate Flesch-Kincaid readability scores."""
    import re
    
    # Count sentences (approximate)
    sentences = len(re.findall(r'[.!?]+', text))
    if sentences == 0:
        sentences = 1
    
    # Count words
    words = len(text.split())
    if words == 0:
        return {'flesch_reading_ease': 0.0, 'flesch_kincaid_grade': 0.0}
    
    # Count syllables (approximate - count vowel groups)
    syllables = len(re.findall(r'[aeiouy]+', text.lower()))
    
    # Flesch Reading Ease: 206.835 - 1.015(words/sentences) - 84.6(syllables/words)
    avg_words_per_sentence = words / sentences
    avg_syllables_per_word = syllables / words if words > 0 else 0
    
    flesch_reading_ease = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    flesch_kincaid_grade = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59
    
    return {
        'flesch_reading_ease': round(flesch_reading_ease, 2),
        'flesch_kincaid_grade': round(flesch_kincaid_grade, 2)
    }

def count_overclaiming(text: str) -> Dict[str, int]:
    """Count overclaiming and hype language."""
    text_lower = text.lower()
    
    return {
        'state_of_the_art': len(re.findall(r'\bstate-of-the-art\b|\bstate\s+of\s+the\s+art\b|\bSOTA\b', text_lower)),
        'revolutionary': len(re.findall(r'\brevolutionary\b|\bbreakthrough\b|\bgroundbreaking\b', text_lower)),
        'significant_improvement': len(re.findall(r'\bsignificant(ly)?\s+(improve|better|enhance|increase)', text_lower)),
        'novel': len(re.findall(r'\bnovel\b', text_lower)),
        'total_hype_words': 0  # computed later
    }

def count_performance_metrics(text: str) -> Dict[str, any]:
    """Count mentions of performance metrics."""
    text_lower = text.lower()
    
    # Common ML/AI metrics
    metrics = [
        'accuracy', 'precision', 'recall', 'f1', 'f-score',
        'auc', 'roc', 'rmse', 'mse', 'mae', 'r2', 'r-squared',
        'iou', 'map', 'bleu', 'rouge', 'perplexity',
        'loss', 'error rate', 'top-1', 'top-5'
    ]
    
    found_metrics = []
    metric_counts = {}
    
    for metric in metrics:
        pattern = r'\b' + re.escape(metric) + r'\b'
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            found_metrics.append(metric)
            metric_counts[metric] = count
    
    return {
        'unique_metrics_count': len(found_metrics),
        'total_metric_mentions': sum(metric_counts.values()),
        'metrics_found': found_metrics
    }

def analyze_paper(pdf_path: str) -> Dict:
    """Analyze a single paper for all quality metrics."""
    paper_id = os.path.basename(pdf_path)
    
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text or len(text.strip()) == 0:
            return {
                'paper_id': paper_id,
                'error': 'Failed to extract text or empty text',
                'ok': False
            }
        
        # Compute all metrics
        math = count_math_density(text)
        stats = count_statistical_keywords(text)
        stats['total_statistical'] = sum([stats['p_value'], stats['confidence_interval'], 
                                          stats['significance'], stats['cohens_d']])
        
        code = detect_code_availability(text)
        figures = count_figures(text)
        tables = count_tables(text)
        
        comparisons = count_baseline_comparisons(text)
        comparisons['total_comparisons'] = sum([comparisons['vs_mentions'], 
                                                comparisons['compared_to'], 
                                                comparisons['outperforms']])
        
        datasets = count_datasets(text)
        contributions = detect_contributions_list(text)
        limitations = detect_limitations_section(text)
        ablation = count_ablation(text)
        
        # New metrics
        multiple_runs = count_multiple_runs(text)
        multiple_runs['total_reproducibility_indicators'] = sum([
            multiple_runs['runs_mentions'],
            multiple_runs['seeds_mentions'],
            multiple_runs['averaged_over']
        ])
        
        error_reporting = count_error_reporting(text)
        readability = calculate_readability(text)
        
        overclaiming = count_overclaiming(text)
        overclaiming['total_hype_words'] = sum([
            overclaiming['state_of_the_art'],
            overclaiming['revolutionary'],
            overclaiming['significant_improvement'],
            overclaiming['novel']
        ])
        
        performance_metrics = count_performance_metrics(text)
        
        result = {
            'paper_id': paper_id,
            'ok': True,
            'word_count': len(text.split()),
            
            # Math density
            **{f'math_{k}': v for k, v in math.items()},
            
            # Statistical keywords
            **{f'stat_{k}': v for k, v in stats.items()},
            
            # Code availability
            **{f'code_{k}': v for k, v in code.items()},
            
            # Figures and tables
            **{f'fig_{k}': v for k, v in figures.items()},
            **{f'table_{k}': v for k, v in tables.items()},
            
            # Comparisons
            **{f'comp_{k}': v for k, v in comparisons.items()},
            
            # Datasets
            **{f'dataset_{k}': v for k, v in datasets.items()},
            
            # Contributions
            **{f'contrib_{k}': v for k, v in contributions.items()},
            
            # Limitations
            **{f'limit_{k}': v for k, v in limitations.items()},
            
            # Ablation
            **{f'ablation_{k}': v for k, v in ablation.items()},
            
            # Multiple runs
            **{f'runs_{k}': v for k, v in multiple_runs.items()},
            
            # Error reporting
            **{f'error_{k}': v for k, v in error_reporting.items()},
            
            # Readability
            **{f'readability_{k}': v for k, v in readability.items()},
            
            # Overclaiming
            **{f'hype_{k}': v for k, v in overclaiming.items()},
            
            # Performance metrics
            **{f'metrics_{k}': v for k, v in performance_metrics.items()},
        }
        
        return result
        
    except Exception as e:
        return {
            'paper_id': paper_id,
            'error': str(e),
            'ok': False
        }

def main():
    import sys
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Check if we should use full collection or test set
    use_full_collection = len(sys.argv) > 1 and sys.argv[1] == "--full"
    
    if use_full_collection:
        print("Querying Qdrant collection: academic_papers_full_specter2")
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        collection_name = "academic_papers_full_specter2"
        
        # Get all points from collection using scroll with pagination
        pdf_files = []
        offset = None
        batch_size = 1000
        
        while True:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = scroll_result
            
            for point in points:
                if point.payload and 'filename' in point.payload:
                    filename = point.payload['filename']
                    if filename.endswith('.pdf'):
                        # Try both downloaded_pdfs and test_pdfs locations
                        pdf_path = base_dir / "downloaded_pdfs" / filename
                        if pdf_path.exists() and pdf_path not in pdf_files:
                            pdf_files.append(pdf_path)
            
            if next_offset is None:
                break
            offset = next_offset
        
        print(f"Found {len(pdf_files)} PDF files from Qdrant collection")
    else:
        # Use test set
        pdf_dir = base_dir / "test_pdfs_100"
        pdf_files = sorted(list(pdf_dir.glob("*.pdf")))
        print(f"Found {len(pdf_files)} PDF files to analyze (test set)")
    
    if not pdf_files:
        print("No PDF files found. Exiting.")
        return
    
    # Process papers in parallel
    results = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(analyze_paper, str(pdf)): pdf for pdf in pdf_files}
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 100 == 0 or (completed % 10 == 0 and len(futures) <= 100):
                print(f"Progress: {completed}/{len(futures)} papers analyzed ({100*completed/len(futures):.1f}%)")
    
    # Filter successful results
    successful = [r for r in results if r.get('ok', False)]
    failed = [r for r in results if not r.get('ok', False)]
    
    print(f"\nProcessed: {len(successful)} successful, {len(failed)} failed")
    
    # Debug: show first few errors
    if failed and len(failed) > 0:
        print("\nFirst 3 errors:")
        for r in failed[:3]:
            print(f"  {r.get('paper_id')}: {r.get('error', 'Unknown error')}")
    
    # Save detailed CSV
    csv_filename = "quality_metrics_detailed_full.csv" if use_full_collection else "quality_metrics_detailed.csv"
    csv_path = output_dir / csv_filename
    if successful:
        fieldnames = list(successful[0].keys())
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(successful)
        print(f"Saved detailed results to {csv_path}")
    
    # Compute summary statistics
    if successful:
        summary = {
            'total_papers_analyzed': len(successful),
            'total_papers_failed': len(failed),
            
            'math_density': {
                'papers_with_math': sum(1 for r in successful if r.get('math_total_math_indicators', 0) > 0),
                'avg_math_indicators': sum(r.get('math_total_math_indicators', 0) for r in successful) / len(successful),
            },
            
            'statistical_tests': {
                'papers_with_stats': sum(1 for r in successful if r.get('stat_total_statistical', 0) > 0),
                'avg_stat_keywords': sum(r.get('stat_total_statistical', 0) for r in successful) / len(successful),
                'papers_with_pvalue': sum(1 for r in successful if r.get('stat_p_value', 0) > 0),
            },
            
            'code_availability': {
                'papers_with_code': sum(1 for r in successful if r.get('code_has_code_link', False)),
                'papers_with_github': sum(1 for r in successful if r.get('code_github_links', 0) > 0),
            },
            
            'figures_tables': {
                'avg_figures': sum(r.get('fig_figure_count', 0) for r in successful) / len(successful),
                'avg_tables': sum(r.get('table_table_count', 0) for r in successful) / len(successful),
            },
            
            'comparisons': {
                'papers_with_comparisons': sum(1 for r in successful if r.get('comp_total_comparisons', 0) > 0),
                'avg_comparisons': sum(r.get('comp_total_comparisons', 0) for r in successful) / len(successful),
            },
            
            'datasets': {
                'avg_dataset_mentions': sum(r.get('dataset_dataset_mentions', 0) for r in successful) / len(successful),
                'papers_with_known_datasets': sum(1 for r in successful if r.get('dataset_unique_known_datasets', 0) > 0),
            },
            
            'contributions': {
                'papers_with_contrib_statement': sum(1 for r in successful if r.get('contrib_has_contributions_statement', False)),
                'avg_bullet_points_intro': sum(r.get('contrib_bullet_points_in_intro', 0) for r in successful) / len(successful),
            },
            
            'limitations': {
                'papers_with_limitations_section': sum(1 for r in successful if r.get('limit_has_limitations_section', False)),
                'papers_mentioning_limitations': sum(1 for r in successful if r.get('limit_limitation_mentions', 0) > 0),
            },
            
            'ablation': {
                'papers_with_ablation': sum(1 for r in successful if r.get('ablation_ablation_mentions', 0) > 0),
                'avg_ablation_mentions': sum(r.get('ablation_ablation_mentions', 0) for r in successful) / len(successful),
            },
            
            'multiple_runs': {
                'papers_with_runs': sum(1 for r in successful if r.get('runs_total_reproducibility_indicators', 0) > 0),
                'avg_reproducibility_indicators': sum(r.get('runs_total_reproducibility_indicators', 0) for r in successful) / len(successful),
                'papers_with_seeds': sum(1 for r in successful if r.get('runs_seeds_mentions', 0) > 0),
            },
            
            'error_reporting': {
                'papers_with_error_reporting': sum(1 for r in successful if r.get('error_total_error_reporting', 0) > 0),
                'avg_error_indicators': sum(r.get('error_total_error_reporting', 0) for r in successful) / len(successful),
                'papers_with_std': sum(1 for r in successful if r.get('error_std_mentions', 0) > 0),
                'papers_with_plus_minus': sum(1 for r in successful if r.get('error_plus_minus_symbols', 0) > 0),
            },
            
            'readability': {
                'avg_flesch_reading_ease': sum(r.get('readability_flesch_reading_ease', 0) for r in successful) / len(successful),
                'avg_flesch_kincaid_grade': sum(r.get('readability_flesch_kincaid_grade', 0) for r in successful) / len(successful),
            },
            
            'overclaiming': {
                'papers_with_hype': sum(1 for r in successful if r.get('hype_total_hype_words', 0) > 0),
                'avg_hype_words': sum(r.get('hype_total_hype_words', 0) for r in successful) / len(successful),
                'papers_with_sota': sum(1 for r in successful if r.get('hype_state_of_the_art', 0) > 0),
                'papers_with_novel': sum(1 for r in successful if r.get('hype_novel', 0) > 0),
            },
            
            'performance_metrics': {
                'avg_unique_metrics': sum(r.get('metrics_unique_metrics_count', 0) for r in successful) / len(successful),
                'avg_total_metric_mentions': sum(r.get('metrics_total_metric_mentions', 0) for r in successful) / len(successful),
            }
        }
        
        # Save summary JSON
        summary_filename = "quality_metrics_summary_full.json" if use_full_collection else "quality_metrics_summary.json"
        summary_path = output_dir / summary_filename
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved summary to {summary_path}")
        
        # Print key findings
        print("\n" + "="*60)
        print("KEY FINDINGS")
        print("="*60)
        print(f"Papers with math: {summary['math_density']['papers_with_math']}/{len(successful)} ({100*summary['math_density']['papers_with_math']/len(successful):.1f}%)")
        print(f"Papers with statistical tests: {summary['statistical_tests']['papers_with_stats']}/{len(successful)} ({100*summary['statistical_tests']['papers_with_stats']/len(successful):.1f}%)")
        print(f"Papers with code links: {summary['code_availability']['papers_with_code']}/{len(successful)} ({100*summary['code_availability']['papers_with_code']/len(successful):.1f}%)")
        print(f"Papers with contributions statement: {summary['contributions']['papers_with_contrib_statement']}/{len(successful)} ({100*summary['contributions']['papers_with_contrib_statement']/len(successful):.1f}%)")
        print(f"Papers with limitations section: {summary['limitations']['papers_with_limitations_section']}/{len(successful)} ({100*summary['limitations']['papers_with_limitations_section']/len(successful):.1f}%)")
        print(f"Papers with ablation studies: {summary['ablation']['papers_with_ablation']}/{len(successful)} ({100*summary['ablation']['papers_with_ablation']/len(successful):.1f}%)")
        print(f"Avg figures per paper: {summary['figures_tables']['avg_figures']:.1f}")
        print(f"Avg tables per paper: {summary['figures_tables']['avg_tables']:.1f}")
        print("\nNEW METRICS:")
        print(f"Papers with multiple runs/seeds: {summary['multiple_runs']['papers_with_runs']}/{len(successful)} ({100*summary['multiple_runs']['papers_with_runs']/len(successful):.1f}%)")
        print(f"Papers with error reporting: {summary['error_reporting']['papers_with_error_reporting']}/{len(successful)} ({100*summary['error_reporting']['papers_with_error_reporting']/len(successful):.1f}%)")
        print(f"Avg Flesch Reading Ease: {summary['readability']['avg_flesch_reading_ease']:.1f}")
        print(f"Papers with hype language: {summary['overclaiming']['papers_with_hype']}/{len(successful)} ({100*summary['overclaiming']['papers_with_hype']/len(successful):.1f}%)")
        print(f"Avg unique performance metrics: {summary['performance_metrics']['avg_unique_metrics']:.1f}")

if __name__ == "__main__":
    main()
