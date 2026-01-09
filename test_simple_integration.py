#!/usr/bin/env python3
"""
Simplified test for external reference integration
Tests the core integration logic with local LLM
"""

import json
import re
import time


def mock_external_reference():
    """Mock ExternalReference class for testing."""
    class MockExternalRef:
        def __init__(self, citation_number, title, authors, year, venue, abstract):
            self.citation_number = citation_number
            self.title = title
            self.authors = authors
            self.year = year
            self.venue = venue
            self.abstract = abstract
            self.selected = True
        
        def to_ieee_format(self):
            authors_str = ", ".join(self.authors[:3])
            if len(self.authors) > 3:
                authors_str += " et al."
            return f"[{self.citation_number}] {authors_str}, \"{self.title},\" {self.venue}, {self.year}."
    
    return MockExternalRef


def call_ollama_simple(prompt, model="gemma3:27b", system=None):
    """Simple Ollama API call without dependencies."""
    import subprocess
    
    # Build command
    cmd = ["curl", "http://localhost:11434/api/generate", 
           "-H", "Content-Type: application/json",
           "-d", json.dumps({
               "model": model,
               "prompt": prompt,
               "system": system or "You are a helpful assistant.",
               "stream": False
           })]
    
    # Execute command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Ollama API error: {result.stderr}")
    
    # Parse response
    response = json.loads(result.stdout)
    return response.get("response", "")


