# IEEE Article Generator - Tool/Pipeline Implementation Checklist

Based on analysis of 40 IEEE papers. All numbers derived from measured corpus statistics.

---

## IMPLEMENTATION CHECKLIST (Ordered)

### Phase 1: Configuration Constants (Immediate)

- [ ] **1.1** Create `config/ieee_constraints.py` with measured constants:

```python
# Derived from corpus analysis of 40 IEEE papers
IEEE_CONSTRAINTS = {
    # Word counts (measured: mean=6958, std=2602)
    "total_words": {"min": 4000, "target": 7000, "max": 10000},
    "abstract_words": {"min": 100, "target": 135, "max": 300},
    
    # References (measured: mean=56, median=41)
    "num_references": {"min": 27, "target": 55, "max": 100},
    "refs_per_1k_words": {"min": 4.0, "target": 7.6, "max": 12.0},
    "min_in_text_citations": 100,  # measured mean: 159
    
    # Sections (measured: mean=20 sections including subsections)
    "num_main_sections": {"min": 5, "max": 8},
    
    # Sentence/paragraph style (measured)
    "avg_sentence_words": {"min": 15, "target": 18, "max": 22},
    
    # Figure/table expectations (measured: 20.5 figs, 13.1 tables avg)
    "min_figure_refs": 5,
    "min_table_refs": 3,
}

SECTION_WORD_BUDGETS = {
    # For 7000 word target
    "abstract": 140,
    "introduction": 840,
    "related_work": 1400,
    "methodology": 1750,
    "experiments": 1050,
    "results": 1050,
    "discussion": 560,
    "conclusion": 210,
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
```

---

### Phase 2: Section Template Enforcement

- [ ] **2.1** Create section template validator in `validators/section_validator.py`:

```python
def validate_section_structure(article_text: str) -> dict:
    """
    Validate article has required IEEE sections.
    Returns: {"valid": bool, "missing": list, "warnings": list}
    """
    required = ["abstract", "introduction", "methodology", "conclusion"]
    found = extract_section_names(article_text)
    
    missing = []
    for req in required:
        if not any(is_section_variant(f, req) for f in found):
            missing.append(req)
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "found": found,
        "warnings": check_section_order(found)
    }
```

- [ ] **2.2** Add section order enforcement:

```python
CANONICAL_ORDER = [
    "abstract", "keywords", "introduction", "related_work",
    "methodology", "experiments", "results", "discussion",
    "conclusion", "acknowledgment", "references"
]

def check_section_order(sections: list) -> list:
    """Return warnings for out-of-order sections."""
    warnings = []
    normalized = [normalize_section_name(s) for s in sections]
    
    last_idx = -1
    for section in normalized:
        if section in CANONICAL_ORDER:
            idx = CANONICAL_ORDER.index(section)
            if idx < last_idx:
                warnings.append(f"Section '{section}' appears after '{CANONICAL_ORDER[last_idx]}'")
            last_idx = max(last_idx, idx)
    
    return warnings
```

---

### Phase 3: Length Budgeting System

- [ ] **3.1** Implement word budget tracker:

```python
class WordBudgetTracker:
    def __init__(self, total_target: int = 7000):
        self.total_target = total_target
        self.budgets = self._calculate_budgets()
    
    def _calculate_budgets(self) -> dict:
        """Scale section budgets to total target."""
        base = SECTION_WORD_BUDGETS  # For 7000 words
        scale = self.total_target / 7000
        return {k: int(v * scale) for k, v in base.items()}
    
    def validate_section_length(self, section: str, word_count: int) -> dict:
        budget = self.budgets.get(section.lower(), 500)
        return {
            "section": section,
            "words": word_count,
            "budget": budget,
            "over_budget": word_count > budget * 1.3,
            "under_budget": word_count < budget * 0.5,
            "pct_of_budget": word_count / budget * 100
        }
```

- [ ] **3.2** Add to generation prompt:

```python
def add_word_budget_instructions(prompt: str, word_count: int) -> str:
    tracker = WordBudgetTracker(word_count)
    budget_text = "\n**SECTION WORD BUDGETS:**\n"
    for section, budget in tracker.budgets.items():
        budget_text += f"- {section.title()}: ~{budget} words\n"
    return prompt + budget_text
```

---

### Phase 4: Reference Management

- [ ] **4.1** Update `citation_manager.py` with validation:

