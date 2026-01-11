#!/usr/bin/env python3
"""
Semantic Reference Filter
Filters external references by semantic similarity and method compatibility.
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from external_reference_fetcher import ExternalReference
from config import call_ollama


class SemanticFilter:
    """Filter references by semantic similarity and compatibility."""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            # Use SPECTER for academic papers
            self.model = SentenceTransformer('allenai/specter-base-v2')
            print("✅ SPECTER model loaded for semantic filtering")
        except ImportError:
            print("⚠️ sentence-transformers not installed. Using fallback.")
            self.model = None
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """Compute embeddings for list of texts."""
        if not self.model:
            # Fallback: simple TF-IDF like scoring
            return np.random.rand(len(texts), 768)
        
        return self.model.encode(texts, convert_to_numpy=True)
    
    def semantic_similarity_filter(
        self,
        query_text: str,
        references: List[ExternalReference],
        threshold: float = 0.3,
        top_k: int = 50
    ) -> List[Tuple[ExternalReference, float]]:
        """
        Filter references by semantic similarity to query.
        
        Args:
            query_text: Article title/abstract for comparison
            references: List of external references
            threshold: Minimum similarity score
            top_k: Maximum number to return
            
        Returns:
            List of (reference, score) tuples sorted by score
        """
        if not references:
            return []
        
        # Prepare texts
        query = f"{query_text}"
        ref_texts = []
        for ref in references:
            title = ref.title or ""
            abstract = getattr(ref, 'abstract', '') or ""
            ref_texts.append(f"{title} {abstract}")
        
        # Compute embeddings
        query_embedding = self.compute_embeddings([query])[0]
        ref_embeddings = self.compute_embeddings(ref_texts)
        
        # Calculate similarities
        similarities = np.dot(ref_embeddings, query_embedding)
        
        # Filter and sort
        scored_refs = list(zip(references, similarities))
        scored_refs = [(r, s) for r, s in scored_refs if s >= threshold]
        scored_refs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_refs[:top_k]
    
    def method_compatibility_check(
        self,
        article_text: str,
        references: List[ExternalReference],
        llm_model: str = "gemma3:27b"
    ) -> List[Tuple[ExternalReference, Dict]]:
        """
        Check method compatibility using local LLM.
        
        Args:
            article_text: Article content to analyze
            references: References to check
            llm_model: Local LLM to use
            
        Returns:
            List of (reference, compatibility_info) tuples
        """
        # Extract methodology from article
        article_methods = self._extract_methods(article_text)
        
        results = []
        for ref in references:
            ref_methods = self._extract_methods_from_reference(ref)
            
            # Check compatibility with LLM
            compatibility = self._check_method_compatibility(
                article_methods, ref_methods, llm_model
            )
            
            results.append((ref, compatibility))
        
        return results
    
    def _extract_methods(self, text: str) -> str:
        """Extract methodology descriptions from text."""
        # Look for methodology sections
        method_pattern = r'(?:method|approach|technique|algorithm)[\s\S]{0,500}'
        matches = re.findall(method_pattern, text.lower())
        return " ".join(matches[:3])  # First 3 matches
    
    def _extract_methods_from_reference(self, ref: ExternalReference) -> str:
        """Extract methods from reference."""
        methods = []
        if ref.title:
            methods.append(ref.title)
        if hasattr(ref, 'abstract') and ref.abstract:
            methods.append(ref.abstract)
        return " ".join(methods)
    
    def _check_method_compatibility(
        self,
        article_methods: str,
        ref_methods: str,
        llm_model: str
    ) -> Dict:
        """Use LLM to check if methods are compatible."""
        prompt = f"""Analyze if these two research approaches are compatible:

ARTICLE METHODS:
{article_methods[:500]}

REFERENCE METHODS:
{ref_methods[:500]}

Return JSON:
{{
    "compatible": true/false,
    "similarity": "high/medium/low",
    "reason": "Brief explanation"
}}"""
        
        try:
            response = call_ollama(prompt, model=llm_model, system="You are a research methodology expert. Respond with valid JSON only.")
            # Extract JSON from response
            import json
            if "{" in response and "}" in response:
                json_str = response[response.find("{"):response.rfind("}")+1]
                return json.loads(json_str)
        except Exception:
            pass
        
        return {"compatible": True, "similarity": "medium", "reason": "Unable to analyze"}
    
    def venue_validation(self, references: List[ExternalReference]) -> List[Tuple[ExternalReference, Dict]]:
        """Validate venue relevance for references."""
        results = []
        
        # Top-tier venues for computer vision/video processing
        top_venues = {
            'CVPR', 'ICCV', 'ECCV', 'NeurIPS', 'ICML', 'ICLR',
            'IEEE T-PAMI', 'IEEE T-IP', 'IEEE T-CSVT',
            'ACM TOG', 'SIGGRAPH', 'AAAI', 'IJCAI'
        }
        
        for ref in references:
            venue = getattr(ref, 'venue', '') or ''
            venue_info = {
                'is_top_tier': any(v.lower() in venue.lower() for v in top_venues),
                'venue': venue,
                'score': 0
            }
            
            if venue_info['is_top_tier']:
                venue_info['score'] = 1.0
            elif 'conference' in venue.lower() or 'journal' in venue.lower():
                venue_info['score'] = 0.5
            else:
                venue_info['score'] = 0.2
            
            results.append((ref, venue_info))
        
        return results
    
    def comprehensive_filter(
        self,
        query_text: str,
        article_text: str,
        references: List[ExternalReference],
        llm_model: str = "gemma3:27b"
    ) -> List[Dict]:
        """
        Run all filtering steps and return comprehensive results.
        
        Returns:
            List of dictionaries with all filtering info
        """
        # Step 1: Semantic similarity
        semantic_results = self.semantic_similarity_filter(query_text, references)
        
        # Extract references for next steps
        semantic_refs = [r for r, _ in semantic_results]
        
        # Step 2: Method compatibility
        method_results = self.method_compatibility_check(article_text, semantic_refs, llm_model)
        
        # Step 3: Venue validation
        venue_results = self.venue_validation(semantic_refs)
        
        # Combine results
        combined = []
        for i, ref in enumerate(semantic_refs):
            _, semantic_score = semantic_results[i]
            _, method_info = method_results[i]
            _, venue_info = venue_results[i]
            
            # Calculate overall score
            overall_score = (
                semantic_score * 0.4 +
                (1.0 if method_info.get('compatible', False) else 0.0) * 0.4 +
                venue_info['score'] * 0.2
            )
            
            combined.append({
                'reference': ref,
                'semantic_score': semantic_score,
                'method_compatible': method_info.get('compatible', False),
                'method_similarity': method_info.get('similarity', 'unknown'),
                'venue_score': venue_info['score'],
                'venue_tier': 'top' if venue_info['score'] == 1.0 else 'medium' if venue_info['score'] == 0.5 else 'low',
                'overall_score': overall_score
            })
        
        # Sort by overall score
        combined.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return combined
