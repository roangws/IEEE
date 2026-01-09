#!/usr/bin/env python3
"""
External Reference Fetcher
Fetches and curates academic papers from external APIs (Semantic Scholar, etc.)
"""

from dataclasses import dataclass
from typing import List, Optional
import requests
import time
import re
from datetime import datetime


@dataclass
class ExternalReference:
    """Represents a fetched external paper."""
    citation_number: int  # Assigned AFTER local refs: [N+1], [N+2], ...
    title: str
    authors: List[str]
    year: int
    venue: str  # Journal/Conference name
    journal: Optional[str] = None
    publisher: Optional[str] = None
    abstract: str = ""
    doi: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0  # 0.0-1.0
    selected: bool = True  # User can deselect irrelevant papers
    
    def _clean_author_name(self, name: str) -> str:
        """Remove noise patterns from author names."""
        import re
        if not isinstance(name, str):
            return ""
        # Remove common noise patterns (case-insensitive)
        noise_patterns = [
            r'\b(Senior\s+)?Member\s*,?\s*Ieee\b',
            r'\bIeee\s+(Senior\s+)?Member\b',
            r'\bFellow\s*,?\s*Ieee\b',
            r'\bIeee\s+Fellow\b',
            r'\bLife\s+(Senior\s+)?Member\b',
            r'\bStudent\s+Member\b',
        ]
        cleaned = name
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        # Clean up extra whitespace and commas
        cleaned = re.sub(r'\s*,\s*,\s*', ', ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = cleaned.strip(',').strip()
        return cleaned
    
    def to_ieee_format(self) -> str:
        """Format as IEEE reference."""
        authors = self.authors if isinstance(self.authors, list) else []
        # Clean author names to remove noise like "Member Ieee"
        safe_authors = [self._clean_author_name(a) for a in authors if isinstance(a, str) and a.strip()]
        safe_authors = [a for a in safe_authors if a]  # Remove empty after cleaning
        author_str = ", ".join(safe_authors[:3]) if safe_authors else "Unknown"
        if len(safe_authors) > 3:
            author_str += " et al."
        venue_str = self.venue if isinstance(self.venue, str) and self.venue else ""
        title_str = self.title if isinstance(self.title, str) and self.title else "Untitled"
        year_val = self.year if isinstance(self.year, int) else 0
        # Match internal format: [N] Authors, "Title," Year. (venue optional)
        if venue_str:
            return f"[{self.citation_number}] {author_str}, \"{title_str},\" {venue_str}, {year_val}."
        else:
            return f"[{self.citation_number}] {author_str}, \"{title_str},\" {year_val}."
    
    def to_context_snippet(self) -> str:
        """Format for LLM context injection."""
        abstract_text = self.abstract if isinstance(self.abstract, str) else ""
        abstract_snippet = abstract_text[:500] + "..." if len(abstract_text) > 500 else abstract_text
        title_str = self.title if isinstance(self.title, str) and self.title else "Untitled"
        year_val = self.year if isinstance(self.year, int) else 0
        return f"**[{self.citation_number}]** {title_str} ({year_val})\n{abstract_snippet}"
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            'citation_number': self.citation_number,
            'title': self.title,
            'authors': self.authors,
            'year': self.year,
            'venue': self.venue,
            'journal': self.journal,
            'publisher': self.publisher,
            'abstract': self.abstract,
            'doi': self.doi,
            'url': self.url,
            'relevance_score': self.relevance_score,
            'selected': self.selected
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExternalReference':
        """Create from dict."""
        if not isinstance(data, dict):
            raise TypeError("ExternalReference.from_dict expects a dict")

        # Backward compatibility for older cached entries
        if 'journal' not in data:
            data = dict(data)
            data['journal'] = None
        if 'publisher' not in data:
            data = dict(data)
            data['publisher'] = None

        # Normalize common nullable fields (older cache entries sometimes store None)
        data = dict(data)
        if data.get('abstract') is None:
            data['abstract'] = ""
        if data.get('title') is None:
            data['title'] = "Untitled"
        if data.get('authors') is None:
            data['authors'] = ["Unknown"]
        if data.get('venue') is None:
            data['venue'] = "Unknown Venue"

        return cls(**data)


class ExternalReferenceFetcher:
    """Fetches and curates external references from academic APIs."""
    
    def __init__(self):
        self.ss_base_url = "https://api.semanticscholar.org/graph/v1"
        self.rate_limit_delay = 0.3  # gentle delay to reduce 429s
        self._http_headers = {
            "User-Agent": "Roan-IEEE/1.0 (+https://github.com/; academic-reference-fetcher)"
        }
    
    def fetch_from_semantic_scholar(
        self, 
        query: str, 
        limit: int = 20,
        year_range: tuple = (2018, 2025),
        fields: str = "title,authors,year,venue,publicationVenue,journal,abstract,externalIds,citationCount,url"
    ) -> List[dict]:
        """
        Query Semantic Scholar API.
        
        Args:
            query: Search query
            limit: Max results
            year_range: (min_year, max_year)
            fields: Comma-separated fields to retrieve
            
        Returns:
            List of paper dictionaries
        """
        try:
            params = {
                "query": query,
                "limit": min(limit, 100),  # API max is 100
                "fields": fields
            }
            
            # Add year filter if specified
            if year_range:
                params["year"] = f"{year_range[0]}-{year_range[1]}"
            
            url = f"{self.ss_base_url}/paper/search"

            for attempt in range(4):
                response = requests.get(
                    url,
                    params=params,
                    headers=self._http_headers,
                    timeout=15,
                )

                if response.status_code == 200:
                    time.sleep(self.rate_limit_delay)
                    data = response.json()
                    return data.get("data", [])

                if response.status_code == 429 or response.status_code >= 500:
                    backoff = min(2.0 * (2 ** attempt), 10.0)
                    time.sleep(backoff)
                    continue

                body_preview = (response.text or "")[:500]
                print(f"Semantic Scholar API error: {response.status_code} body={body_preview}")
                time.sleep(self.rate_limit_delay)
                return []

            print("Semantic Scholar API error: 429 (rate limited)")
            return []
                
        except Exception as e:
            print(f"Error fetching from Semantic Scholar: {str(e)}")
            return []
    
    def deduplicate_against_corpus(
        self, 
        external_papers: List[dict], 
        local_citation_map: dict
    ) -> List[dict]:
        """
        Remove papers already in local corpus.
        
        Args:
            external_papers: Papers from external API
            local_citation_map: Local corpus citation mapping (filename -> number)
            
        Returns:
            Deduplicated list
        """
        # Extract titles from local corpus filenames (rough matching)
        local_titles = set()
        for filename in local_citation_map.keys():
            # Clean filename to approximate title
            title_approx = filename.replace('.pdf', '').replace('_', ' ').lower()
            local_titles.add(title_approx)
        
        deduplicated = []
        for paper in external_papers:
            title = paper.get("title", "").lower()
            # Simple substring matching to avoid duplicates
            is_duplicate = any(
                title in local_title or local_title in title 
                for local_title in local_titles
            )
            if not is_duplicate:
                deduplicated.append(paper)
        
        return deduplicated
    
    def score_relevance(
        self, 
        paper: dict, 
        topic: str, 
        article_text: str = ""
    ) -> float:
        """
        Score paper relevance to topic and article content.
        
        Args:
            paper: Paper dict from API
            topic: Article topic
            article_text: Generated article text (optional)
            
        Returns:
            Relevance score 0.0-1.0
        """
        score = 0.0
        
        title = (paper.get("title") or "").lower()
        abstract = (paper.get("abstract") or "").lower()
        topic_lower = topic.lower()
        
        # Extract topic keywords
        topic_words = set(w for w in topic_lower.split() if len(w) > 3)
        
        # 1. Keyword overlap (50% weight)
        text_words = set(title.split() + abstract.split())
        if topic_words:
            overlap = len(topic_words & text_words) / len(topic_words)
            score += overlap * 0.5
        
        # 2. Recency bonus (30% weight) - prefer newer papers
        year = paper.get("year", 2020)
        current_year = datetime.now().year
        if year >= 2020:
            recency = min((year - 2015) / (current_year - 2015), 1.0)
            score += recency * 0.3
        
        # 3. Citation count (20% weight) - normalized
        citation_count = paper.get("citationCount", 0)
        if citation_count > 0:
            citation_score = min(citation_count / 100, 1.0)
            score += citation_score * 0.2
        
        return min(score, 1.0)
    
    def extract_keywords_with_llm(
        self, 
        article_text: str,
        num_keywords: int = 10,
        technical_level: int = 3,
        max_words_per_keyword: int = 3,
        model: str = "gemma3:27b",
        use_openai: bool = False
    ) -> List[str]:
        """
        Extract key academic concepts from article using LLM.
        
        Args:
            article_text: Full article text
            num_keywords: Number of keywords to extract (5-20)
            technical_level: 1=Generic, 5=Highly Technical
            model: Model name to use
            use_openai: If True, use OpenAI API instead of Ollama
            
        Returns:
            List of keyword strings
        """
        # Extract first 2000 chars (intro + abstract)
        excerpt = article_text[:2000]
        
        # Technical level descriptions
        tech_descriptions = {
            1: "broad, general terms that would be understood by non-specialists",
            2: "somewhat general terms with some domain-specific language",
            3: "balanced mix of general and technical terminology",
            4: "technical terms and specific methodologies",
            5: "highly technical, specialized jargon and specific algorithms/frameworks"
        }
        tech_desc = tech_descriptions.get(technical_level, tech_descriptions[3])

        try:
            max_words_per_keyword = int(max_words_per_keyword)
        except Exception:
            max_words_per_keyword = 3
        max_words_per_keyword = max(1, min(10, max_words_per_keyword))

        prompt = f"""Extract exactly {num_keywords} key academic search keyphrases from this article excerpt for searching related papers.

Article excerpt:
{excerpt}

TECHNICAL LEVEL: Extract {tech_desc}.

PHRASE LENGTH: Each keyphrase must be between 1 and {max_words_per_keyword} words.

PRIORITIZE HARD-TECHNICAL TERMS:
- Model/architecture names, algorithm names, loss functions, optimization methods
- Datasets, benchmarks, evaluation metrics, ablation terms
- Specific methods (e.g., "contrastive learning", "federated averaging", "beam search")
- Domain-specific technical phrases (not generic words like "performance", "system", "study")

Return ONLY a comma-separated list of {num_keywords} keywords. Focus on:
- Technical terms and methodologies appropriate for the technical level
- Research domains and topics
- Key technologies mentioned
- Application areas

Example output: "knowledge graphs, cultural context, generative AI, semantic reasoning, data integration"

Keywords:"""

        system_msg = "You are a research librarian extracting search keywords. Return only comma-separated keywords, no other text. No explanations."
        
        try:
            if use_openai:
                from config import call_openai
                response = call_openai(
                    prompt, 
                    model=model,
                    max_tokens=200,
                    system=system_msg
                )
            else:
                from config import call_ollama
                response = call_ollama(
                    prompt, 
                    model=model, 
                    system=system_msg
                )
            
            # Parse comma-separated keywords
            keywords = []
            for raw in response.split(','):
                k = raw.strip().strip('"').strip("'")
                if not k:
                    continue
                words = [w for w in k.split() if w]
                if len(words) > max_words_per_keyword:
                    k = " ".join(words[:max_words_per_keyword])
                keywords.append(k)
            return keywords[:num_keywords]
        except Exception as e:
            print(f"Error extracting keywords with LLM: {str(e)}")
            # Fallback: extract from title/first paragraph
            words = excerpt.split()[:50]
            return [w for w in words if len(w) > 4][:num_keywords]
    
    def search_internet_with_gpt4o(
        self,
        keywords: List[str],
        num_papers: int = 10,
        year_range: tuple = (2020, 2025),
        analysis_guidance: Optional[dict] = None,
    ) -> List[ExternalReference]:
        """
        Search internet for academic papers using GPT-4o with web search.
        
        Args:
            keywords: List of search keywords
            num_papers: Target number of papers
            year_range: (min_year, max_year)
            
        Returns:
            List of ExternalReference objects
        """
        try:
            num_papers = int(num_papers)
        except Exception:
            num_papers = 10
        num_papers = max(1, min(50, num_papers))

        keywords = [k.strip() for k in (keywords or []) if isinstance(k, str) and k.strip()]
        if not keywords:
            return []

        def _safe_year(v) -> Optional[int]:
            try:
                if v is None:
                    return None
                if isinstance(v, bool):
                    return None
                return int(v)
            except Exception:
                return None

        query_variants = []
        query_variants.append(" ".join(keywords[:8]))
        query_variants.append(" \"" + "\" \"".join(keywords[:6]) + "\"")
        if len(keywords) >= 2:
            query_variants.append(" ".join(keywords[:2]))

        # Fallback strategies if queries are too long/specific for Semantic Scholar search.
        top_terms = [k for k in keywords[:6] if k]
        if top_terms:
            query_variants.append(" OR ".join([f'"{t}"' for t in top_terms[:4]]))
        if len(keywords) >= 1:
            query_variants.append(f'"{keywords[0]}" survey')

        fetch_limit = min(max(num_papers * 6, 30), 100)

        def _collect_candidates(qs: List[str], yr: Optional[tuple]) -> List[dict]:
            seen_titles_local = set()
            collected: List[dict] = []
            for q in qs:
                papers = self.fetch_from_semantic_scholar(query=q, limit=fetch_limit, year_range=yr)
                for p in papers:
                    t = (p.get("title") or "").strip()
                    if not t:
                        continue
                    key = re.sub(r"\s+", " ", t).lower()
                    if key in seen_titles_local:
                        continue
                    seen_titles_local.add(key)
                    collected.append(p)
                if len(collected) >= fetch_limit:
                    break
            return collected

        candidates = _collect_candidates(query_variants, year_range)

        # If the year filter yields nothing (or API rejects it), retry once without year filtering.
        if not candidates:
            candidates = _collect_candidates(query_variants[-3:], None)

        if not candidates:
            return []

        def _looks_fake_authors(auth_list: List[str]) -> bool:
            joined = " ".join([a.lower() for a in auth_list if isinstance(a, str)])
            return any(x in joined for x in ["john doe", "jane smith", "foo bar", "test author"])

        valid: List[dict] = []
        for p in candidates:
            title = (p.get("title") or "").strip()
            if len(title) < 8:
                continue
            authors_raw = p.get("authors", [])
            authors = []
            for a in authors_raw if isinstance(authors_raw, list) else []:
                if isinstance(a, dict):
                    name = a.get("name")
                else:
                    name = str(a)
                if name:
                    authors.append(name.strip())
            # Don't drop otherwise-good papers just because author metadata is missing.
            if _looks_fake_authors(authors):
                continue
            year = _safe_year(p.get("year"))
            if year is None:
                year = _safe_year(p.get("publicationYear"))
            valid.append(p)

        if not valid:
            return []

        topic_hint = " ".join(keywords[:8])
        scored = [(p, self.score_relevance(p, topic_hint)) for p in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        external_refs: List[ExternalReference] = []
        for p, score in scored:
            authors = []
            for author in p.get("authors", []) if isinstance(p.get("authors", []), list) else []:
                if isinstance(author, dict):
                    authors.append(author.get("name", "Unknown"))
                else:
                    authors.append(str(author))
            external_ids = p.get("externalIds", {})
            doi = None
            if isinstance(external_ids, dict):
                doi = external_ids.get("DOI")

            journal_name = None
            journal_obj = p.get("journal")
            if isinstance(journal_obj, dict):
                journal_name = journal_obj.get("name")

            publisher_name = None
            pub_venue = p.get("publicationVenue")
            if isinstance(pub_venue, dict):
                publisher_name = pub_venue.get("publisher")
                if not journal_name:
                    journal_name = pub_venue.get("name")

            ref = ExternalReference(
                citation_number=0,
                title=p.get("title", "Untitled"),
                authors=[a for a in authors if a and a != "Unknown"] or ["Unknown"],
                year=_safe_year(p.get("year")) or max(min(int(year_range[1]), datetime.now().year), int(year_range[0])),
                venue=p.get("venue", "Unknown Venue"),
                journal=journal_name,
                publisher=publisher_name,
                abstract=p.get("abstract", "No abstract available."),
                doi=doi,
                url=p.get("url"),
                relevance_score=float(score),
                selected=True,
            )
            external_refs.append(ref)
            if len(external_refs) >= num_papers:
                break

        return external_refs
    
    def curate_external_refs(
        self,
        topic: str,
        article_text: str,
        local_citation_map: dict,
        num_refs: int = 10,
        year_range: tuple = (2018, 2025)
    ) -> List[ExternalReference]:
        """
        Fetch, deduplicate, score, and curate external references.
        
        Args:
            topic: Article topic
            article_text: Generated article text
            local_citation_map: Local corpus citation mapping
            num_refs: Target number of external refs
            year_range: (min_year, max_year)
            
        Returns:
            List of curated ExternalReference objects
        """
        # Fetch from Semantic Scholar (request more than needed for filtering)
        fetch_limit = min(num_refs * 3, 100)
        raw_papers = self.fetch_from_semantic_scholar(
            query=topic,
            limit=fetch_limit,
            year_range=year_range
        )
        
        if not raw_papers:
            return []
        
        # Deduplicate against local corpus
        deduplicated = self.deduplicate_against_corpus(raw_papers, local_citation_map)
        
        # Score relevance
        scored_papers = []
        for paper in deduplicated:
            score = self.score_relevance(paper, topic, article_text)
            scored_papers.append((paper, score))
        
        # Sort by relevance score (descending)
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N and convert to ExternalReference objects
        max_local_citation = max(local_citation_map.values()) if local_citation_map else 0
        external_refs = []
        
        for i, (paper, score) in enumerate(scored_papers[:num_refs]):
            # Extract authors
            authors = []
            for author in paper.get("authors", []):
                if isinstance(author, dict):
                    authors.append(author.get("name", "Unknown"))
                else:
                    authors.append(str(author))
            
            # Extract DOI
            doi = None
            external_ids = paper.get("externalIds", {})
            if isinstance(external_ids, dict):
                doi = external_ids.get("DOI")
            
            ref = ExternalReference(
                citation_number=max_local_citation + i + 1,
                title=paper.get("title", "Untitled"),
                authors=authors if authors else ["Unknown"],
                year=paper.get("year", 2024),
                venue=paper.get("venue", "Unknown Venue"),
                journal=(paper.get("journal", {}) or {}).get("name") if isinstance(paper.get("journal"), dict) else None,
                publisher=(paper.get("publicationVenue", {}) or {}).get("publisher") if isinstance(paper.get("publicationVenue"), dict) else None,
                abstract=paper.get("abstract", "No abstract available."),
                doi=doi,
                url=paper.get("url"),
                relevance_score=score,
                selected=True
            )
            external_refs.append(ref)
        
        return external_refs