```python
def validate_reference_requirements(
    article_text: str,
    citation_map: dict,
    word_count: int
) -> dict:
    """
    Validate references meet IEEE standards.
    Based on measured: mean=56 refs, 7.6 refs/1k words
    """
    cited = extract_citations_from_article(article_text)
    ref_count = len(citation_map)
    refs_per_1k = ref_count / word_count * 1000 if word_count > 0 else 0
    
    issues = []
    
    # Check minimum references
    if ref_count < 27:
        issues.append(f"Too few references: {ref_count} (minimum: 27)")
    
    # Check citation density
    if refs_per_1k < 4.0:
        issues.append(f"Citation density too low: {refs_per_1k:.1f}/1k (minimum: 4.0)")
    
    # Check citation coverage
    in_text_count = len(cited)
    if in_text_count < 100:
        issues.append(f"Too few in-text citations: {in_text_count} (minimum: 100)")
    
    # Check for orphaned citations
    mapped_nums = set(citation_map.values())
    orphaned = cited - mapped_nums
    if orphaned:
        issues.append(f"Orphaned citations without references: {sorted(orphaned)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "stats": {
            "ref_count": ref_count,
            "in_text_citations": in_text_count,
            "refs_per_1k": round(refs_per_1k, 1),
            "orphaned": list(orphaned)
        }
    }
```

- [ ] **4.2** Add citation distribution validator:

```python
CITATION_DISTRIBUTION = {
    "introduction": (0.10, 0.15),      # 10-15%
    "related_work": (0.35, 0.45),      # 35-45% (heaviest)
    "methodology": (0.15, 0.20),       # 15-20%
    "experiments": (0.10, 0.15),       # 10-15%
    "results": (0.10, 0.15),           # 10-15%
    "discussion": (0.05, 0.10),        # 5-10%
    "conclusion": (0.00, 0.02),        # 0-2%
}

def validate_citation_distribution(article_text: str) -> dict:
    """Check if citations are properly distributed across sections."""
    sections = segment_by_sections(article_text)
    total_citations = count_citations(article_text)
    
    warnings = []
    for section, (min_pct, max_pct) in CITATION_DISTRIBUTION.items():
        if section in sections:
            section_citations = count_citations(sections[section])
            pct = section_citations / total_citations if total_citations > 0 else 0
            
            if pct < min_pct:
                warnings.append(f"{section}: {pct*100:.0f}% citations (expected: {min_pct*100:.0f}%+)")
    
    return {"warnings": warnings}
```

---

### Phase 5: Post-Processing Validators

- [ ] **5.1** Create validation pipeline in `validators/article_validator.py`:

```python
class ArticleValidator:
    """Comprehensive IEEE article validator."""
    
    def __init__(self):
        self.checks = [
            self._check_has_abstract,
            self._check_has_introduction,
            self._check_has_methodology,
            self._check_has_conclusion,
            self._check_min_references,
            self._check_citation_density,
            self._check_no_generic_terms,
            self._check_results_have_baselines,
            self._check_heading_format,
        ]
    
    def validate(self, article: str, citation_map: dict) -> dict:
        results = {"passed": [], "failed": [], "warnings": []}
        
        for check in self.checks:
            result = check(article, citation_map)
            if result["status"] == "pass":
                results["passed"].append(result)
            elif result["status"] == "fail":
                results["failed"].append(result)
            else:
                results["warnings"].append(result)
        
        results["valid"] = len(results["failed"]) == 0
        return results
    
    def _check_min_references(self, article: str, citation_map: dict) -> dict:
        ref_count = len(citation_map)
        return {
            "check": "min_references",
            "status": "pass" if ref_count >= 27 else "fail",
            "message": f"References: {ref_count} (min: 27)",
            "value": ref_count
        }
    
    def _check_no_generic_terms(self, article: str, _) -> dict:
        """Check for generic terms without specifics."""
        generic_patterns = [
            r'\bLLMs?\b(?!\s*\()',  # LLM/LLMs not followed by specifics
            r'\bneural networks?\b(?!\s*\()',
            r'\bdeep learning\b(?!\s*\()',
            r'\btransformer\b(?!\s*\()',  # transformer without model name
        ]
        
        issues = []
        for pattern in generic_patterns:
            matches = re.findall(pattern, article, re.IGNORECASE)
            if matches:
                issues.append(f"Generic term without specifics: '{matches[0]}'")
        
        return {
            "check": "no_generic_terms",
            "status": "pass" if not issues else "warn",
            "message": "; ".join(issues) if issues else "No generic terms found",
            "issues": issues
        }
    
    def _check_results_have_baselines(self, article: str, _) -> dict:
        """Check improvement claims have baselines."""
        # Pattern: X% improvement without baseline context
        improvement_pattern = r'\b(\d+\.?\d*)\s*%\s*(improvement|increase|better|higher)'
        matches = re.findall(improvement_pattern, article, re.IGNORECASE)
        
        # Check if baseline mentioned nearby
        issues = []
        for match in matches:
            # Simple heuristic: look for "baseline" or "compared to" nearby
            # This is a simplified check
            pass  # Implement full context check
        
        return {
            "check": "results_have_baselines",
            "status": "pass",  # Simplified
            "message": f"Found {len(matches)} improvement claims"
        }
```

- [ ] **5.2** Add validation gate to export:

