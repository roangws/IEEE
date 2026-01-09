#!/usr/bin/env python3
"""
Web Search References Module
Fetches external academic references from the internet to diversify citation sources.
Uses Semantic Scholar API (free, no API key required).
"""

import requests
from typing import List, Optional
from dataclasses import dataclass
import re


@dataclass
class ExternalReference:
    """Represents an external reference fetched from the internet."""
    citation_number: int
    title: str
    authors: List[str]
    year: int
    venue: str
    doi: str = ""
    url: str = ""
    abstract: str = ""
    citation_count: int = 0
    
    def to_ieee_format(self) -> str:
        """Format the external reference in IEEE style."""
        # Format authors
        if len(self.authors) == 0:
            author_str = "Unknown"
        elif len(self.authors) == 1:
            author_str = self.authors[0]
        elif len(self.authors) == 2:
            author_str = f"{self.authors[0]} and {self.authors[1]}"
        else:
            author_str = f"{self.authors[0]} et al."
        
        # Build IEEE citation
        parts = [f"[{self.citation_number}]", author_str]
        
        if self.title:
            parts.append(f'"{self.title}"')
        
        if self.venue:
            parts.append(f"*{self.venue}*")
        
        if self.year:
            parts.append(str(self.year))
        
        if self.doi:
            parts.append(f"doi: {self.doi}")
        elif self.url:
            parts.append(f"[Online]. Available: {self.url}")
        
        return ", ".join(parts) + "."
    
    def to_context_string(self) -> str:
        """Format for LLM context."""
        author_str = self.authors[0] if self.authors else "Unknown"
        if len(self.authors) > 1:
            author_str += " et al."
        
        context = f"[{self.citation_number}] {author_str} ({self.year}). {self.title}"
        if self.abstract:
            # Truncate abstract for context
            abstract_preview = self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract
            context += f"\n    Abstract: {abstract_preview}"
        return context


class WebReferenceSearcher:
    """Searches for external academic references using Semantic Scholar API."""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.rate_limit_delay = 1.0  # Increased to 1 second between requests (60 requests/minute)
        self.last_request_time = 0
        
    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        min_citations: int = 5,
        year_from: int = 2015
    ) -> List[ExternalReference]:
        """
        Search for academic papers using Semantic Scholar.
        
        Args:
            query: Search query (topic, keywords)
            max_results: Maximum number of papers to return
            min_citations: Minimum citation count filter
            year_from: Only papers from this year onwards
            
        Returns:
            List of ExternalReference objects
        """
        try:
            # Rate limiting: wait if needed
            import time
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            # Semantic Scholar search endpoint
            search_url = f"{self.base_url}/paper/search"
            
            params = {
                'query': query,
                'limit': min(max_results * 2, 100),  # Fetch more to filter
                'fields': 'title,authors,year,venue,citationCount,abstract,externalIds,url',
                'year': f'{year_from}-'
            }
            
            # Retry mechanism with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                response = requests.get(search_url, params=params, timeout=10)
                self.last_request_time = time.time()
                
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        print(f"Semantic Scholar API rate limit reached. Waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("Rate limit exceeded after multiple retries. Please wait before trying again.")
                        return []
                
                if response.status_code == 200:
                    break
                else:
                    print(f"Semantic Scholar API error: {response.status_code}")
                    return []
            
            if response.status_code != 200:
                print(f"Semantic Scholar API error: {response.status_code}")
                if response.status_code == 429:
                    print("Rate limit exceeded. Please wait before making more requests.")
                return []
            
            data = response.json()
            papers = data.get('data', [])
            
            external_refs = []
            for paper in papers:
                # Filter by citation count
                if paper.get('citationCount', 0) < min_citations:
                    continue
                
                # Extract authors
                authors = []
                for author in paper.get('authors', []):
                    name = author.get('name', '')
                    if name:
                        authors.append(name)
                
                # Extract DOI
                external_ids = paper.get('externalIds', {})
                doi = external_ids.get('DOI', '')
                
                # Create reference
                ref = ExternalReference(
                    citation_number=0,  # Will be assigned later
                    title=paper.get('title', 'Unknown Title'),
                    authors=authors,
                    year=paper.get('year', 0),
                    venue=paper.get('venue', 'Unknown Venue'),
                    doi=doi,
                    url=paper.get('url', ''),
                    abstract=paper.get('abstract', ''),
                    citation_count=paper.get('citationCount', 0)
                )
                
                external_refs.append(ref)
                
                if len(external_refs) >= max_results:
                    break
            
            # Sort by citation count (most cited first)
            external_refs.sort(key=lambda x: x.citation_count, reverse=True)
            
            return external_refs[:max_results]
            
        except Exception as e:
            print(f"Error searching Semantic Scholar: {e}")
            return []
    
    def search_by_keywords(
        self,
        keywords: List[str],
        max_results: int = 10,
        min_citations: int = 5
    ) -> List[ExternalReference]:
        """
        Search using multiple keywords.
        
        Args:
            keywords: List of keywords to search
            max_results: Maximum results
            min_citations: Minimum citation filter
            
        Returns:
            List of ExternalReference objects
        """
        # Combine keywords into query
        query = " ".join(keywords[:5])  # Use top 5 keywords
        return self.search_papers(query, max_results, min_citations)
    
    def extract_keywords_from_article(self, article_text: str, max_keywords: int = 5) -> List[str]:
        """
        Extract key terms from article for searching.
        
        Args:
            article_text: The article text
            max_keywords: Maximum keywords to extract
            
        Returns:
            List of keywords
        """
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', article_text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Remove common words and extract key terms
            keywords = [word for word in title.split() if len(word) > 4]
            return keywords[:max_keywords]
        
        # Fallback: extract from first paragraph
        lines = article_text.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                words = [word.strip('.,;:()[]') for word in line.split() if len(word) > 5]
                return words[:max_keywords]
        
        return []
    
    def assign_citation_numbers(
        self,
        external_refs: List[ExternalReference],
        start_number: int
    ) -> List[ExternalReference]:
        """
        Assign citation numbers to external references.
        
        Args:
            external_refs: List of external references
            start_number: Starting citation number
            
        Returns:
            Updated list with citation numbers assigned
        """
        for idx, ref in enumerate(external_refs):
            ref.citation_number = start_number + idx
        return external_refs


def fetch_external_references(
    article_text: str,
    num_external_refs: int = 10,
    start_citation_number: int = 31,
    min_citations: int = 10,
    search_query: Optional[str] = None
) -> List[ExternalReference]:
    """
    Main function to fetch external references for an article.
    
    Args:
        article_text: The article text to analyze
        num_external_refs: Number of external refs to fetch
        start_citation_number: Starting citation number for external refs
        min_citations: Minimum citation count filter
        search_query: Optional custom search query (uses article keywords if None)
        
    Returns:
        List of ExternalReference objects with assigned citation numbers
    """
    searcher = WebReferenceSearcher()
    
    # Determine search query
    if search_query:
        query = search_query
    else:
        # Extract keywords from article
        keywords = searcher.extract_keywords_from_article(article_text)
        query = " ".join(keywords)
    
    # Search for papers
    external_refs = searcher.search_papers(
        query=query,
        max_results=num_external_refs,
        min_citations=min_citations
    )
    
    # Assign citation numbers
    external_refs = searcher.assign_citation_numbers(external_refs, start_citation_number)
    
    return external_refs
