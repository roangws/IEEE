#!/usr/bin/env python3
"""
IEEE Article Pattern Analyzer
Extracts structural and writing patterns from IEEE-style articles using the vector DB.
"""

import json
import os
import re
import csv
import math
import random
import argparse
import time
from pathlib import Path
from collections import Counter, defaultdict
import statistics
from typing import Dict, List, Tuple, Optional

from concurrent.futures import ProcessPoolExecutor, as_completed

from qdrant_client import QdrantClient
from sklearn.cluster import KMeans
import numpy as np

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "academic_papers_full_specter2"
PDF_FOLDER = "downloaded_pdfs"
METADATA_FILE = "pdf_metadata.json"
OUTPUT_DIR = "output"

CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")
PROCESSED_IDS_PATH = os.path.join(CHECKPOINT_DIR, "processed_paper_ids.txt")

# Sample size calculation: min(40, max(20, round(sqrt(5805)))) = 40
ESTIMATED_PAPERS = 5805
SAMPLE_SIZE = min(40, max(20, round(math.sqrt(ESTIMATED_PAPERS))))
NUM_CLUSTERS = SAMPLE_SIZE  # One paper per cluster for max diversity


class IEEEPatternAnalyzer:
    """Analyzes IEEE article patterns for generation improvement."""
    
    # IEEE section detection patterns
    SECTION_PATTERNS = [
        (r'^\s*(?:abstract)\s*$', 'Abstract'),
        (r'^\s*(?:index\s+terms|keywords?|key\s+words)\s*[:\-—]?\s*', 'Keywords'),
        (r'^\s*(?:I\.|1\.?\s+)?(?:introduction)\s*$', 'Introduction'),
        (r'^\s*(?:II\.|2\.?\s+)?(?:related\s+work|literature\s+review|background|prior\s+work)\s*$', 'Related Work'),
        (r'^\s*(?:III\.|3\.?\s+)?(?:method(?:ology)?|approach|proposed\s+(?:method|approach|system)|system\s+(?:design|overview)|materials?\s+and\s+methods?)\s*$', 'Methodology'),
        (r'^\s*(?:IV\.|4\.?\s+)?(?:experiment(?:s|al)?(?:\s+(?:setup|results?))?|evaluation|implementation)\s*$', 'Experiments'),
        (r'^\s*(?:V\.|5\.?\s+)?(?:results?(?:\s+and\s+(?:discussion|analysis))?|findings)\s*$', 'Results'),
        (r'^\s*(?:VI\.|6\.?\s+)?(?:discussion|analysis)\s*$', 'Discussion'),
        (r'^\s*(?:VII\.|7\.?\s+)?(?:conclusion(?:s)?(?:\s+and\s+future\s+work)?|summary)\s*$', 'Conclusion'),
        (r'^\s*(?:VIII\.|8\.?\s+)?(?:future\s+work|limitations?(?:\s+and\s+future\s+work)?)\s*$', 'Future Work'),
        (r'^\s*(?:acknowledgment(?:s)?|acknowledgement(?:s)?)\s*$', 'Acknowledgment'),
        (r'^\s*(?:references|bibliography)\s*$', 'References'),
    ]
    
    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.metadata = self._load_metadata()
        self.papers_data = []
        self.analysis_results = []

    @staticmethod
    def _safe_int(x, default=None):
        try:
            return int(x)
        except Exception:
            return default
        
    def _load_metadata(self) -> Dict:
        """Load PDF metadata."""
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def sample_papers_via_clustering(self) -> List[Dict]:
        """
        Sample papers using embedding clustering for diversity.
        Retrieves embeddings, clusters them, and picks one paper per cluster.
        """
        print(f"Sampling {SAMPLE_SIZE} papers via clustering...")
        
        # Get a large candidate pool from the vector DB
        # We'll scroll through to get paper IDs and embeddings
        candidate_pool = []
        paper_ids_seen = set()
        
        # Scroll through the collection to get vectors
        scroll_result = self.client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,  # Get enough candidates
            with_vectors=True,
            with_payload=True
        )
        
        points = scroll_result[0]
        print(f"Retrieved {len(points)} vectors from DB")
        
        # Group by paper (filename)
        paper_embeddings = {}
        paper_chunks = defaultdict(list)
        
        for point in points:
            payload = point.payload
            filename = payload.get('filename', payload.get('paper_id', str(point.id)))
            
            if filename not in paper_embeddings:
                paper_embeddings[filename] = point.vector
                
            paper_chunks[filename].append({
                'chunk_text': payload.get('chunk_text', payload.get('text', '')),
                'chunk_index': payload.get('chunk_index', 0),
                'vector': point.vector
            })
        
        print(f"Found {len(paper_embeddings)} unique papers")
        
        # Prepare for clustering
        filenames = list(paper_embeddings.keys())
        embeddings = np.array([paper_embeddings[f] for f in filenames])
        
        # Cluster embeddings
        n_clusters = min(SAMPLE_SIZE, len(filenames))
        print(f"Clustering into {n_clusters} clusters...")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Select one paper per cluster (closest to centroid)
        selected_papers = []
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_embeddings = embeddings[cluster_indices]
            
            # Find paper closest to centroid
            centroid = kmeans.cluster_centers_[cluster_id]
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            best_idx = cluster_indices[np.argmin(distances)]
            
            filename = filenames[best_idx]
            chunks = paper_chunks[filename]
            
            # Reconstruct full text from chunks
            sorted_chunks = sorted(chunks, key=lambda x: x.get('chunk_index', 0))
            full_text = ' '.join([c['chunk_text'] for c in sorted_chunks])
            
            # Get metadata
            meta = self.metadata.get(filename, {})
            
            selected_papers.append({
                'paper_id': filename,
                'title': meta.get('title', 'Unknown'),
                'year': meta.get('year', 'Unknown'),
                'authors': meta.get('authors', 'Unknown'),
                'full_text': full_text,
                'cluster_id': cluster_id,
                'source_path': meta.get('path', f'{PDF_FOLDER}/{filename}')
            })
        
        print(f"Selected {len(selected_papers)} papers across {n_clusters} clusters")
        return selected_papers

    def iter_unique_papers_from_qdrant(self) -> List[str]:
        """Return all unique paper IDs (filenames) from Qdrant payloads."""
        seen = set()
        unique = []

        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=10000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            if not points:
                break

            for p in points:
                filename = (p.payload or {}).get("filename")
                if not filename:
                    continue
                if filename in seen:
                    continue
                seen.add(filename)
                unique.append(filename)

            if offset is None:
                break

        return unique
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF if available."""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                return text
        except Exception as e:
            return None
    
    def analyze_paper(self, paper: Dict) -> Dict:
        """Analyze a single paper for IEEE patterns."""
        text = paper['full_text']
        
        # ALWAYS try to get text from PDF first - chunks are incomplete
        pdf_path = paper.get('source_path', '')
        if not pdf_path or not os.path.exists(pdf_path):
            # Try alternative path
            pdf_path = os.path.join(PDF_FOLDER, paper['paper_id'])
        
        if pdf_path and os.path.exists(pdf_path):
            pdf_text = self.extract_text_from_pdf(pdf_path)
            if pdf_text and len(pdf_text) > 500:  # Use PDF if substantial
                text = pdf_text
        
        result = {
            'paper_id': paper['paper_id'],
            'title': paper['title'],
            'year': paper['year'],
            'cluster_id': paper.get('cluster_id', -1),
            'source_path': paper.get('source_path', ''),
        }
        
        # A) Structure / sections
        sections = self._extract_sections(text)
        result['sections'] = sections
        result['section_list'] = [s['name'] for s in sections]
        result['num_sections'] = len([s for s in sections if s['level'] == 1])
        result['num_subsections'] = len([s for s in sections if s['level'] > 1])
        
        # Track subsections with their full numbering and titles
        result['subsection_patterns'] = [
            f"{s.get('section_number', '')}: {s['name']}" 
            for s in sections 
            if s['level'] > 1 and s.get('section_number')
        ]

        section_word_counts = self._compute_section_word_counts(text, sections)
        result['section_word_counts'] = section_word_counts
        result['section_words_abstract'] = section_word_counts.get('Abstract', 0)
        result['section_words_introduction'] = section_word_counts.get('Introduction', 0)
        result['section_words_related_work'] = section_word_counts.get('Related Work', 0)
        result['section_words_methodology'] = section_word_counts.get('Methodology', 0)
        result['section_words_experiments'] = section_word_counts.get('Experiments', 0)
        result['section_words_results'] = section_word_counts.get('Results', 0)
        result['section_words_discussion'] = section_word_counts.get('Discussion', 0)
        result['section_words_conclusion'] = section_word_counts.get('Conclusion', 0)
        
        # Detect presence of key components
        section_names_lower = [s['name'].lower() for s in sections]
        result['has_abstract'] = any('abstract' in s for s in section_names_lower)
        result['has_keywords'] = any('keyword' in s or 'index term' in s for s in section_names_lower)
        result['has_introduction'] = any('introduction' in s for s in section_names_lower)
        result['has_related_work'] = any('related' in s or 'background' in s or 'literature' in s for s in section_names_lower)
        result['has_methodology'] = any('method' in s or 'approach' in s or 'proposed' in s for s in section_names_lower)
        result['has_experiments'] = any('experiment' in s or 'evaluation' in s for s in section_names_lower)
        result['has_results'] = any('result' in s for s in section_names_lower)
        result['has_discussion'] = any('discussion' in s for s in section_names_lower)
        result['has_conclusion'] = any('conclusion' in s or 'summary' in s for s in section_names_lower)
        result['has_acknowledgment'] = any('acknowledgment' in s or 'acknowledgement' in s for s in section_names_lower)
        result['has_references'] = any('reference' in s or 'bibliography' in s for s in section_names_lower)
        
        # B) Length / style
        result['word_count_total'] = len(text.split())
        result['abstract_words'] = self._count_abstract_words(text)
        
        sentences = self._split_sentences(text)
        result['num_sentences'] = len(sentences)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        result['avg_sentence_len'] = statistics.mean(sentence_lengths) if sentence_lengths else 0
        result['median_sentence_len'] = statistics.median(sentence_lengths) if sentence_lengths else 0
        
        paragraphs = self._split_paragraphs(text)
        result['num_paragraphs'] = len(paragraphs)
        para_lengths = [len(p.split()) for p in paragraphs if p.strip()]
        result['avg_paragraph_len'] = statistics.mean(para_lengths) if para_lengths else 0
        
        # Figure/table counts
        result['figure_mentions'] = len(re.findall(r'\b(?:Fig\.?|Figure)\s*\d+', text, re.IGNORECASE))
        result['table_mentions'] = len(re.findall(r'\bTable\s*\d+', text, re.IGNORECASE))
        
        # C) Citations and references
        citations = self._extract_citations(text)
        result['in_text_citations'] = len(citations)
        result['unique_citations'] = len(set(citations))
        result['max_citation_num'] = max(citations) if citations else 0
        
        ref_count = self._count_references(text)
        result['num_references'] = ref_count
        result['refs_per_1k_words'] = (ref_count / result['word_count_total'] * 1000) if result['word_count_total'] > 0 else 0
        
        # Citation range patterns
        result['has_citation_ranges'] = bool(re.search(r'\[\d+\]\s*[-–—]\s*\[\d+\]|\[\d+[-–—]\d+\]', text))
        
        return result

    @classmethod
    def analyze_pdf_worker(cls, payload: Dict) -> Dict:
        """Process worker: extract text from PDF and compute metrics."""
        paper_id = payload["paper_id"]
        source_path = payload.get("source_path")
        title = payload.get("title", "Unknown")
        year = payload.get("year", "Unknown")

        analyzer = cls.__new__(cls)
        # Only need methods/regex; avoid Qdrant initialization in worker.

        # Load PDF
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(source_path) as pdf:
                parts = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        parts.append(t)
                text = "\n".join(parts)
        except Exception:
            text = ""

        if not text:
            return {
                "paper_id": paper_id,
                "title": title,
                "year": year,
                "source_path": source_path,
                "error": "pdf_extract_failed",
            }

        # Reuse parsing helpers
        result = {
            "paper_id": paper_id,
            "title": title,
            "year": year,
            "cluster_id": payload.get("cluster_id", "full"),
            "source_path": source_path,
        }

        sections = cls._extract_sections(analyzer, text)
        result["sections"] = sections
        result["section_list"] = [s["name"] for s in sections]
        result["num_sections"] = len([s for s in sections if s["level"] == 1])
        result["num_subsections"] = len([s for s in sections if s["level"] > 1])

        section_word_counts = cls._compute_section_word_counts(analyzer, text, sections)
        result["section_word_counts"] = section_word_counts
        result["section_words_abstract"] = section_word_counts.get("Abstract", 0)
        result["section_words_introduction"] = section_word_counts.get("Introduction", 0)
        result["section_words_related_work"] = section_word_counts.get("Related Work", 0)
        result["section_words_methodology"] = section_word_counts.get("Methodology", 0)
        result["section_words_experiments"] = section_word_counts.get("Experiments", 0)
        result["section_words_results"] = section_word_counts.get("Results", 0)
        result["section_words_discussion"] = section_word_counts.get("Discussion", 0)
        result["section_words_conclusion"] = section_word_counts.get("Conclusion", 0)

        section_names_lower = [s["name"].lower() for s in sections]
        result["has_abstract"] = any("abstract" in s for s in section_names_lower)
        result["has_keywords"] = any("keyword" in s or "index term" in s for s in section_names_lower)
        result["has_introduction"] = any("introduction" in s for s in section_names_lower)
        result["has_related_work"] = any("related" in s or "background" in s or "literature" in s for s in section_names_lower)
        result["has_methodology"] = any("method" in s or "approach" in s or "proposed" in s for s in section_names_lower)
        result["has_experiments"] = any("experiment" in s or "evaluation" in s for s in section_names_lower)
        result["has_results"] = any("result" in s for s in section_names_lower)
        result["has_discussion"] = any("discussion" in s for s in section_names_lower)
        result["has_conclusion"] = any("conclusion" in s or "summary" in s for s in section_names_lower)
        result["has_acknowledgment"] = any("acknowledgment" in s or "acknowledgement" in s for s in section_names_lower)
        result["has_references"] = any("reference" in s or "bibliography" in s for s in section_names_lower)

        result["word_count_total"] = len(text.split())
        result["abstract_words"] = cls._count_abstract_words(analyzer, text)

        sentences = cls._split_sentences(analyzer, text)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        result["num_sentences"] = len(sentences)
        result["avg_sentence_len"] = statistics.mean(sentence_lengths) if sentence_lengths else 0
        result["median_sentence_len"] = statistics.median(sentence_lengths) if sentence_lengths else 0

        paragraphs = cls._split_paragraphs(analyzer, text)
        para_lengths = [len(p.split()) for p in paragraphs if p.strip()]
        result["num_paragraphs"] = len(paragraphs)
        result["avg_paragraph_len"] = statistics.mean(para_lengths) if para_lengths else 0

        result["figure_mentions"] = len(re.findall(r"\b(?:Fig\.?|Figure)\s*\d+", text, re.IGNORECASE))
        result["table_mentions"] = len(re.findall(r"\bTable\s*\d+", text, re.IGNORECASE))

        citations = cls._extract_citations(analyzer, text)
        result["in_text_citations"] = len(citations)
        result["unique_citations"] = len(set(citations))
        result["max_citation_num"] = max(citations) if citations else 0

        ref_count = cls._count_references(analyzer, text)
        result["num_references"] = ref_count
        result["refs_per_1k_words"] = (ref_count / result["word_count_total"] * 1000) if result["word_count_total"] > 0 else 0
        
        result["has_citation_ranges"] = bool(re.search(r'\[\d+\]\s*[-–—]\s*\[\d+\]|\[\d+[-–—]\d+\]', text))
        
        # Track subsections with their full numbering and titles
        result['subsection_patterns'] = [
            f"{s.get('section_number', '')}: {s['name']}" 
            for s in sections 
            if s['level'] > 1 and s.get('section_number')
        ]
        
        return result

    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract section headers from text, including subsections."""
        lines = text.split('\n')
        sections = []
        
        # Patterns for section headers
        numbered_pattern = r'^([IVX0-9]+\.?(?:\.[0-9]+)*)[\s\-—]*(.+)$'
        roman_pattern = r'^([IVX]+)\.?[\s\-—]*(.+)$'
        caps_pattern = r'^[A-Z][A-Z\s]+$'
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) > 100:  # Skip empty or very long lines
                continue
            
            level = 1
            name = None
            section_number = None
            
            # Check roman numeral
            match = re.match(roman_pattern, line)
            if match:
                name = match.group(2).strip()
                section_number = match.group(1)
                level = 1
            
            # Check numbered sections (including subsections like 4.1, 4.2)
            if not name:
                match = re.match(numbered_pattern, line)
                if match:
                    num = match.group(1)
                    name = match.group(2).strip()
                    section_number = num.rstrip('.')
                    # Count dots to determine level: "4" = level 1, "4.1" = level 2, "4.1.1" = level 3
                    level = section_number.count('.') + 1
            
            # Check ALL CAPS
            if not name:
                match = re.match(caps_pattern, line)
                if match and len(line.split()) <= 5:
                    name = line.title()
                    level = 1
            
            # Check known section patterns
            if not name:
                for pattern, canonical in self.SECTION_PATTERNS:
                    if re.match(pattern, line, re.IGNORECASE):
                        name = canonical
                        level = 1
                        break
            
            if name and len(name) > 2:
                sections.append({
                    'name': name,
                    'level': level,
                    'line_num': i,
                    'section_number': section_number
                })
        
        return sections

    def _normalize_section_name(self, name: str) -> Optional[str]:
        if not name:
            return None
        s_lower = name.lower()
        if 'abstract' in s_lower:
            return 'Abstract'
        if 'keyword' in s_lower or 'index term' in s_lower:
            return 'Keywords'
        if 'introduction' in s_lower:
            return 'Introduction'
        if 'related' in s_lower or 'background' in s_lower or 'literature' in s_lower or 'context' in s_lower:
            return 'Related Work'
        if 'method' in s_lower or 'approach' in s_lower or 'proposed' in s_lower or 'materials and methods' in s_lower:
            return 'Methodology'
        if 'experiment' in s_lower or 'evaluation' in s_lower or 'implementation' in s_lower:
            return 'Experiments'
        if 'result' in s_lower or 'finding' in s_lower:
            return 'Results'
        if 'discussion' in s_lower or 'analysis' in s_lower:
            return 'Discussion'
        if 'conclusion' in s_lower or 'summary' in s_lower:
            return 'Conclusion'
        if 'future' in s_lower:
            return 'Future Work'
        if 'acknowledgment' in s_lower or 'acknowledgement' in s_lower:
            return 'Acknowledgment'
        if 'reference' in s_lower or 'bibliography' in s_lower:
            return 'References'
        return None

    def _compute_section_word_counts(self, text: str, sections: List[Dict]) -> Dict[str, int]:
        lines = text.split('\n')
        headers = []
        for s in sections or []:
            try:
                ln = int(s.get('line_num', -1))
            except Exception:
                ln = -1
            if ln < 0:
                continue
            canonical = self._normalize_section_name(s.get('name', ''))
            if not canonical:
                continue
            headers.append((ln, canonical))

        if not headers:
            return {}

        headers.sort(key=lambda x: x[0])
        counts: Dict[str, int] = {}
        for idx, (start_ln, canonical) in enumerate(headers):
            end_ln = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
            if end_ln <= start_ln:
                continue
            body_lines = lines[start_ln + 1:end_ln]
            body_text = "\n".join(body_lines).strip()
            w = len(body_text.split()) if body_text else 0
            counts[canonical] = counts.get(canonical, 0) + w

        return counts
    
    def _count_abstract_words(self, text: str) -> int:
        abstract_match = re.search(
            r'(?:^|\n)\s*(?:Abstract|ABSTRACT)[:\s\-—]*\n?(.*?)(?=\n\s*(?:[IVX]+\.|1\.|Introduction|INTRODUCTION|Index\s+Terms|Keywords)|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            return len(abstract_text.split())
        return 0
    
    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip() and len(p.split()) > 10]
    
    def _extract_citations(self, text: str) -> List[int]:
        citations = []
        single = re.findall(r'\[(\d+)\]', text)
        citations.extend([int(c) for c in single])
        ranges = re.findall(r'\[(\d+)\]\s*[-–—]\s*\[(\d+)\]|\[(\d+)[-–—](\d+)\]', text)
        for match in ranges:
            start = int(match[0] or match[2])
            end = int(match[1] or match[3])
            citations.extend(range(start, end + 1))
        return citations
    
    def _count_references(self, text: str) -> int:
        ref_match = re.search(
            r'(?:^|\n)\s*(?:References|REFERENCES|Bibliography)\s*\n(.*?)(?:\n\s*(?:Appendix|APPENDIX)|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if ref_match:
            ref_text = ref_match.group(1)
            ref_lines = [line.strip() for line in ref_text.split('\n') if line.strip()]
            bracket_refs = len(re.findall(r'^\[\d+\]', '\n'.join(ref_lines), re.MULTILINE))
            if bracket_refs > 0:
                return bracket_refs
            numbered_refs = len([line for line in ref_lines if re.match(r'^\d+[\.\)]\s+', line)])
            return numbered_refs if numbered_refs > 0 else max(1, len(ref_lines) // 3)
        return 0

    def run_analysis(self):
        """Run the full analysis pipeline."""
        print("=" * 60)
        print("IEEE Article Pattern Analyzer")
        print("=" * 60)
        print(f"Sample size: {SAMPLE_SIZE} (sqrt({ESTIMATED_PAPERS}) ≈ 76, capped at 40)")
        print()
        
        # Sample papers
        self.papers_data = self.sample_papers_via_clustering()
        
        # Analyze each paper
        print("\nAnalyzing papers...")
        for i, paper in enumerate(self.papers_data):
            print(f"  [{i+1}/{len(self.papers_data)}] {paper['title'][:50]}...")
            result = self.analyze_paper(paper)
            self.analysis_results.append(result)
        
        # Generate outputs
        self._write_manifest()
        self._write_patterns_table()
        self._write_patterns_summary()
        
        print("\n" + "=" * 60)
        print("Analysis complete!")
        print("=" * 60)

    def run_full_corpus_parallel(self, workers: int = 8, resume: bool = True):
        """Run analysis on full corpus using parallel processing."""
        print("=" * 60)
        print("IEEE Full Corpus Pattern Analyzer (Parallel)")
        print("=" * 60)
        
        # Get all PDF files from downloaded_pdfs directory
        all_papers = []
        pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            paper_id = pdf_file.replace('.pdf', '')
            all_papers.append({
                'paper_id': paper_id,
                'title': paper_id,
                'year': 'Unknown',
                'source_path': os.path.join(PDF_FOLDER, pdf_file),
                'full_text': ''
            })
        
        print(f"Found {len(all_papers)} PDF files in {PDF_FOLDER}")
        
        # Resume logic
        processed_ids = set()
        if resume and os.path.exists(PROCESSED_IDS_PATH):
            with open(PROCESSED_IDS_PATH, 'r') as f:
                processed_ids = set(line.strip() for line in f if line.strip())
            print(f"Resume enabled: {len(processed_ids)} already processed")
        
        # Filter to unprocessed
        papers_to_process = [p for p in all_papers if p['paper_id'] not in processed_ids]
        print(f"Queued {len(papers_to_process)} papers for processing (workers={workers})")
        
        if len(papers_to_process) == 0:
            print("No new papers to process. Loading existing results...")
            self._load_existing_results()
            self._write_patterns_summary()
            section_table_path = os.path.join(OUTPUT_DIR, 'ieee_section_stats_table.csv')
            section_summary_path = os.path.join(OUTPUT_DIR, 'ieee_section_stats_summary.json')
            self._write_section_stats_summary(section_table_path, section_summary_path)
            return
        
        # Parallel processing
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        table_path = os.path.join(OUTPUT_DIR, 'ieee_patterns_table.csv')
        section_table_path = os.path.join(OUTPUT_DIR, 'ieee_section_stats_table.csv')
        subsection_patterns_path = os.path.join(OUTPUT_DIR, 'ieee_subsection_patterns.jsonl')
        
        # Write headers if new file
        if not os.path.exists(table_path):
            with open(table_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'paper_id', 'title', 'year', 'word_count_total', 'abstract_words',
                    'num_sections', 'section_list', 'num_subsections', 'in_text_citations', 'num_references',
                    'refs_per_1k_words', 'avg_sentence_len', 'avg_paragraph_len'
                ])
        
        if not os.path.exists(section_table_path):
            with open(section_table_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'paper_id', 'title', 'year',
                    'section_words_abstract', 'section_words_introduction',
                    'section_words_related_work', 'section_words_methodology',
                    'section_words_experiments', 'section_words_results',
                    'section_words_discussion', 'section_words_conclusion'
                ])
        
        from multiprocessing import Pool
        with Pool(processes=workers) as pool:
            results = pool.map(self.analyze_pdf_worker, papers_to_process)
        
        # Write results incrementally
        with open(table_path, 'a', newline='') as f, \
             open(section_table_path, 'a', newline='') as f_sec, \
             open(subsection_patterns_path, 'a') as f_subsec, \
             open(PROCESSED_IDS_PATH, 'a') as f_ids:
            writer = csv.writer(f)
            writer_sec = csv.writer(f_sec)
            
            for result in results:
                if not result or 'error' in result:
                    # Skip failed extractions
                    if result:
                        f_ids.write(f"{result['paper_id']}\n")
                    continue
                
                writer.writerow([
                    result['paper_id'], result['title'], result['year'],
                    result['word_count_total'], result['abstract_words'],
                    result['num_sections'], '|'.join(result['section_list']),
                    result['num_subsections'], result['in_text_citations'],
                    result['num_references'], round(result['refs_per_1k_words'], 2),
                    round(result['avg_sentence_len'], 1), round(result['avg_paragraph_len'], 1)
                ])
                
                writer_sec.writerow([
                    result['paper_id'], result['title'], result['year'],
                    result.get('section_words_abstract', 0),
                    result.get('section_words_introduction', 0),
                    result.get('section_words_related_work', 0),
                    result.get('section_words_methodology', 0),
                    result.get('section_words_experiments', 0),
                    result.get('section_words_results', 0),
                    result.get('section_words_discussion', 0),
                    result.get('section_words_conclusion', 0)
                ])
                
                # Write subsection patterns as JSONL
                if result.get('subsection_patterns'):
                    f_subsec.write(json.dumps({
                        'paper_id': result['paper_id'],
                        'subsections': result['subsection_patterns']
                    }) + '\n')
                
                f_ids.write(f"{result['paper_id']}\n")
        
        print(f"\nProcessed {len(results)} papers")
        
        # Load all results and generate summary
        print("Loading results from CSV for summary generation...")
        self._load_existing_results()
        print(f"Loaded {len(self.analysis_results)} results")
        
        if len(self.analysis_results) > 0:
            self._write_patterns_summary()
            section_summary_path = os.path.join(OUTPUT_DIR, 'ieee_section_stats_summary.json')
            self._write_section_stats_summary(section_table_path, section_summary_path)
        else:
            print("Warning: No results loaded, skipping summary generation")

    def _load_existing_results(self):
        """Load existing results from CSV for summary generation."""
        table_path = os.path.join(OUTPUT_DIR, 'ieee_patterns_table.csv')
        if not os.path.exists(table_path):
            return
        
        self.analysis_results = []
        with open(table_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("paper_id"):
                    continue
                self.analysis_results.append({
                    'paper_id': row['paper_id'],
                    'title': row['title'],
                    'year': row['year'],
                    'word_count_total': int(float(row.get('word_count_total', 0))),
                    'abstract_words': int(float(row.get('abstract_words', 0))),
                    'num_sections': int(float(row.get('num_sections', 0))),
                    'section_list': row.get('section_list', '').split('|') if row.get('section_list') else [],
                    'num_subsections': int(float(row.get('num_subsections', 0))),
                    'in_text_citations': int(float(row.get('in_text_citations', 0))),
                    'num_references': int(float(row.get('num_references', 0))),
                    'refs_per_1k_words': float(row.get('refs_per_1k_words', 0)),
                    'avg_sentence_len': float(row.get('avg_sentence_len', 0)),
                    'avg_paragraph_len': float(row.get('avg_paragraph_len', 0)),
                    'has_abstract': False,
                    'has_keywords': False,
                    'has_introduction': False,
                    'has_related_work': False,
                    'has_methodology': False,
                    'has_experiments': False,
                    'has_results': False,
                    'has_discussion': False,
                    'has_conclusion': False,
                    'has_acknowledgment': False,
                    'has_references': False,
                    'figure_mentions': 0,
                    'table_mentions': 0,
                    'has_citation_ranges': False,
                    'subsection_patterns': []
                })

    def _write_manifest(self):
        """Write sample manifest CSV."""
        manifest_path = os.path.join(OUTPUT_DIR, 'ieee_sample_manifest.csv')
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['paper_id', 'title', 'year', 'source_path_or_url', 'cluster_id_or_sampling_note'])
            
            for paper in self.papers_data:
                writer.writerow([
                    paper['paper_id'],
                    paper['title'],
                    paper['year'],
                    paper.get('source_path', ''),
                    paper.get('cluster_id', 'N/A')
                ])
        
        print(f"Wrote sample manifest: {manifest_path}")

    def _write_patterns_table(self):
        """Write patterns table CSV."""
        table_path = os.path.join(OUTPUT_DIR, 'ieee_patterns_table.csv')
        
        with open(table_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'paper_id', 'title', 'year', 'word_count_total', 'abstract_words',
                'num_sections', 'section_list', 'num_subsections', 'in_text_citations', 'num_references',
                'refs_per_1k_words', 'avg_sentence_len', 'avg_paragraph_len'
            ])
            
            for r in self.analysis_results:
                writer.writerow([
                    r['paper_id'],
                    r['title'],
                    r['year'],
                    r['word_count_total'],
                    r['abstract_words'],
                    r['num_sections'],
                    '|'.join(r['section_list']),
                    r['num_subsections'],
                    r['in_text_citations'],
                    r['num_references'],
                    round(r['refs_per_1k_words'], 2),
                    round(r['avg_sentence_len'], 1),
                    round(r['avg_paragraph_len'], 1)
                ])
        
        print(f"Wrote patterns table: {table_path}")

    def _write_section_stats_summary(self, section_table_path: str, section_summary_path: str):
        if not os.path.exists(section_table_path):
            return

        rows = []
        with open(section_table_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get("paper_id"):
                    rows.append(row)

        def _to_int(v):
            try:
                return int(float(v))
            except Exception:
                return 0

        def safe_stats(values):
            values = [v for v in values if v > 0]
            if not values:
                return {'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'p10': 0, 'p90': 0}
            values_sorted = sorted(values)
            n = len(values_sorted)
            p10 = values_sorted[max(0, int(round(0.10 * (n - 1))))]
            p90 = values_sorted[max(0, int(round(0.90 * (n - 1))))]
            return {
                'min': int(min(values_sorted)),
                'max': int(max(values_sorted)),
                'mean': round(statistics.mean(values_sorted), 1),
                'median': round(statistics.median(values_sorted), 1),
                'p10': int(p10),
                'p90': int(p90),
            }

        section_keys = [
            ("Abstract", "section_words_abstract"),
            ("Introduction", "section_words_introduction"),
            ("Related Work", "section_words_related_work"),
            ("Methodology", "section_words_methodology"),
            ("Experiments", "section_words_experiments"),
            ("Results", "section_words_results"),
            ("Discussion", "section_words_discussion"),
            ("Conclusion", "section_words_conclusion"),
        ]

        distributions = {}
        presence = {}
        total = max(len(rows), 1)
        for label, col in section_keys:
            vals = [_to_int(r.get(col)) for r in rows]
            distributions[label] = safe_stats(vals)
            presence[label] = round(100.0 * (sum(1 for v in vals if v > 0) / total), 1)

        summary = {
            'papers_analyzed': len(rows),
            'section_word_distributions': distributions,
            'section_presence_rates': presence,
        }

        with open(section_summary_path, "w") as f:
            json.dump(summary, f, indent=2)
    
    def _write_patterns_summary(self):
        """Write patterns summary JSON."""
        summary_path = os.path.join(OUTPUT_DIR, 'ieee_patterns_summary.json')
        
        # Calculate distributions
        word_counts = [r['word_count_total'] for r in self.analysis_results]
        abstract_lengths = [r['abstract_words'] for r in self.analysis_results if r['abstract_words'] > 0]
        ref_counts = [r['num_references'] for r in self.analysis_results if r['num_references'] > 0]
        citation_counts = [r['in_text_citations'] for r in self.analysis_results]
        section_counts = [r['num_sections'] for r in self.analysis_results]
        sentence_lens = [r['avg_sentence_len'] for r in self.analysis_results if r['avg_sentence_len'] > 0]
        para_lens = [r['avg_paragraph_len'] for r in self.analysis_results if r['avg_paragraph_len'] > 0]
        refs_per_1k = [r['refs_per_1k_words'] for r in self.analysis_results if r['refs_per_1k_words'] > 0]
        
        # Component presence rates
        presence_rates = {
            'abstract': sum(1 for r in self.analysis_results if r['has_abstract']) / len(self.analysis_results),
            'keywords': sum(1 for r in self.analysis_results if r['has_keywords']) / len(self.analysis_results),
            'introduction': sum(1 for r in self.analysis_results if r['has_introduction']) / len(self.analysis_results),
            'related_work': sum(1 for r in self.analysis_results if r['has_related_work']) / len(self.analysis_results),
            'methodology': sum(1 for r in self.analysis_results if r['has_methodology']) / len(self.analysis_results),
            'experiments': sum(1 for r in self.analysis_results if r['has_experiments']) / len(self.analysis_results),
            'results': sum(1 for r in self.analysis_results if r['has_results']) / len(self.analysis_results),
            'discussion': sum(1 for r in self.analysis_results if r['has_discussion']) / len(self.analysis_results),
            'conclusion': sum(1 for r in self.analysis_results if r['has_conclusion']) / len(self.analysis_results),
            'acknowledgment': sum(1 for r in self.analysis_results if r['has_acknowledgment']) / len(self.analysis_results),
            'references': sum(1 for r in self.analysis_results if r['has_references']) / len(self.analysis_results),
        }
        
        # Section sequence analysis
        section_sequences = Counter()
        for r in self.analysis_results:
            # Normalize section names
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
        
        # Subsection pattern analysis - load from JSONL file
        subsection_patterns = Counter()
        subsection_patterns_path = os.path.join(OUTPUT_DIR, 'ieee_subsection_patterns.jsonl')
        if os.path.exists(subsection_patterns_path):
            with open(subsection_patterns_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            for subsec in data.get('subsections', []):
                                subsection_patterns[subsec] += 1
                        except Exception:
                            pass
        
        # Section name variants
        section_variants = defaultdict(list)
        for r in self.analysis_results:
            for s in r['section_list']:
                s_lower = s.lower()
                if 'method' in s_lower or 'approach' in s_lower:
                    if s not in section_variants['Methodology']:
                        section_variants['Methodology'].append(s)
                elif 'related' in s_lower or 'background' in s_lower:
                    if s not in section_variants['Related Work']:
                        section_variants['Related Work'].append(s)
                elif 'result' in s_lower:
                    if s not in section_variants['Results']:
                        section_variants['Results'].append(s)
                elif 'experiment' in s_lower:
                    if s not in section_variants['Experiments']:
                        section_variants['Experiments'].append(s)
        
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
        
        summary = {
            'corpus_stats': {
                'papers_analyzed': len(self.analysis_results),
                'sampling_rule': f'min(40, max(20, sqrt({ESTIMATED_PAPERS}))) = {SAMPLE_SIZE}',
                'sampling_method': 'KMeans clustering on SPECTER2 embeddings',
                'num_clusters': NUM_CLUSTERS
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
            'component_presence_rates': {k: round(v * 100, 1) for k, v in presence_rates.items()},
            'common_section_templates': [
                {'template': t, 'frequency': c}
                for t, c in section_sequences.most_common(5)
            ],
            'section_name_variants': dict(section_variants),
            'common_subsection_patterns': [
                {'subsection': pattern, 'frequency': count, 'percentage': round(count / len(self.analysis_results) * 100, 1)}
                for pattern, count in subsection_patterns.most_common(50)
            ],
            'recommended_constraints': {
                'abstract_words': {
                    'min': 100,
                    'target': round(statistics.mean(abstract_lengths)) if abstract_lengths else 200,
                    'max': 300
                },
                'total_words': {
                    'min': max(1500, int(safe_stats(word_counts)['mean'] * 0.6)),
                    'target': int(safe_stats(word_counts)['mean']),
                    'max': int(safe_stats(word_counts)['mean'] * 1.5)
                },
                'num_references': {
                    'min': max(10, int(safe_stats(ref_counts)['mean'] * 0.5)),
                    'target': int(safe_stats(ref_counts)['mean']),
                    'max': int(safe_stats(ref_counts)['max'])
                },
                'refs_per_1k_words': {
                    'min': max(3, round(safe_stats(refs_per_1k)['mean'] * 0.5, 1)),
                    'target': round(safe_stats(refs_per_1k)['mean'], 1),
                    'max': round(safe_stats(refs_per_1k)['max'], 1)
                },
                'num_sections': {
                    'min': 5,
                    'target': int(safe_stats(section_counts)['median']),
                    'max': 12
                }
            },
            'figure_table_stats': {
                'papers_with_figures': sum(1 for r in self.analysis_results if r['figure_mentions'] > 0),
                'avg_figures': round(statistics.mean([r['figure_mentions'] for r in self.analysis_results]), 1),
                'papers_with_tables': sum(1 for r in self.analysis_results if r['table_mentions'] > 0),
                'avg_tables': round(statistics.mean([r['table_mentions'] for r in self.analysis_results]), 1),
            },
            'citation_style': {
                'papers_with_citation_ranges': sum(1 for r in self.analysis_results if r['has_citation_ranges']),
                'format': 'IEEE bracket style [N] or ranges [N]-[M]'
            }
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Wrote patterns summary: {summary_path}")
        
        # Print key findings
        print("\n" + "=" * 60)
        print("KEY FINDINGS")
        print("=" * 60)
        print(f"\nWord Count: {safe_stats(word_counts)['mean']:.0f} avg (range: {safe_stats(word_counts)['min']}-{safe_stats(word_counts)['max']})")
        print(f"Abstract Length: {safe_stats(abstract_lengths)['mean']:.0f} words avg")
        print(f"References: {safe_stats(ref_counts)['mean']:.0f} avg ({safe_stats(refs_per_1k)['mean']:.1f} per 1k words)")
        print(f"In-text Citations: {safe_stats(citation_counts)['mean']:.0f} avg")
        print(f"Sections: {safe_stats(section_counts)['mean']:.0f} avg")
        print(f"\nComponent Presence Rates:")
        for k, v in sorted(presence_rates.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v*100:.0f}%")
        
        print(f"\nTop Section Templates:")
        for i, (template, count) in enumerate(section_sequences.most_common(3)):
            print(f"  {i+1}. {template} ({count} papers)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="IEEE Article Pattern Analyzer")
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    analyzer = IEEEPatternAnalyzer()

    if args.mode == "full":
        analyzer.run_full_corpus_parallel(workers=args.workers, resume=(not args.no_resume))
    else:
        analyzer.run_analysis()
