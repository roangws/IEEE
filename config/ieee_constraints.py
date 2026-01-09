"""
IEEE Article Constraints - Full Corpus Analysis
Based on analysis of 5,671 IEEE papers from the complete dataset.
"""

# Derived from full corpus analysis of 5,671 IEEE papers
IEEE_CONSTRAINTS = {
    # Word counts (measured: mean=6551, median=6025, p90=9601)
    "total_words": {"min": 3000, "target": 6550, "max": 12000},
    "abstract_words": {"min": 80, "target": 118, "max": 250},
    
    # References (measured: mean=47, median=38, p90=79)
    "num_references": {"min": 19, "target": 47, "max": 113},
    "refs_per_1k_words": {"min": 3.5, "target": 7.1, "max": 14.0},
    "min_in_text_citations": 68,  # measured mean: 135, median: 106
    "target_in_text_citations": 135,
    
    # Sections (measured: mean=20, median=17, p90=29)
    "num_main_sections": {"min": 5, "target": 7, "max": 12},
    
    # Sentence/paragraph style (measured: mean=18.0)
    "avg_sentence_words": {"min": 15, "target": 18, "max": 22},
}

SECTION_WORD_BUDGETS = {
    # For 6550 word target (full corpus mean)
    "abstract": 130,
    "introduction": 785,
    "related_work": 1310,
    "methodology": 1640,
    "experiments": 980,
    "results": 980,
    "discussion": 525,
    "conclusion": 200,
}

SECTION_CITATION_BUDGETS = {
    "introduction": {"min": 8, "max": 12},
    "related_work": {"min": 20, "max": 30},  # Heaviest
    "methodology": {"min": 12, "max": 18},
    "experiments": {"min": 8, "max": 12},
    "results": {"min": 6, "max": 10},
    "discussion": {"min": 4, "max": 8},
    "conclusion": {"min": 0, "max": 2},
}

REQUIRED_SECTIONS = [
    "Abstract",
    "Introduction", 
    "Methodology",  # Or variant
    "Conclusion",
]

OPTIONAL_SECTIONS = [
    "Keywords",
    "Related Work",
    "Experiments",
    "Results",
    "Discussion",
    "Acknowledgment",
]

SECTION_NAME_VARIANTS = {
    "Related Work": ["Background", "Prior Work", "Literature Review"],
    "Methodology": ["Proposed Method", "Approach", "System Design", "Materials and Methods"],
    "Experiments": ["Experimental Setup", "Experimental Design", "Evaluation"],
    "Results": ["Experimental Results", "Results and Discussion", "Results and Analysis"],
}

# Quality tiers based on percentiles
QUALITY_TIERS = {
    "conservative": {  # 50th percentile (median)
        "total_words": 6025,
        "references": 38,
        "citations": 106,
        "abstract": 105,
    },
    "target": {  # Mean
        "total_words": 6551,
        "references": 47,
        "citations": 135,
        "abstract": 118,
    },
    "high_quality": {  # 90th percentile
        "total_words": 9601,
        "references": 79,
        "citations": 231,
        "abstract": 161,
    }
}
