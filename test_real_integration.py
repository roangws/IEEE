#!/usr/bin/env python3
"""
Test with actual LLM integration
"""

import subprocess
import json
import re
import time


def call_ollama_simple(prompt, model="gemma3:27b", system=None):
    """Simple Ollama API call."""
    cmd = ["curl", "http://localhost:11434/api/generate", 
           "-H", "Content-Type: application/json",
           "-d", json.dumps({
               "model": model,
               "prompt": prompt,
               "system": system or "You are a helpful assistant.",
               "stream": False
           })]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Ollama API error: {result.stderr}")
    
    response = json.loads(result.stdout)
    return response.get("response", "")


def test_real_integration():
    """Test with actual LLM to ensure integration works."""
    
    print("="*70)
    print("REAL LLM INTEGRATION TEST")
    print("="*70)
    
    # Test section with internal citations
    test_section = """## 2. Deep Learning Revolution

The introduction of deep learning, particularly convolutional neural networks (CNNs), has transformed medical image analysis [6]. CNNs can automatically learn hierarchical features from raw pixel data, eliminating the need for manual feature extraction.

Recent advances in attention mechanisms have further improved model performance by focusing on relevant regions of interest [7]. These mechanisms allow models to prioritize clinically important features while ignoring irrelevant background information.

The integration of multi-scale processing has enabled better handling of varying anatomical structures and pathologies [8]."""
    
    # External references
    external_refs = [
        {"number": 13, "title": "Vision Transformers in Medical Imaging", "year": 2023},
        {"number": 14, "title": "Self-Supervised Learning for Medical Images", "year": 2024},
        {"number": 15, "title": "Federated Learning in Healthcare", "year": 2023}
    ]
    
    print("\n📝 Test Section with Internal Citations:")
    print("-" * 70)
    print(test_section)
    
    print("\n🌐 External References to Integrate:")
    for ref in external_refs:
        print(f"   [{ref['number']}] {ref['title']} ({ref['year']})")
    
    # Build prompt with explicit citation numbers
    citation_context = "\nAVAILABLE CITATIONS:\n"
    for ref in external_refs:
        citation_context += f"[{ref['number']}] {ref['title']} ({ref['year']})\n"
    
    system_msg = """You are an expert academic writer. CRITICAL: You MUST use ONLY the exact citation numbers provided in the AVAILABLE CITATIONS list. Do NOT invent or use any other numbers."""
    
    prompt = f"""Enhance this section with citations from the AVAILABLE CITATIONS list:

{test_section}

{citation_context}

CRITICAL: You MUST add citations using ONLY these numbers: [13], [14], [15]
Add citations where they naturally support the content.
Return the enhanced text with citations added."""

    print("\n🔄 Testing with Gemma 3 27B...")
    start_time = time.time()
    
    try:
        enhanced = call_ollama_simple(prompt, model="gemma3:27b", system=system_msg)
        elapsed = time.time() - start_time
        
        print(f"✅ Response received in {elapsed:.1f} seconds")
        
        # Analyze results
        original_citations = set(re.findall(r'\[(\d+)\]', test_section))
        enhanced_citations = set(re.findall(r'\[(\d+)\]', enhanced))
        new_citations = enhanced_citations - original_citations
        external_numbers = {str(ref['number']) for ref in external_refs}
        
        print("\n📊 Results:")
        print(f"  Original citations: {sorted(original_citations)}")
        print(f"  Enhanced citations: {sorted(enhanced_citations)}")
        print(f"  New citations added: {sorted(new_citations)}")
        
        # Check if external citations are present
        all_external_in_text = external_numbers & enhanced_citations
        integration_rate = len(all_external_in_text) / len(external_numbers) * 100
        
        print(f"\n  External citations in text: {sorted(all_external_in_text)}")
        print(f"  Integration rate: {integration_rate:.1f}%")
        
        print("\n📝 Enhanced Section:")
        print("-" * 70)
        print(enhanced)
        
        # Show where citations were added
        print("\n📍 Citation Analysis:")
        print("-" * 70)
        lines = enhanced.split('\n')
        for i, line in enumerate(lines):
            citations = set(re.findall(r'\[(\d+)\]', line))
            if citations:
                print(f"Line {i+1}: {line[:80]}...")
                print(f"  Citations: {sorted(citations)}")
                for cit in citations:
                    if cit in external_numbers:
                        ref = next(r for r in external_refs if str(r['number']) == cit)
                        print(f"    → [{cit}] is EXTERNAL: {ref['title']}")
        
        # Check 60% threshold
        if integration_rate >= 60:
            print(f"\n✅ SUCCESS: Integration rate {integration_rate:.1f}% meets 60% threshold!")
        else:
            print(f"\n⚠️  WARNING: Integration rate {integration_rate:.1f}% below 60% threshold")
            print("    (This may be due to LLM not following instructions perfectly)")
            print("    The fallback validation would insert missing citations automatically")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    test_real_integration()
