"""
Query and Answer Module
Handles semantic search and question answering using Qdrant and Ollama.
"""

import os

# CRITICAL: Set up cache BEFORE importing any HF libraries
HF_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hf_cache")
os.makedirs(HF_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_CACHE_DIR, "transformers")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(HF_CACHE_DIR, "sentence_transformers")
os.environ["HF_TOKEN_PATH"] = os.path.join(HF_CACHE_DIR, "token")
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(HF_CACHE_DIR, "hub")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from config import call_ollama, call_claude, call_openai


class QueryEngine:
    """Handles semantic search and question answering."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "academic_papers_100_specter",
        model_name: str = "qwen3:8b"
    ):
        """
        Initialize the query engine.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of the Qdrant collection
            model_name: Ollama model name for generation
        """
        self.collection_name = collection_name
        self.model_name = model_name
        
        # Initialize embedding model (same as ingestion) - SPECTER2 base
        print("Loading embedding model (allenai/specter2_base)...")
        self.embedder = SentenceTransformer("allenai/specter2_base", cache_folder=HF_CACHE_DIR)
        
        # Initialize Qdrant client
        print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        print("Query engine ready!")
    
    def embed_query(self, query: str) -> List[float]:
        """
        Create embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        # Use search_query prefix for queries (different from document prefix)
        prefixed_query = "search_query: " + query
        embedding = self.embedder.encode(prefixed_query, show_progress_bar=False)
        return embedding.tolist()
    
    def search(self, query: str, top_k: int = 15) -> List[Dict]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        # Create query embedding
        query_vector = self.embed_query(query)
        
        # Search in Qdrant
        search_results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        ).points
        
        # Format results
        results = []
        for hit in search_results:
            results.append({
                'filename': hit.payload['filename'],
                'chunk_text': hit.payload['chunk_text'],
                'chunk_id': hit.payload['chunk_id'],
                'score': hit.score
            })
        
        return results
    
    def format_context(self, search_results: List[Dict]) -> str:
        """
        Format search results into context for LLM.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"[Source {i}: {result['filename']}]\n{result['chunk_text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def create_prompt(self, query: str, context: str) -> str:
        """
        Create a prompt for the LLM.
        
        Args:
            query: User's question
            context: Retrieved context from papers
            
        Returns:
            Complete prompt for LLM
        """
        prompt = f"""You are an expert research assistant analyzing academic papers. Answer the user's question based ONLY on the provided context from academic papers.

CRITICAL REQUIREMENTS:
1. You MUST cite sources using [Source X: Filename.pdf] format when referencing specific information
2. Every factual statement derived from the context must include a citation
3. Use the source numbers provided in the context (Source 1, Source 2, etc.)
4. If the context doesn't contain enough information to answer fully, clearly state that
5. Be precise and academic in your language
6. Synthesize information across multiple sources when relevant, citing each source
7. If sources contradict each other, mention the different perspectives with citations

EXAMPLE CITATIONS:
- "According to [Source 3: Smith2020.pdf], the method achieves 95% accuracy."
- "Multiple studies ([Source 1: Jones2019.pdf], [Source 2: Lee2021.pdf]) support this finding."

Context from academic papers:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def search_and_answer(
        self, 
        query: str, 
        top_k: int = 15,
        temperature: float = 0.7,
        model_type: str = "ollama"
    ) -> Dict:
        """
        Search for relevant chunks and generate an answer.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            temperature: LLM temperature
            model_type: Type of LLM to use (ollama, claude_sonnet, claude_opus, openai_gpt4o, openai_gpt4o_mini)
            
        Returns:
            Dictionary with 'answer' and 'sources' keys
        """
        # Search for relevant chunks
        search_results = self.search(query, top_k=top_k)
        
        if not search_results:
            return {
                'answer': "I couldn't find any relevant information in the academic papers to answer your question.",
                'sources': []
            }
        
        # Format context
        context = self.format_context(search_results)
        
        # Create prompt
        prompt = self.create_prompt(query, context)
        
        # Generate answer using selected LLM
        system_msg = "You are an expert research assistant analyzing academic papers. Provide accurate, detailed answers based on the provided context."
        
        try:
            if model_type == "ollama":
                answer = call_ollama(prompt, model=self.model_name, temperature=temperature)
            elif model_type == "claude_sonnet":
                answer = call_claude(prompt, model="claude-3-5-sonnet-20241022", temperature=temperature, system=system_msg)
            elif model_type == "claude_opus":
                answer = call_claude(prompt, model="claude-3-opus-20240229", temperature=temperature, system=system_msg)
            elif model_type == "openai_gpt4o":
                answer = call_openai(prompt, model="gpt-4o", temperature=temperature, system=system_msg)
            elif model_type == "openai_gpt4o_mini":
                answer = call_openai(prompt, model="gpt-4o-mini", temperature=temperature, system=system_msg)
            else:
                answer = call_ollama(prompt, model=self.model_name, temperature=temperature)
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"
        
        # Extract unique sources
        sources = []
        seen_files = set()
        for result in search_results:
            if result['filename'] not in seen_files:
                sources.append({
                    'filename': result['filename'],
                    'chunk_text': result['chunk_text'],
                    'score': result['score']
                })
                seen_files.add(result['filename'])
        
        return {
            'query': query,  # Store the query for PDF generation
            'answer': answer,
            'sources': sources,
            'all_chunks': search_results
        }
    
    def retrieve_for_synthesis(self, topic: str, top_k: int = 50) -> Tuple[str, List[Dict]]:
        """
        Retrieve context for article synthesis.
        
        Args:
            topic: Article topic
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (formatted_context, sources_list)
        """
        # Search for relevant chunks
        search_results = self.search(topic, top_k=top_k)
        
        # Format context with source labels
        context_parts = []
        for result in search_results:
            context_parts.append(
                f"[{result['filename']}]\n{result['chunk_text']}\n"
            )
        
        formatted_context = "\n---\n".join(context_parts)
        
        return formatted_context, search_results


# Global instance for easy import
_query_engine = None


def get_query_engine(**kwargs) -> QueryEngine:
    """
    Get or create the global query engine instance.
    
    Args:
        **kwargs: Arguments to pass to QueryEngine constructor
        
    Returns:
        QueryEngine instance
    """
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine(**kwargs)
    return _query_engine


def search_and_answer(query: str, **kwargs) -> Dict:
    """
    Convenience function for search and answer.
    
    Args:
        query: User's question
        **kwargs: Additional arguments for search_and_answer
        
    Returns:
        Dictionary with answer and sources
    """
    engine = get_query_engine()
    return engine.search_and_answer(query, **kwargs)


def retrieve_for_synthesis(topic: str, **kwargs) -> Tuple[str, List[Dict]]:
    """
    Convenience function for article synthesis retrieval.
    
    Args:
        topic: Article topic
        **kwargs: Additional arguments for retrieve_for_synthesis
        
    Returns:
        Tuple of (formatted_context, sources_list)
    """
    engine = get_query_engine()
    return engine.retrieve_for_synthesis(topic, **kwargs)


if __name__ == '__main__':
    # Test the query engine
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python query.py <your question>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print(f"\nQuestion: {query}\n")
    print("Searching and generating answer...\n")
    
    result = search_and_answer(query)
    
    print("="*70)
    print("ANSWER")
    print("="*70)
    print(result['answer'])
    print("\n" + "="*70)
    print("SOURCES")
    print("="*70)
    for i, source in enumerate(result['sources'][:5], 1):
        print(f"{i}. {source['filename']} (score: {source['score']:.3f})")
    print("="*70)
