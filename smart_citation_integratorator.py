#!/usr/bin/env python3
"""
Smart Citation Integrator
Intelligently places citations based on content type and context.
"""

import re
from typing import List, Dict, Tuple
from external_reference_fetcher import ExternalReference
from config import call_openai, call_claude, call_ollama


class SmartCitationIntegrator:
    """Intelligently integrates citations with context-aware placement."""
    
    def __init__(self):
        pass
    
    def categorize_content(self, text: str) -> Dict[str, List[str]]:
        """
        Categorize text segments by type.
        
        Returns:
            Dict with keys: methods, results, background, discussion
        """
        segments = {
            'methods': [],
            'results': [],
            'background': [],
            'discussion': []
        }
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Classify sentence type
            lower = sentence.lower()
            
            # Method indicators
            if any(word in lower for word in ['propose', 'method', 'algorithm', 'approach', 'technique', 'implement', 'architecture']):
                segments['methods'].append(sentence)
            
            # Result indicators
            elif any(word in lower for word in ['achieve', 'obtain', 'result', 'performance', 'accuracy', 'improvement', 'outperform']):
                segments['results'].append(sentence)
            
            # Background indicators
            elif any(word in lower for word in ['previous', 'prior', 'existing', 'traditional', 'conventional', 'state-of-the-art']):
                segments['background'].append(sentence)
            
            # Discussion/Future
            elif any(word in lower for word in ['future', 'challenge', 'limitation', 'potential', 'direction']):
                segments['discussion'].append(sentence)
        
        return segments
    
    def match_citations_to_content(
        self,
        content_segments: Dict[str, List[str]],
        references: List[ExternalReference]
    ) -> Dict[str, List[Tuple[str, ExternalReference]]]:
        """
        Match citations to appropriate content segments.
        
        Returns:
            Dict mapping content type to list of (segment, reference) pairs
        """
        matches = {content_type: [] for content_type in content_segments.keys()}
        
        # Categorize references
        ref_categories = self._categorize_references(references)
        
        # Match based on type
        for content_type, segments in content_segments.items():
            for segment in segments:
                # Get appropriate references for this content type
                appropriate_refs = ref_categories.get(content_type, [])
                
                # Find best matching references
                # Increased from 3 to 10 to be more inclusive
                for ref in appropriate_refs[:10]:  # Top 10 per segment
                    if self._is_segment_relevant(segment, ref):
                        matches[content_type].append((segment, ref))
        
        # IMPORTANT: Ensure ALL selected references get included
        # If any reference wasn't matched, add it to discussion category
        all_matched_refs = set()
        for content_matches in matches.values():
            for _, ref in content_matches:
                all_matched_refs.add(ref.citation_number)
        
        unmatched_refs = [ref for ref in references if ref.citation_number not in all_matched_refs]
        if unmatched_refs:
            # Add unmatched references to the first available segment
            for content_type, segments in content_segments.items():
                if segments:
                    for ref in unmatched_refs:
                        matches[content_type].append((segments[0], ref))
                    break
        
        return matches
    
    def _categorize_references(self, references: List[ExternalReference]) -> Dict[str, List[ExternalReference]]:
        """Categorize references by type."""
        categories = {
            'methods': [],
            'results': [],
            'background': [],
            'discussion': []
        }
        
        for ref in references:
            title = (ref.title or "").lower()
            abstract = getattr(ref, 'abstract', '').lower()
            text = f"{title} {abstract}"
            
            # Method papers
            if any(word in text for word in ['method', 'approach', 'algorithm', 'architecture', 'framework']):
                categories['methods'].append(ref)
            
            # Results/benchmark papers
            elif any(word in text for word in ['benchmark', 'dataset', 'evaluation', 'performance', 'result']):
                categories['results'].append(ref)
            
            # Survey/review papers
            elif any(word in text for word in ['survey', 'review', 'overview', 'comprehensive']):
                categories['background'].append(ref)
            
            # Others go to discussion
            else:
                categories['discussion'].append(ref)
        
        return categories
    
    def _is_segment_relevant(self, segment: str, reference: ExternalReference) -> bool:
        """Check if segment is relevant to reference."""
        segment_words = set(segment.lower().split())
        ref_text = f"{reference.title or ''} {getattr(reference, 'abstract', '')}".lower()
        ref_words = set(ref_text.split())
        
        # Check word overlap - lowered threshold from 2 to 1 for more flexibility
        overlap = len(segment_words & ref_words)
        return overlap >= 1  # At least 1 shared word (more inclusive)
    
    def integrate_citations_smart(
        self,
        article_text: str,
        references: List[ExternalReference],
        llm_type: str = "openai",
        model: str = "gpt-4o",
        return_usage: bool = False,
        progress_callback=None
    ) -> str:
        """
        Integrate citations with smart placement based on content type.
        
        Args:
            article_text: Original article
            references: Filtered, high-quality references
            llm_type: LLM to use for integration
            model: Model name
            return_usage: If True, returns (article, usage) tuple
            progress_callback: Optional callback for real-time progress updates
            
        Returns:
            Article with intelligently placed citations, or (article, usage) if return_usage=True
        """
        # Parse article into sections
        sections = self._parse_sections(article_text)
        print(f"Processing {len(sections)} sections with {len(references)} references...")
        
        # Track used references to ensure all are distributed
        used_references = set()
        
        enhanced_sections = []
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        for i, (heading, content) in enumerate(sections, 1):
            section_name = heading[:50] if heading else f"Section {i}"
            print(f"Processing section {i}/{len(sections)}: {section_name}...")
            
            if progress_callback:
                progress_callback(f"[3.4.{i}] Processing section {i}/{len(sections)}: {section_name}")
            
            # Extract heading from the heading line (remove # markers)
            section_name = heading.replace('#', '').strip() if heading else f"Section {i}"
            
            # CRITICAL: Skip sections with no content (e.g., title-only sections)
            # This prevents LLM from hallucinating content
            if not content.strip():
                print(f"  ⏭️ Skipping '{section_name}' - no content (title-only)")
                enhanced_sections.append((heading, content))
                continue
            
            if progress_callback:
                progress_callback(f"[3.4.{i}] Processing section: {section_name}")
            
            # Categorize content in this section
            content_segments = self.categorize_content(content)
            
            # Match citations to content
            matches = self.match_citations_to_content(content_segments, references)
            
            if progress_callback:
                progress_callback(f"[3.4.{i}] Found {len(matches)} content segments to enhance")
            
            # Enhance section with smart citations
            if progress_callback:
                progress_callback(f"[3.4.{i}] Calling API for section {i}...")
            
            # Get unused references for this section
            unused_refs = [ref for ref in references if ref.citation_number not in used_references]
            
            # CRITICAL: Pass unused references to ensure all get used
            result = self._enhance_section_with_citations(
                heading, content, matches, llm_type, model, return_usage=return_usage,
                all_references=unused_refs,  # Pass only unused refs
                used_references=used_references  # Track usage
            )
            
            # Handle different return formats (OpenAI returns usage, others don't)
            if return_usage and isinstance(result, tuple) and len(result) == 2:
                enhanced_section, usage = result
            else:
                enhanced_section = result if isinstance(result, str) else result[0] if isinstance(result, tuple) else str(result)
                usage = None
            
            # Accumulate usage
            if usage:
                total_usage["prompt_tokens"] += usage.prompt_tokens
                total_usage["completion_tokens"] += usage.completion_tokens
                total_usage["total_tokens"] += usage.total_tokens
                
                if progress_callback:
                    progress_callback(f"[3.4.{i}] API response received!")
                    progress_callback(f"[3.4.{i}] Tokens: {usage.prompt_tokens} input, {usage.completion_tokens} output")
                    progress_callback(f"[3.4.{i}] Running total: {total_usage['total_tokens']} tokens")
                    
                print(f"  Section {i} tokens: {usage.prompt_tokens} input, {usage.completion_tokens} output")
            
            enhanced_sections.append((heading, enhanced_section))
        
        # Reassemble article
        final_article = self._reassemble_article(enhanced_sections)
        
        # Truncate article before References section to avoid duplication
        # The system will handle references separately in Step 4
        references_match = re.search(r'\n\n#+\s*(References|Bibliography)', final_article, re.IGNORECASE)
        if references_match:
            final_article = final_article[:references_match.start()]
            final_article = final_article.rstrip()  # Remove trailing whitespace
        
        # Note: Unused references will still appear in the reference list (UI layer handles this)
        # We don't add them to the article text to maintain IEEE compliance
        # The UI layer will include all selected references in the reference list
        
        if return_usage:
            return final_article, total_usage
        else:
            return final_article
    
    def _parse_sections(self, article_text: str) -> List[Tuple[str, str]]:
        """Parse article into sections, stopping before References."""
        sections = []
        lines = article_text.split('\n')
        
        current_heading = ""
        current_content = []
        
        for line in lines:
            # Check if we've reached the References section
            if re.match(r'^#+\s*(References|Bibliography)', line, re.IGNORECASE):
                # Stop parsing - don't include References or anything after
                break
                
            if re.match(r'^#{1,3}\s+', line):
                # Save previous section
                if current_heading or current_content:
                    sections.append((current_heading, '\n'.join(current_content)))
                
                # Start new section
                current_heading = line
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section (but not if it's References)
        if current_heading or current_content:
            # Check if last section is References
            heading_text = current_heading.lower() if current_heading else ""
            if "references" not in heading_text and "bibliography" not in heading_text:
                sections.append((current_heading, '\n'.join(current_content)))
        
        return sections
    
    def _enhance_section_with_citations(
        self,
        heading: str,
        content: str,
        citation_matches: Dict[str, List[Tuple[str, ExternalReference]]],
        llm_type: str,
        model: str,
        return_usage: bool = False,
        all_references: List[ExternalReference] = None,
        used_references: set = None
    ) -> str:
        """Enhance a section with appropriately placed citations."""
        
        # Check if this section should be skipped
        heading_lower = heading.lower()
        if "abstract" in heading_lower:
            # Abstract should NOT have citations - return unchanged
            print("  ⏭️ Skipping Abstract section - no citations added")
            return content
        elif "references" in heading_lower or "bibliography" in heading_lower:
            # References section should NOT be processed - return unchanged
            # The system handles references separately
            print("  ⏭️ Skipping References section - handled by system")
            return content
        
        # Build citation context
        citation_context = self._build_citation_context(citation_matches)
        
        # Create enhanced prompt for regular sections (abstract and references already handled above)
        system_msg = """You are an expert academic writer. Your task is to enhance a section by adding citations in the correct locations.

CRITICAL RULES:
1. PRESERVE all existing citations exactly as they appear
2. Add new citations based on content type
3. Place citations immediately after the claim they support
4. Use IEEE format: [number]
5. DO NOT invent citation numbers - ONLY use the numbers provided in the prompt
6. Keep the section structure unchanged
7. DO NOT add titles, headings, or any section headers - only enhance the existing content with citations
8. NEVER EVER add new paragraphs or sentences - only add citations to existing text
9. NEVER EVER generate content - only enhance what is provided
10. PRESERVE all mathematical formulas, equations, LaTeX expressions, and mathematical functions EXACTLY as they appear
11. DO NOT modify any mathematical content including \[ \], \( \), \begin{equation}, \frac, \sqrt, \sum, \int, etc.

WARNING: You MUST use ONLY the exact citation numbers listed in the AVAILABLE CITATIONS section. Do NOT use any other numbers."""

        prompt = f"""Enhance this section with smart citation placement:

SECTION HEADING: {heading}

SECTION CONTENT:
{content}

AVAILABLE CITATIONS BY TYPE:
{citation_context}

CRITICAL REQUIREMENTS:
- You MUST add citations from the AVAILABLE CITATIONS list
- You MUST use ONLY the exact citation numbers shown above
- Add citations where they naturally support the content
- Match citation type to content type
- Preserve all existing citations
- PRESERVE all mathematical formulas, equations, and LaTeX expressions EXACTLY as written
- DO NOT modify any mathematical content (fractions, square roots, integrals, sums, etc.)
- Output ONLY the enhanced content (WITHOUT the heading)
- Do NOT include "{heading}" in your response
- Start your response directly with the content text
- NEVER add new paragraphs, sentences, or words
- ONLY add [number] citations to existing text

FORBIDDEN ACTIONS:
- DO NOT use any citation numbers not listed above
- DO NOT write new content
- DO NOT add paragraphs
- DO NOT expand the text
- DO NOT generate new sentences
- DO NOT modify mathematical formulas or equations
- DO NOT add a References section or bibliography
- DO NOT include any reference entries
- ONLY add the provided [number] citations to existing text

MATHEMATICAL CONTENT PRESERVATION:
- Keep all \\( ... \\) inline math unchanged
- Keep all \\[ ... \\] display math unchanged
- Keep all \\begin{{equation}}...\\end{{equation}} blocks unchanged
- Keep all \\frac, \\sqrt, \\sum, \\int, \\partial, \\alpha, \\beta, etc. unchanged
- DO NOT alter any mathematical symbols or expressions

IMPORTANT: If you return the content without adding ANY new citations, you have failed the task.
The available citations are highly relevant and MUST be integrated into this section.

EXAMPLE OUTPUT FORMAT:
[First paragraph of EXISTING content with citations like [13] added...]
[Second paragraph of EXISTING content with citations like [14] added...]
(Do NOT start with the heading "{heading}")
(Do NOT add new content - only citations to existing content)"""

        # Call LLM
        try:
            if llm_type == "openai":
                result = call_openai(prompt, model=model, max_tokens=2000, system=system_msg, return_usage=True)
                if return_usage:
                    enhanced, usage = result
                    # Validation: Remove heading if LLM included it despite instructions
                    enhanced = self._strip_duplicate_heading(enhanced.strip(), heading)
                    
                    # CRITICAL: Validate that citations were actually added
                    # Skip validation for abstract sections (handled above)
                    enhanced = self._validate_citations_added(content, enhanced, citation_matches, all_references, used_references)
                    
                    return enhanced, usage
                else:
                    enhanced = result[0] if isinstance(result, tuple) else result
                    enhanced = self._strip_duplicate_heading(enhanced.strip(), heading)
                    enhanced = self._validate_citations_added(content, enhanced, citation_matches, all_references, used_references)
                    return enhanced
            elif llm_type == "claude":
                enhanced = call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=2000, system=system_msg)
                enhanced = self._strip_duplicate_heading(enhanced.strip(), heading)
                # Claude doesn't need validation for abstracts
                return enhanced
            else:
                enhanced = call_ollama(prompt, model=model, system=system_msg)
                enhanced = self._strip_duplicate_heading(enhanced.strip(), heading)
                # Ollama doesn't need validation for abstracts
                return enhanced
        except Exception as e:
            print("Error enhancing section: {}".format(e))
            if return_usage:
                return "{heading}\n\n{content}".format(heading=heading, content=content), None
            else:
                return "{heading}\n\n{content}".format(heading=heading, content=content)
    
    def _validate_citations_added(self, original_content: str, enhanced_content: str, citation_matches: Dict, all_references: List[ExternalReference] = None, used_references: set = None) -> str:
        """
        Validate that the LLM actually added citations. If not, manually insert them.
        This fixes the silent failure where LLM returns content unchanged.
        """
        import re
        
        # Extract citation numbers from both versions
        original_citations = set(re.findall(r'\[(\d+)\]', original_content))
        enhanced_citations = set(re.findall(r'\[(\d+)\]', enhanced_content))
        
        # Check if any new citations were added
        new_citations = enhanced_citations - original_citations
        
        # Get the expected external citation numbers
        expected_external = set()
        if all_references:
            expected_external = {ref.citation_number for ref in all_references}
        
        # Check which external citations were actually used
        external_used = new_citations & expected_external
        
        # If we didn't use the expected external citations, fix it
        if expected_external and len(external_used) < len(expected_external):
            print("⚠️ LLM failed to use correct external citations")
            print("  Expected: {}".format(sorted(expected_external)))
            print("  Used: {}".format(sorted(external_used)))
            
            # Remove any incorrect citations and insert the correct ones
            # First, remove any citations that are not original or expected external
            all_valid = original_citations | expected_external
            lines = enhanced_content.split('\n')
            
            # Clean up incorrect citations
            for i, line in enumerate(lines):
                citations_in_line = set(re.findall(r'\[(\d+)\]', line))
                for cit in citations_in_line:
                    if cit not in all_valid:
                        # Remove incorrect citation
                        lines[i] = line.replace(f'[{cit}]', '').replace('  ', ' ').strip()
            
            enhanced_content = '\n'.join(lines)
            
            # Now insert the missing external citations
            missing_external = expected_external - external_used
            
            if missing_external:
                # Find sentences to add citations to
                sentences = re.split(r'[.!?]+', enhanced_content)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                # Distribute missing citations across sentences
                for i, cit_num in enumerate(sorted(missing_external)):
                    if i < len(sentences):
                        # Add citation to sentence end
                        sentence_idx = i % len(sentences)
                        if sentences[sentence_idx]:
                            sentences[sentence_idx] += " [{}]".format(cit_num)
                
                # Rebuild content
                enhanced_content = '. '.join(sentences)
                
                # Update used references set
                if used_references is not None:
                    for cit in missing_external:
                        used_references.add(cit)
                
                print("  ✅ Manually inserted citations: {}".format(sorted(missing_external)))
        
        return enhanced_content
    
    def _strip_duplicate_heading(self, enhanced_content: str, heading: str) -> str:
        """
        Remove heading from enhanced content if LLM included it despite instructions.
        This is a safety net in case the LLM doesn't follow the prompt correctly.
        """
        if not enhanced_content or not heading:
            return enhanced_content
        
        lines = enhanced_content.split('\n')
        heading_stripped = heading.strip()
        
        # Check if first line matches the heading
        if lines[0].strip() == heading_stripped:
            # Remove first line and any following empty lines
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
            return '\n'.join(lines)
        
        # Check if heading appears without markdown formatting
        # e.g., "1. Introduction" vs "## 1. Introduction"
        heading_without_markdown = heading_stripped.lstrip('#').strip()
        if lines[0].strip() == heading_without_markdown:
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
            return '\n'.join(lines)
        
        return enhanced_content
    
    def _build_citation_context(self, citation_matches: Dict[str, List[Tuple[str, ExternalReference]]]) -> str:
        """Build context string showing available citations by type."""
        context_parts = []
        
        for content_type, matches in citation_matches.items():
            if not matches:
                continue
            
            context_parts.append(f"\n{content_type.upper()} CITATIONS:")
            for segment, ref in matches[:5]:  # Limit to 5 per type
                context_parts.append(f"[{ref.citation_number}] {ref.title[:80]}...")
        
        return "\n".join(context_parts)
    
    def _reassemble_article(self, sections: List[Tuple[str, str]]) -> str:
        """Reassemble article from enhanced sections."""
        return "\n\n".join([f"{heading}\n\n{content}" for heading, content in sections])
