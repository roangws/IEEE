#!/usr/bin/env python3
"""Test semantic filtering functionality"""

from semantic_filter import SemanticFilter
from external_reference_fetcher import ExternalReference

# Create test references
test_refs = [
    ExternalReference(
        citation_number=40,
        title="Video Inpainting with Diffusion Models",
        authors=["Smith, J.", "Doe, J."],
        year=2024,
        venue="CVPR",
        abstract="We propose a novel diffusion-based approach for video inpainting...",
        url="http://example.com"
    ),
    ExternalReference(
        citation_number=41,
        title="Deep Learning for Video Restoration",
        authors=["Wang, L."],
        year=2023,
        venue="ICCV",
        abstract="A comprehensive survey of video restoration techniques...",
        url="http://example.com"
    )
]

print("Testing Semantic Filter...")
print("="*50)

filter = SemanticFilter()

# Test semantic similarity
query = "video inpainting using diffusion models"
semantic_results = filter.semantic_similarity_filter(query, test_refs)

print("\nSemantic similarity results:")
for ref, score in semantic_results:
    print(f"  [{ref.citation_number}] Score: {score:.3f} - {ref.title[:50]}...")

# Test comprehensive filter
article_text = "This paper presents a diffusion-based method for video inpainting..."
comprehensive_results = filter.comprehensive_filter(query, article_text, test_refs)

print("\nComprehensive filter results:")
for result in comprehensive_results:
    ref = result['reference']
    print(f"  [{ref.citation_number}] Overall: {result['overall_score']:.3f}")
    print(f"    Semantic: {result['semantic_score']:.3f}")
    print(f"    Method Compatible: {result['method_compatible']}")
    print(f"    Venue Tier: {result['venue_tier']}")

print("\n✅ Semantic filter test complete!")