def test_simple_integration():
    """Test integration with a simple section."""
    
    print("="*60)
    print("SIMPLE INTEGRATION TEST")
    print("="*60)
    
    # Test section with internal citations
    test_section = """## 2. Deep Learning Revolution

The introduction of deep learning, particularly convolutional neural networks (CNNs), has transformed medical image analysis [6]. CNNs can automatically learn hierarchical features from raw pixel data, eliminating the need for manual feature extraction.

Recent advances in attention mechanisms have further improved model performance by focusing on relevant regions of interest [7]. These mechanisms allow models to prioritize clinically important features while ignoring irrelevant background information.

The integration of multi-scale processing has enabled better handling of varying anatomical structures and pathologies [8]."""
    
    # External references
    MockExternalRef = mock_external_reference()
    external_refs = [
        MockExternalRef(
            citation_number=13,
            title="Vision Transformers for Medical Image Recognition",
            authors=["Dosovitskiy, A.", "Beyer, L.", "Kolesnikov, A."],
            year=2023,
            venue="Nature Medicine",
            abstract="We apply vision transformers to medical image recognition tasks..."
        ),
        MockExternalRef(
            citation_number=14,
            title="Attention Guided CNN for Medical Image Analysis",
            authors=["Wang, X.", "Li, Y.", "Zhang, M."],
            year=2024,
            venue="IEEE TMI",
            abstract="A novel attention mechanism that guides CNNs to focus on clinically relevant regions..."
        ),
        MockExternalRef(
            citation_number=15,
            title="Multi-Scale Deep Learning for Medical Diagnosis",
            authors=["Chen, L.", "Liu, H.", "Patel, R."],
            year=2023,
            venue="Medical Image Analysis",
            abstract="Multi-scale processing architecture for improved medical diagnosis..."
        )
    ]
    
    print("\n📝 Test section:")
    print("-" * 40)
    print(test_section[:300] + "...")
    print("-" * 40)
    
    # Test with Gemma 3 27B
    print("="*60)
    print("TESTING WITH GEMMA 3 27B (LOCAL)")
    print("="*60)
    
    # Build citation context
    citation_context = "\nAVAILABLE CITATIONS:\n"
    for ref in external_refs:
        citation_context += f"[{ref.citation_number}] {ref.title} ({ref.year})\n"
    
    # Create prompt
    system_msg = """You are an expert academic writer. Your task is to enhance a section by adding citations in the correct locations.

CRITICAL RULES:
1. PRESERVE all existing citations exactly as they appear
2. Add new citations based on content relevance
3. Place citations immediately after the claim they support
4. Use IEEE format: [number]
5. Do not invent citation numbers
6. Keep the section structure unchanged
7. DO NOT add titles or headings - only enhance the existing content with citations
8. NEVER EVER add new paragraphs or sentences - only add citations to existing text

Return ONLY the enhanced content (WITHOUT the heading)."""
    
    prompt = f"""Enhance this section with smart citation placement:

SECTION CONTENT:
{test_section}

{citation_context}

CRITICAL REQUIREMENTS:
- You MUST add at least one citation from the available citations list
- Add citations where they naturally support the content
- Match citation type to content type
- Preserve all existing citations
- Output ONLY the enhanced content (WITHOUT the heading)
- Do NOT include "## 2. Deep Learning Revolution" in your response
- Start your response directly with the content text
- NEVER add new paragraphs, sentences, or words
- ONLY add [number] citations to existing text

EXAMPLE OUTPUT FORMAT:
[First paragraph of EXISTING content with citations like [13] added...]
[Second paragraph of EXISTING content with citations like [14] added...]"""
    
    print("\n🔄 Calling Ollama API...")
    start_time = time.time()
    
    try:
        enhanced = call_ollama_simple(prompt, model="gemma3:27b", system=system_msg)
        
        elapsed = time.time() - start_time
        print("✅ Response received in {:.1f} seconds".format(elapsed))
        
        # Analyze results
        original_citations = set(re.findall(r'\[(\d+)\]', test_section))
        enhanced_citations = set(re.findall(r'\[(\d+)\]', enhanced))
        new_citations = enhanced_citations - original_citations
        external_numbers = {ref.citation_number for ref in external_refs}
        external_integrated = new_citations & external_numbers
        
        print("\n📊 Analysis:")
        print("  Original citations: {}".format(sorted(original_citations)))
        print("  Enhanced citations: {}".format(sorted(enhanced_citations)))
        print("  New citations added: {}".format(sorted(new_citations)))
        print("  External integrated: {}".format(sorted(external_integrated)))
        
        integration_rate = len(external_integrated) / len(external_numbers) * 100
        print("  Integration rate: {:.1f}%".format(integration_rate))
        
        # Check if external citations are in the text (not just new)
        all_external_in_text = external_numbers & enhanced_citations
        actual_integration_rate = len(all_external_in_text) / len(external_numbers) * 100
        print("  Actual external citations in text: {}".format(sorted(all_external_in_text)))
        print("  Actual integration rate: {:.1f}%".format(actual_integration_rate))
        
        print("\n📝 Enhanced section:")
        print("-" * 40)
        print(enhanced)
        print("-" * 40)
        
        # Check 60% threshold
        if actual_integration_rate >= 60:
            print("\n✅ PASSED 60% threshold!")
        else:
            print("\n❌ FAILED 60% threshold (need ≥60%)")
            
    except Exception as e:
        print("\n❌ ERROR: {}".format(str(e)))
    
    # Test with Qwen 3 8B
    print("\n" + "="*60)
    print("TESTING WITH QWEN 3 8B (LOCAL)")
    print("="*60)
    
    print("\n🔄 Calling Ollama API...")
    start_time = time.time()
    
    try:
        enhanced = call_ollama_simple(prompt, model="qwen3:8b", system=system_msg)
        
        elapsed = time.time() - start_time
        print("✅ Response received in {:.1f} seconds".format(elapsed))
        
        # Analyze results
        enhanced_citations = set(re.findall(r'\[(\d+)\]', enhanced))
        new_citations = enhanced_citations - original_citations
        external_integrated = new_citations & external_numbers
        
        print("\n📊 Analysis:")
        print("  Original citations: {}".format(sorted(original_citations)))
        print("  Enhanced citations: {}".format(sorted(enhanced_citations)))
        print("  New citations added: {}".format(sorted(new_citations)))
        print("  External integrated: {}".format(sorted(external_integrated)))
        
        integration_rate = len(external_integrated) / len(external_numbers) * 100
        
        # Check if external citations are in the text (not just new)
        all_external_in_text = external_numbers & enhanced_citations
        actual_integration_rate = len(all_external_in_text) / len(external_numbers) * 100
        print("  Actual external citations in text: {}".format(sorted(all_external_in_text)))
        print("  Actual integration rate: {:.1f}%".format(actual_integration_rate))
        
        print("\n📝 Enhanced section:")
        print("-" * 40)
        print(enhanced)
        print("-" * 40)
        
        # Check 60% threshold
        if actual_integration_rate >= 60:
            print("\n✅ PASSED 60% threshold!")
        else:
            print("\n❌ FAILED 60% threshold (need ≥60%)")
            
    except Exception as e:
        print("\n❌ ERROR: {}".format(str(e)))


