#!/usr/bin/env python3
"""
External Reference Integrator
Integrates external references into article text section-by-section while preserving structure.
"""

import re
from typing import List, Tuple, Optional
from external_reference_fetcher import ExternalReference
from config import InsufficientQuotaError, call_claude, call_openai, call_ollama


class ExternalIntegrator:
    """Integrates external references into article text."""
    
    def __init__(self):
        pass
    
    def parse_sections(self, article_text: str) -> List[Tuple[str, str, str]]:
        """
        Parse article into sections by markdown headings.
        
        Args:
            article_text: Full article text
            
        Returns:
            List of (heading, heading_text, section_content) tuples
        """
        sections = []
        lines = article_text.split('\n')
        
        current_heading = ""
        current_heading_text = ""
        current_content = []
        
        for line in lines:
            # Check if line is a heading (## or ###)
            heading_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            
            if heading_match:
                # Save previous section if exists
                if current_heading or current_content:
                    sections.append((
                        current_heading,
                        current_heading_text,
                        '\n'.join(current_content).strip()
                    ))
                
                # Start new section
                current_heading = heading_match.group(1)  # ## or ###
                current_heading_text = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_heading or current_content:
            sections.append((
                current_heading,
                current_heading_text,
                '\n'.join(current_content).strip()
            ))
        
        return sections
    
    def get_relevant_external_refs(
        self,
        section_heading: str,
        section_content: str,
        external_refs: List[ExternalReference],
        max_refs: int = 5
    ) -> List[ExternalReference]:
        """
        Select most relevant external refs for a section.
        
        Args:
            section_heading: Section heading text
            section_content: Section content
            external_refs: All external references
            max_refs: Max refs to return
            
        Returns:
            List of relevant ExternalReference objects
        """
        # Only include selected refs
        selected_refs = [ref for ref in external_refs if ref.selected]
        
        if not selected_refs:
            return []
        
        # Score each ref based on keyword overlap with section
        section_text = (section_heading + " " + section_content).lower()
        section_words = set(w for w in section_text.split() if len(w) > 3)
        
        scored_refs = []
        for ref in selected_refs:
            ref_title = ref.title if isinstance(ref.title, str) else ""
            ref_abstract = ref.abstract if isinstance(getattr(ref, 'abstract', ''), str) else ""
            ref_text = (ref_title + " " + ref_abstract).lower()
            ref_words = set(ref_text.split())
            
            if section_words:
                overlap = len(section_words & ref_words) / len(section_words)
                scored_refs.append((ref, overlap))
            else:
                # If no section words to compare, give neutral score
                scored_refs.append((ref, 0.1))
        
        # Sort by overlap score
        scored_refs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N, but ensure we return up to max_refs even with low scores
        # This helps ensure more references get integrated
        if len(scored_refs) <= max_refs:
            return [ref for ref, _ in scored_refs]
        else:
            # Take all refs with non-zero overlap, then fill with highest-scoring remaining
            non_zero = [ref for ref, score in scored_refs if score > 0]
            if len(non_zero) >= max_refs:
                return non_zero[:max_refs]
            else:
                remaining = max_refs - len(non_zero)
                zero_score = [ref for ref, score in scored_refs if score == 0]
                return non_zero + zero_score[:remaining]
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (1 token ≈ 4 characters for English)."""
        return len(text) // 4
    
    def _chunk_section_by_paragraphs(self, section_content: str, max_tokens: int = 1500) -> List[str]:
        """
        Split section into smaller chunks if it exceeds token limit.
        Splits on paragraph boundaries to preserve coherence.
        
        Args:
            section_content: Section text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of content chunks
        """
        if self._estimate_tokens(section_content) <= max_tokens:
            return [section_content]
        
        # Split by double newlines (paragraphs)
        paragraphs = section_content.split('\n\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            
            if current_tokens + para_tokens > max_tokens and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [section_content]
    
    def integrate_section(
        self,
        heading: str,
        heading_text: str,
        section_content: str,
        relevant_refs: List[ExternalReference],
        llm_type: str = "openai",
        model: str = "gpt-4o"
    ) -> str:
        """
        Integrate external references into a single section.
        Uses token-aware chunking for large sections.
        
        Args:
            heading: Heading markdown (## or ###)
            heading_text: Heading text
            section_content: Section content
            relevant_refs: Relevant external references for this section
            llm_type: "openai", "claude", or "ollama"
            model: Model name
            
        Returns:
            Updated section text (with heading)
        """
        if not relevant_refs or not section_content.strip():
            # No refs or empty section, return as-is
            return f"{heading} {heading_text}\n\n{section_content}"
        
        # Check if section needs chunking
        chunks = self._chunk_section_by_paragraphs(section_content, max_tokens=1500)
        
        if len(chunks) > 1:
            print(f"Section '{heading_text}' split into {len(chunks)} chunks for processing")
            enhanced_chunks = []
            for i, chunk in enumerate(chunks, 1):
                print(f"  Processing chunk {i}/{len(chunks)}...")
                enhanced_chunk = self._integrate_section_chunk(
                    heading, heading_text, chunk, relevant_refs, llm_type, model, chunk_num=i, total_chunks=len(chunks)
                )
                # Remove heading from all but first chunk
                if i > 1 and enhanced_chunk.startswith(heading):
                    enhanced_chunk = enhanced_chunk.split('\n', 2)[-1].strip()
                enhanced_chunks.append(enhanced_chunk)
            
            # Combine chunks with heading only on first
            return '\n\n'.join(enhanced_chunks)
        else:
            return self._integrate_section_chunk(heading, heading_text, section_content, relevant_refs, llm_type, model)
    
    def _integrate_section_chunk(
        self,
        heading: str,
        heading_text: str,
        section_content: str,
        relevant_refs: List[ExternalReference],
        llm_type: str,
        model: str,
        chunk_num: int = 1,
        total_chunks: int = 1
    ) -> str:
        """
        Integrate external references into a section chunk.
        
        Args:
            heading: Heading markdown
            heading_text: Heading text
            section_content: Section/chunk content
            relevant_refs: Relevant external references
            llm_type: LLM type
            model: Model name
            chunk_num: Current chunk number (for multi-chunk sections)
            total_chunks: Total chunks (for multi-chunk sections)
            
        Returns:
            Enhanced section/chunk text
        """
        
        # Build context from external refs
        ref_context = "\n\n".join([
            ref.to_context_snippet() for ref in relevant_refs
        ])
        
        # Build citation number list
        citation_numbers = [ref.citation_number for ref in relevant_refs]
        
        chunk_context = f" (part {chunk_num}/{total_chunks})" if total_chunks > 1 else ""
        
        system_msg = f"""You are an IEEE-style academic writer. Your task is to enhance a section of an academic article by adding citations to external references while PRESERVING ALL existing citations.

CRITICAL RULES (FOLLOW EXACTLY):
1. Keep the section heading EXACTLY as provided: "{heading} {heading_text}"{chunk_context}
2. PRESERVE ALL existing citations - DO NOT remove, renumber, or change any existing [number] citations
3. Add NEW citations ONLY from these external references: {citation_numbers}
4. Goal: Keep ALL local citations + add at least 60% of external citations where relevant
5. Use IEEE format: [number] after relevant claims
6. Add 2-4 new citations per paragraph where they support the content
7. Do NOT invent citation numbers outside the provided list
8. Do NOT add a References section
9. Do NOT change the heading text or level
10. Maintain academic tone and technical precision

IMPORTANT: The section likely contains local citations [1-40]. These MUST be preserved exactly. External citations [{min(citation_numbers)}-{max(citation_numbers)}] should be ADDED, not replace existing ones."""

        chunk_note = f"\n\n**NOTE:** This is part {chunk_num} of {total_chunks} for this section. Process this chunk independently." if total_chunks > 1 else ""
        
        prompt = f"""Enhance this section by adding citations to the provided external references.

**SECTION TO ENHANCE:**
{heading} {heading_text}

{section_content}{chunk_note}

**AVAILABLE EXTERNAL REFERENCES:**
{ref_context}

**INSTRUCTIONS:**
- PRESERVE all existing citations in the section exactly as they appear
- Add new citations ONLY from these exact numbers: {citation_numbers}
- Do NOT use any citation numbers not listed above
- Keep the heading EXACTLY: "{heading} {heading_text}"
- Preserve the section structure and main points
- Only add new citations where they genuinely support the content
- Do not rewrite extensively - focus on adding new citations
- Output the complete enhanced section including the heading"""

        # Call LLM
        try:
            if llm_type == "openai":
                enhanced = call_openai(prompt, model=model, max_tokens=2000, system=system_msg)
            elif llm_type == "claude":
                enhanced = call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=2000, system=system_msg)
            else:  # ollama
                enhanced = call_ollama(prompt, model=model, system=system_msg)
            
            enhanced = enhanced.strip()
            
            # Validate citations
            import re
            found_citations = set(re.findall(r"\[(\d+)\]", enhanced))
            valid_external_citations = set(citation_numbers)
            
            # Check for invalid citations (not in external refs)
            invalid_external = found_citations - valid_external_citations
            
            # Note: We don't remove invalid citations here because they might be 
            # valid local citations from the original article
            if invalid_external:
                print(f"⚠️ Found citations not in external refs: {sorted(invalid_external)}")
                print("These might be local citations from the original article")
            
            return enhanced
            
        except Exception as e:
            if isinstance(e, InsufficientQuotaError):
                raise
            print(f"Error integrating section: {str(e)}")
            return f"{heading} {heading_text}\n\n{section_content}"
    
    def integrate_external_refs(
        self,
        article_text: str,
        external_refs: List[ExternalReference],
        llm_type: str = "openai",
        model: str = "gpt-4o",
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Integrate external references into article section-by-section.
        
        Args:
            article_text: Original article text
            external_refs: List of external references
            llm_type: "openai", "claude", or "ollama"
            model: Model name
            progress_callback: Optional callback(section_num, total_sections, section_name)
            
        Returns:
            Enhanced article text
        """
        # Parse into sections
        sections = self.parse_sections(article_text)
        
        if not sections:
            return article_text
        
        enhanced_sections = []
        total_sections = len(sections)
        
        for i, (heading, heading_text, content) in enumerate(sections):
            if progress_callback:
                progress_callback(i + 1, total_sections, heading_text)
            
            # Skip if no heading (preamble/title)
            if not heading:
                enhanced_sections.append(content)
                continue
            
            # Get relevant refs for this section
            # Increased max_refs to ensure more references get integrated
            relevant_refs = self.get_relevant_external_refs(
                heading_text,
                content,
                external_refs,
                max_refs=10
            )
            
            # Integrate refs into section
            enhanced_section = self.integrate_section(
                heading,
                heading_text,
                content,
                relevant_refs,
                llm_type,
                model
            )
            
            enhanced_sections.append(enhanced_section)
        
        # Combine all sections
        enhanced_article = '\n\n'.join(enhanced_sections)
        
        # Final validation - only remove truly invalid citations
        # (not in local refs from original article or external refs)
        print("\n=== Final Citation Validation ===")
        all_found = re.findall(r"\[(\d+)\]", enhanced_article)
        
        # Get all valid citations (this would need access to the original citation_map)
        # For now, we'll only remove citations that are clearly invalid (e.g., very high numbers)
        invalid = []
        for citation in all_found:
            cit_num = int(citation)
            # Remove citations that are likely hallucinated (e.g., > 1000)
            if cit_num > 1000:
                invalid.append(cit_num)
        
        if invalid:
            print(f"⚠️ Found likely invalid citations: {sorted(invalid)}")
            print(f"Removing {len(invalid)} invalid citations...")
            for inv in sorted(invalid, reverse=True):
                enhanced_article = enhanced_article.replace(f"[{inv}]", "")
            print("✅ Invalid citations removed")
        else:
            print(f"✅ Found {len(all_found)} total citations")
        
        return enhanced_article
