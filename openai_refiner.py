#!/usr/bin/env python3
"""
OpenAI Article Refiner
Polishes the article while preserving all citations.
"""

import re
from typing import List, Set, Tuple
from config import call_openai


class OpenAIRefiner:
    """Refine article with OpenAI while preserving citations."""
    
    def __init__(self):
        pass
    
    def refine_article(
        self,
        article_text: str,
        llm_model: str = "gpt-4o",
        preserve_citations: bool = True
    ) -> str:
        """
        Refine article with OpenAI GPT-4.
        
        Args:
            article_text: Article with citations
            llm_model: OpenAI model to use
            preserve_citations: Whether to preserve all citations
            
        Returns:
            Refined article
        """
        if preserve_citations:
            return self._refine_with_citation_preservation(article_text, llm_model)
        else:
            return self._refine_standard(article_text, llm_model)
    
    def _refine_with_citation_preservation(self, article_text: str, model: str) -> str:
        """Refine article while strictly preserving citations."""
        
        # Extract all citations before refinement
        original_citations = self._extract_all_citations(article_text)
        
        # Parse into sections
        sections = self._parse_sections(article_text)
        
        refined_sections = []
        
        for heading, content in sections:
            # Get citations in this section
            section_citations = self._extract_citations_from_text(content)
            
            # Refine section while preserving citations
            refined_content = self._refine_section_preserve_citations(
                heading, content, section_citations, model
            )
            
            refined_sections.append((heading, refined_content))
        
        # Reassemble and validate
        refined_article = self._reassemble_sections(refined_sections)
        
        # Final validation
        final_citations = self._extract_all_citations(refined_article)
        self._validate_citations(original_citations, final_citations)
        
        return refined_article
    
    def _refine_section_preserve_citations(
        self,
        heading: str,
        content: str,
        required_citations: Set[str],
        model: str
    ) -> str:
        """Refine a section while ensuring all required citations are present."""
        
        citations_list = sorted(list(required_citations))
        
        system_msg = f"""You are an expert academic editor. Your task is to refine this section for clarity, flow, and academic rigor.

CRITICAL REQUIREMENTS:
1. You MUST include ALL of these citations in the output: {citations_list}
2. Place citations in logically appropriate locations
3. Do NOT invent new citation numbers
4. Do NOT remove any of the required citations
5. Improve sentence structure and academic tone
6. Fix any grammatical issues
7. Ensure smooth transitions between ideas
8. Keep the heading exactly as provided"""

        prompt = f"""Refine this academic section while preserving all citations:

{heading}

{content}

REQUIRED CITATIONS (must all appear): {citations_list}

Instructions:
- Improve clarity and academic writing
- Ensure all required citations are included
- Place citations where they best support the content
- Maintain technical accuracy
- Output the complete refined section with heading"""

        try:
            refined = call_openai(prompt, model=model, max_tokens=2000, system=system_msg)
            return refined.strip()
        except Exception as e:
            print(f"Error refining section: {e}")
            return f"{heading}\n\n{content}"
    
    def _extract_all_citations(self, text: str) -> Set[str]:
        """Extract all citation numbers from text."""
        return set(re.findall(r'\[(\d+)\]', text))
    
    def _extract_citations_from_text(self, text: str) -> Set[str]:
        """Extract citations from a text segment."""
        return self._extract_all_citations(text)
    
    def _parse_sections(self, article_text: str) -> List[Tuple[str, str]]:
        """Parse article into sections."""
        sections = []
        lines = article_text.split('\n')
        
        current_heading = ""
        current_content = []
        
        for line in lines:
            if re.match(r'^#{1,3}\s+', line):
                # Save previous section
                if current_heading or current_content:
                    sections.append((current_heading, '\n'.join(current_content)))
                
                # Start new section
                current_heading = line
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_heading or current_content:
            sections.append((current_heading, '\n'.join(current_content)))
        
        return sections
    
    def _reassemble_sections(self, sections: List[Tuple[str, str]]) -> str:
        """Reassemble article from sections."""
        return "\n\n".join([f"{heading}\n\n{content}" for heading, content in sections])
    
    def _validate_citations(self, original: Set[str], final: Set[str]):
        """Validate that all original citations are preserved."""
        missing = original - final
        extra = final - original
        
        if missing:
            print(f"⚠️ Warning: Lost citations: {sorted(missing)}")
        
        if extra:
            print(f"ℹ️ Info: Added citations: {sorted(extra)}")
        
        if not missing and not extra:
            print("✅ All citations preserved perfectly")
    
    def _refine_standard(self, article_text: str, model: str) -> str:
        """Standard refinement without strict citation preservation."""
        
        system_msg = """You are an expert academic editor. Refine this article for:
- Clarity and readability
- Academic tone and style
- Logical flow and structure
- Grammatical correctness
- Technical accuracy

Preserve all citations and technical content."""

        prompt = f"""Refine this academic article:

{article_text}

Improve the writing while preserving all citations and technical content."""

        try:
            refined = call_openai(prompt, model=model, max_tokens=4000, system=system_msg)
            return refined.strip()
        except Exception as e:
            print(f"Error refining article: {e}")
            return article_text
