#!/usr/bin/env python3
"""
Citation Manager
Manages citations to ensure only sources used in article appear in references.
"""

import re
from citation_formatter import CitationFormatter


class CitationManager:
    """Manages article citations and references."""
    
    def __init__(self, metadata_file="pdf_metadata.json"):
        """Initialize citation manager."""
        self.formatter = CitationFormatter(metadata_file)
        self.metadata_file = metadata_file
    
    def extract_title(self, article_text):
        """
        Extract the title from the article.
        
        Args:
            article_text: The generated article text
            
        Returns:
            Tuple of (title, article_without_title)
        """
        if not article_text:
            return "Research Article", article_text
        
        lines = article_text.split('\n')
        
        # Look for title in first few non-empty lines
        for i, line in enumerate(lines[:10]):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if it's a markdown title (# Title)
            if stripped.startswith('# '):
                title = stripped[2:].strip()
                # Remove title line from article
                remaining_lines = lines[:i] + lines[i+1:]
                return title, '\n'.join(remaining_lines)
            
            # Check if it's a bold title (**Title**)
            bold_match = re.match(r'^\*\*(.+?)\*\*$', stripped)
            if bold_match and len(bold_match.group(1)) > 10:
                title = bold_match.group(1)
                remaining_lines = lines[:i] + lines[i+1:]
                return title, '\n'.join(remaining_lines)
        
        # No explicit title found, use first non-empty line if it looks like a title
        for i, line in enumerate(lines[:5]):
            stripped = line.strip()
            if stripped and len(stripped) > 10 and len(stripped) < 200:
                # Use first substantive line as title
                remaining_lines = lines[i+1:]
                return stripped, '\n'.join(remaining_lines)
        
        return "Research Article", article_text
    
    def extract_citations_from_article(self, article_text):
        """
        Extract all citation numbers used in the article.
        
        Args:
            article_text: The generated article text
            
        Returns:
            Set of citation numbers found in article
        """
        if not article_text:
            return set()

        citation_numbers: set[int] = set()

        # 1) Simple citations like [1], [23]
        citations = re.findall(r"\[(\d+)\]", article_text)
        citation_numbers.update(int(c) for c in citations)

        # 2) Multiple citations in one bracket like [2, 3, 4] or [5, 6]
        multi_citations = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", article_text)
        for citation_group in multi_citations:
            # Split by comma and clean up
            nums = [int(n.strip()) for n in citation_group.split(',')]
            citation_numbers.update(nums)

        # 3) Ranges like [1]-[5] or [1]–[5]
        range_matches = re.findall(r"\[(\d+)\]\s*(?:-|–|—)\s*\[(\d+)\]", article_text)
        for start_s, end_s in range_matches:
            start = int(start_s)
            end = int(end_s)
            if start <= end:
                citation_numbers.update(range(start, end + 1))
            else:
                citation_numbers.update([start, end])

        # 4) Compact ranges like [1-5] or [1–5]
        compact_range_matches = re.findall(r"\[(\d+)\s*(?:-|–|—)\s*(\d+)\]", article_text)
        for start_s, end_s in compact_range_matches:
            start = int(start_s)
            end = int(end_s)
            if start <= end:
                citation_numbers.update(range(start, end + 1))
            else:
                citation_numbers.update([start, end])

        return citation_numbers
    
    def build_reference_list_from_citations(self, article_text, citation_map, external_refs=None):
        """
        Build reference list containing ONLY sources cited in article.
        
        Args:
            article_text: The generated article text
            citation_map: Mapping of filenames to citation numbers
            external_refs: Optional list of ExternalReference objects from web search
            
        Returns:
            Formatted reference list with only cited sources
        """
        # Extract citation numbers from article
        cited_numbers = self.extract_citations_from_article(article_text)
        
        if not cited_numbers:
            return "\n## References\n\nNo citations found in article.\n"
        
        # Reverse the citation map to get filename from number
        number_to_filename = {num: filename for filename, num in citation_map.items()}
        
        # Build external refs lookup
        external_lookup = {}
        if external_refs:
            for ref in external_refs:
                external_lookup[ref.citation_number] = ref
        
        # Build reference list for cited sources only
        references = []
        references.append("\n## References\n")
        
        orphaned = []
        for num in sorted(cited_numbers):
            if num in number_to_filename:
                filename = number_to_filename[num]
                ref = self.formatter.format_reference(filename, num)
                references.append(f"{ref}\n")
            elif num in external_lookup:
                # Add external reference from web search
                ref = external_lookup[num].to_ieee_format()
                references.append(f"{ref}\n")
            else:
                # Track orphaned citations
                orphaned.append(num)
                # Add placeholder reference
                references.append(f"[{num}] **MISSING REFERENCE** - Citation used in text but no source mapping found.\n")
        
        return "\n".join(references)
    
    def validate_and_fix_article(self, article_text, citation_map, sources_list):
        """
        Validate article citations and fix reference section.
        
        Args:
            article_text: Generated article
            citation_map: Citation mapping
            sources_list: List of source dictionaries
            
        Returns:
            Tuple of (fixed_article, citation_stats)
        """
        # Remove LLM-generated notes about citations (IEEE doesn't have these)
        article_text = self._remove_citation_notes(article_text)
        
        # Extract citations from article
        cited_numbers = self.extract_citations_from_article(article_text)
        
        # CRITICAL VALIDATION: Check for orphaned citations
        mapped_numbers = set(citation_map.values())
        orphaned_citations = cited_numbers - mapped_numbers
        
        # Calculate word count and citation density
        word_count = len(article_text.split())
        refs_per_1k = (len(citation_map) / word_count * 1000) if word_count > 0 else 0
        
        # Statistics with IEEE standards validation (from 5,671 paper corpus)
        stats = {
            'total_sources_provided': len(sources_list),
            'unique_papers_provided': len(citation_map),
            'citations_in_article': len(cited_numbers),
            'cited_papers': len(cited_numbers),
            'orphaned_citations': sorted(orphaned_citations),
            'has_orphaned': len(orphaned_citations) > 0,
            'completeness_percent': (len(cited_numbers - orphaned_citations) / len(cited_numbers) * 100) if cited_numbers else 100,
            'word_count': word_count,
            'refs_per_1k_words': round(refs_per_1k, 1),
            # IEEE standards validation (full corpus: mean=47 refs, 7.1 refs/1k, 135 citations)
            'meets_min_references': len(citation_map) >= 19,  # Full corpus minimum
            'meets_min_citations': len(cited_numbers) >= 68,  # Full corpus 50th percentile
            'meets_min_density': refs_per_1k >= 3.5,  # Full corpus minimum density
            'ieee_compliant': len(citation_map) >= 19 and len(cited_numbers) >= 68 and refs_per_1k >= 3.5
        }
        
        # AGGRESSIVELY remove ALL LLM-generated References sections
        # This is critical because LLMs often ignore instructions and generate references anyway
        
        # Method 1: Split by "## References" header (case insensitive)
        parts = re.split(r'\n##\s*References?\s*\n', article_text, flags=re.IGNORECASE)
        article_body = parts[0] if parts else article_text
        
        # Method 2: Also try to catch references that start with "# References" (single hash)
        parts = re.split(r'\n#\s*References?\s*\n', article_body, flags=re.IGNORECASE)
        article_body = parts[0] if parts else article_body
        
        # Method 3: Split by "References" as a standalone line
        parts = re.split(r'\n\*\*References\*\*\s*\n', article_body, flags=re.IGNORECASE)
        article_body = parts[0] if parts else article_body
        
        # Method 4: Remove any section that looks like a bibliography at the end
        # Pattern: Lines starting with [1], [2], etc. followed by author names/titles
        lines = article_body.split('\n')
        cleaned_lines = []
        in_fake_references = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect start of fake reference section - multiple patterns
            is_ref_entry = False
            
            # Pattern 1: [1] Author et al. ...
            if re.match(r'^\[\d+\]\s+[A-Z]', stripped):
                if any(pattern in line for pattern in [' et al.', ', "', '", ', '(20', '(19', 'IEEE', 'Journal', 'Conference', 'Proceedings']):
                    is_ref_entry = True
            
            # Pattern 2: [1] "Title of paper"
            if re.match(r'^\[\d+\]\s*"', stripped):
                is_ref_entry = True
            
            # Pattern 3: 1. Author, "Title"
            if re.match(r'^\d+\.\s+[A-Z][a-z]+,?\s+[A-Z]', stripped):
                if any(pattern in line for pattern in [' et al.', ', "', '", ']):
                    is_ref_entry = True
            
            if is_ref_entry:
                in_fake_references = True
                continue
            
            # If we're in fake references, skip until we hit a real section or end
            if in_fake_references:
                # Check if we hit a new section header (would indicate end of fake refs)
                if re.match(r'^#{1,3}\s+', stripped):
                    in_fake_references = False
                elif stripped and not re.match(r'^\[\d+\]', stripped) and not re.match(r'^\d+\.', stripped):
                    # Non-reference line, might be end of fake refs
                    if len(stripped) > 50 and not any(p in stripped for p in ['et al.', 'IEEE', 'Journal']):
                        in_fake_references = False
                else:
                    continue
            
            cleaned_lines.append(line)
        
        article_body = '\n'.join(cleaned_lines).strip()
        
        # Final cleanup: Remove any trailing reference-like content after Conclusion
        conclusion_match = re.search(r'(##\s*Conclusion.*?)(\n##\s*References|\n\*\*References|\n\[\d+\]\s+[A-Z])', article_body, re.IGNORECASE | re.DOTALL)
        if conclusion_match:
            # Find the conclusion section and truncate after it
            conclusion_end = article_body.lower().rfind('## conclusion')
            if conclusion_end != -1:
                # Find the end of the conclusion section (next ## or end)
                remaining = article_body[conclusion_end:]
                next_section = re.search(r'\n##\s+(?!Conclusion)', remaining, re.IGNORECASE)
                if next_section:
                    article_body = article_body[:conclusion_end + next_section.start()]
        
        # Build new reference list with only cited sources
        new_references = self.build_reference_list_from_citations(article_body, citation_map)
        
        # Combine
        fixed_article = article_body.strip() + "\n\n" + new_references
        
        return fixed_article, stats
    
    def _remove_citation_notes(self, text):
        """
        Remove LLM-generated notes about citations that don't belong in IEEE papers.
        
        Args:
            text: Article text
            
        Returns:
            Cleaned text
        """
        # Remove notes like "(Note: This article cites X sources...)"
        text = re.sub(r'\(Note:.*?cites.*?sources.*?\)', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove notes like "Note: This article cites..."
        text = re.sub(r'Note:.*?cites.*?sources.*?\.', '', text, flags=re.IGNORECASE)
        
        # Remove any standalone notes about citation counts
        text = re.sub(r'\(.*?\d+\s+sources.*?citations.*?\)', '', text, flags=re.IGNORECASE)
        
        # Remove duplicate reference sections (keep only the first one)
        # Find all reference section headers
        ref_headers = list(re.finditer(r'\n##\s*References\s*\n', text, re.IGNORECASE))
        if len(ref_headers) > 1:
            # Keep up to the second reference section (which removes the duplicate)
            second_ref_start = ref_headers[1].start()
            text = text[:second_ref_start]
        
        # Remove any malformed references (like random numbers or broken citations)
        # This catches references that don't follow IEEE format
        text = re.sub(r'\n\[\d+\]\s*\n(?=\[\d+\])', '', text)  # Remove empty references
        
        # Remove extra blank lines
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        return text
    
    def create_citation_report(self, article_text, citation_map, sources_list):
        """
        Create a report about citations in the article.
        
        Args:
            article_text: Generated article
            citation_map: Citation mapping
            sources_list: List of sources
            
        Returns:
            Report string
        """
        cited_numbers = self.extract_citations_from_article(article_text)
        number_to_filename = {num: filename for filename, num in citation_map.items()}
        
        report = []
        report.append("="*70)
        report.append("CITATION ANALYSIS REPORT")
        report.append("="*70)
        
        report.append("\n📊 Statistics:")
        report.append(f"  Sources provided to LLM: {len(sources_list)} chunks")
        report.append(f"  Unique papers provided: {len(citation_map)}")
        report.append(f"  Citations in article: {len(cited_numbers)}")
        report.append(f"  Utilization rate: {len(cited_numbers)/len(citation_map)*100:.1f}%")
        
        report.append(f"\n✅ Cited Papers ({len(cited_numbers)}):")
        for num in sorted(cited_numbers):
            if num in number_to_filename:
                filename = number_to_filename[num]
                info = self.formatter.get_source_info(filename)
                report.append(f"  [{num}] {info}")
        
        # Find uncited papers
        all_numbers = set(citation_map.values())
        uncited = all_numbers - cited_numbers
        
        if uncited:
            report.append(f"\n⚠️  Uncited Papers ({len(uncited)}):")
            for num in sorted(uncited):
                if num in number_to_filename:
                    filename = number_to_filename[num]
                    report.append(f"  [{num}] {filename}")
        
        report.append("="*70)
        
        return "\n".join(report)


def test_citation_manager():
    """Test the citation manager."""
    manager = CitationManager()
    
    # Sample article with citations
    sample_article = """
    # Machine Learning in Code Analysis
    
    ## Introduction
    Recent studies have shown improvements [1], [2]. Various approaches exist [3].
    
    ## Methods
    The methodology follows [1] and extends [5].
    
    ## References
    [1] Old reference
    [2] Old reference
    [3] Old reference
    [4] Old reference
    [5] Old reference
    """
    
    # Sample citation map
    citation_map = {
        'paper1.pdf': 1,
        'paper2.pdf': 2,
        'paper3.pdf': 3,
        'paper4.pdf': 4,
        'paper5.pdf': 5
    }
    
    sources_list = [{'filename': f'paper{i}.pdf'} for i in range(1, 6)]
    
    # Test extraction
    cited = manager.extract_citations_from_article(sample_article)
    print(f"Citations found: {sorted(cited)}")
    
    # Test validation
    fixed_article, stats = manager.validate_and_fix_article(sample_article, citation_map, sources_list)
    print(f"\nStats: {stats}")
    
    # Test report
    report = manager.create_citation_report(sample_article, citation_map, sources_list)
    print(f"\n{report}")


if __name__ == '__main__':
    test_citation_manager()