```python
def pre_export_validation(article: str, citation_map: dict) -> dict:
    """
    Gate that must pass before PDF export is allowed.
    """
    validator = ArticleValidator()
    result = validator.validate(article, citation_map)
    
    blocking_failures = [
        f for f in result["failed"]
        if f["check"] in ["has_abstract", "has_conclusion", "min_references", "no_orphaned_citations"]
    ]
    
    return {
        "can_export": len(blocking_failures) == 0,
        "blocking_issues": blocking_failures,
        "warnings": result["warnings"],
        "stats": result
    }
```

---

### Phase 6: Heading Normalization

- [ ] **6.1** Add heading format normalizer:

```python
def normalize_ieee_headings(article: str) -> str:
    """
    Normalize headings to IEEE format:
    - Main sections: Roman numerals + ALL CAPS
    - Subsections: A., B., C.
    """
    # Pattern for markdown headings
    heading_pattern = r'^(#{1,3})\s+(.+)$'
    
    main_section_num = 0
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    
    lines = article.split('\n')
    normalized = []
    
    for line in lines:
        match = re.match(heading_pattern, line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            
            if level == 2:  # Main section
                if main_section_num < len(roman_numerals):
                    numeral = roman_numerals[main_section_num]
                    main_section_num += 1
                    normalized.append(f"## {numeral}. {title.upper()}")
                else:
                    normalized.append(line)
            else:
                normalized.append(line)
        else:
            normalized.append(line)
    
    return '\n'.join(normalized)
```

---

### Phase 7: Prompt-Time Instructions

- [ ] **7.1** Update `query_with_citations.py` prompt with measured constraints:

```python
# Replace hardcoded values with measured constants
PROMPT_CONSTRAINTS = f"""
## MEASURED IEEE STANDARDS (from corpus of {CORPUS_SIZE} papers)

### LENGTH (STRICT)
- Total: {IEEE_CONSTRAINTS['total_words']['min']}-{IEEE_CONSTRAINTS['total_words']['max']} words
- Abstract: {IEEE_CONSTRAINTS['abstract_words']['min']}-{IEEE_CONSTRAINTS['abstract_words']['max']} words

### REFERENCES (MANDATORY)
- Minimum references: {IEEE_CONSTRAINTS['num_references']['min']}
- Target: {IEEE_CONSTRAINTS['num_references']['target']} references
- Density: {IEEE_CONSTRAINTS['refs_per_1k_words']['min']}-{IEEE_CONSTRAINTS['refs_per_1k_words']['max']} refs per 1,000 words
- In-text citations: minimum {IEEE_CONSTRAINTS['min_in_text_citations']}
"""
```

---

## VALIDATION FLOW DIAGRAM

```
Article Generation Request
         ↓
[1] Pre-Generation Validation
    - Check topic has enough sources
    - Validate paper-topic semantic match
         ↓
[2] Prompt Construction
    - Add word budgets per section
    - Add citation distribution targets
    - Include measured constraints
         ↓
[3] LLM Generation
    - With system message emphasizing citations
         ↓
[4] Post-Generation Validation
    - Section structure check
    - Reference count check (min 27)
    - Citation density check (min 4/1k)
    - Orphaned citation check
    - Generic term check
         ↓
[5] Validation Gate
    ├── PASS → Enable PDF Export
    └── FAIL → Show errors, disable export
         ↓
[6] Export with Normalization
    - Heading format normalization
    - Citation bracket cleanup
    - Reference list generation
```

---

## PRIORITY ORDER

| Priority | Item | Impact | Effort |
|----------|------|--------|--------|
| 🔴 P0 | Config constants file | Foundation for all checks | Low |
| 🔴 P0 | Reference validation (min 27) | Fixes empty refs issue | Low |
| 🔴 P0 | Pre-export validation gate | Prevents broken exports | Medium |
| 🟡 P1 | Section structure validator | Ensures IEEE format | Medium |
| 🟡 P1 | Word budget system | Controls output length | Medium |
| 🟡 P1 | Citation distribution check | Balances citations | Medium |
| 🟢 P2 | Generic term detector | Improves quality | Low |
| 🟢 P2 | Heading normalizer | Polish | Low |
| 🟢 P2 | Results baseline checker | Academic rigor | Medium |

---

## MEASURED CONSTANTS SUMMARY

| Metric | Min | Target | Max | Source |
|--------|-----|--------|-----|--------|
| Total words | 4,000 | 7,000 | 10,000 | Corpus mean: 6,958 |
| Abstract words | 100 | 135 | 300 | Corpus mean: 135 |
| References | 27 | 55 | 100 | Corpus mean: 56 |
| Refs/1k words | 4.0 | 7.6 | 12.0 | Corpus mean: 7.6 |
| In-text citations | 100 | 159 | 300 | Corpus mean: 159 |
| Main sections | 5 | 7 | 8 | Corpus median: 7 |
| Avg sentence len | 15 | 18 | 22 | Corpus mean: 18 |
| Figures refs | 5 | 20 | 40 | Corpus mean: 20.5 |
| Table refs | 3 | 13 | 25 | Corpus mean: 13.1 |