def test_unified_bibliography():
    """Test Step 4: Unified bibliography generation."""
    
    print("\n\n" + "="*60)
    print("TESTING STEP 4: UNIFIED BIBLIOGRAPHY")
    print("="*60)
    
    # Simulate after integration
    MockExternalRef = mock_external_reference()
    
    # Internal references (local)
    internal_refs = {
        1: "Smith et al., \"Medical Image Analysis with Deep Learning,\" Nature, 2023.",
        2: "Johnson et al., \"CNN Architectures for Healthcare,\" IEEE TMI, 2023.",
        3: "Brown et al., \"Attention in Medical Imaging,\" Medical Image Analysis, 2024.",
    }
    
    # External references
    external_refs = [
        MockExternalRef(
            citation_number=13,
            title="Vision Transformers for Medical Image Recognition",
            authors=["Dosovitskiy, A.", "Beyer, L.", "Kolesnikov, A."],
            year=2023,
            venue="Nature Medicine",
            abstract="..."
        ),
        MockExternalRef(
            citation_number=14,
            title="Attention Guided CNN for Medical Image Analysis",
            authors=["Wang, X.", "Li, Y.", "Zhang, M."],
            year=2024,
            venue="IEEE TMI",
            abstract="..."
        ),
    ]
    
    # Citations found in enhanced article
    cited_numbers = [1, 2, 3, 13, 14]  # All references were cited
    
    print("\n📚 Building unified bibliography from {} citations...".format(len(cited_numbers)))
    
    # Build unified list
    unified_refs = []
    old_to_new = {}
    
    for new_num, old_num in enumerate(sorted(cited_numbers), start=1):
        old_to_new[old_num] = new_num
        
        if old_num in internal_refs:
            # Local reference
            ref_text = "[{}] {}".format(new_num, internal_refs[old_num])
            unified_refs.append(ref_text)
        else:
            # External reference
            ext_ref = next((r for r in external_refs if r.citation_number == old_num), None)
            if ext_ref:
                ref_text = ext_ref.to_ieee_format()
                ref_text = ref_text.replace("[{}]".format(old_num), "[{}]".format(new_num), 1)
                unified_refs.append(ref_text)
    
    print("\n📋 Unified Reference List:")
    print("-" * 60)
    for ref in unified_refs:
        print(ref)
    
    print("\n✅ Unified bibliography complete!")
    print("   Total references: {}".format(len(unified_refs)))
    print("   Local: {}".format(len(internal_refs)))
    print("   External: {}".format(len(external_refs)))
    
    # Show citation mapping
    print("\n📊 Citation number mapping:")
    for old, new in sorted(old_to_new.items()):
        ref_type = "Local" if old in internal_refs else "External"
        print("   [{}] → [{}] ({})".format(old, new, ref_type))


if __name__ == "__main__":
    print("🧪 Starting Simplified External Reference Integration Test")
    print("This test will:")
    print("  1. Test citation integration with local LLMs")
    print("  2. Measure integration success rates")
    print("  3. Verify unified bibliography generation")
    print()
    
    # Run tests
    test_simple_integration()
    test_unified_bibliography()
    
    print("\n\n🎉 All tests completed!")
    print("\n💡 Next steps:")
    print("  1. Run the full test in the Streamlit app")
    print("  2. Check if Step 4 shows the unified bibliography")
    print("  3. Verify the 60% threshold validation works")
