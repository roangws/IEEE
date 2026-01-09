#!/usr/bin/env python3
"""
Regenerate summary JSON from CSV with outlier filtering.
"""

import csv
import json
import statistics
from collections import Counter, defaultdict

# Outlier thresholds (conservative IEEE paper constraints)
MAX_REFS = 500
MAX_CITATIONS = 5000
MAX_WORDS = 50000
MIN_WORDS = 100
MAX_REFS_PER_1K = 50

def safe_stats(values):
    if not values:
        return {'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'std': 0}
    return {
        'min': min(values),
        'max': max(values),
        'mean': round(statistics.mean(values), 1),
        'median': round(statistics.median(values), 1),
        'std': round(statistics.stdev(values), 1) if len(values) > 1 else 0
    }

# Load and filter CSV
rows = []
with open('output/ieee_patterns_table.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            nr = int(float(row['num_references'] or 0))
            ic = int(float(row['in_text_citations'] or 0))
            wc = int(float(row['word_count_total'] or 0))
            aw = int(float(row.get('abstract_words', 0) or 0))
            ns = int(float(row.get('num_sections', 0) or 0))
            asl = float(row.get('avg_sentence_len', 0) or 0)
            apl = float(row.get('avg_paragraph_len', 0) or 0)
            rpk = float(row.get('refs_per_1k_words', 0) or 0)
            
            # Filter outliers
            if nr > MAX_REFS:
                nr = 0
            if ic > MAX_CITATIONS:
                ic = 0
            if wc > MAX_WORDS or wc < MIN_WORDS:
                continue
            if rpk > MAX_REFS_PER_1K:
                rpk = 0
                
            rows.append({
                'paper_id': row['paper_id'],
                'title': row.get('title', 'Unknown'),
                'year': row.get('year', 'Unknown'),
                'word_count_total': wc,
                'abstract_words': aw,
                'num_sections': ns,
                'section_list': (row.get('section_list') or '').split('|') if row.get('section_list') else [],
                'in_text_citations': ic,
                'num_references': nr,
                'refs_per_1k_words': rpk,
                'avg_sentence_len': asl,
                'avg_paragraph_len': apl,
            })
        except Exception:
            continue

print(f"Loaded {len(rows)} valid papers after outlier filtering")

# Extract metrics
word_counts = [r['word_count_total'] for r in rows]
abstract_lengths = [r['abstract_words'] for r in rows if r['abstract_words'] > 0]
ref_counts = [r['num_references'] for r in rows if r['num_references'] > 0]
citation_counts = [r['in_text_citations'] for r in rows if r['in_text_citations'] > 0]
section_counts = [r['num_sections'] for r in rows if r['num_sections'] > 0]
sentence_lens = [r['avg_sentence_len'] for r in rows if r['avg_sentence_len'] > 0]
para_lens = [r['avg_paragraph_len'] for r in rows if r['avg_paragraph_len'] > 0]
refs_per_1k = [r['refs_per_1k_words'] for r in rows if r['refs_per_1k_words'] > 0]

# Section sequence analysis
section_sequences = Counter()
for r in rows:
    normalized = []
    for s in r['section_list']:
        s_lower = s.lower()
        if 'abstract' in s_lower:
            normalized.append('Abstract')
        elif 'keyword' in s_lower or 'index' in s_lower:
            normalized.append('Keywords')
        elif 'introduction' in s_lower:
            normalized.append('Introduction')
        elif 'related' in s_lower or 'background' in s_lower or 'literature' in s_lower:
            normalized.append('Related Work')
        elif 'method' in s_lower or 'approach' in s_lower or 'proposed' in s_lower:
            normalized.append('Methodology')
        elif 'experiment' in s_lower or 'evaluation' in s_lower:
            normalized.append('Experiments')
        elif 'result' in s_lower:
            normalized.append('Results')
        elif 'discussion' in s_lower:
            normalized.append('Discussion')
        elif 'conclusion' in s_lower or 'summary' in s_lower:
            normalized.append('Conclusion')
        elif 'future' in s_lower:
            normalized.append('Future Work')
        elif 'acknowledgment' in s_lower or 'acknowledgement' in s_lower:
            normalized.append('Acknowledgment')
        elif 'reference' in s_lower or 'bibliography' in s_lower:
            normalized.append('References')
    
    if normalized:
        section_sequences[' → '.join(normalized)] += 1

# Build summary
summary = {
    'corpus_stats': {
        'papers_analyzed': len(rows),
        'sampling_rule': 'Full corpus (all papers in Qdrant)',
        'sampling_method': 'Complete enumeration with 8-worker parallel extraction',
        'outlier_filtering': f'Applied: refs<={MAX_REFS}, citations<={MAX_CITATIONS}, words {MIN_WORDS}-{MAX_WORDS}'
    },
    'distributions': {
        'word_count': safe_stats(word_counts),
        'abstract_length': safe_stats(abstract_lengths),
        'num_references': safe_stats(ref_counts),
        'in_text_citations': safe_stats(citation_counts),
        'refs_per_1k_words': safe_stats(refs_per_1k),
        'num_sections': safe_stats(section_counts),
        'avg_sentence_length': safe_stats(sentence_lens),
        'avg_paragraph_length': safe_stats(para_lens),
    },
    'common_section_templates': [
        {'template': t, 'frequency': c}
        for t, c in section_sequences.most_common(10)
    ],
    'recommended_constraints': {
        'abstract_words': {
            'min': 80,
            'target': int(safe_stats(abstract_lengths)['mean']),
            'max': 250
        },
        'total_words': {
            'min': max(3000, int(safe_stats(word_counts)['mean'] * 0.5)),
            'target': int(safe_stats(word_counts)['mean']),
            'max': int(safe_stats(word_counts)['mean'] * 1.8)
        },
        'num_references': {
            'min': max(15, int(safe_stats(ref_counts)['mean'] * 0.4)),
            'target': int(safe_stats(ref_counts)['mean']),
            'max': int(safe_stats(ref_counts)['p95']) if 'p95' in safe_stats(ref_counts) else 150
        },
        'refs_per_1k_words': {
            'min': max(3, round(safe_stats(refs_per_1k)['mean'] * 0.5, 1)),
            'target': round(safe_stats(refs_per_1k)['mean'], 1),
            'max': round(safe_stats(refs_per_1k)['mean'] * 2, 1)
        },
        'in_text_citations': {
            'min': max(50, int(safe_stats(citation_counts)['mean'] * 0.5)),
            'target': int(safe_stats(citation_counts)['mean']),
            'max': int(safe_stats(citation_counts)['mean'] * 2)
        },
        'num_sections': {
            'min': 5,
            'target': int(safe_stats(section_counts)['median']),
            'max': 12
        }
    }
}

# Write summary
with open('output/ieee_patterns_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("Wrote: output/ieee_patterns_summary.json")

# Print key findings
print("\n" + "=" * 60)
print("FULL CORPUS ANALYSIS - KEY FINDINGS")
print("=" * 60)
print(f"\nPapers analyzed: {len(rows):,}")
print(f"\nWord Count: {safe_stats(word_counts)['mean']:.0f} avg (range: {safe_stats(word_counts)['min']}-{safe_stats(word_counts)['max']})")
print(f"  - Median: {safe_stats(word_counts)['median']:.0f}")
print(f"  - 90th percentile: {sorted(word_counts)[int(0.9*len(word_counts))]}")
print(f"\nAbstract Length: {safe_stats(abstract_lengths)['mean']:.0f} words avg")
print(f"  - Median: {safe_stats(abstract_lengths)['median']:.0f}")
print(f"\nReferences: {safe_stats(ref_counts)['mean']:.0f} avg")
print(f"  - Median: {safe_stats(ref_counts)['median']:.0f}")
print(f"  - 90th percentile: {sorted(ref_counts)[int(0.9*len(ref_counts))]}")
print(f"\nIn-text Citations: {safe_stats(citation_counts)['mean']:.0f} avg")
print(f"  - Median: {safe_stats(citation_counts)['median']:.0f}")
print(f"  - 90th percentile: {sorted(citation_counts)[int(0.9*len(citation_counts))]}")
print(f"\nRefs per 1k words: {safe_stats(refs_per_1k)['mean']:.1f} avg")
print(f"  - Median: {safe_stats(refs_per_1k)['median']:.1f}")
print(f"\nSections: {safe_stats(section_counts)['mean']:.0f} avg")
print(f"  - Median: {safe_stats(section_counts)['median']:.0f}")
print(f"\nAvg Sentence Length: {safe_stats(sentence_lens)['mean']:.1f} words")
print(f"\nTop 5 Section Templates:")
for i, (template, count) in enumerate(section_sequences.most_common(5)):
    print(f"  {i+1}. {template}")
    print(f"     ({count} papers, {count/len(rows)*100:.1f}%)")
